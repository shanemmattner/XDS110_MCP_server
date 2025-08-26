#!/usr/bin/env python3
"""
Debug version of advanced dashboard to find connection issues
"""

import sys
import logging
from pathlib import Path

# Import our legacy dashboard connector
from legacy_dash_connector import (
    initialize_hardware, 
    get_available_variables,
    disconnect
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test the connection without starting dashboard"""
    
    # File paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    print("Debug: Testing advanced dashboard connection...")
    print(f"CCXML: {ccxml_path.exists()}")
    print(f"MAP: {map_path.exists()}")
    print(f"Binary: {binary_path.exists()}")
    
    # Initialize hardware
    logger.info("Debug: Initializing XDS110 connection...")
    if initialize_hardware(str(ccxml_path), str(map_path), str(binary_path)):
        logger.info("Debug: ✅ Hardware initialized successfully")
        
        # Get variables
        variables = get_available_variables()
        logger.info(f"Debug: Found {len(variables)} variables")
        
        if variables:
            logger.info(f"Debug: Sample variables: {', '.join(list(variables)[:10])}")
            
            # Check for priority variables
            priority_vars = ['motorVars_M1', 'motorHandle_M1', 'debug_bypass', 'motor1_drive', 'motor_common']
            found_priority = [v for v in priority_vars if v in variables]
            logger.info(f"Debug: Found priority variables: {found_priority}")
            
            # Check for motor variables
            motor_vars = [v for v in variables if 'motor' in v.lower()]
            logger.info(f"Debug: Found {len(motor_vars)} motor variables")
            
            # Check for debug variables
            debug_vars = [v for v in variables if 'debug' in v.lower()]
            logger.info(f"Debug: Found {len(debug_vars)} debug variables")
        
        # Cleanup on exit
        disconnect()
        logger.info("Debug: Disconnected from hardware")
        return True
    else:
        logger.error("Debug: Failed to initialize hardware")
        return False

if __name__ == '__main__':
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nDebug: Shutting down...")
        disconnect()
        sys.exit(0)