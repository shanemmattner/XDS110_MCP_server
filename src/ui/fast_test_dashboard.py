#!/usr/bin/env python3
"""
Fast Test Dashboard - Using persistent DSS connection for rapid variable reads
"""

import dash
from dash import dcc, html, Input, Output, State
import argparse
from pathlib import Path
import sys
import logging
from datetime import datetime
import subprocess
import tempfile
import threading
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Dash app
app = dash.Dash(__name__, title="XDS110 Fast Test Dashboard")

# Global state
dss_process = None
temp_dir = None
session_active = False
session_lock = threading.Lock()
last_read_results = {}

def create_persistent_dss_script(ccxml_path: str, binary_path: str = None) -> str:
    """Create a simplified persistent DSS script using proven working syntax"""
    return f"""
// Fast DSS Session - Based on working read_motor_vars_v1.js
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

print("=== Starting Fast DSS Session ===");

var debugSession = null;

try {{
    // Connect using proven working method
    var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
    ds.setConfig("{ccxml_path}");
    
    debugSession = ds.openSession("*", "C28xx_CPU1");
    debugSession.target.connect();
    print("Connected to target");
    
    // Load firmware
    {f'''
    print("Loading firmware...");
    try {{
        debugSession.memory.loadProgram("{binary_path}");
        print("Firmware loaded");
    }} catch (e) {{
        print("Could not load firmware: " + e.message);
    }}
    ''' if binary_path else '// No binary to load'}
    
    // Halt target  
    debugSession.target.halt();
    print("TARGET_READY");

// Main read loop - simplified for testing
print("READY_FOR_READS");

// Read a few test variables
try {{
    var motorVars = session.expression.evaluate("motorVars_M1");
    print("READ_RESULT:motorVars_M1=" + motorVars);
}} catch (e) {{
    print("READ_ERROR:motorVars_M1:" + e.toString());
}}

try {{
    var debug_bypass = session.expression.evaluate("debug_bypass");  
    print("READ_RESULT:debug_bypass=" + debug_bypass);
}} catch (e) {{
    print("READ_ERROR:debug_bypass:" + e.toString());
}}

try {{
    var systemVars = session.expression.evaluate("systemVars");
    print("READ_RESULT:systemVars=" + systemVars);
}} catch (e) {{
    print("READ_ERROR:systemVars:" + e.toString());
}}

print("READS_COMPLETE");

// Keep session alive for 30 seconds
for (var i = 0; i < 30; i++) {{
    java.lang.Thread.sleep(1000);
    
    // Try to read motorVars_M1.motorState every second
    try {{
        var motorState = session.expression.evaluate("motorVars_M1.motorState");
        print("LIVE_READ:" + i + ":motorState=" + motorState);
    }} catch (e) {{
        print("LIVE_ERROR:" + i + ":motorState:" + e.toString());
    }}
}}

print("SESSION_ENDING");
session.terminate();
print("SESSION_CLOSED");
"""

def start_fast_session(ccxml_path: str, binary_path: str = None) -> bool:
    """Start a fast persistent DSS session for testing"""
    global dss_process, temp_dir, session_active
    
    try:
        # Create temp directory and script
        temp_dir = tempfile.mkdtemp(prefix="xds110_fast_")
        script_file = Path(temp_dir) / "fast_session.js"
        
        with open(script_file, 'w') as f:
            f.write(create_persistent_dss_script(ccxml_path, binary_path))
        
        # Start DSS process
        dss_cmd = [
            "/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh",
            str(script_file)
        ]
        
        logger.info("Starting fast DSS session...")
        dss_process = subprocess.Popen(
            dss_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=temp_dir
        )
        
        session_active = True
        return True
        
    except Exception as e:
        logger.error(f"Failed to start fast session: {e}")
        return False

def get_session_output() -> str:
    """Get current output from DSS session"""
    global dss_process, last_read_results
    
    if not dss_process:
        return "No session active"
    
    try:
        # Read available output (non-blocking)
        output_lines = []
        
        # Check if process is still running
        if dss_process.poll() is None:
            # Process is still running
            output_lines.append("🟢 DSS Session Active")
        else:
            # Process has terminated, get final output
            stdout, stderr = dss_process.communicate()
            if stdout:
                output_lines.extend(stdout.split('\n'))
            if stderr:
                output_lines.append(f"STDERR: {stderr}")
        
        return '\n'.join(output_lines) if output_lines else "Waiting for output..."
        
    except Exception as e:
        return f"Error reading output: {e}"

