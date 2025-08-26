#!/usr/bin/env python3
"""
Simple XDS110 test using direct USB access to read device info
"""

import usb.core
import usb.util
import struct
import time

# XDS110 USB IDs
VENDOR_ID = 0x0451
PRODUCT_ID = 0xbef3

def find_xds110():
    """Find XDS110 device"""
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("XDS110 not found via USB")
        return None
    
    print(f"XDS110 found!")
    print(f"  Manufacturer: {usb.util.get_string(dev, dev.iManufacturer)}")
    print(f"  Product: {usb.util.get_string(dev, dev.iProduct)}")
    print(f"  Serial: {usb.util.get_string(dev, dev.iSerialNumber)}")
    print(f"  Configuration: {dev.get_active_configuration()}")
    
    return dev

def get_device_info(dev):
    """Get device configuration info"""
    print("\nDevice Information:")
    print(f"  bcdUSB: {hex(dev.bcdUSB)}")
    print(f"  bDeviceClass: {dev.bDeviceClass}")
    print(f"  bDeviceSubClass: {dev.bDeviceSubClass}")
    print(f"  bDeviceProtocol: {dev.bDeviceProtocol}")
    print(f"  bMaxPacketSize0: {dev.bMaxPacketSize0}")
    print(f"  bcdDevice: {hex(dev.bcdDevice)}")
    
    # List all configurations
    for cfg in dev:
        print(f"\n  Configuration {cfg.bConfigurationValue}:")
        for intf in cfg:
            print(f"    Interface {intf.bInterfaceNumber}:")
            print(f"      Class: {intf.bInterfaceClass}")
            print(f"      SubClass: {intf.bInterfaceSubClass}")
            print(f"      Protocol: {intf.bInterfaceProtocol}")
            
            for ep in intf:
                print(f"      Endpoint {hex(ep.bEndpointAddress)}:")
                print(f"        Type: {ep.bmAttributes & 0x03}")
                print(f"        Max packet size: {ep.wMaxPacketSize}")

def try_cmsis_dap(dev):
    """Try to communicate via CMSIS-DAP protocol"""
    print("\nTrying CMSIS-DAP communication...")
    
    # CMSIS-DAP typically uses bulk endpoints
    # Standard CMSIS-DAP commands
    CMD_DAP_INFO = 0x00
    CMD_DAP_CONNECT = 0x02
    CMD_DAP_DISCONNECT = 0x03
    CMD_DAP_TRANSFER = 0x05
    CMD_DAP_SWD_CONFIGURE = 0x13
    
    # Try to find bulk endpoints
    cfg = dev.get_active_configuration()
    
    for intf in cfg:
        if intf.bInterfaceClass == 0xFF:  # Vendor specific class (common for debug probes)
            print(f"  Found vendor-specific interface: {intf.bInterfaceNumber}")
            
            # Find bulk IN and OUT endpoints
            ep_in = None
            ep_out = None
            
            for ep in intf:
                if ep.bmAttributes & 0x03 == 0x02:  # Bulk endpoint
                    if ep.bEndpointAddress & 0x80:  # IN endpoint
                        ep_in = ep
                        print(f"    Found bulk IN endpoint: {hex(ep.bEndpointAddress)}")
                    else:  # OUT endpoint
                        ep_out = ep
                        print(f"    Found bulk OUT endpoint: {hex(ep.bEndpointAddress)}")
            
            if ep_in and ep_out:
                try:
                    # Try to claim interface
                    if dev.is_kernel_driver_active(intf.bInterfaceNumber):
                        print(f"    Detaching kernel driver from interface {intf.bInterfaceNumber}")
                        dev.detach_kernel_driver(intf.bInterfaceNumber)
                    
                    # Set configuration
                    dev.set_configuration()
                    
                    # Try DAP_INFO command
                    cmd = bytes([CMD_DAP_INFO, 0x01])  # Get Vendor Name
                    cmd = cmd + b'\x00' * (64 - len(cmd))  # Pad to 64 bytes
                    
                    print(f"    Sending DAP_INFO command...")
                    ep_out.write(cmd)
                    
                    # Read response
                    response = ep_in.read(64, timeout=1000)
                    print(f"    Response: {response.hex()}")
                    
                    # Try to parse response if it looks valid
                    if response[0] == CMD_DAP_INFO:
                        length = response[1]
                        if length > 0:
                            info = response[2:2+length].decode('utf-8', errors='ignore')
                            print(f"    Vendor: {info}")
                    
                except Exception as e:
                    print(f"    CMSIS-DAP communication failed: {e}")

def read_uptime_registers():
    """
    Try to read typical uptime/counter registers on TMS320F280039C
    These are usually in the System Control registers
    """
    print("\nAttempting to read system registers...")
    print("Note: Direct USB access to processor registers requires proper debug protocol implementation")
    print("For TMS320F280039C, common system registers include:")
    print("  - SYSCLKOUT: System clock counter")
    print("  - CPUTIMER0: CPU Timer 0 counter (often used for uptime)")
    print("  - Address 0x0C00: Timer 0 counter register")
    print("  - Address 0x0C04: Timer 0 period register")
    print("  - Address 0x0C06: Timer 0 control register")
    
    return None

if __name__ == "__main__":
    print("=== XDS110 Simple Test ===\n")
    
    # Find XDS110
    dev = find_xds110()
    if dev is None:
        print("\nPlease ensure XDS110 is connected")
        exit(1)
    
    # Get device information
    get_device_info(dev)
    
    # Try CMSIS-DAP protocol
    try_cmsis_dap(dev)
    
    # Try to read uptime registers (would need proper debug protocol)
    read_uptime_registers()
    
    print("\nNote: Full processor access requires proper DSS/OpenOCD setup")
    print("The XDS110 is detected and accessible via USB!")