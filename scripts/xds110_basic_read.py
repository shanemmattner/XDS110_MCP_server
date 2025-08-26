#!/usr/bin/env python3
"""
Basic XDS110 memory read test for TMS320F280039C
Using known memory addresses for system registers
"""

import subprocess
import json
import time

# TMS320F280039C Memory Map (from datasheet)
MEMORY_MAP = {
    # System Control Registers
    "SYSCTRL_BASE": 0x00007000,
    "CPUTIMER0_BASE": 0x00000C00,
    "CPUTIMER1_BASE": 0x00000C08,
    "CPUTIMER2_BASE": 0x00000C10,
    
    # Specific registers
    "TIM": 0x00000C00,          # CPU-Timer 0 Counter Register (32-bit uptime counter)
    "PRD": 0x00000C02,          # CPU-Timer 0 Period Register
    "TCR": 0x00000C04,          # CPU-Timer 0 Control Register
    "TPR": 0x00000C06,          # CPU-Timer 0 Prescale Register
    "TPRH": 0x00000C07,         # CPU-Timer 0 Prescale Register High
    
    # System control
    "PLLSTS": 0x0000700A,       # PLL Status Register (shows system clock status)
    "SCSR": 0x00007022,         # System Control and Status Register
    "WDCR": 0x00007029,         # Watchdog Control Register
    
    # Device ID
    "PARTIDL": 0x00000882,      # Part ID Low Register
    "PARTIDH": 0x00000883,      # Part ID High Register
    "REVID": 0x00000884,        # Device Revision ID
}

def test_openocd_basic():
    """Try basic OpenOCD connection with simpler config"""
    print("Testing basic OpenOCD connection...")
    
    # Create minimal config
    config = """
# XDS110 interface
adapter driver xds110
adapter speed 1000

# Try JTAG first (C2000 uses JTAG, not SWD)
transport select jtag

# XDS110 settings
xds110 supply 3300

# Just try to detect
init
scan_chain
shutdown
"""
    
    # Write config to temp file
    with open('/tmp/xds110_test.cfg', 'w') as f:
        f.write(config)
    
    # Run OpenOCD
    result = subprocess.run(
        ['openocd', '-f', '/tmp/xds110_test.cfg'],
        capture_output=True,
        text=True
    )
    
    print("OpenOCD output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0

def get_system_info():
    """Display known system register information"""
    print("\n=== TMS320F280039C System Register Information ===")
    print("\nImportant Memory Locations:")
    print(f"  CPU Timer 0 (Uptime Counter):")
    print(f"    - TIM (Counter): 0x{MEMORY_MAP['TIM']:08X} - 32-bit free-running counter")
    print(f"    - PRD (Period):   0x{MEMORY_MAP['PRD']:08X} - Period register")
    print(f"    - TCR (Control):  0x{MEMORY_MAP['TCR']:08X} - Timer control")
    print(f"\n  System Status:")
    print(f"    - PLLSTS: 0x{MEMORY_MAP['PLLSTS']:08X} - PLL/Clock status")
    print(f"    - SCSR:   0x{MEMORY_MAP['SCSR']:08X} - System control status")
    print(f"\n  Device ID:")
    print(f"    - PARTIDL: 0x{MEMORY_MAP['PARTIDL']:08X} - Part ID Low")
    print(f"    - PARTIDH: 0x{MEMORY_MAP['PARTIDH']:08X} - Part ID High")
    print(f"    - REVID:   0x{MEMORY_MAP['REVID']:08X} - Revision ID")
    
    print("\nNote: CPU Timer 0 typically counts at SYSCLK rate (100MHz on F280039C)")
    print("      So TIM register increments 100,000,000 times per second")
    print("      Uptime in seconds = TIM / 100000000")

def check_xds110_status():
    """Check XDS110 connection status"""
    result = subprocess.run(
        ["system_profiler", "SPUSBDataType"],
        capture_output=True,
        text=True
    )
    
    if "XDS110" in result.stdout and "0x0451" in result.stdout:
        print("✓ XDS110 is connected via USB")
        return True
    else:
        print("✗ XDS110 not detected")
        return False

def try_uniflash():
    """Check if UniFlash CLI is available (alternative to DSS)"""
    print("\nChecking for UniFlash CLI...")
    
    # Common UniFlash locations on Mac
    paths = [
        "/Applications/ti/uniflash_8.8.0/dslite.sh",
        "/Applications/ti/uniflash/dslite.sh",
        "/opt/ti/uniflash/dslite.sh"
    ]
    
    for path in paths:
        result = subprocess.run(
            ["ls", "-la", path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  Found UniFlash at: {path}")
            
            # Try to use it
            result = subprocess.run(
                [path, "--mode", "processors", "--search"],
                capture_output=True,
                text=True
            )
            print("  Processors found:")
            print(result.stdout)
            return True
    
    print("  UniFlash not found")
    return False

if __name__ == "__main__":
    print("=== XDS110 Basic Memory Read Test ===\n")
    
    # Check XDS110 connection
    if not check_xds110_status():
        print("Please connect XDS110 debug probe")
        exit(1)
    
    # Display system info
    get_system_info()
    
    # Try OpenOCD
    print("\n" + "="*50)
    test_openocd_basic()
    
    # Try UniFlash
    print("\n" + "="*50)
    try_uniflash()
    
    print("\n" + "="*50)
    print("\nSUMMARY:")
    print("The XDS110 is connected and detected by macOS.")
    print("However, accessing the TMS320F280039C processor requires:")
    print("  1. Fixing the DSS library issue on macOS, OR")
    print("  2. Using a Linux VM/container with proper DSS support, OR")
    print("  3. Installing and using UniFlash CLI tool, OR")
    print("  4. Using Windows/Linux machine for actual debugging")
    print("\nThe CPU Timer 0 register at 0x00000C00 would contain the uptime counter.")
    print("Once we can connect, we can read it to get system uptime.")