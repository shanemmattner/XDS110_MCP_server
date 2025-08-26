#!/usr/bin/env python3
"""
Run the XDS110 Dashboard with hardware connection
Simple example to get started quickly
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import argparse
from pathlib import Path
import sys
import logging
from datetime import datetime

# Import our legacy dashboard connector (uses proven working legacy scripts)
from legacy_dash_connector import (
    initialize_hardware, 
    get_available_variables,
    start_monitoring,
    stop_monitoring,
    get_current_data,
    get_variable_history,
    write_value,
    disconnect
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Dash app
app = dash.Dash(__name__, title="XDS110 Debug Dashboard")

# Simple layout
app.layout = html.Div([
    html.H1("XDS110 DSP Debug Dashboard", style={'textAlign': 'center'}),
    
    # Connection status
    html.Div(id='connection-status', style={'textAlign': 'center', 'fontSize': '20px', 'margin': '20px'}),
    
    # Variable selection
    html.Div([
        html.Label("Select Variables to Monitor:", style={'marginRight': '10px'}),
        dcc.Dropdown(
            id='variable-select',
            options=[],
            multi=True,
            value=[],
            style={'width': '80%', 'display': 'inline-block'}
        ),
        html.Button('Start Monitoring', id='start-btn', n_clicks=0, style={'marginLeft': '10px'}),
        html.Button('Stop', id='stop-btn', n_clicks=0, style={'marginLeft': '10px'}),
    ], style={'margin': '20px'}),
    
    # Current values display
    html.Div([
        html.H3("Current Values"),
        html.Div(id='current-values', style={'fontFamily': 'monospace', 'fontSize': '14px'})
    ], style={'margin': '20px', 'backgroundColor': '#f0f0f0', 'padding': '10px'}),
    
    # Plot
    dcc.Graph(
        id='live-plot',
        figure={
            'data': [],
            'layout': {
                'title': 'Real-Time Data',
                'xaxis': {'title': 'Time (s)'},
                'yaxis': {'title': 'Value'},
            }
        },
        style={'height': '500px'}
    ),
    
    # Write control
    html.Div([
        html.H3("Write Variable"),
        dcc.Dropdown(
            id='write-variable',
            options=[],
            value=None,
            style={'width': '300px', 'display': 'inline-block'}
        ),
        dcc.Input(
            id='write-value',
            type='number',
            placeholder='Value',
            style={'marginLeft': '10px', 'marginRight': '10px'}
        ),
        html.Button('Write', id='write-btn', n_clicks=0),
        html.Div(id='write-status', style={'marginTop': '10px'})
    ], style={'margin': '20px'}),
    
    # Update interval
    dcc.Interval(
        id='interval-component',
        interval=200,  # 5Hz update
        n_intervals=0
    ),
    
    # Hidden div to store state
    html.Div(id='monitoring-state', style={'display': 'none'}, children='stopped'),
])

# Callbacks
@app.callback(
    Output('variable-select', 'options'),
    Output('write-variable', 'options'),
    Output('connection-status', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_variable_list(n):
    """Update available variables list"""
    variables = get_available_variables()
    
    if variables:
        # Prioritize important motor and debug variables
        priority_vars = [
            'motorVars_M1', 'motorHandle_M1', 'debug_bypass', 
            'motor1_drive', 'motor_common'
        ]
        
        # Start with priority variables that exist
        selected_vars = [v for v in priority_vars if v in variables]
        
        # Add remaining variables up to 100 total, avoiding duplicates
        remaining_vars = [v for v in sorted(variables) if v not in selected_vars]
        selected_vars.extend(remaining_vars[:100-len(selected_vars)])
        
        options = [{'label': var, 'value': var} for var in selected_vars]
        status = f"✅ Connected - {len(variables)} variables available (showing {len(selected_vars)} in dropdown)"
        return options, options, status
    else:
        return [], [], "❌ Not connected"

@app.callback(
    Output('monitoring-state', 'children'),
    Input('start-btn', 'n_clicks'),
    Input('stop-btn', 'n_clicks'),
    State('variable-select', 'value')
)
def control_monitoring(start_clicks, stop_clicks, selected_vars):
    """Start/stop monitoring"""
    ctx = callback_context
    if not ctx.triggered:
        return 'stopped'
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'start-btn' and selected_vars:
        start_monitoring(selected_vars, rate_hz=5)
        return 'running'
    elif button_id == 'stop-btn':
        stop_monitoring()
        return 'stopped'
    
    return 'stopped'

@app.callback(
    Output('current-values', 'children'),
    Output('live-plot', 'figure'),
    Input('interval-component', 'n_intervals'),
    State('monitoring-state', 'children'),
    State('variable-select', 'value')
)
def update_display(n, state, selected_vars):
    """Update current values and plot"""
    
    # Current values display
    current_data = get_current_data()
    
    if current_data:
        value_text = []
        for var, value in current_data.items():
            value_text.append(f"{var:30s} = {value:12.4f}")
        current_display = html.Pre('\n'.join(value_text))
    else:
        current_display = "No data"
    
    # Update plot
    fig = go.Figure()
    
    if state == 'running' and selected_vars:
        for var in selected_vars:
            timestamps, values = get_variable_history(var, duration=30)  # Last 30 seconds
            
            if timestamps and values:
                # Convert to relative time
                if timestamps:
                    start_time = timestamps[0]
                    rel_times = [(t - start_time) for t in timestamps]
                else:
                    rel_times = []
                
                fig.add_trace(
                    go.Scatter(
                        x=rel_times,
                        y=values,
                        mode='lines',
                        name=var,
                        line={'width': 2}
                    )
                )
        
        fig.update_layout(
            title='Real-Time Data',
            xaxis_title='Time (s)',
            yaxis_title='Value',
            hovermode='x unified'
        )
    else:
        fig.update_layout(
            title='Real-Time Data (Not Monitoring)',
            xaxis_title='Time (s)',
            yaxis_title='Value'
        )
    
    return current_display, fig

@app.callback(
    Output('write-status', 'children'),
    Input('write-btn', 'n_clicks'),
    State('write-variable', 'value'),
    State('write-value', 'value')
)
def handle_write(n_clicks, variable, value):
    """Handle variable write"""
    if n_clicks == 0 or not variable or value is None:
        return ""
    
    success = write_value(variable, float(value))
    
    if success:
        return f"✅ Successfully wrote {value} to {variable}"
    else:
        return f"❌ Failed to write to {variable}"

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='XDS110 Debug Dashboard')
    parser.add_argument('--ccxml', required=True, help='Path to CCXML configuration file')
    parser.add_argument('--map', required=True, help='Path to MAP file')
    parser.add_argument('--binary', help='Path to binary file to load (optional)')
    parser.add_argument('--port', type=int, default=8050, help='Dashboard port (default: 8050)')
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
    
    # Initialize hardware
    logger.info("Initializing XDS110 connection...")
    if initialize_hardware(str(ccxml_path), str(map_path), str(binary_path) if binary_path else None):
        logger.info("✅ Hardware initialized successfully")
        
        # Get some initial variables
        variables = get_available_variables()
        logger.info(f"Found {len(variables)} variables in MAP file")
        
        if variables:
            logger.info(f"Sample variables: {', '.join(list(variables)[:10])}")
        
        # Run the dashboard
        logger.info(f"Starting dashboard on http://{args.host}:{args.port}")
        app.run_server(debug=False, host=args.host, port=args.port)
        
        # Cleanup on exit
        disconnect()
        logger.info("Disconnected from hardware")
    else:
        logger.error("Failed to initialize hardware")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        stop_monitoring()
        disconnect()
        sys.exit(0)