#!/usr/bin/env python3
"""
Mock Variable API Server - Returns test data for development
"""

import json
import time
import random
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Mock data generator
def get_mock_value(variable_path):
    """Generate realistic mock values based on variable name"""
    if "motorState" in variable_path:
        return random.choice([0, 1, 2, 3])  # IDLE, ALIGNMENT, CTRL_RUN, CL_RUNNING
    elif "Position" in variable_path or "position" in variable_path:
        return round(random.uniform(-3.14159, 3.14159), 4)  # Radians
    elif "speed" in variable_path or "Speed" in variable_path:
        return round(random.uniform(0, 3000), 1)  # Hz
    elif "current" in variable_path or "Idq" in variable_path:
        return round(random.uniform(-10, 10), 3)  # Amps
    elif "value[0]" in variable_path:
        return round(random.uniform(-5, 5), 3)
    elif "value[1]" in variable_path:
        return round(random.uniform(-5, 5), 3)
    elif "bypass" in variable_path:
        return random.choice([True, False])
    elif "angle" in variable_path:
        return round(random.uniform(0, 6.28318), 4)
    else:
        return round(random.random() * 100, 2)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "mock_variable_api", "mode": "MOCK DATA"})

@app.route('/api/read', methods=['POST'])
def read_variables():
    """Read multiple variables (mock)"""
    try:
        data = request.json
        variables = data.get('variables', [])
        
        results = {}
        for var in variables:
            results[var] = get_mock_value(var)
        
        return jsonify({
            "success": True,
            "data": results,
            "timestamp": time.time(),
            "mode": "MOCK"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/read/<path:variable_path>', methods=['GET'])
def read_single_variable(variable_path):
    """Read single variable (mock)"""
    try:
        value = get_mock_value(variable_path)
        return jsonify({
            "success": True,
            "variable": variable_path,
            "value": value,
            "timestamp": time.time(),
            "mode": "MOCK"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/struct/<path:struct_base>', methods=['GET'])
def read_struct_members(struct_base):
    """Read struct members (mock)"""
    members = {
        f"{struct_base}.motorState": random.choice([0, 1, 2, 3]),
        f"{struct_base}.absPosition_rad": round(random.uniform(-3.14, 3.14), 4),
        f"{struct_base}.speed_Hz": round(random.uniform(0, 3000), 1),
        f"{struct_base}.angleENC_rad": round(random.uniform(0, 6.28), 4),
        f"{struct_base}.Idq_out_A.value[0]": round(random.uniform(-5, 5), 3),
        f"{struct_base}.Idq_out_A.value[1]": round(random.uniform(-5, 5), 3)
    }
    
    return jsonify({
        "success": True,
        "struct": struct_base,
        "members": members,
        "timestamp": time.time(),
        "mode": "MOCK"
    })

@app.route('/api/info', methods=['GET'])
def api_info():
    return jsonify({
        "service": "Mock Variable API",
        "version": "1.0.0",
        "mode": "MOCK DATA - Not connected to real hardware",
        "endpoints": [
            {"path": "/api/read", "method": "POST", "description": "Read multiple variables"},
            {"path": "/api/read/<variable>", "method": "GET", "description": "Read single variable"},
            {"path": "/api/struct/<struct>", "method": "GET", "description": "Read struct members"},
            {"path": "/api/health", "method": "GET", "description": "Health check"},
            {"path": "/api/info", "method": "GET", "description": "API information"}
        ]
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("MOCK Variable API Server (Test Data Only)")
    print("="*60)
    print("This server returns MOCK DATA for testing")
    print("Access at: http://localhost:5001")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5001, debug=True)