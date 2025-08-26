#!/usr/bin/env python3
"""
Test XDS110 connection from Docker container via host bridge
"""

import requests
import json
import sys

BRIDGE_URL = "http://host.docker.internal:5555"

def test_xds110_connection():
    print("=== Testing XDS110 Connection from Docker ===\n")
    
    # Test 1: Check bridge is accessible
    try:
        response = requests.get(f"{BRIDGE_URL}/test")
        data = response.json()
        print("✓ Bridge connection successful")
        print(f"  Platform: {data['platform']}")
    except Exception as e:
        print(f"✗ Failed to connect to bridge: {e}")
        return False
    
    # Test 2: Check XDS110 status
    try:
        response = requests.get(f"{BRIDGE_URL}/status")
        data = response.json()
        
        if data['status'] == 'connected':
            print("\n✓ XDS110 DETECTED!")
            device = data['device']
            print(f"  Name: {device['name']}")
            print(f"  Vendor ID: {device['vendor_id']}")
            print(f"  Product ID: {device['product_id']}")
            print(f"  Serial: {device['serial']}")
            print(f"  Location: {device['location']}")
        else:
            print("\n✗ XDS110 not connected")
            return False
            
    except Exception as e:
        print(f"✗ Failed to get XDS110 status: {e}")
        return False
    
    # Test 3: Get detailed USB info
    try:
        response = requests.get(f"{BRIDGE_URL}/usb/info")
        usb_data = response.json()
        print("\n✓ USB subsystem accessible")
        
        # Look for XDS110 in USB tree
        if "SPUSBDataType" in str(usb_data):
            print("  Full USB tree data available")
    except Exception as e:
        print(f"⚠ Could not get detailed USB info: {e}")
    
    print("\n=== XDS110 Bridge Integration Test Complete ===")
    print("The XDS110 is accessible from Docker through the host bridge!")
    print("\nNext steps:")
    print("1. Install TI Code Composer Studio on the host Mac")
    print("2. Configure DSS paths in the bridge script")
    print("3. Run DSS JavaScript scripts via the bridge API")
    
    return True

if __name__ == "__main__":
    success = test_xds110_connection()
    sys.exit(0 if success else 1)