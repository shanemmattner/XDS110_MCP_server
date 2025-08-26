#!/usr/bin/env python3
"""
REST API Server for XDS110 Dashboard
Provides testable endpoints for automated testing
"""

from flask import Flask, jsonify, request
import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import threading
import time

from xds110_dash_connector import (
    initialize_hardware,
    get_available_variables,
    start_monitoring,
    stop_monitoring,
    get_current_data,
    get_variable_history,
    write_value,
    disconnect,
    xds110
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global state
hardware_initialized = False
monitoring_active = False
monitored_variables = []

# ============================================================================
# Hardware Management Endpoints
# ============================================================================

@app.route('/api/connect', methods=['POST'])
def connect_hardware():
    """Connect to XDS110 hardware"""
    global hardware_initialized
    
    data = request.get_json() or {}
    
    ccxml_path = data.get('ccxml_path')
    map_path = data.get('map_path')
    binary_path = data.get('binary_path')
    
    if not ccxml_path or not map_path:
        return jsonify({
            'success': False,
            'error': 'ccxml_path and map_path are required'
        }), 400
    
    try:
        success = initialize_hardware(ccxml_path, map_path, binary_path)
        hardware_initialized = success
        
        if success:
            variables = get_available_variables()
            return jsonify({
                'success': True,
                'message': 'Hardware connected successfully',
                'variable_count': len(variables),
                'sample_variables': list(variables)[:20]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to hardware'
            }), 500
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/disconnect', methods=['POST'])
def disconnect_hardware():
    """Disconnect from hardware"""
    global hardware_initialized, monitoring_active
    
    try:
        stop_monitoring()
        disconnect()
        hardware_initialized = False
        monitoring_active = False
        
        return jsonify({
            'success': True,
            'message': 'Hardware disconnected'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'hardware_connected': hardware_initialized,
        'monitoring_active': monitoring_active,
        'monitored_variables': monitored_variables,
        'variable_count': len(get_available_variables()) if hardware_initialized else 0,
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# Variable Discovery Endpoints
# ============================================================================

@app.route('/api/variables', methods=['GET'])
def list_variables():
    """Get all available variables"""
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    variables = get_available_variables()
    
    # Optional filtering
    filter_pattern = request.args.get('filter')
    if filter_pattern:
        import re
        try:
            pattern = re.compile(filter_pattern, re.IGNORECASE)
            variables = [v for v in variables if pattern.search(v)]
        except re.error:
            # Fall back to simple string search
            variables = [v for v in variables if filter_pattern.lower() in v.lower()]
    
    # Categorize variables
    categories = {
        'motor': [],
        'debug': [],
        'calibration': [],
        'adc': [],
        'pwm': [],
        'communication': [],
        'control': [],
        'other': []
    }
    
    for var in variables:
        var_lower = var.lower()
        if 'motor' in var_lower:
            categories['motor'].append(var)
        elif 'debug' in var_lower:
            categories['debug'].append(var)
        elif 'calib' in var_lower:
            categories['calibration'].append(var)
        elif 'adc' in var_lower:
            categories['adc'].append(var)
        elif 'pwm' in var_lower or 'epwm' in var_lower:
            categories['pwm'].append(var)
        elif any(x in var_lower for x in ['uart', 'spi', 'can', 'i2c', 'comm']):
            categories['communication'].append(var)
        elif any(x in var_lower for x in ['ctrl', 'pid', 'control']):
            categories['control'].append(var)
        else:
            categories['other'].append(var)
    
    return jsonify({
        'success': True,
        'total_count': len(variables),
        'variables': sorted(variables),
        'categories': {k: sorted(v) for k, v in categories.items()},
        'filter_applied': filter_pattern
    })

@app.route('/api/variables/<variable_name>/info', methods=['GET'])
def get_variable_info(variable_name):
    """Get information about a specific variable"""
    if not hardware_initialized or not xds110:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    if variable_name not in xds110.map_symbols:
        return jsonify({
            'success': False,
            'error': f'Variable {variable_name} not found'
        }), 404
    
    address = xds110.map_symbols[variable_name]
    
    return jsonify({
        'success': True,
        'name': variable_name,
        'address': f'0x{address:08x}',
        'address_decimal': address,
        'type': 'data' if address >= 0x8000 else 'function'  # Rough heuristic
    })

# ============================================================================
# Variable Read/Write Endpoints
# ============================================================================

@app.route('/api/variables/<variable_name>/read', methods=['GET'])
def read_variable(variable_name):
    """Read a single variable"""
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    try:
        # For now, return mock data since DSS reads are timing out
        # TODO: Fix DSS session persistence
        mock_values = {
            'debug_bypass': 0x1234,
            'motorVars_M1': 5.0,
            'motorHandle_M1': 0xd3c0,
            'motorSetVars_M1': 2.5
        }
        
        value = mock_values.get(variable_name, 0.0)
        
        return jsonify({
            'success': True,
            'variable': variable_name,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'note': 'Mock data - DSS session needs fixing for real reads'
        })
        
    except Exception as e:
        logger.error(f"Read error for {variable_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/variables/<variable_name>/write', methods=['POST'])
def write_variable_api(variable_name):
    """Write a value to a variable"""
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    data = request.get_json() or {}
    value = data.get('value')
    
    if value is None:
        return jsonify({
            'success': False,
            'error': 'value is required'
        }), 400
    
    try:
        success = write_value(variable_name, float(value))
        
        return jsonify({
            'success': success,
            'variable': variable_name,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Write error for {variable_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/variables/read_multiple', methods=['POST'])
def read_multiple_variables():
    """Read multiple variables at once"""
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    data = request.get_json() or {}
    variable_names = data.get('variables', [])
    
    if not variable_names:
        return jsonify({
            'success': False,
            'error': 'variables list is required'
        }), 400
    
    try:
        # Mock data for now
        mock_values = {
            'debug_bypass': 0x1234,
            'motorVars_M1': 5.0,
            'motorHandle_M1': 0xd3c0,
            'motorSetVars_M1': 2.5,
            'calibration': 100,
            'motor1_drive': 0.75
        }
        
        results = {}
        for var_name in variable_names:
            results[var_name] = mock_values.get(var_name, 0.0)
        
        return jsonify({
            'success': True,
            'variables': results,
            'timestamp': datetime.now().isoformat(),
            'note': 'Mock data - DSS session needs fixing for real reads'
        })
        
    except Exception as e:
        logger.error(f"Multi-read error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# Monitoring Endpoints
# ============================================================================

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring_api():
    """Start monitoring variables"""
    global monitoring_active, monitored_variables
    
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    data = request.get_json() or {}
    variables = data.get('variables', [])
    rate_hz = data.get('rate_hz', 5)
    
    if not variables:
        return jsonify({
            'success': False,
            'error': 'variables list is required'
        }), 400
    
    try:
        success = start_monitoring(variables, rate_hz)
        
        if success:
            monitoring_active = True
            monitored_variables = variables
            
            return jsonify({
                'success': True,
                'message': f'Started monitoring {len(variables)} variables at {rate_hz} Hz',
                'variables': variables,
                'rate_hz': rate_hz
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start monitoring'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring_api():
    """Stop monitoring"""
    global monitoring_active, monitored_variables
    
    try:
        stop_monitoring()
        monitoring_active = False
        monitored_variables = []
        
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitoring/data', methods=['GET'])
def get_monitoring_data():
    """Get current monitoring data"""
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    try:
        current_data = get_current_data()
        
        return jsonify({
            'success': True,
            'monitoring_active': monitoring_active,
            'variables': monitored_variables,
            'data': current_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/variables/<variable_name>/history', methods=['GET'])
def get_variable_history_api(variable_name):
    """Get historical data for a variable"""
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    duration = request.args.get('duration', type=int)  # seconds
    
    try:
        timestamps, values = get_variable_history(variable_name, duration)
        
        # Convert to list of records
        history = []
        for ts, val in zip(timestamps, values):
            history.append({
                'timestamp': ts,
                'value': val,
                'iso_time': datetime.fromtimestamp(ts).isoformat()
            })
        
        return jsonify({
            'success': True,
            'variable': variable_name,
            'count': len(history),
            'history': history,
            'duration_seconds': duration
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# Utility Endpoints
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'XDS110 Debug API',
        'timestamp': datetime.now().isoformat(),
        'hardware_connected': hardware_initialized
    })

@app.route('/api/variables/search', methods=['GET'])
def search_variables():
    """Search variables by pattern"""
    if not hardware_initialized:
        return jsonify({
            'success': False,
            'error': 'Hardware not connected'
        }), 400
    
    query = request.args.get('q', '')
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter "q" is required'
        }), 400
    
    variables = get_available_variables()
    
    # Search in variable names
    matches = []
    for var in variables:
        if query.lower() in var.lower():
            matches.append({
                'name': var,
                'address': f"0x{xds110.map_symbols[var]:08x}" if xds110 and var in xds110.map_symbols else None
            })
    
    return jsonify({
        'success': True,
        'query': query,
        'matches': sorted(matches, key=lambda x: x['name']),
        'count': len(matches)
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

def main():
    """Run the API server"""
    print("XDS110 Debug API Server")
    print("======================")
    print("Starting on http://localhost:5000")
    print("API Documentation:")
    print("  GET  /api/health                    - Health check")
    print("  POST /api/connect                   - Connect to hardware")
    print("  GET  /api/status                    - Get system status")
    print("  GET  /api/variables                 - List all variables")
    print("  GET  /api/variables/<name>/read     - Read single variable")
    print("  POST /api/variables/<name>/write    - Write single variable")
    print("  POST /api/variables/read_multiple   - Read multiple variables")
    print("  POST /api/monitoring/start          - Start monitoring")
    print("  POST /api/monitoring/stop           - Stop monitoring")
    print("  GET  /api/monitoring/data           - Get monitoring data")
    print("")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    main()