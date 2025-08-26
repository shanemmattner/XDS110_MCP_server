#!/usr/bin/env python3
"""
Simple Test Dashboard - Just verify we can read and display variable values
"""

import dash
from dash import dcc, html, Input, Output, State
import argparse
from pathlib import Path
import sys
import logging
from datetime import datetime

# Import our legacy dashboard connector
from legacy_dash_connector import (
    initialize_hardware, 
    get_available_variables,
    disconnect
)

# Import the legacy loop connector directly for testing
from legacy_loop_connector import LegacyLoopConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Dash app
app = dash.Dash(__name__, title="XDS110 Simple Test Dashboard")

# Global connector for direct testing
test_connector = None
hardware_ready = False

# Simple layout
app.layout = html.Div([
    html.H1("🔧 XDS110 Simple Test Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    html.Div([
        html.H3("Connection Status:", style={'color': '#34495e'}),
        html.Div(id='connection-status', 
                style={'fontSize': '18px', 'fontWeight': 'bold', 'margin': '10px 0'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    html.Div([
        html.H3("Variable Count:", style={'color': '#34495e'}),
        html.Div(id='variable-count', 
                style={'fontSize': '18px', 'fontWeight': 'bold', 'margin': '10px 0'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    html.Div([
        html.H3("Test Variable Reading:", style={'color': '#34495e'}),
        html.Button('Read motorVars_M1.motorState', 
                   id='read-motor-state-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
        html.Button('Read debug_bypass', 
                   id='read-debug-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
        html.Button('Read motorVars_M1 (base)', 
                   id='read-motor-base-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    html.Div([
        html.H3("Results:", style={'color': '#34495e'}),
        html.Div(id='test-results', 
                children="Click a button to test variable reading...",
                style={'fontSize': '14px', 'fontFamily': 'monospace', 'backgroundColor': '#ecf0f1',
                      'padding': '15px', 'borderRadius': '5px', 'minHeight': '200px',
                      'whiteSpace': 'pre-wrap'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    # Update interval for status
    dcc.Interval(
        id='status-interval',
        interval=2000,  # 2 seconds
        n_intervals=0
    ),
], style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'})

@app.callback(
    [Output('connection-status', 'children'),
     Output('connection-status', 'style'),
     Output('variable-count', 'children')],
    Input('status-interval', 'n_intervals')
)
def update_status(n):
    """Update connection status and variable count"""
    global hardware_ready, test_connector
    
    if not hardware_ready:
        return "🔄 Initializing...", {'color': '#f39c12'}, "Waiting for initialization..."
    
    if test_connector:
        variables = test_connector.get_available_variables()
        var_count = len(variables)
        
        if var_count > 0:
            status = f"✅ Connected - Hardware Ready"
            style = {'color': '#27ae60', 'fontSize': '18px', 'fontWeight': 'bold'}
            count = f"📊 Found {var_count} variables in MAP file"
        else:
            status = "⚠️ Connected but no variables found"
            style = {'color': '#e67e22', 'fontSize': '18px', 'fontWeight': 'bold'}
            count = "No variables available"
    else:
        status = "❌ Not connected"
        style = {'color': '#e74c3c', 'fontSize': '18px', 'fontWeight': 'bold'}
        count = "Connection failed"
    
    return status, style, count

@app.callback(
    Output('test-results', 'children'),
    [Input('read-motor-state-btn', 'n_clicks'),
     Input('read-debug-btn', 'n_clicks'),
     Input('read-motor-base-btn', 'n_clicks')],
    prevent_initial_call=True
)
def test_variable_reading(motor_state_clicks, debug_clicks, motor_base_clicks):
    """Test reading specific variables"""
    global test_connector, hardware_ready
    
    if not hardware_ready or not test_connector:
        return "❌ Hardware not ready for testing"
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        return "No button clicked yet..."
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    results = []
    results.append(f"=== Variable Reading Test - {datetime.now().strftime('%H:%M:%S')} ===\\n")
    
    try:
        if button_id == 'read-motor-state-btn':
            results.append("Testing: motorVars_M1.motorState")
            test_vars = ['motorVars_M1.motorState']
            
        elif button_id == 'read-debug-btn':
            results.append("Testing: debug_bypass (structured variable)")
            test_vars = ['debug_bypass']
            
        elif button_id == 'read-motor-base-btn':
            results.append("Testing: motorVars_M1 (base variable)")
            test_vars = ['motorVars_M1']
        
        results.append(f"Variables to read: {test_vars}\\n")
        
        # Use the legacy loop connector to read variables
        read_results = test_connector.run_monitoring_cycle(test_vars)
        
        if read_results:
            results.append("✅ Read Results:")
            for var_name, value in read_results.items():
                if value is not None:
                    results.append(f"  {var_name:25s} = {value}")
                else:
                    results.append(f"  {var_name:25s} = NULL (failed to read)")
        else:
            results.append("❌ No results returned from monitoring cycle")
            
        # Also test available variables
        available_vars = test_connector.get_available_variables()
        results.append(f"\\n📋 Available variables: {len(available_vars)}")
        
        # Show which of our test variables are available
        results.append("\\n🔍 Test variable availability:")
        for var in test_vars:
            base_var = var.split('.')[0]
            if base_var in available_vars:
                results.append(f"  ✅ {base_var} (base variable found in MAP)")
            else:
                results.append(f"  ❌ {base_var} (NOT found in MAP)")
        
        # Show some sample available variables
        results.append(f"\\n📄 Sample available variables:")
        sample_vars = [v for v in available_vars if 'motor' in v.lower() or 'debug' in v.lower()][:10]
        if not sample_vars:
            sample_vars = available_vars[:10]
        
        for var in sample_vars:
            results.append(f"  - {var}")
            
    except Exception as e:
        results.append(f"❌ Error during test: {str(e)}")
    
    return "\\n".join(results)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='XDS110 Simple Test Dashboard')
    parser.add_argument('--ccxml', required=True, help='Path to CCXML configuration file')
    parser.add_argument('--map', required=True, help='Path to MAP file') 
    parser.add_argument('--binary', help='Path to binary file to load (optional)')
    parser.add_argument('--port', type=int, default=8053, help='Dashboard port (default: 8053)')
    parser.add_argument('--host', default='0.0.0.0', help='Dashboard host (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Validate files exist
    ccxml_path = Path(args.ccxml)
    map_path = Path(args.map)
    
    if not ccxml_path.exists():
        logger.error(f"CCXML file not found: {ccxml_path}")
        sys.exit(1)
    
    if not map_path.exists():
        logger.error(f"MAP file not found: {map_path}")
        sys.exit(1)
    
    binary_path = None
    if args.binary:
        binary_path = Path(args.binary)
        if not binary_path.exists():
            logger.error(f"Binary file not found: {binary_path}")
            sys.exit(1)
    
    # Initialize hardware using legacy loop connector directly
    global test_connector, hardware_ready
    
    logger.info("Initializing XDS110 connection for simple test...")
    try:
        test_connector = LegacyLoopConnector(
            str(ccxml_path), 
            str(map_path), 
            str(binary_path) if binary_path else None
        )
        
        # Test that we can get variables
        variables = test_connector.get_available_variables()
        if variables:
            logger.info(f"✅ Found {len(variables)} variables in MAP file")
            hardware_ready = True
        else:
            logger.error("❌ No variables found in MAP file")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize hardware: {e}")
        sys.exit(1)
    
    # Run the simple test dashboard
    logger.info(f"Starting simple test dashboard on http://{args.host}:{args.port}")
    app.run_server(debug=False, host=args.host, port=args.port)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\\nShutting down...")
        if test_connector:
            test_connector.disconnect()
        sys.exit(0)