#!/usr/bin/env python3
"""
Persistent DSS Session Manager
Keeps a single DSS session alive for multiple variable operations
"""

import subprocess
import threading
import queue
import time
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class PersistentDSSSession:
    """Manages a persistent DSS session for continuous variable access"""
    
    def __init__(self, dss_path: str = "/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh"):
        self.dss_path = Path(dss_path)
        self.process = None
        self.session_active = False
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.worker_thread = None
        
    def start_session(self, ccxml_path: str, binary_path: Optional[str] = None) -> bool:
        """Start persistent DSS session"""
        
        # Create comprehensive DSS script that stays alive
        js_script = f"""
// Persistent DSS Session Script
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);
importPackage(java.io);

function main() {{
    print("=== Starting Persistent DSS Session ===");
    
    var debugSession = null;
    var connected = false;
    
    try {{
        // Connect to target
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{ccxml_path}");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Load binary if provided
        {"debugSession.memory.loadProgram('" + binary_path + "');" if binary_path else ""}
        
        // Initialize target
        debugSession.target.runAsynch();
        Thread.sleep(2000);
        debugSession.target.halt();
        
        connected = true;
        print("SESSION_READY");
        
        // Command processing loop
        var stdin = new java.io.BufferedReader(new java.io.InputStreamReader(java.lang.System.in));
        var running = true;
        
        while (running) {{
            try {{
                // Check for command input (non-blocking)
                if (stdin.ready()) {{
                    var command = stdin.readLine();
                    
                    if (command === null || command === "QUIT") {{
                        running = false;
                        break;
                    }}
                    
                    var parts = command.split(":");
                    var action = parts[0];
                    
                    if (action === "READ") {{
                        var varName = parts[1];
                        try {{
                            // Try expression evaluation first
                            var value = debugSession.expression.evaluate(varName);
                            print("RESULT:" + varName + "=" + value);
                        }} catch (e) {{
                            print("ERROR:" + varName + ":" + e.message);
                        }}
                    }}
                    else if (action === "READ_MEM") {{
                        var address = parseInt(parts[1], 16);
                        var size = parts[2] || "32";
                        try {{
                            var value = debugSession.memory.readData(0, address, parseInt(size));
                            print("MEM_RESULT:0x" + address.toString(16) + "=" + value);
                        }} catch (e) {{
                            print("MEM_ERROR:0x" + address.toString(16) + ":" + e.message);
                        }}
                    }}
                    else if (action === "WRITE") {{
                        var varName = parts[1];
                        var value = parts[2];
                        try {{
                            debugSession.expression.evaluate(varName + " = " + value);
                            print("WRITE_SUCCESS:" + varName + "=" + value);
                        }} catch (e) {{
                            print("WRITE_ERROR:" + varName + ":" + e.message);
                        }}
                    }}
                    else if (action === "STATUS") {{
                        var isConnected = debugSession.target.isConnected();
                        var isRunning = false;
                        try {{
                            isRunning = debugSession.target.isRunning();
                        }} catch (e) {{
                            // isRunning might not be available
                        }}
                        print("STATUS:connected=" + isConnected + ":running=" + isRunning);
                    }}
                    else if (action === "PING") {{
                        print("PONG");
                    }}
                }} else {{
                    // Small delay to prevent busy waiting
                    Thread.sleep(50);
                }}
                
            }} catch (e) {{
                print("COMMAND_ERROR:" + e.message);
            }}
        }}
        
        print("SESSION_ENDING");
        
    }} catch (error) {{
        print("SESSION_ERROR:" + error.message);
    }} finally {{
        if (debugSession && connected) {{
            try {{
                debugSession.target.disconnect();
            }} catch (e) {{
                // Ignore cleanup errors
            }}
        }}
        print("SESSION_CLOSED");
    }}
}}

main();
"""
        
        # Save the persistent script
        script_path = Path("/tmp/persistent_dss_session.js")
        script_path.write_text(js_script)
        
        try:
            # Start DSS process with stdin/stdout pipes
            self.process = subprocess.Popen(
                [str(self.dss_path), str(script_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Start worker thread to handle I/O
            self.worker_thread = threading.Thread(target=self._session_worker, daemon=True)
            self.worker_thread.start()
            
            # Wait for session ready
            timeout = 30
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response = self.response_queue.get(timeout=1)
                    if response == "SESSION_READY":
                        self.session_active = True
                        logger.info("✅ Persistent DSS session started")
                        return True
                    elif "ERROR" in response:
                        logger.error(f"Session start error: {response}")
                        break
                except queue.Empty:
                    continue
            
            logger.error("Session startup timeout")
            self.stop_session()
            return False
            
        except Exception as e:
            logger.error(f"Failed to start persistent session: {e}")
            return False
    
    def _session_worker(self):
        """Worker thread to handle DSS I/O"""
        while self.process and self.process.poll() is None:
            try:
                # Handle outgoing commands
                try:
                    command = self.command_queue.get(timeout=0.1)
                    if command:
                        self.process.stdin.write(command + '\n')
                        self.process.stdin.flush()
                except queue.Empty:
                    pass
                
                # Handle incoming responses
                if self.process.stdout.readable():
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:
                            self.response_queue.put(line)
                            
            except Exception as e:
                logger.error(f"Session worker error: {e}")
                break
        
        logger.info("Session worker thread ended")
    
    def send_command(self, command: str, timeout: float = 5.0) -> Optional[str]:
        """Send command and wait for response"""
        if not self.session_active:
            return None
        
        try:
            # Send command
            self.command_queue.put(command)
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = self.response_queue.get(timeout=0.5)
                    
                    # Check if this is our response
                    if (command.startswith("READ:") and response.startswith("RESULT:")) or \
                       (command.startswith("WRITE:") and response.startswith("WRITE_")) or \
                       (command.startswith("STATUS") and response.startswith("STATUS:")) or \
                       (command == "PING" and response == "PONG"):
                        return response
                    
                    # Not our response, put back and continue
                    self.response_queue.put(response)
                    
                except queue.Empty:
                    continue
            
            logger.warning(f"Command timeout: {command}")
            return None
            
        except Exception as e:
            logger.error(f"Command error: {e}")
            return None
    
    def read_variable(self, var_name: str) -> Optional[float]:
        """Read a variable using persistent session"""
        if not self.session_active:
            return None
        
        response = self.send_command(f"READ:{var_name}")
        
        if response and response.startswith("RESULT:"):
            # Format: RESULT:var_name=value
            try:
                result_part = response[7:]  # Remove "RESULT:"
                if '=' in result_part:
                    _, value_str = result_part.split('=', 1)
                    return float(value_str)
            except (ValueError, IndexError):
                pass
        
        return None
    
    def read_memory(self, address: int, size: int = 32) -> Optional[int]:
        """Read memory using persistent session"""
        if not self.session_active:
            return None
        
        response = self.send_command(f"READ_MEM:{address:x}:{size}")
        
        if response and response.startswith("MEM_RESULT:"):
            try:
                # Format: MEM_RESULT:0xaddress=value
                result_part = response[11:]  # Remove "MEM_RESULT:"
                if '=' in result_part:
                    _, value_str = result_part.split('=', 1)
                    return int(float(value_str))
            except (ValueError, IndexError):
                pass
        
        return None
    
    def write_variable(self, var_name: str, value: Any) -> bool:
        """Write a variable using persistent session"""
        if not self.session_active:
            return False
        
        response = self.send_command(f"WRITE:{var_name}:{value}")
        
        return response and response.startswith("WRITE_SUCCESS:")
    
    def get_status(self) -> Dict[str, bool]:
        """Get session status"""
        if not self.session_active:
            return {'connected': False, 'running': False}
        
        response = self.send_command("STATUS")
        
        if response and response.startswith("STATUS:"):
            # Format: STATUS:connected=true:running=false
            status = {'connected': False, 'running': False}
            parts = response[7:].split(':')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=')
                    status[key] = value.lower() == 'true'
            return status
        
        return {'connected': False, 'running': False}
    
    def ping(self) -> bool:
        """Test if session is responsive"""
        response = self.send_command("PING", timeout=2.0)
        return response == "PONG"
    
    def stop_session(self):
        """Stop persistent session"""
        if self.session_active:
            self.command_queue.put("QUIT")
            self.session_active = False
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except:
                pass
            self.process = None
        
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        
        logger.info("Persistent DSS session stopped")

# Test the persistent session
def test_persistent_session():
    """Test the persistent session approach"""
    print("Testing Persistent DSS Session")
    print("==============================")
    
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    session = PersistentDSSSession()
    
    # Start session
    print("Starting persistent session...")
    if not session.start_session(str(ccxml_path), str(binary_path)):
        print("❌ Failed to start persistent session")
        return
    
    print("✅ Persistent session started")
    
    # Test ping
    print("\nTesting ping...")
    if session.ping():
        print("✅ Session responding to ping")
    else:
        print("❌ Session not responding")
    
    # Test status
    print("\nTesting status...")
    status = session.get_status()
    print(f"Connected: {status.get('connected')}")
    print(f"Running: {status.get('running')}")
    
    # Test variable reads
    print("\nTesting variable reads...")
    test_vars = ['motorVars_M1', 'debug_bypass', 'motorHandle_M1']
    
    for var in test_vars:
        print(f"Reading {var}...")
        value = session.read_variable(var)
        if value is not None:
            print(f"  ✅ {var} = {value}")
        else:
            print(f"  ❌ Failed to read {var}")
    
    # Test memory reads
    print("\nTesting memory reads...")
    debug_bypass_addr = 0xd262
    
    for i in range(4):  # Read 4 consecutive addresses
        addr = debug_bypass_addr + (i * 4)
        value = session.read_memory(addr)
        if value is not None:
            print(f"  ✅ Memory 0x{addr:04x} = {value}")
        else:
            print(f"  ❌ Failed to read memory 0x{addr:04x}")
    
    # Test multiple rapid reads
    print("\nTesting rapid multiple reads...")
    for i in range(10):
        value = session.read_variable('motorVars_M1')
        if value is not None:
            print(f"  Read {i+1}: motorVars_M1 = {value}")
        else:
            print(f"  Read {i+1}: Failed")
        time.sleep(0.1)
    
    # Clean up
    print("\nStopping session...")
    session.stop_session()
    print("✅ Test complete")

if __name__ == "__main__":
    test_persistent_session()