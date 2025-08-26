#!/usr/bin/env python3
"""
Test client for XDS110 Debug API
Demonstrates automated testing capabilities
"""

import requests
import json
import time
from pathlib import Path

# API base URL
API_BASE = "http://localhost:5000/api"

def test_api():
    """Test the XDS110 Debug API"""
    print("XDS110 Debug API Test Client")
    print("===========================")
    
    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    print()
    
    # Test connection
    print("2. Testing hardware connection...")
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    
    connect_data = {
        "ccxml_path": str(obake_dir / "TMS320F280039C_LaunchPad.ccxml"),
        "map_path": str(obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"),
        "binary_path": str(obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out")
    }
    
    try:
        response = requests.post(f"{API_BASE}/connect", json=connect_data)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Success: {result.get('success')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Variables found: {result.get('variable_count')}")
        
        if not result.get('success'):
            print("   Connection failed, stopping test")
            return
            
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    print()
    
    # Test variable listing
    print("3. Testing variable discovery...")
    try:
        response = requests.get(f"{API_BASE}/variables")
        result = response.json()
        print(f"   Total variables: {result.get('total_count')}")
        
        categories = result.get('categories', {})
        for category, vars_list in categories.items():
            if vars_list:
                print(f"   {category.title()}: {len(vars_list)} variables")
                for var in vars_list[:3]:  # Show first 3
                    print(f"     - {var}")
                if len(vars_list) > 3:
                    print(f"     ... and {len(vars_list) - 3} more")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test variable search
    print("4. Testing variable search...")
    search_terms = ["debug", "motor", "calibration"]
    
    for term in search_terms:
        try:
            response = requests.get(f"{API_BASE}/variables/search?q={term}")
            result = response.json()
            matches = result.get('matches', [])
            print(f"   '{term}': {len(matches)} matches")
            for match in matches[:5]:  # Show first 5
                print(f"     - {match['name']} @ {match['address']}")
            if len(matches) > 5:
                print(f"     ... and {len(matches) - 5} more")
                
        except Exception as e:
            print(f"   Error searching {term}: {e}")
    
    print()
    
    # Test variable info
    print("5. Testing variable info...")
    test_variables = ["debug_bypass", "motorVars_M1", "motorHandle_M1"]
    
    for var_name in test_variables:
        try:
            response = requests.get(f"{API_BASE}/variables/{var_name}/info")
            if response.status_code == 200:
                result = response.json()
                print(f"   {var_name}:")
                print(f"     Address: {result.get('address')}")
                print(f"     Type: {result.get('type')}")
            else:
                print(f"   {var_name}: Not found")
                
        except Exception as e:
            print(f"   Error getting info for {var_name}: {e}")
    
    print()
    
    # Test variable reads
    print("6. Testing variable reads...")
    for var_name in test_variables:
        try:
            response = requests.get(f"{API_BASE}/variables/{var_name}/read")
            if response.status_code == 200:
                result = response.json()
                print(f"   {var_name} = {result.get('value')}")
                if result.get('note'):
                    print(f"     Note: {result.get('note')}")
            else:
                print(f"   {var_name}: Read failed")
                
        except Exception as e:
            print(f"   Error reading {var_name}: {e}")
    
    print()
    
    # Test multiple variable read
    print("7. Testing multiple variable read...")
    try:
        read_data = {
            "variables": ["debug_bypass", "motorVars_M1", "calibration"]
        }
        response = requests.post(f"{API_BASE}/variables/read_multiple", json=read_data)
        result = response.json()
        
        if result.get('success'):
            print("   Multi-read results:")
            for var, value in result.get('variables', {}).items():
                print(f"     {var} = {value}")
        else:
            print(f"   Multi-read failed: {result.get('error')}")
            
    except Exception as e:
        print(f"   Error in multi-read: {e}")
    
    print()
    
    # Test monitoring
    print("8. Testing monitoring...")
    try:
        # Start monitoring
        monitor_data = {
            "variables": ["debug_bypass", "motorVars_M1"],
            "rate_hz": 5
        }
        response = requests.post(f"{API_BASE}/monitoring/start", json=monitor_data)
        result = response.json()
        
        if result.get('success'):
            print("   Monitoring started successfully")
            print(f"   Monitoring: {result.get('variables')}")
            
            # Wait and get data
            print("   Waiting 2 seconds for data...")
            time.sleep(2)
            
            response = requests.get(f"{API_BASE}/monitoring/data")
            result = response.json()
            print(f"   Current data: {result.get('data')}")
            
            # Stop monitoring
            requests.post(f"{API_BASE}/monitoring/stop")
            print("   Monitoring stopped")
            
        else:
            print(f"   Monitoring failed: {result.get('error')}")
            
    except Exception as e:
        print(f"   Error in monitoring: {e}")
    
    print()
    
    # Test status
    print("9. Testing system status...")
    try:
        response = requests.get(f"{API_BASE}/status")
        result = response.json()
        print(f"   Hardware connected: {result.get('hardware_connected')}")
        print(f"   Monitoring active: {result.get('monitoring_active')}")
        print(f"   Variables available: {result.get('variable_count')}")
        
    except Exception as e:
        print(f"   Error getting status: {e}")
    
    print()
    print("API Test Complete!")

if __name__ == "__main__":
    test_api()