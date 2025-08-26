#!/usr/bin/env python3
"""
Persistent Session XDS110 Connector - Keeps DSS session open for fast variable reads
Much faster than single-session approach since it doesn't reconnect every time
"""

import os
import subprocess
import tempfile
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import our MAP parser
import sys
sys.path.append(str(Path(__file__).parent.parent / "generic"))
from map_parser_poc import MapFileParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SessionState:
    connected: bool = False
    target_loaded: bool = False
    last_read_time: float = 0
    session_start_time: float = 0
    read_count: int = 0
    error_count: int = 0

class PersistentSessionXDS110:
    """
    Persistent XDS110 connector that maintains a long-running DSS session
    for fast variable reads without reconnection overhead
    """
    
    def __init__(self, ccxml_path: str, map_file: str, binary_path: Optional[str] = None):
        self.ccxml_path = ccxml_path
        self.map_file = map_file 
        self.binary_path = binary_path
        
        # Parse MAP file for available variables
        self.map_parser = MapFileParser(map_file)
        parsed_data = self.map_parser.parse()
        self.available_variables = parsed_data.get('symbols', {})
        logger.info(f"Loaded {len(self.available_variables)} variables from MAP file")
        
        # DSS session management
        self.dss_process = None
        self.session_active = False
        self.session_lock = threading.Lock()
        self.session_state = SessionState()
        
        # Communication files
        self.temp_dir = tempfile.mkdtemp(prefix="xds110_persistent_")
        self.js_script_file = Path(self.temp_dir) / "persistent_session.js"
        self.command_file = Path(self.temp_dir) / "commands.txt"
        self.response_file = Path(self.temp_dir) / "responses.txt"
        self.control_file = Path(self.temp_dir) / "control.txt"
        
        logger.info(f"PersistentSessionXDS110 initialized with {len(self.available_variables)} variables")
    
    def get_available_variables(self) -> List[str]:
        """Get list of available variables from MAP file"""
        return list(self.available_variables.keys())
    
    def _create_persistent_js_script(self) -> str:
        """Create JavaScript for persistent DSS session"""
        return f"""
// Persistent DSS Session Script
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.java.io);

print("=== Persistent DSS Session Starting ===");

var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
ds.setConfig("{self.ccxml_path}");

var debugSession;
var sessionActive = false;
var targetLoaded = false;

// File paths for communication
var commandFile = "{self.command_file}";
var responseFile = "{self.response_file}"; 
var controlFile = "{self.control_file}";

function initializeTarget() {{
    try {{
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Load program if binary provided
        {f'debugSession.memory.loadProgram("{self.binary_path}");' if self.binary_path else '// No binary to load'}
        
        debugSession.target.halt();
        sessionActive = true;
        targetLoaded = true;
        
        print("TARGET_INITIALIZED");
        return true;
    }} catch (e) {{
        print("INIT_ERROR:" + e.toString());
        return false;
    }}
}}

function readVariable(varName) {{
    try {{
        if (!sessionActive || !debugSession) {{
            return "ERROR:Session not active";
        }}
        
        var value = debugSession.expression.evaluate(varName);
        return "VALUE:" + varName + "=" + value;
    }} catch (e) {{
        return "ERROR:" + varName + ":" + e.toString();
    }}
}}

function writeResponse(response) {{
    try {{
        var writer = new PrintWriter(new FileWriter(responseFile, true));
        writer.println(response);
        writer.close();
    }} catch (e) {{
        print("WRITE_ERROR:" + e.toString());
    }}
}}

function readCommands() {{
    try {{
        var file = new File(commandFile);
        if (!file.exists()) {{
            return null;
        }}
        
        var reader = new BufferedReader(new FileReader(commandFile));
        var commands = [];
        var line;
        while ((line = reader.readLine()) != null) {{
            commands.push(line.trim());
        }}
        reader.close();
        
        // Clear command file after reading
        new PrintWriter(new FileWriter(commandFile)).close();
        
        return commands;
    }} catch (e) {{
        print("READ_ERROR:" + e.toString());
        return null;
    }}
}}

function shouldExit() {{
    try {{
        var file = new File(controlFile);
        if (file.exists()) {{
            var reader = new BufferedReader(new FileReader(controlFile));
            var control = reader.readLine();
            reader.close();
            return control && control.trim() === "EXIT";
        }}
    }} catch (e) {{
        // Continue if can't read control file
    }}
    return false;
}}

// Initialize the target
if (!initializeTarget()) {{
    print("FATAL_ERROR:Could not initialize target");
    quit(1);
}}

// Main command processing loop
print("READY_FOR_COMMANDS");
while (!shouldExit()) {{
    try {{
        var commands = readCommands();
        if (commands && commands.length > 0) {{
            for (var i = 0; i < commands.length; i++) {{
                var cmd = commands[i];
                if (cmd.startsWith("READ:")) {{
                    var varName = cmd.substring(5);
                    var result = readVariable(varName);
                    writeResponse(result);
                }} else if (cmd === "PING") {{
                    writeResponse("PONG");
                }} else if (cmd === "STATUS") {{
                    writeResponse("STATUS:active=" + sessionActive + ",loaded=" + targetLoaded);
                }}
            }}
        }}
        
        // Small delay to prevent busy waiting
        java.lang.Thread.sleep(50);
        
    }} catch (e) {{
        print("LOOP_ERROR:" + e.toString());
        writeResponse("LOOP_ERROR:" + e.toString());
    }}
}}

print("SESSION_ENDING");
if (debugSession && sessionActive) {{
    debugSession.terminate();
}}
print("SESSION_CLOSED");
"""
    
    def start_persistent_session(self) -> bool:
        """Start the persistent DSS session"""
        with self.session_lock:
            if self.session_active:
                logger.warning("Session already active")
                return True
            
            try:
                # Create the JavaScript file
                with open(self.js_script_file, 'w') as f:
                    f.write(self._create_persistent_js_script())
                
                # Clear communication files
                self.command_file.touch()
                self.response_file.touch()
                
                # Start DSS process
                dss_cmd = [
                    "/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh",
                    str(self.js_script_file)
                ]
                
                logger.info("Starting persistent DSS session...")
                self.dss_process = subprocess.Popen(
                    dss_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=self.temp_dir
                )
                
                # Wait for session to be ready
                timeout = 30  # 30 seconds
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if self.dss_process.poll() is not None:
                        # Process terminated
                        stdout, stderr = self.dss_process.communicate()
                        logger.error(f"DSS process terminated early: {stderr}")
                        return False
                    
                    # Check for "READY_FOR_COMMANDS" in stdout
                    # We'll use a simple file-based check instead
                    if self._send_command("PING"):
                        response = self._read_response(timeout=2)
                        if response and "PONG" in response:
                            self.session_active = True
                            self.session_state.connected = True
                            self.session_state.session_start_time = time.time()
                            logger.info("✅ Persistent DSS session ready")
                            return True
                    
                    time.sleep(0.5)
                
                logger.error("Timeout waiting for DSS session to be ready")
                self.stop_persistent_session()
                return False
                
            except Exception as e:
                logger.error(f"Failed to start persistent session: {e}")
                return False
    
    def _send_command(self, command: str) -> bool:
        """Send a command to the persistent session"""
        try:
            with open(self.command_file, 'a') as f:
                f.write(f"{command}\\n")
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def _read_response(self, timeout: float = 5.0) -> Optional[str]:
        """Read response from the persistent session"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if self.response_file.exists() and self.response_file.stat().st_size > 0:
                    with open(self.response_file, 'r') as f:
                        content = f.read().strip()
                    
                    if content:
                        # Clear response file
                        with open(self.response_file, 'w') as f:
                            pass
                        return content
                        
            except Exception as e:
                logger.debug(f"Error reading response: {e}")
            
            time.sleep(0.1)
        
        return None
    
    def read_variable(self, variable_name: str, timeout: float = 5.0) -> Optional[Any]:
        """Read a single variable using the persistent session"""
        if not self.session_active:
            logger.error("Session not active")
            return None
        
        with self.session_lock:
            try:
                # Send read command
                if not self._send_command(f"READ:{variable_name}"):
                    return None
                
                # Wait for response
                response = self._read_response(timeout)
                if not response:
                    logger.warning(f"Timeout reading {variable_name}")
                    self.session_state.error_count += 1
                    return None
                
                # Parse response
                if response.startswith("VALUE:"):
                    # Extract value from "VALUE:varname=value"
                    try:
                        equals_pos = response.find('=')
                        if equals_pos != -1:
                            value_str = response[equals_pos + 1:].strip()
                            # Try to convert to appropriate type
                            if value_str.lower() in ['null', 'undefined']:
                                return None
                            try:
                                # Try integer first
                                if '.' not in value_str:
                                    return int(value_str)
                                else:
                                    return float(value_str)
                            except ValueError:
                                return value_str
                    except Exception as e:
                        logger.debug(f"Error parsing value: {e}")
                        return response
                
                elif response.startswith("ERROR:"):
                    error_msg = response[6:]
                    logger.debug(f"Variable read error for {variable_name}: {error_msg}")
                    self.session_state.error_count += 1
                    return None
                
                self.session_state.read_count += 1
                self.session_state.last_read_time = time.time()
                return response
                
            except Exception as e:
                logger.error(f"Error reading variable {variable_name}: {e}")
                self.session_state.error_count += 1
                return None
    
    def read_variables_batch(self, variable_names: List[str], timeout: float = 10.0) -> Dict[str, Any]:
        """Read multiple variables using the persistent session"""
        results = {}
        
        for var_name in variable_names:
            value = self.read_variable(var_name, timeout=timeout / len(variable_names))
            results[var_name] = value
        
        return results
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get status of the persistent session"""
        return {
            'active': self.session_active,
            'connected': self.session_state.connected,
            'target_loaded': self.session_state.target_loaded,
            'read_count': self.session_state.read_count,
            'error_count': self.session_state.error_count,
            'uptime': time.time() - self.session_state.session_start_time if self.session_state.session_start_time > 0 else 0,
            'last_read': self.session_state.last_read_time
        }
    
    def stop_persistent_session(self):
        """Stop the persistent DSS session"""
        with self.session_lock:
            if not self.session_active:
                return
            
            try:
                # Send exit command
                with open(self.control_file, 'w') as f:
                    f.write("EXIT\\n")
                
                # Wait for process to terminate
                if self.dss_process:
                    try:
                        self.dss_process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        logger.warning("DSS process didn't terminate gracefully, killing it")
                        self.dss_process.kill()
                        self.dss_process.wait()
                
                self.session_active = False
                self.session_state = SessionState()
                logger.info("Persistent DSS session stopped")
                
            except Exception as e:
                logger.error(f"Error stopping session: {e}")
    
    def disconnect(self):
        """Disconnect and cleanup"""
        logger.info("Disconnecting persistent session connector...")
        
        self.stop_persistent_session()
        
        # Cleanup temp files
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Could not cleanup temp directory: {e}")
        
        logger.info("Persistent session connector disconnected")


