#!/usr/bin/env python3
"""
Working Script Dashboard - Uses the proven working read_motor_vars_v1.js script
Shows real-time output and demonstrates successful variable reading
"""

import dash
from dash import dcc, html, Input, Output, State
import argparse
from pathlib import Path
import sys
import logging
from datetime import datetime
import subprocess
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Dash app
app = dash.Dash(__name__, title="XDS110 Working Script Dashboard")

# Global state
script_output = []
script_running = False
output_lock = threading.Lock()

def run_working_script() -> str:
    """Run the proven working DSS script and capture output"""
    global script_output, script_running
    
    script_running = True
    script_output.clear()
    
    # Path to fixed script with absolute paths
    script_path = "/home/shane/shane/XDS110_MCP_server/legacy_ti_debugger/js_scripts/read_motor_vars_absolute.js"
    
    try:
        # Change to the script directory so relative paths work
        script_dir = Path(script_path).parent
        
        dss_cmd = [
            "/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh",
            "read_motor_vars_absolute.js"
        ]
        
        logger.info("Running working DSS script...")
        
        with output_lock:
            script_output.append(f"=== Starting Working Script at {datetime.now().strftime('%H:%M:%S')} ===")
            script_output.append(f"Command: {' '.join(dss_cmd)}")
            script_output.append(f"Working directory: {script_dir}")
            script_output.append("")
        
        process = subprocess.Popen(
            dss_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=script_dir
        )
        
        # Read output in real-time
        def read_output(pipe, prefix):
            try:
                for line in iter(pipe.readline, ''):
                    if line.strip():
                        with output_lock:
                            script_output.append(f"{prefix}: {line.strip()}")
            except Exception as e:
                with output_lock:
                    script_output.append(f"{prefix}_ERROR: {e}")
        
        # Start threads to read stdout and stderr
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, "DSS"))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, "ERR"))
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Wait for output threads to finish
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)
        
        with output_lock:
            script_output.append("")
            script_output.append(f"=== Script completed with return code: {return_code} ===")
            script_output.append(f"Finished at {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        with output_lock:
            script_output.append(f"SCRIPT_EXCEPTION: {e}")
    
    finally:
        script_running = False

def run_check_init_script() -> str:
    """Run the check_init_state.js script"""
    global script_output, script_running
    
    script_running = True
    
    script_path = "/home/shane/shane/XDS110_MCP_server/legacy_ti_debugger/js_scripts/check_init_state.js"
    script_dir = Path(script_path).parent
    
    try:
        dss_cmd = [
            "/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh", 
            "check_init_state.js"
        ]
        
        with output_lock:
            script_output.append("")
            script_output.append(f"=== Running Init Check Script at {datetime.now().strftime('%H:%M:%S')} ===")
        
        process = subprocess.run(
            dss_cmd,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        with output_lock:
            if process.stdout:
                for line in process.stdout.split('\n'):
                    if line.strip():
                        script_output.append(f"INIT: {line}")
            
            if process.stderr:
                for line in process.stderr.split('\n'):
                    if line.strip():
                        script_output.append(f"INIT_ERR: {line}")
            
            script_output.append(f"=== Init script completed with code: {process.returncode} ===")
    
    except Exception as e:
        with output_lock:
            script_output.append(f"INIT_EXCEPTION: {e}")
    
    finally:
        script_running = False

# Dashboard layout
app.layout = html.Div([
    html.H1("🔧 XDS110 Working Script Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    html.Div([
        html.H3("Script Status:", style={'color': '#34495e'}),
        html.Div(id='script-status', 
                style={'fontSize': '18px', 'fontWeight': 'bold', 'margin': '10px 0'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    html.Div([
        html.H3("Script Controls:", style={'color': '#34495e'}),
        html.Button('Run Motor Variables Script', 
                   id='run-motor-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
        html.Button('Run Init Check Script', 
                   id='run-init-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
        html.Button('Clear Output', 
                   id='clear-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#95a5a6', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    html.Div([
        html.H3("DSS Script Output (Real-time):", style={'color': '#34495e'}),
        html.Div(id='script-output', 
                children="Click 'Run Motor Variables Script' to test variable reading...",
                style={'fontSize': '14px', 'fontFamily': 'monospace', 'backgroundColor': '#2c3e50',
                      'color': '#ecf0f1', 'padding': '15px', 'borderRadius': '5px', 'minHeight': '500px',
                      'whiteSpace': 'pre-wrap', 'maxHeight': '700px', 'overflowY': 'auto'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    # Auto-update interval
    dcc.Interval(
        id='output-update',
        interval=500,  # 0.5 seconds for smooth updates
        n_intervals=0
    ),
], style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'})

@app.callback(
    Output('script-status', 'children'),
    Input('output-update', 'n_intervals')
)
def update_status(n):
    """Update script status"""
    global script_running
    
    if script_running:
        return "🟡 Script Running..."
    else:
        return "🟢 Ready for Commands"

@app.callback(
    Output('script-output', 'children'),
    [Input('run-motor-btn', 'n_clicks'),
     Input('run-init-btn', 'n_clicks'),
     Input('clear-btn', 'n_clicks'),
     Input('output-update', 'n_intervals')],
    prevent_initial_call=True
)
def handle_script_controls(motor_clicks, init_clicks, clear_clicks, auto_update):
    """Handle script control buttons and show live output"""
    global script_output, script_running
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return "No action..."
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'run-motor-btn':
        # Start motor variables script in background thread
        thread = threading.Thread(target=run_working_script, daemon=True)
        thread.start()
        return "🚀 Starting motor variables script..."
    
    elif trigger_id == 'run-init-btn':
        # Start init check script in background thread  
        thread = threading.Thread(target=run_check_init_script, daemon=True)
        thread.start()
        return "🔍 Starting init check script..."
    
    elif trigger_id == 'clear-btn':
        # Clear output
        with output_lock:
            script_output.clear()
        return "Output cleared"
    
    elif trigger_id == 'output-update':
        # Return current output
        with output_lock:
            if script_output:
                return '\n'.join(script_output)
            else:
                return "No output yet... Click a script button to start!"
    
    return "Unknown action"

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='XDS110 Working Script Dashboard')
    parser.add_argument('--port', type=int, default=8055, help='Dashboard port (default: 8055)')
    parser.add_argument('--host', default='0.0.0.0', help='Dashboard host (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Run the dashboard
    logger.info(f"Starting working script dashboard on http://{args.host}:{args.port}")
    app.run_server(debug=False, host=args.host, port=args.port)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\\nShutting down...")
        sys.exit(0)