# Simple layout
app.layout = html.Div([
    html.H1("🚀 XDS110 Fast Test Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),
    
    html.Div([
        html.H3("Fast Session Status:", style={'color': '#34495e'}),
        html.Div(id='session-status', 
                style={'fontSize': '18px', 'fontWeight': 'bold', 'margin': '10px 0'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    html.Div([
        html.H3("Quick Tests:", style={'color': '#34495e'}),
        html.Button('Start Fast Session', 
                   id='start-session-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#27ae60', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
        html.Button('Get Session Output', 
                   id='get-output-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
        html.Button('Stop Session', 
                   id='stop-session-btn', 
                   n_clicks=0,
                   style={'backgroundColor': '#e74c3c', 'color': 'white', 'border': 'none', 
                         'padding': '10px 20px', 'fontSize': '16px', 'borderRadius': '5px',
                         'cursor': 'pointer', 'margin': '5px'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    html.Div([
        html.H3("Session Output:", style={'color': '#34495e'}),
        html.Div(id='session-output', 
                children="Click 'Start Fast Session' to begin...",
                style={'fontSize': '14px', 'fontFamily': 'monospace', 'backgroundColor': '#ecf0f1',
                      'padding': '15px', 'borderRadius': '5px', 'minHeight': '400px',
                      'whiteSpace': 'pre-wrap', 'maxHeight': '600px', 'overflowY': 'auto'}),
    ], style={'margin': '20px', 'padding': '20px', 'border': '2px solid #bdc3c7', 'borderRadius': '5px'}),
    
    # Auto-update interval
    dcc.Interval(
        id='auto-update',
        interval=1000,  # 1 second
        n_intervals=0
    ),
], style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'})

@app.callback(
    Output('session-status', 'children'),
    Input('auto-update', 'n_intervals')
)
def update_status(n):
    """Update session status"""
    global session_active, dss_process
    
    if session_active and dss_process:
        if dss_process.poll() is None:
            return "🟢 Fast DSS Session Running"
        else:
            return "🔴 DSS Session Terminated" 
    else:
        return "⚪ No Session Active"

@app.callback(
    Output('session-output', 'children'),
    [Input('start-session-btn', 'n_clicks'),
     Input('get-output-btn', 'n_clicks'),
     Input('stop-session-btn', 'n_clicks'),
     Input('auto-update', 'n_intervals')],
    prevent_initial_call=True
)
def handle_session_controls(start_clicks, output_clicks, stop_clicks, auto_update):
    """Handle session control buttons and auto-updates"""
    global dss_process, session_active, temp_dir
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return "No action taken..."
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle button clicks
    if trigger_id == 'start-session-btn':
        # Start session
        ccxml_path = "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml"
        binary_path = "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out"
        
        if start_fast_session(ccxml_path, binary_path):
            return f"✅ Fast session started at {datetime.now().strftime('%H:%M:%S')}\\n\\nWaiting for DSS output..."
        else:
            return "❌ Failed to start fast session"
    
    elif trigger_id == 'stop-session-btn':
        # Stop session
        if dss_process:
            try:
                dss_process.terminate()
                dss_process.wait(timeout=5)
            except:
                dss_process.kill()
            dss_process = None
        
        session_active = False
        
        # Cleanup
        if temp_dir:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
        
        return "🛑 Session stopped"
    
    elif trigger_id in ['get-output-btn', 'auto-update']:
        # Get current output
        return get_session_output()
    
    return "Unknown action"

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='XDS110 Fast Test Dashboard')
    parser.add_argument('--port', type=int, default=8054, help='Dashboard port (default: 8054)')
    parser.add_argument('--host', default='0.0.0.0', help='Dashboard host (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Run the dashboard
    logger.info(f"Starting fast test dashboard on http://{args.host}:{args.port}")
    app.run_server(debug=False, host=args.host, port=args.port)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\\nShutting down...")
        # Cleanup
        if dss_process:
            dss_process.terminate()
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir)
        sys.exit(0)