# Test function
def test_persistent_connector():
    """Test the persistent session connector"""
    print("Testing Persistent Session XDS110 Connector")
    print("=" * 50)
    
    # File paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    # Create connector
    connector = PersistentSessionXDS110(
        str(ccxml_path),
        str(map_path),
        str(binary_path)
    )
    
    try:
        print("1. Starting persistent session...")
        if connector.start_persistent_session():
            print("✅ Session started successfully")
            
            # Test status
            status = connector.get_session_status()
            print(f"Session status: {status}")
            
            # Test single variable read
            print("2. Testing single variable read...")
            test_vars = ['motorVars_M1', 'debug_bypass', 'systemVars']
            
            for var in test_vars:
                if var in connector.get_available_variables():
                    print(f"Reading {var}...")
                    start_time = time.time()
                    value = connector.read_variable(var)
                    read_time = time.time() - start_time
                    print(f"  {var} = {value} (took {read_time:.3f}s)")
                else:
                    print(f"  {var} not available in MAP")
            
            # Test batch read
            print("3. Testing batch read...")
            available_test_vars = [v for v in test_vars if v in connector.get_available_variables()]
            if available_test_vars:
                start_time = time.time()
                results = connector.read_variables_batch(available_test_vars)
                batch_time = time.time() - start_time
                print(f"Batch read took {batch_time:.3f}s:")
                for var, val in results.items():
                    print(f"  {var} = {val}")
            
            # Test speed - multiple reads
            print("4. Speed test - 10 rapid reads...")
            if available_test_vars:
                test_var = available_test_vars[0]
                start_time = time.time()
                for i in range(10):
                    value = connector.read_variable(test_var)
                    print(f"  Read {i+1}: {test_var} = {value}")
                speed_test_time = time.time() - start_time
                print(f"10 reads took {speed_test_time:.3f}s (avg: {speed_test_time/10:.3f}s per read)")
            
            # Final status
            final_status = connector.get_session_status()
            print(f"Final status: {final_status}")
            
        else:
            print("❌ Failed to start session")
    
    finally:
        print("5. Cleaning up...")
        connector.disconnect()
        print("✅ Test completed")

if __name__ == "__main__":
    test_persistent_connector()