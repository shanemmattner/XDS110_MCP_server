#!/usr/bin/env python3
"""
API-based Variable Testing
Tests reading variables through REST API for automated testing
"""

import requests
import json
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import argparse

API_BASE = "http://localhost:5000/api"

class APIVariableTester:
    """Test variables through REST API"""
    
    def __init__(self, api_base: str = API_BASE):
        self.api_base = api_base
        self.results = []
        
    def check_api_health(self) -> bool:
        """Check if API server is running"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def connect_hardware(self) -> bool:
        """Connect to hardware via API"""
        obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
        
        connect_data = {
            "ccxml_path": str(obake_dir / "TMS320F280039C_LaunchPad.ccxml"),
            "map_path": str(obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"),
            "binary_path": str(obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out")
        }
        
        try:
            response = requests.post(f"{self.api_base}/connect", json=connect_data, timeout=30)
            return response.status_code == 200 and response.json().get('success', False)
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def get_all_variables(self) -> List[str]:
        """Get list of all available variables"""
        try:
            response = requests.get(f"{self.api_base}/variables")
            if response.status_code == 200:
                return response.json().get('variables', [])
        except Exception as e:
            print(f"Failed to get variables: {e}")
        return []
    
    def search_variables(self, query: str) -> List[Dict]:
        """Search for variables matching query"""
        try:
            response = requests.get(f"{self.api_base}/variables/search?q={query}")
            if response.status_code == 200:
                return response.json().get('matches', [])
        except Exception as e:
            print(f"Search failed: {e}")
        return []
    
    def read_variable(self, var_name: str) -> Dict:
        """Read a single variable"""
        try:
            response = requests.get(f"{self.api_base}/variables/{var_name}/read")
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def read_multiple_variables(self, var_names: List[str]) -> Dict:
        """Read multiple variables at once"""
        try:
            data = {"variables": var_names}
            response = requests.post(f"{self.api_base}/variables/read_multiple", json=data)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_variable_categories(self) -> Dict:
        """Test variables by category"""
        results = {}
        
        categories = {
            'debug': ['debug', 'bypass'],
            'motor': ['motor', 'Motor'],
            'calibration': ['calib'],
            'adc': ['adc', 'ADC'],
            'pwm': ['pwm', 'PWM', 'epwm', 'EPWM'],
            'control': ['ctrl', 'Ctrl', 'pid', 'PID'],
            'communication': ['uart', 'spi', 'can', 'i2c', 'rs485']
        }
        
        for category, search_terms in categories.items():
            print(f"\nTesting {category} variables...")
            
            # Find variables in this category
            category_vars = []
            for term in search_terms:
                matches = self.search_variables(term)
                for match in matches:
                    if match['name'] not in [v['name'] for v in category_vars]:
                        category_vars.append(match)
            
            if not category_vars:
                print(f"  No {category} variables found")
                continue
            
            print(f"  Found {len(category_vars)} {category} variables")
            
            # Test reading first 5 variables in category
            test_vars = [v['name'] for v in category_vars[:5]]
            
            category_results = {
                'variables_found': len(category_vars),
                'variables_tested': test_vars,
                'successful_reads': {},
                'failed_reads': {}
            }
            
            for var_name in test_vars:
                print(f"    Testing {var_name}...")
                result = self.read_variable(var_name)
                
                if result.get('success'):
                    value = result.get('value')
                    print(f"      ✅ {var_name} = {value}")
                    category_results['successful_reads'][var_name] = value
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"      ❌ {var_name}: {error}")
                    category_results['failed_reads'][var_name] = error
                
                time.sleep(0.1)  # Small delay
            
            results[category] = category_results
        
        return results
    
    def run_comprehensive_test(self) -> Dict:
        """Run comprehensive API testing"""
        test_report = {
            'test_start': datetime.now().isoformat(),
            'api_health': False,
            'hardware_connection': False,
            'variable_discovery': {},
            'category_tests': {},
            'monitoring_test': {}
        }
        
        # Test 1: API Health
        print("1. Testing API health...")
        test_report['api_health'] = self.check_api_health()
        if not test_report['api_health']:
            print("   ❌ API server not responding")
            return test_report
        print("   ✅ API server healthy")
        
        # Test 2: Hardware Connection
        print("2. Testing hardware connection...")
        test_report['hardware_connection'] = self.connect_hardware()
        if not test_report['hardware_connection']:
            print("   ❌ Hardware connection failed")
            return test_report
        print("   ✅ Hardware connected")
        
        # Test 3: Variable Discovery
        print("3. Testing variable discovery...")
        variables = self.get_all_variables()
        test_report['variable_discovery'] = {
            'total_count': len(variables),
            'sample_variables': variables[:20]
        }
        print(f"   ✅ Discovered {len(variables)} variables")
        
        # Test 4: Category Testing
        print("4. Testing variable categories...")
        test_report['category_tests'] = self.test_variable_categories()
        
        # Test 5: Monitoring
        print("\n5. Testing monitoring capability...")
        if variables:
            test_vars = variables[:3]  # Test first 3 variables
            
            # Start monitoring
            monitor_data = {
                "variables": test_vars,
                "rate_hz": 2
            }
            
            try:
                response = requests.post(f"{self.api_base}/monitoring/start", json=monitor_data)
                if response.status_code == 200:
                    print(f"   ✅ Started monitoring {test_vars}")
                    
                    # Wait and check data
                    time.sleep(3)
                    response = requests.get(f"{self.api_base}/monitoring/data")
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ Monitoring data: {data.get('data', {})}")
                        test_report['monitoring_test'] = {
                            'success': True,
                            'variables': test_vars,
                            'data': data.get('data', {})
                        }
                    
                    # Stop monitoring
                    requests.post(f"{self.api_base}/monitoring/stop")
                    print("   ✅ Monitoring stopped")
                else:
                    print(f"   ❌ Failed to start monitoring: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Monitoring error: {e}")
        
        test_report['test_end'] = datetime.now().isoformat()
        return test_report
    
    def save_test_report(self, report: Dict, filename: str = None):
        """Save test report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nTest report saved to: {filename}")
        return filename

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test XDS110 API systematically')
    parser.add_argument('--api-url', default=API_BASE, help='API base URL')
    parser.add_argument('--categories-only', action='store_true', help='Test categories only')
    parser.add_argument('--specific', nargs='+', help='Test specific variables')
    
    args = parser.parse_args()
    
    tester = APIVariableTester(args.api_url)
    
    if args.specific:
        # Test specific variables
        print(f"Testing specific variables: {args.specific}")
        # This would need the SystematicVariableTester for direct DSS access
        print("Note: Use systematic_variable_test.py for direct DSS testing")
        
    else:
        # Run comprehensive test
        report = tester.run_comprehensive_test()
        filename = tester.save_test_report(report)
        
        # Print summary
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"API Health: {'✅' if report['api_health'] else '❌'}")
        print(f"Hardware: {'✅' if report['hardware_connection'] else '❌'}")
        print(f"Variables: {report.get('variable_discovery', {}).get('total_count', 0)}")
        
        # Category summary
        category_results = report.get('category_tests', {})
        for category, results in category_results.items():
            successful = len(results.get('successful_reads', {}))
            failed = len(results.get('failed_reads', {}))
            total = successful + failed
            if total > 0:
                print(f"{category.title()}: {successful}/{total} successful ({successful/total*100:.1f}%)")

if __name__ == "__main__":
    main()