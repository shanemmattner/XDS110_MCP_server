#!/usr/bin/env python3
"""
Start both API server and Dashboard for complete testing
"""

import subprocess
import time
import threading
import sys
import signal
from pathlib import Path

def start_api_server():
    """Start the API server in background"""
    print("Starting API server on port 5000...")
    
    # Initialize hardware first
    from xds110_dash_connector import initialize_hardware
    from pathlib import Path
    
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    print("Initializing hardware...")
    success = initialize_hardware(str(ccxml_path), str(map_path), str(binary_path))
    
    if not success:
        print("❌ Failed to initialize hardware")
        return None
    
    print("✅ Hardware initialized")
    
    # Start API server
    from api_server import app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

def main():
    """Main entry point"""
    print("XDS110 Debug API + Dashboard Launcher")
    print("===================================")
    
    # Start API server in thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait for API to start
    print("Waiting for API server to start...")
    time.sleep(3)
    
    # Test API
    print("Testing API...")
    try:
        import requests
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server responding")
        else:
            print("❌ API server not responding properly")
    except Exception as e:
        print(f"❌ API server test failed: {e}")
    
    print()
    print("Services running:")
    print("  🔌 API Server:  http://localhost:5000")
    print("  📊 Dashboard:   http://localhost:8050 (if running separately)")
    print()
    print("Test commands:")
    print("  python3 test_api.py")
    print("  curl http://localhost:5000/api/health")
    print("  curl http://localhost:5000/api/variables")
    print()
    print("Press Ctrl+C to stop")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()