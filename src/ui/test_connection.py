#!/usr/bin/env python3
"""
Test XDS110 connection without starting full dashboard
"""

import logging
import sys
from pathlib import Path
from xds110_dash_connector import initialize_hardware

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("XDS110 Connection Test")
    print("=====================")
    
    # Paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    print(f"CCXML: {ccxml_path}")
    print(f"MAP:   {map_path}")
    print(f"Binary: {binary_path}")
    print()
    
    # Check files exist
    if not ccxml_path.exists():
        print(f"❌ CCXML not found: {ccxml_path}")
        return 1
    
    if not map_path.exists():
        print(f"❌ MAP not found: {map_path}")
        return 1
        
    if not binary_path.exists():
        print(f"❌ Binary not found: {binary_path}")
        return 1
    
    print("✅ All files found")
    print()
    
    # Test hardware connection
    print("Testing hardware connection...")
    success = initialize_hardware(
        str(ccxml_path),
        str(map_path), 
        str(binary_path)
    )
    
    if success:
        print("✅ Connection successful!")
        
        # Import the global instances
        from xds110_dash_connector import xds110, get_available_variables
        
        # Show some variables
        variables = get_available_variables()
        print(f"Found {len(variables)} variables")
        
        # Test reading a few variables
        print("\nTesting variable reads...")
        test_vars = ['motorVars_M1', 'debug_bypass']
        
        for var in test_vars:
            if var in variables:
                print(f"  Reading {var}...")
                value = xds110.read_variable(var)
                if value is not None:
                    print(f"    ✅ {var} = {value}")
                else:
                    print(f"    ❌ Failed to read {var}")
            else:
                print(f"    ⚠️ Variable {var} not found in MAP")
        
        return 0
    else:
        print("❌ Connection failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())