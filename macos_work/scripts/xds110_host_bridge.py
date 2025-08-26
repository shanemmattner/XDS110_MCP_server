#!/usr/bin/env python3
"""
XDS110 Host Bridge for macOS
Provides TCP API to access XDS110 from Docker containers
"""

import subprocess
import json
import sys
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# XDS110 detection info
XDS110_INFO = {
    "vendor_id": "0x0451",
    "product_id": "0xbef3",
    "serial": "LS4104RF",
    "name": "XDS110 (03.00.00.32) Embed with CMSIS-DAP",
    "detected": True,
    "location": "0x02100000"
}

# Paths for TI tools (adjust for macOS)
CCS_PATH = "/Applications/ti/ccs2020"  # Adjust if different
DSS_PATH = f"{CCS_PATH}/ccs/ccs_base/scripting/bin/dss.sh"

@app.route('/status', methods=['GET'])
def get_status():
    """Check XDS110 connection status"""
    # Check if XDS110 is still connected
    result = subprocess.run(
        ["system_profiler", "SPUSBDataType"],
        capture_output=True,
        text=True
    )
    
    xds110_connected = "0x0451" in result.stdout and "0xbef3" in result.stdout
    
    return jsonify({
        "status": "connected" if xds110_connected else "disconnected",
        "device": XDS110_INFO if xds110_connected else None,
        "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip()
    })

@app.route('/dss/execute', methods=['POST'])
def execute_dss():
    """Execute DSS JavaScript scripts"""
    if not os.path.exists(DSS_PATH):
        return jsonify({
            "status": "error",
            "message": f"DSS not found at {DSS_PATH}. Please install Code Composer Studio."
        }), 404
    
    script_path = request.json.get('script')
    if not script_path:
        return jsonify({
            "status": "error",
            "message": "No script path provided"
        }), 400
    
    # Execute DSS script
    result = subprocess.run(
        [DSS_PATH, script_path],
        capture_output=True,
        text=True,
        cwd=request.json.get('working_dir', '.')
    )
    
    return jsonify({
        "status": "success" if result.returncode == 0 else "error",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    })

@app.route('/usb/info', methods=['GET'])
def get_usb_info():
    """Get detailed USB information"""
    result = subprocess.run(
        ["system_profiler", "SPUSBDataType", "-json"],
        capture_output=True,
        text=True
    )
    
    try:
        usb_data = json.loads(result.stdout)
        return jsonify(usb_data)
    except:
        return jsonify({"raw": result.stdout})

@app.route('/test', methods=['GET'])
def test_connection():
    """Test endpoint"""
    return jsonify({
        "message": "XDS110 Host Bridge is running",
        "platform": sys.platform,
        "python": sys.version
    })

if __name__ == '__main__':
    print("=== XDS110 Host Bridge for macOS ===")
    print("This bridge allows Docker containers to access XDS110")
    print(f"XDS110 Status: {XDS110_INFO}")
    print("\nStarting server on http://0.0.0.0:5555")
    print("Docker containers can access this at host.docker.internal:5555")
    print("\nPress Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5555, debug=True)