#!/usr/bin/env python3
"""
Systematic Variable Testing - Test reading all discovered variables
Uses proven legacy DSS method to systematically test each variable
"""

import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import csv
import re

from xds110_dash_connector import XDS110Interface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystematicVariableTester:
    """Test reading all variables systematically"""
    
    def __init__(self, map_file: str, ccxml_file: str, binary_file: str):
        self.map_file = Path(map_file)
        self.ccxml_file = Path(ccxml_file) 
        self.binary_file = Path(binary_file)
        
        # Initialize XDS110 interface to get symbols
        self.xds110 = XDS110Interface()
        self.symbols = self.xds110.load_map_file(str(map_file))
        
        # TI DSS path
        self.dss_path = Path("/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh")
        
        # Results storage
        self.test_results = {}
        self.successful_reads = {}
        self.failed_reads = {}
        
    def generate_test_script(self, variables_to_test: List[str]) -> str:
        """Generate comprehensive DSS script to test multiple variables"""
        
        js_script = f"""
// Systematic Variable Testing Script
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {{
    print("=== Systematic Variable Test ===");
    
    var debugSession = null;
    var testResults = {{}};
    
    try {{
        // Connect to target (same as working legacy script)
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{self.ccxml_file}");
        
        // Open session
        try {{
            debugSession = ds.openSession("*", "C28xx_CPU1");
            print("SUCCESS: Session opened");
        }} catch (e) {{
            debugSession = ds.openSession("*");
            print("SUCCESS: Session opened with wildcard");
        }}
        
        // Connect and load firmware
        debugSession.target.connect();
        debugSession.memory.loadProgram("{self.binary_file}");
        
        // Initialize target
        debugSession.target.runAsynch();
        Thread.sleep(2000);
        debugSession.target.halt();
        
        print("SUCCESS: Target initialized");
        print("TESTING_START");
        
        // Test each variable
"""
        
        # Add test for each variable
        for var_name in variables_to_test:
            address = self.symbols.get(var_name)
            if address:
                js_script += f"""
        // Test {var_name}
        try {{
            print("TESTING:{var_name}");
            
            // Try multiple read methods
            var success = false;
            var value = null;
            var method = "unknown";
            
            // Method 1: Direct expression evaluation
            try {{
                value = debugSession.expression.evaluate("{var_name}");
                method = "expression";
                success = true;
            }} catch (e1) {{
                // Method 2: Memory read from address
                try {{
                    value = debugSession.memory.readData(0, 0x{address:08X}, 32);
                    method = "memory";
                    success = true;
                }} catch (e2) {{
                    // Method 3: Memory read as float
                    try {{
                        value = debugSession.memory.readData(0, 0x{address:08X}, 32, 1);
                        method = "memory_float";
                        success = true;
                    }} catch (e3) {{
                        method = "failed";
                        value = "ERROR: " + e3.message;
                    }}
                }}
            }}
            
            if (success) {{
                print("RESULT:{var_name}=" + value + ":METHOD=" + method + ":ADDRESS=0x{address:08X}");
            }} else {{
                print("FAILED:{var_name}:" + value + ":ADDRESS=0x{address:08X}");
            }}
            
        }} catch (error) {{
            print("EXCEPTION:{var_name}:" + error.message);
        }}
"""
        
        js_script += """
        print("TESTING_COMPLETE");
        
    } catch (mainError) {
        print("MAIN_ERROR: " + mainError.message);
    } finally {
        if (debugSession) {
            try {
                debugSession.terminate();
            } catch (e) {
                // Ignore cleanup errors
            }
        }
    }
}

// Execute main function
main();
"""
        
        return js_script
    
    def test_variable_batch(self, variables: List[str], batch_name: str = "batch") -> Dict:
        """Test a batch of variables"""
        logger.info(f"Testing batch '{batch_name}' with {len(variables)} variables")
        
        # Generate test script
        js_script = self.generate_test_script(variables)
        
        # Save script
        script_path = Path(f"/tmp/test_{batch_name}.js")
        script_path.write_text(js_script)
        
        batch_results = {
            'batch_name': batch_name,
            'variables_tested': len(variables),
            'successful_reads': {},
            'failed_reads': {},
            'exceptions': {},
            'execution_time': 0,
            'script_path': str(script_path)
        }
        
        try:
            start_time = time.time()
            
            # Execute DSS script with extended timeout
            result = subprocess.run(
                [str(self.dss_path), str(script_path)],
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout for batch
            )
            
            batch_results['execution_time'] = time.time() - start_time
            
            # Parse results from stdout
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if line.startswith("RESULT:"):
                    # Format: RESULT:var_name=value:METHOD=method:ADDRESS=0xaddress
                    parts = line[7:].split(':')
                    if len(parts) >= 3:
                        var_value = parts[0].split('=', 1)
                        if len(var_value) == 2:
                            var_name, value = var_value
                            method = parts[1].split('=')[1] if '=' in parts[1] else "unknown"
                            address = parts[2].split('=')[1] if '=' in parts[2] else "unknown"
                            
                            batch_results['successful_reads'][var_name] = {
                                'value': value,
                                'method': method,
                                'address': address
                            }
                
                elif line.startswith("FAILED:"):
                    # Format: FAILED:var_name:error_msg:ADDRESS=0xaddress
                    parts = line[7:].split(':', 2)
                    if len(parts) >= 2:
                        var_name = parts[0]
                        error_msg = parts[1]
                        batch_results['failed_reads'][var_name] = error_msg
                
                elif line.startswith("EXCEPTION:"):
                    # Format: EXCEPTION:var_name:error_msg
                    parts = line[10:].split(':', 1)
                    if len(parts) == 2:
                        var_name, error_msg = parts
                        batch_results['exceptions'][var_name] = error_msg
            
            # Log stderr if any
            if result.stderr:
                logger.warning(f"DSS stderr for {batch_name}:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.warning(f"  {line}")
            
        except subprocess.TimeoutExpired:
            logger.error(f"Batch {batch_name} timed out")
            batch_results['error'] = 'Timeout'
        except Exception as e:
            logger.error(f"Batch {batch_name} failed: {e}")
            batch_results['error'] = str(e)
        
        return batch_results
    
    def test_all_variables(self, batch_size: int = 20) -> Dict:
        """Test all variables in batches"""
        logger.info(f"Testing {len(self.symbols)} variables in batches of {batch_size}")
        
        all_results = {
            'start_time': datetime.now().isoformat(),
            'total_variables': len(self.symbols),
            'batch_size': batch_size,
            'batches': [],
            'summary': {
                'total_successful': 0,
                'total_failed': 0,
                'total_exceptions': 0,
                'success_rate': 0.0
            }
        }
        
        # Split variables into batches
        variable_list = list(self.symbols.keys())
        
        for i in range(0, len(variable_list), batch_size):
            batch_vars = variable_list[i:i+batch_size]
            batch_name = f"batch_{i//batch_size + 1}"
            
            logger.info(f"Testing {batch_name}: variables {i+1}-{i+len(batch_vars)}")
            
            batch_result = self.test_variable_batch(batch_vars, batch_name)
            all_results['batches'].append(batch_result)
            
            # Update summary
            all_results['summary']['total_successful'] += len(batch_result.get('successful_reads', {}))
            all_results['summary']['total_failed'] += len(batch_result.get('failed_reads', {}))
            all_results['summary']['total_exceptions'] += len(batch_result.get('exceptions', {}))
            
            # Short delay between batches
            time.sleep(1)
        
        # Calculate success rate
        total_tested = all_results['summary']['total_successful'] + all_results['summary']['total_failed'] + all_results['summary']['total_exceptions']
        if total_tested > 0:
            all_results['summary']['success_rate'] = all_results['summary']['total_successful'] / total_tested * 100
        
        all_results['end_time'] = datetime.now().isoformat()
        
        return all_results
    
    def test_specific_variables(self, variable_names: List[str]) -> Dict:
        """Test specific variables of interest"""
        logger.info(f"Testing specific variables: {variable_names}")
        
        # Filter to only variables that exist
        existing_vars = [v for v in variable_names if v in self.symbols]
        missing_vars = [v for v in variable_names if v not in self.symbols]
        
        if missing_vars:
            logger.warning(f"Variables not found in MAP: {missing_vars}")
        
        if not existing_vars:
            return {'error': 'No valid variables to test'}
        
        return self.test_variable_batch(existing_vars, "specific_test")
    
    def save_results(self, results: Dict, filename: str = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"variable_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {filename}")
        
        # Also create CSV summary
        csv_filename = filename.replace('.json', '_summary.csv')
        self.create_csv_summary(results, csv_filename)
        
        return filename
    
    def create_csv_summary(self, results: Dict, filename: str):
        """Create CSV summary of test results"""
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Variable', 'Status', 'Value', 'Method', 'Address', 'Batch'])
            
            for batch in results.get('batches', []):
                batch_name = batch.get('batch_name', 'unknown')
                
                # Successful reads
                for var_name, info in batch.get('successful_reads', {}).items():
                    writer.writerow([
                        var_name,
                        'SUCCESS',
                        info.get('value', ''),
                        info.get('method', ''),
                        info.get('address', ''),
                        batch_name
                    ])
                
                # Failed reads
                for var_name, error in batch.get('failed_reads', {}).items():
                    address = f"0x{self.symbols[var_name]:08x}" if var_name in self.symbols else ""
                    writer.writerow([
                        var_name,
                        'FAILED',
                        '',
                        error,
                        address,
                        batch_name
                    ])
                
                # Exceptions
                for var_name, error in batch.get('exceptions', {}).items():
                    address = f"0x{self.symbols[var_name]:08x}" if var_name in self.symbols else ""
                    writer.writerow([
                        var_name,
                        'EXCEPTION',
                        '',
                        error,
                        address,
                        batch_name
                    ])
        
        logger.info(f"CSV summary saved to {filename}")

def main():
    """Main testing function"""
    print("XDS110 Systematic Variable Testing")
    print("================================")
    
    # File paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    # Create tester
    tester = SystematicVariableTester(str(map_path), str(ccxml_path), str(binary_path))
    
    print(f"Found {len(tester.symbols)} variables to test")
    print()
    
    # Test specific variables of interest first
    print("1. Testing key variables...")
    key_variables = [
        'debug_bypass',
        'motorVars_M1', 
        'motorHandle_M1',
        'motorSetVars_M1',
        'calibration',
        'motor1_drive',
        'communication',
        'hal'
    ]
    
    key_results = tester.test_specific_variables(key_variables)
    
    print("Key variable test results:")
    successful = key_results.get('successful_reads', {})
    failed = key_results.get('failed_reads', {})
    exceptions = key_results.get('exceptions', {})
    
    for var, info in successful.items():
        print(f"  ✅ {var} = {info['value']} (method: {info['method']})")
    
    for var, error in failed.items():
        print(f"  ❌ {var}: {error}")
    
    for var, error in exceptions.items():
        print(f"  💥 {var}: {error}")
    
    print()
    
    # Ask if user wants to test all variables
    response = input("Test all 447 variables? This may take several minutes. (y/n): ")
    if response.lower().startswith('y'):
        print("2. Testing ALL variables...")
        print("This will take several minutes...")
        
        all_results = tester.test_all_variables(batch_size=15)  # Smaller batches for reliability
        
        # Save comprehensive results
        results_file = tester.save_results(all_results)
        
        # Print summary
        summary = all_results['summary']
        print(f"""
Test Summary:
============
Total Variables: {summary['total_successful'] + summary['total_failed'] + summary['total_exceptions']}
✅ Successful: {summary['total_successful']} ({summary['success_rate']:.1f}%)
❌ Failed: {summary['total_failed']}
💥 Exceptions: {summary['total_exceptions']}

Results saved to: {results_file}
        """)
        
        # Show some successful reads
        if any(batch.get('successful_reads') for batch in all_results['batches']):
            print("Sample successful reads:")
            count = 0
            for batch in all_results['batches']:
                for var, info in batch.get('successful_reads', {}).items():
                    if count < 10:
                        print(f"  ✅ {var} = {info['value']}")
                        count += 1
                    else:
                        break
                if count >= 10:
                    break
    else:
        # Just save key results
        results_file = tester.save_results({'batches': [key_results]}, "key_variable_test.json")
        print(f"Key results saved to: {results_file}")

if __name__ == "__main__":
    main()