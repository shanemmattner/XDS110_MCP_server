#!/usr/bin/env python3
"""
Flexible Variable API Server
Provides REST endpoints for reading any TI C2000 variable including struct members
"""

import json
import subprocess
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

# Configuration
DSS_PATH = "/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh"
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "legacy_ti_debugger" / "js_scripts"
TEMP_SCRIPT = SCRIPTS_DIR / "temp_read_variable.js"

# Global state for caching
variable_cache = {}
cache_lock = threading.Lock()
CACHE_TTL = 5  # seconds

class VariableReader:
    """Handles reading variables from TI C2000 using DSS scripts"""
    
    def __init__(self):
        self.ccxml_path = "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml"
        self.binary_path = "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out"
        
    def create_read_script(self, variable_names: List[str]) -> str:
        """Use the pre-made API script with arguments"""
        # We'll use the api_read_variable.js script with arguments instead
        return None  # Not used anymore
    
    def read_variables(self, variable_names: List[str]) -> Dict[str, Any]:
        """Read multiple variables from the target"""
        # Use the api_read_variable.js script with arguments
        script_path = SCRIPTS_DIR / "api_read_variable.js"
        
        # Execute DSS script with variable names as arguments
        cmd = [DSS_PATH, str(script_path)] + variable_names
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=25,  # Give DSS more time for firmware loading
                cwd=str(SCRIPTS_DIR)
            )
            
            # Parse output
            output = result.stdout + result.stderr
            variables = {}
            
            for line in output.split('\n'):
                if line.startswith('VAR_READ:'):
                    match = re.match(r'VAR_READ:(.+?)=(.+)', line)
                    if match:
                        var_name = match.group(1)
                        var_value = match.group(2)
                        # Try to parse as number - always try float first for precision
                        try:
                            variables[var_name] = float(var_value)
                        except:
                            variables[var_name] = var_value
                            
                elif line.startswith('VAR_ERROR:'):
                    match = re.match(r'VAR_ERROR:(.+?)=(.+)', line)
                    if match:
                        var_name = match.group(1)
                        error_msg = match.group(2)
                        variables[var_name] = {"error": error_msg}
            
            return variables
            
        except subprocess.TimeoutExpired:
            return {"error": "Timeout reading variables"}
        except Exception as e:
            return {"error": str(e)}
    
    def parse_struct_path(self, path: str) -> List[str]:
        """Parse a struct path into components"""
        # Handle array indexing like value[0]
        parts = []
        current = ""
        in_brackets = False
        
        for char in path:
            if char == '[':
                if current:
                    parts.append(current)
                    current = ""
                in_brackets = True
                current = "["
            elif char == ']':
                current += "]"
                parts.append(current)
                current = ""
                in_brackets = False
            elif char == '.' and not in_brackets:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
            
        return parts

# Initialize reader
reader = VariableReader()

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "flexible_variable_api"})

