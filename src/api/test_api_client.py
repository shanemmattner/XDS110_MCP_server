#!/usr/bin/env python3
"""
Test client for Flexible Variable API
Demonstrates various ways to read TI C2000 variables
"""

import requests
import json
import time
from typing import Dict, Any, List

class VariableAPIClient:
    """Client for interacting with the Flexible Variable API"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def read_single(self, variable_path: str) -> Dict[str, Any]:
        """Read a single variable"""
        response = self.session.get(f"{self.base_url}/api/read/{variable_path}")
        return response.json()
    
    def read_multiple(self, variables: List[str]) -> Dict[str, Any]:
        """Read multiple variables"""
        response = self.session.post(
            f"{self.base_url}/api/read",
            json={"variables": variables}
        )
        return response.json()
    
    def read_struct(self, struct_name: str) -> Dict[str, Any]:
        """Read all members of a struct"""
        response = self.session.get(f"{self.base_url}/api/struct/{struct_name}")
        return response.json()
    
    def batch_read(self, requests: List[Dict]) -> Dict[str, Any]:
        """Batch read with aliases"""
        response = self.session.post(
            f"{self.base_url}/api/batch",
            json={"requests": requests}
        )
        return response.json()
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear the variable cache"""
        response = self.session.post(f"{self.base_url}/api/cache/clear")
        return response.json()

def main():
    """Test the API with various variable types"""
    client = VariableAPIClient()
    
    print("=" * 60)
    print("Flexible Variable API Test Client")
    print("=" * 60)
    
    # Test 1: Read single variable
    print("\n1. Reading single variable: motorVars_M1.motorState")
    try:
        result = client.read_single("motorVars_M1.motorState")
        if result['success']:
            print(f"   Value: {result['value']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Connection error: {e}")
    
    # Test 2: Read array element
    print("\n2. Reading array element: motorVars_M1.Idq_out_A.value[0]")
    try:
        result = client.read_single("motorVars_M1.Idq_out_A.value[0]")
        if result['success']:
            print(f"   Value: {result['value']}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Connection error: {e}")
    
    # Test 3: Read multiple variables
    print("\n3. Reading multiple variables")
    variables = [
        "motorVars_M1.motorState",
        "motorVars_M1.absPosition_rad",
        "motorVars_M1.speed_Hz",
        "debug_bypass.bypass_alignment_called"
    ]
    try:
        result = client.read_multiple(variables)
        if result['success']:
            for var, value in result['data'].items():
                if isinstance(value, dict) and 'error' in value:
                    print(f"   {var}: ERROR - {value['error']}")
                else:
                    print(f"   {var}: {value}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Connection error: {e}")
    
    # Test 4: Read struct members
    print("\n4. Reading struct members: motorVars_M1")
    try:
        result = client.read_struct("motorVars_M1")
        if result['success']:
            print(f"   Found {len(result['members'])} valid members:")
            for member, value in result['members'].items():
                print(f"   {member}: {value}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Connection error: {e}")
    
    # Test 5: Batch read with aliases
    print("\n5. Batch read with custom aliases")
    requests = [
        {"variable": "motorVars_M1.motorState", "alias": "state"},
        {"variable": "motorVars_M1.absPosition_rad", "alias": "position"},
        {"variable": "motorVars_M1.speed_Hz", "alias": "speed"}
    ]
    try:
        result = client.batch_read(requests)
        if result['success']:
            for alias, value in result['data'].items():
                print(f"   {alias}: {value}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   Connection error: {e}")
    
    # Test 6: Performance test - rapid reads
    print("\n6. Performance test - 10 rapid reads")
    start_time = time.time()
    for i in range(10):
        try:
            result = client.read_single("motorVars_M1.motorState")
            if result['success']:
                elapsed = time.time() - start_time
                print(f"   Read {i+1}: {result['value']} (t={elapsed:.3f}s)")
        except Exception as e:
            print(f"   Read {i+1}: Error - {e}")
    
    total_time = time.time() - start_time
    print(f"   Total time: {total_time:.3f}s, Average: {total_time/10:.3f}s per read")
    
    # Test 7: Clear cache
    print("\n7. Clearing cache")
    try:
        result = client.clear_cache()
        print(f"   {result.get('message', 'Cache cleared')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    main()