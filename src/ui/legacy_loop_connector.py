#!/usr/bin/env python3
"""
Legacy Loop Connector - Uses working legacy DSS script pattern in monitoring loop
Calls the proven legacy scripts repeatedly to get continuous real data
"""

import subprocess
import time
import threading
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import deque
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LegacyLoopConnector:
    """
    Connector that uses the proven legacy DSS script pattern for continuous monitoring
    Each monitoring cycle runs a complete DSS script (connect + read + disconnect)
    """
    
    def __init__(self, ccxml_path: str, map_file: str, binary_path: str, max_history: int = 1000):
        self.ccxml_path = Path(ccxml_path)
        self.map_file = Path(map_file)
        self.binary_path = Path(binary_path)
        self.dss_path = Path("/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh")
        
        # Validate paths
        for path, name in [(self.ccxml_path, "CCXML"), (self.map_file, "MAP"), (self.binary_path, "Binary")]:
            if not path.exists():
                raise FileNotFoundError(f"{name} file not found: {path}")
        
        if not self.dss_path.exists():
            raise FileNotFoundError(f"DSS not found at {self.dss_path}")
        
        # Data management
        self.max_history = max_history
        self.data_history = {}  # {variable: deque of (timestamp, value)}
        self.current_values = {}  # {variable: latest_value}
        self.available_variables = []
        
        # Monitoring
        self.monitoring = False
        self.monitor_thread = None
        self.monitored_variables = []
        self.monitor_rate = 5.0  # Hz
        
        # Parse MAP file for available variables
        self._load_map_symbols()
        
        logger.info(f"LegacyLoopConnector initialized with {len(self.available_variables)} variables")
    
    def _load_map_symbols(self):
        """Load available variables from MAP file"""
        symbols = []
        
        try:
            with open(self.map_file, 'r') as f:
                content = f.read()
            
            # TI MAP format: page_num  hex_address  symbol_name
            symbol_pattern = re.compile(r'^\s*\d+\s+([0-9a-f]+)\s+(\w+)', re.MULTILINE | re.IGNORECASE)
            
            for match in symbol_pattern.finditer(content):
                address_str, name = match.groups()
                symbols.append(name)
            
            self.available_variables = sorted(symbols)
            logger.info(f"Loaded {len(symbols)} variables from MAP file")
            
        except Exception as e:
            logger.error(f"Failed to parse MAP file: {e}")
    
    def create_monitoring_script(self, variables: List[str]) -> str:
        """Create DSS script based on working legacy pattern"""
        
        # Create variable list for the script
        # Handle both simple variables and structured references
        var_list = []
        for var in variables:
            # For structured vars like 'motorVars_M1.motorState', check if base exists
            base_var = var.split('.')[0]
            if base_var in self.available_variables:
                var_list.append(f'"{var}"')  # Use full structured name
        
        if not var_list:
            raise ValueError("No valid variables to monitor")
        
        # Create DSS JavaScript based on proven working legacy script
        js_script = f"""
// Legacy Loop Monitoring Script - Based on working read_motor_vars_v1.js
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {{
    print("=== Legacy Loop Monitor Cycle ===");
    
    var debugSession = null;
    
    try {{
        // Get the Debug Server and connect (EXACT same as working script)
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{self.ccxml_path}");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Load firmware (same as legacy script)
        try {{
            debugSession.memory.loadProgram("{self.binary_path}");
        }} catch (e) {{
            // Firmware may already be loaded
        }}
        
        // Halt target (same as legacy script)
        try {{
            debugSession.target.halt();
        }} catch (e) {{
            // Target may already be halted
        }}
        
        print("TARGET_READY");
        
        // Read all requested variables (using same method as legacy script)
        var variables = [{', '.join(var_list)}];
        
        for (var i = 0; i < variables.length; i++) {{
            try {{
                var value = debugSession.expression.evaluate(variables[i]);
                print("VAR:" + variables[i] + "=" + value);
            }} catch (e) {{
                print("ERR:" + variables[i] + ":" + e.message);
            }}
        }}
        
        print("READING_COMPLETE");
        
    }} catch (e) {{
        print("SCRIPT_ERROR:" + e.message);
    }} finally {{
        // Clean disconnect (same as legacy script)
        if (debugSession != null) {{
            try {{
                debugSession.target.disconnect();
                debugSession.terminate();
            }} catch (e) {{
                // Ignore cleanup errors
            }}
        }}
        print("SESSION_CLOSED");
    }}
}}

main();
"""
        
        return js_script
    
    def run_monitoring_cycle(self, variables: List[str]) -> Dict[str, Any]:
        """Run one monitoring cycle using legacy script pattern"""
        
        try:
            # Create script
            script_content = self.create_monitoring_script(variables)
            
            # Save to temp file
            timestamp = int(time.time() * 1000)
            script_path = Path(f"/tmp/legacy_monitor_{timestamp}.js")
            script_path.write_text(script_content)
            
            # Execute DSS script (same command as working legacy scripts)
            # Use longer timeout since DSS can take time for initialization
            result = subprocess.run(
                [str(self.dss_path), str(script_path)],
                capture_output=True,
                text=True,
                timeout=30  # Increased timeout for DSS initialization
            )
            
            # Parse results (same format as our working single session connector)
            variables_data = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if line.startswith("VAR:"):
                    # Format: VAR:variable_name=value
                    var_part = line[4:]  # Remove "VAR:"
                    if '=' in var_part:
                        var_name, value_str = var_part.split('=', 1)
                        try:
                            value = float(value_str)
                            variables_data[var_name] = value
                        except ValueError:
                            # Handle non-numeric values
                            variables_data[var_name] = value_str
                            
                elif line.startswith("ERR:"):
                    # Format: ERR:variable_name:error_message
                    err_part = line[4:]
                    if ':' in err_part:
                        var_name, error_msg = err_part.split(':', 1)
                        logger.debug(f"Variable read error {var_name}: {error_msg}")
                        variables_data[var_name] = None
                        
                elif "TARGET_READY" in line:
                    logger.debug("Target ready for reading")
                elif "READING_COMPLETE" in line:
                    logger.debug("Variable reading completed")
                elif "SESSION_CLOSED" in line:
                    logger.debug("DSS session closed cleanly")
            
            # Clean up temp script
            try:
                script_path.unlink()
            except:
                pass
            
            # Log stderr warnings
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip() and "SLF4J" not in line and "SEVERE:" in line:
                        logger.debug(f"DSS warning: {line}")
            
            success_count = len([v for v in variables_data.values() if v is not None])
            if success_count > 0:
                logger.info(f"✅ Legacy cycle: {success_count}/{len(variables)} variables read successfully")
            else:
                logger.warning(f"❌ Legacy cycle: No variables read successfully")
                # Log the full output for debugging
                logger.debug("DSS stdout:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.debug(f"  {line}")
            
            return variables_data
            
        except subprocess.TimeoutExpired:
            logger.warning("Legacy monitoring cycle timed out")
            return {}
        except Exception as e:
            logger.error(f"Legacy monitoring cycle error: {e}")
            return {}
    
    def start_monitoring(self, variables: List[str], rate_hz: float = 2.0) -> bool:
        """Start monitoring using legacy script loop"""
        
        if self.monitoring:
            logger.warning("Already monitoring - stopping previous session")
            self.stop_monitoring()
        
        # Validate variables (handle structured variable names)
        valid_variables = []
        for var in variables:
            # For structured vars, check if base variable exists in MAP
            base_var = var.split('.')[0]
            if base_var in self.available_variables:
                valid_variables.append(var)
        if not valid_variables:
            logger.error("No valid variables to monitor")
            return False
        
        # Initialize history storage
        for var in valid_variables:
            if var not in self.data_history:
                self.data_history[var] = deque(maxlen=self.max_history)
        
        self.monitored_variables = valid_variables
        self.monitor_rate = rate_hz
        self.monitoring = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"✅ Started legacy loop monitoring: {len(valid_variables)} variables at {rate_hz:.1f} Hz")
        return True
    
    def _monitor_loop(self):
        """Background monitoring loop using legacy DSS scripts"""
        interval = 1.0 / self.monitor_rate
        
        logger.info(f"Legacy monitor loop starting (interval: {interval:.2f}s)")
        
        cycle_count = 0
        while self.monitoring:
            try:
                start_time = time.time()
                cycle_count += 1
                
                # Run one legacy script cycle
                results = self.run_monitoring_cycle(self.monitored_variables)
                
                if results:
                    timestamp = datetime.now().timestamp()
                    
                    # Update current values and history
                    success_count = 0
                    for var_name, value in results.items():
                        if value is not None:
                            self.current_values[var_name] = value
                            
                            # Add to history
                            if var_name in self.data_history:
                                self.data_history[var_name].append((timestamp, value))
                            success_count += 1
                    
                    logger.info(f"Cycle {cycle_count}: {success_count}/{len(self.monitored_variables)} variables updated")
                else:
                    logger.warning(f"Cycle {cycle_count}: No data returned from legacy script")
                
                # Maintain target rate
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Monitor loop cycle {cycle_count} error: {e}")
                time.sleep(2)  # Error recovery delay
        
        logger.info(f"Legacy monitor loop stopped after {cycle_count} cycles")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
                if self.monitor_thread.is_alive():
                    logger.warning("Monitor thread did not stop cleanly")
            logger.info("Legacy monitoring stopped")
    
    def get_available_variables(self) -> List[str]:
        """Get list of available variables"""
        return list(self.available_variables)
    
    def get_current_data(self) -> Dict[str, float]:
        """Get current values for dashboard"""
        return dict(self.current_values)
    
    def get_variable_history(self, variable: str, duration: Optional[int] = None) -> tuple:
        """Get historical data for plotting"""
        if variable not in self.data_history:
            return [], []
        
        history = list(self.data_history[variable])
        
        # Filter by duration if specified
        if duration and history:
            cutoff = time.time() - duration
            history = [(t, v) for t, v in history if t >= cutoff]
        
        if history:
            timestamps, values = zip(*history)
            return list(timestamps), list(values)
        
        return [], []
    
    def disconnect(self):
        """Disconnect (stop monitoring and clean up)"""
        logger.info("Disconnecting legacy loop connector...")
        
        self.stop_monitoring()
        
        # Clear data
        self.current_values.clear()
        self.data_history.clear()
        self.monitored_variables.clear()
        
        logger.info("Legacy loop connector disconnected")


