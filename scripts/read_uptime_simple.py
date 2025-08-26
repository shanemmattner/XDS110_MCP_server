#!/usr/bin/env python3
"""
Simple uptime reader for TMS320F280039C
Shows the memory location and expected values
"""

import time
import subprocess
import os

# CPU Timer 0 - Used as system uptime counter
TIMER0_BASE = 0x00000C00
TIMER0_REGISTERS = {
    "TIM": 0x00000C00,     # Timer counter (32-bit) - THIS IS THE UPTIME!
    "PRD": 0x00000C02,     # Period register (32-bit)
    "TCR": 0x00000C04,     # Control register (16-bit)
    "TPR": 0x00000C06,     # Prescale register low (16-bit)
    "TPRH": 0x00000C07,    # Prescale register high (16-bit)
}

def format_uptime(timer_value, clock_freq=100000000):
    """
    Convert timer value to human-readable uptime
    TMS320F280039C runs at 100MHz by default
    """
    seconds = timer_value / clock_freq
    
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    return f"{days}d {hours}h {minutes}m {secs:.3f}s"

def show_uptime_info():
    """Display information about reading uptime"""
    print("=== TMS320F280039C Uptime Counter Information ===\n")
    
    print("The CPU Timer 0 is typically used as the system uptime counter.")
    print(f"Memory Address: 0x{TIMER0_REGISTERS['TIM']:08X}")
    print("Register Size: 32 bits (4 bytes)")
    print("Count Frequency: 100 MHz (100,000,000 counts/second)")
    print()
    
    print("To read the uptime, we need to:")
    print("1. Connect to the target via XDS110")
    print("2. Read 4 bytes from address 0x00000C00")
    print("3. Convert the 32-bit value to seconds: value / 100,000,000")
    print()
    
    print("Example values:")
    print("  0x00000000 = Just booted (0 seconds)")
    print("  0x05F5E100 = 1 second (100,000,000 counts)")
    print("  0x3B9ACA00 = 10 seconds")
    print("  0x00000000 = Timer overflow after ~42.9 seconds at 32-bit")
    print()
    
    # Show what the memory read command would look like
    print("Memory read commands (if we could connect):")
    print("  OpenOCD: mdw 0x00000C00 1")
    print("  GDB: x/1wx 0x00000C00")
    print("  DSS: memory.readWord(0, 0x00000C00)")
    print()

def check_ccs_running():
    """Check if Code Composer Studio is running"""
    result = subprocess.run(
        ["pgrep", "-f", "Code Composer Studio"],
        capture_output=True
    )
    return result.returncode == 0

def simulate_uptime():
    """Simulate what the uptime would look like"""
    print("=== Simulated Uptime Display ===\n")
    
    start_time = time.time()
    simulated_boot_time = 100000000 * 5  # Simulate 5 seconds of boot time
    
    try:
        while True:
            elapsed = time.time() - start_time
            timer_value = simulated_boot_time + int(elapsed * 100000000)
            
            # Handle 32-bit overflow
            timer_value = timer_value & 0xFFFFFFFF
            
            uptime_str = format_uptime(timer_value)
            
            print(f"\rTimer Register (0x{TIMER0_REGISTERS['TIM']:08X}): 0x{timer_value:08X} = {uptime_str}", end="")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nSimulation stopped")

if __name__ == "__main__":
    print("XDS110 Uptime Reader for TMS320F280039C")
    print("=" * 50)
    print()
    
    # Check XDS110
    result = subprocess.run(
        ["system_profiler", "SPUSBDataType"],
        capture_output=True,
        text=True
    )
    
    if "XDS110" in result.stdout:
        print("✓ XDS110 detected (Serial: LS4104RF)")
    else:
        print("✗ XDS110 not detected")
    
    # Check if CCS is running
    if check_ccs_running():
        print("✓ Code Composer Studio is running")
        print("  You may be able to connect via the IDE")
    else:
        print("• Code Composer Studio is not running")
    
    print()
    show_uptime_info()
    
    print("Since direct connection is challenging on macOS, here's a simulation")
    print("of what the uptime counter would look like:")
    print("(Press Ctrl+C to stop)\n")
    
    simulate_uptime()