@app.route('/api/read', methods=['POST'])
def read_variables():
    """
    Read one or more variables
    
    Request body:
    {
        "variables": ["motorVars_M1.motorState", "debug_bypass.bypass_alignment_called"]
    }
    
    Response:
    {
        "success": true,
        "data": {
            "motorVars_M1.motorState": 0,
            "debug_bypass.bypass_alignment_called": false
        },
        "timestamp": 1234567890
    }
    """
    try:
        data = request.json
        if not data or 'variables' not in data:
            return jsonify({"success": False, "error": "Missing 'variables' in request"}), 400
        
        variable_names = data['variables']
        if not isinstance(variable_names, list):
            variable_names = [variable_names]
        
        # Check cache first
        results = {}
        uncached = []
        current_time = time.time()
        
        with cache_lock:
            for var_name in variable_names:
                if var_name in variable_cache:
                    cached_data = variable_cache[var_name]
                    if current_time - cached_data['timestamp'] < CACHE_TTL:
                        results[var_name] = cached_data['value']
                    else:
                        uncached.append(var_name)
                else:
                    uncached.append(var_name)
        
        # Read uncached variables
        if uncached:
            new_values = reader.read_variables(uncached)
            
            # Update cache and results
            with cache_lock:
                for var_name, value in new_values.items():
                    results[var_name] = value
                    variable_cache[var_name] = {
                        'value': value,
                        'timestamp': current_time
                    }
        
        return jsonify({
            "success": True,
            "data": results,
            "timestamp": current_time
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/read/<path:variable_path>', methods=['GET'])
def read_single_variable(variable_path):
    """
    Read a single variable by path
    
    Example: GET /api/read/motorVars_M1.motorState
    """
    try:
        result = reader.read_variables([variable_path])
        
        if variable_path in result:
            return jsonify({
                "success": True,
                "variable": variable_path,
                "value": result[variable_path],
                "timestamp": time.time()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Variable not found or error reading"
            }), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/struct/<path:struct_base>', methods=['GET'])
def read_struct_members(struct_base):
    """
    Read all common members of a struct
    
    Example: GET /api/struct/motorVars_M1
    """
    # Common struct members to try
    common_members = [
        "motorState",
        "absPosition_rad",
        "angleENC_rad",
        "angleFOC_rad",
        "Idq_out_A.value[0]",
        "Idq_out_A.value[1]",
        "IsRef_A",
        "speed_Hz",
        "speedINT_Hz",
        "speedAbs_Hz"
    ]
    
    variables_to_read = [f"{struct_base}.{member}" for member in common_members]
    
    try:
        results = reader.read_variables(variables_to_read)
        
        # Filter out errors
        valid_results = {k: v for k, v in results.items() if not isinstance(v, dict) or 'error' not in v}
        
        return jsonify({
            "success": True,
            "struct": struct_base,
            "members": valid_results,
            "timestamp": time.time()
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def batch_read():
    """
    Read multiple variables with different options
    
    Request body:
    {
        "requests": [
            {"variable": "motorVars_M1.motorState", "alias": "motor_state"},
            {"variable": "debug_bypass.bypass_alignment_called", "alias": "bypass_called"}
        ]
    }
    """
    try:
        data = request.json
        if not data or 'requests' not in data:
            return jsonify({"success": False, "error": "Missing 'requests' in request"}), 400
        
        requests = data['requests']
        variable_names = [req['variable'] for req in requests]
        
        results = reader.read_variables(variable_names)
        
        # Map to aliases if provided
        response_data = {}
        for req in requests:
            var_name = req['variable']
            alias = req.get('alias', var_name)
            if var_name in results:
                response_data[alias] = results[var_name]
        
        return jsonify({
            "success": True,
            "data": response_data,
            "timestamp": time.time()
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/monitor', methods=['POST'])
def monitor_variables():
    """
    Start monitoring variables (returns current values, client should poll)
    
    Request body:
    {
        "variables": ["motorVars_M1.motorState"],
        "interval": 500  # milliseconds
    }
    """
    try:
        data = request.json
        variable_names = data.get('variables', [])
        
        # Just read once - client will poll
        results = reader.read_variables(variable_names)
        
        return jsonify({
            "success": True,
            "data": results,
            "timestamp": time.time(),
            "note": "Poll this endpoint at your desired interval"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the variable cache"""
    with cache_lock:
        variable_cache.clear()
    
    return jsonify({"success": True, "message": "Cache cleared"})

@app.route('/api/info', methods=['GET'])
def api_info():
    """Get API information and available endpoints"""
    return jsonify({
        "service": "Flexible Variable API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/api/read", "method": "POST", "description": "Read multiple variables"},
            {"path": "/api/read/<variable>", "method": "GET", "description": "Read single variable"},
            {"path": "/api/struct/<struct_name>", "method": "GET", "description": "Read struct members"},
            {"path": "/api/batch", "method": "POST", "description": "Batch read with aliases"},
            {"path": "/api/monitor", "method": "POST", "description": "Monitor variables (poll-based)"},
            {"path": "/api/cache/clear", "method": "POST", "description": "Clear variable cache"},
            {"path": "/api/health", "method": "GET", "description": "Health check"},
            {"path": "/api/info", "method": "GET", "description": "API information"}
        ],
        "examples": {
            "read_single": "GET /api/read/motorVars_M1.motorState",
            "read_struct": "GET /api/struct/motorVars_M1",
            "read_array": "GET /api/read/motorVars_M1.Idq_out_A.value[0]",
            "read_multiple": {
                "method": "POST /api/read",
                "body": {"variables": ["motorVars_M1.motorState", "debug_bypass.bypass_alignment_called"]}
            }
        }
    })

if __name__ == '__main__':
    print("Starting Flexible Variable API Server...")
    print("Access the API at: http://localhost:5001")
    print("Example: curl http://localhost:5001/api/read/motorVars_M1.motorState")
    app.run(host='0.0.0.0', port=5001, debug=True)