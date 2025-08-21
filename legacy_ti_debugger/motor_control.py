#!/usr/bin/env python3
"""
Main Motor Control Script for TI Debugger
Simplified entry point for PMSM motor control operations.
"""

import asyncio
import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent / "framework"))

from working_memory_motor_control import execute_working_memory_motor_control

async def main():
    """Main entry point for motor control"""
    print("🔧 TI Debugger - PMSM Motor Control")
    print("=" * 50)
    print("✅ Verified Hardware: Custom F280039C + XDS110 + PMSM")
    print("✅ Automatic calibration and safe motor control")
    print()
    
    success = await execute_working_memory_motor_control()
    
    if success:
        print("🎉 Motor control script completed successfully!")
        print("💡 If no motor movement: check power, connections, and current limit")
    else:
        print("❌ Motor control script failed")
        print("🔧 Check hardware connection and try tests/test_connection.py")
    
    return 0 if success else 1

if __name__ == "__main__":
    # Environment check
    current_dir = Path.cwd()
    if not (current_dir / "TMS320F280039C_LaunchPad.ccxml").exists():
        print("❌ Please run from firmware root directory")
        sys.exit(1)
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(1)