# Test function
def test_legacy_loop_connector():
    """Test the legacy loop connector"""
    print("Testing Legacy Loop Connector")
    print("=============================")
    
    # File paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    try:
        # Create connector
        connector = LegacyLoopConnector(str(ccxml_path), str(map_path), str(binary_path))
        
        print(f"Available variables: {len(connector.get_available_variables())}")
        
        # Test with EXACT variables from working legacy script
        test_variables = [
            'motorVars_M1.motorState',           # EXACT from legacy script
            'motorVars_M1.Idq_out_A.value[0]',  # EXACT from legacy script  
            'motorVars_M1.absPosition_rad'      # EXACT from legacy script
        ]
        
        # For structured variables, we need to check if the base exists in MAP
        # e.g., 'motorVars_M1.motorState' needs 'motorVars_M1' in MAP
        available = connector.get_available_variables()
        valid_test_vars = []
        
        for var in test_variables:
            # Extract base variable name (part before first dot)
            base_var = var.split('.')[0]
            if base_var in available:
                valid_test_vars.append(var)  # Use the full structured name
                print(f"  ✅ {var} (base: {base_var} found in MAP)")
            else:
                print(f"  ❌ {var} (base: {base_var} NOT in MAP)")
        
        print(f"Testing variables: {valid_test_vars}")
        
        if valid_test_vars:
            # Test single cycle first
            print("\\n1. Testing single monitoring cycle...")
            results = connector.run_monitoring_cycle(valid_test_vars)
            
            print("Single cycle results:")
            for var, value in results.items():
                if value is not None:
                    print(f"  ✅ {var} = {value}")
                else:
                    print(f"  ❌ {var} = <failed>")
            
            # Test continuous monitoring
            print("\\n2. Testing continuous monitoring for 10 seconds...")
            if connector.start_monitoring(valid_test_vars, rate_hz=1.0):  # 1 Hz for testing
                print("✅ Monitoring started")
                
                for i in range(10):
                    time.sleep(1)
                    current = connector.get_current_data()
                    if current:
                        print(f"  {i+1}s: {len(current)} variables with data")
                        for var, val in list(current.items())[:2]:  # Show first 2
                            print(f"    {var} = {val}")
                    else:
                        print(f"  {i+1}s: No data")
                
                connector.stop_monitoring()
                print("✅ Monitoring stopped")
            else:
                print("❌ Failed to start monitoring")
        
        connector.disconnect()
        print("\\n✅ Test complete")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    test_legacy_loop_connector()