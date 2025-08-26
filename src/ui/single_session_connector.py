#!/usr/bin/env python3
"""
Single Session XDS110 Connector
Uses the working legacy pattern: connect + read all + disconnect in ONE DSS session
"""

import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SingleSessionXDS110:
    """XDS110 interface using single DSS session approach (like working legacy scripts)"""
    
    def __init__(self, ccxml_path: str, map_file: str, binary_path: str):
        self.ccxml_path = Path(ccxml_path)
        self.map_file = Path(map_file)
        self.binary_path = Path(binary_path)
        self.dss_path = Path("/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh")
        
        # Load symbols from MAP file
        self.symbols = self._parse_map_file()
        logger.info(f"Loaded {len(self.symbols)} symbols from MAP file")
    
    def _parse_map_file(self) -> Dict[str, int]:
        """Parse MAP file for symbol addresses"""
        symbols = {}
        
        try:
            with open(self.map_file, 'r') as f:
                content = f.read()
            
            # TI MAP format: page_num  hex_address  symbol_name
            symbol_pattern = re.compile(r'^\s*\d+\s+([0-9a-f]+)\s+(\w+)', re.MULTILINE | re.IGNORECASE)
            
            for match in symbol_pattern.finditer(content):
                address_str, name = match.groups()
                address = int(address_str, 16)
                symbols[name] = address
                
        except Exception as e:
            logger.error(f"Failed to parse MAP file: {e}")
            
        return symbols
    
    def read_variables_batch(self, variable_names: List[str]) -> Dict[str, Any]:
        """
        Read multiple variables in a single DSS session (WORKING APPROACH)
        This mimics the successful legacy script pattern
        """
        
        if not variable_names:
            return {}
        
        # Filter to only variables that exist in MAP
        valid_vars = [v for v in variable_names if v in self.symbols]
        if not valid_vars:
            logger.warning("No valid variables to read")
            return {}
        
        # Create comprehensive DSS script (based on working legacy pattern)
        js_script = f"""
// Single Session Variable Reader (Based on Working Legacy Scripts)
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {{
    print("=== Single Session Variable Reader ===");
    
    try {{
        // Connect to target (exact same as working legacy scripts)
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{self.ccxml_path}");
        
        var debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Load firmware
        debugSession.memory.loadProgram("{self.binary_path}");
        
        // Initialize target (same as legacy)
        debugSession.target.runAsynch();
        Thread.sleep(2000);
        debugSession.target.halt();
        
        print("TARGET_READY");
        
        // Read all requested variables in this SAME session
"""
        
        # Add read commands for each variable
        for var_name in valid_vars:
            address = self.symbols[var_name]
            js_script += f"""
        // Read {var_name}
        try {{
            // Method 1: Try expression evaluation first (most reliable)
            try {{
                var val_{var_name} = debugSession.expression.evaluate("{var_name}");
                print("VAR:{var_name}=" + val_{var_name});
            }} catch (expr_error) {{
                // Method 2: Try memory read as fallback
                try {{
                    var mem_val = debugSession.memory.readData(0, 0x{address:08X}, 32);
                    print("VAR:{var_name}=" + mem_val);
                }} catch (mem_error) {{
                    print("ERR:{var_name}:" + expr_error.message);
                }}
            }}
        }} catch (error) {{
            print("ERR:{var_name}:" + error.message);
        }}
"""
        
        js_script += """
        print("READING_COMPLETE");
        
        // Disconnect (clean up like legacy scripts)
        debugSession.target.disconnect();
        print("SESSION_CLOSED");
        
    } catch (main_error) {
        print("MAIN_ERROR:" + main_error.message);
    }
}

// Execute main function
main();
"""
        
        # Save script
        timestamp = int(time.time())
        script_path = Path(f"/tmp/batch_read_{timestamp}.js")
        script_path.write_text(js_script)
        
        logger.info(f"Reading {len(valid_vars)} variables in single session")
        
        try:
            # Execute DSS script
            result = subprocess.run(
                [str(self.dss_path), str(script_path)],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            # Parse results
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
                            logger.debug(f"Read {var_name} = {value}")
                        except ValueError:
                            # Handle non-numeric values
                            variables_data[var_name] = value_str
                            
                elif line.startswith("ERR:"):
                    # Format: ERR:variable_name:error_message
                    err_part = line[4:]
                    if ':' in err_part:
                        var_name, error_msg = err_part.split(':', 1)
                        logger.warning(f"Error reading {var_name}: {error_msg}")
                        variables_data[var_name] = None
                        
                elif "TARGET_READY" in line:
                    logger.info("Target initialized successfully")
                elif "READING_COMPLETE" in line:
                    logger.info("Variable reading completed")
                elif "SESSION_CLOSED" in line:
                    logger.info("Session closed cleanly")
            
            # Log any stderr
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip() and "SLF4J" not in line:
                        logger.warning(f"DSS stderr: {line}")
            
            logger.info(f"Successfully read {len(variables_data)} variables")
            return variables_data
            
        except subprocess.TimeoutExpired:
            logger.error(f"Batch read timed out for {len(valid_vars)} variables")
            return {}
        except Exception as e:
            logger.error(f"Batch read error: {e}")
            return {}
    
    def get_available_variables(self) -> List[str]:
        """Get list of all available variables"""
        return list(self.symbols.keys())
    
    def search_variables(self, pattern: str) -> List[str]:
        """Search for variables matching pattern"""
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            return [name for name in self.symbols.keys() if regex.search(name)]
        except re.error:
            # Fall back to simple string search
            return [name for name in self.symbols.keys() if pattern.lower() in name.lower()]
    
    def get_variable_info(self, var_name: str) -> Optional[Dict]:
        """Get information about a variable"""
        if var_name not in self.symbols:
            return None
        
        address = self.symbols[var_name]
        return {
            'name': var_name,
            'address': address,
            'address_hex': f'0x{address:08x}',
            'type': 'data' if address >= 0x8000 else 'function'  # Rough heuristic
        }


def test_single_session_connector():
    """Test the single session connector"""
    print("Testing Single Session XDS110 Connector")
    print("======================================")
    
    # File paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    # Create connector
    connector = SingleSessionXDS110(str(ccxml_path), str(map_path), str(binary_path))
    
    print(f"Loaded {len(connector.symbols)} symbols")
    
    # Test 1: Search for debug variables
    print("\n1. Testing debug variable search...")
    debug_vars = connector.search_variables("debug")
    print(f"Found {len(debug_vars)} debug variables:")
    for var in debug_vars:
        info = connector.get_variable_info(var)
        print(f"  - {var} @ {info['address_hex']}")
    
    # Test 2: Search for motor variables
    print("\n2. Testing motor variable search...")
    motor_vars = connector.search_variables("motor")
    print(f"Found {len(motor_vars)} motor variables:")
    for var in motor_vars[:5]:  # Show first 5
        info = connector.get_variable_info(var)
        print(f"  - {var} @ {info['address_hex']}")
    if len(motor_vars) > 5:
        print(f"  ... and {len(motor_vars) - 5} more")
    
    # Test 3: Read key variables using single session
    print("\n3. Testing single session variable reading...")
    test_variables = [
        'debug_bypass',
        'motorVars_M1', 
        'motorHandle_M1',
        'calibration',
        'motor1_drive'
    ]
    
    # Filter to only existing variables
    existing_vars = [v for v in test_variables if v in connector.symbols]
    print(f"Testing {len(existing_vars)} variables: {existing_vars}")
    
    # Read all in single session
    results = connector.read_variables_batch(existing_vars)
    
    print("Results:")
    for var_name, value in results.items():
        if value is not None:
            print(f"  ✅ {var_name} = {value}")
        else:
            print(f"  ❌ {var_name} = <failed to read>")
    
    # Test 4: Read some data structures
    print("\n4. Testing data structure variables...")
    struct_vars = [v for v in connector.symbols.keys() if any(x in v.lower() for x in ['vars', 'handle', 'data'])]
    
    if struct_vars:
        print(f"Found {len(struct_vars)} structure variables")
        test_structs = struct_vars[:3]  # Test first 3
        
        struct_results = connector.read_variables_batch(test_structs)
        for var_name, value in struct_results.items():
            print(f"  {var_name} = {value}")
    
    print("\n✅ Single session testing complete!")
    return results

if __name__ == "__main__":
    test_single_session_connector()