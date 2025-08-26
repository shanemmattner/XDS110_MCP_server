#!/usr/bin/env python3
"""
Simple test dashboard for the flexible API
This is separate from existing dashboards and won't interfere with them
"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import json
from datetime import datetime

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# API configuration
API_URL = "http://localhost:5001"

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("API Test Dashboard", className="text-center mb-4"),
            html.P("Simple dashboard for testing the flexible variable API", className="text-center"),
            html.Hr()
        ])
    ]),
    
    # Connection status
    dbc.Row([
        dbc.Col([
            dbc.Alert(id="api-status", color="info", children="Checking API connection...")
        ])
    ], className="mb-3"),
    
    # Quick test buttons
    dbc.Row([
        dbc.Col([
            html.H4("Quick Variable Tests"),
            dbc.ButtonGroup([
                dbc.Button("Read motorState", id="btn-motor-state", color="primary", className="me-1"),
                dbc.Button("Read position", id="btn-position", color="primary", className="me-1"),
                dbc.Button("Read current", id="btn-current", color="primary", className="me-1"),
                dbc.Button("Read debug_bypass", id="btn-debug", color="primary", className="me-1"),
            ])
        ])
    ], className="mb-4"),
    
    # Custom variable input
    dbc.Row([
        dbc.Col([
            html.H4("Custom Variable"),
            dbc.InputGroup([
                dbc.Input(id="custom-var-input", placeholder="e.g., motorVars_M1.motorState"),
                dbc.Button("Read", id="btn-custom", color="success")
            ])
        ])
    ], className="mb-4"),
    
    # Results display
    dbc.Row([
        dbc.Col([
            html.H4("Results"),
            dbc.Card([
                dbc.CardBody([
                    html.Div(id="results-display", style={"fontFamily": "monospace"})
                ])
            ])
        ])
    ]),
    
    # Auto-refresh interval
    dcc.Interval(id="status-interval", interval=5000)  # 5 seconds
], fluid=True)

# Callbacks
@app.callback(
    Output("api-status", "children"),
    Output("api-status", "color"),
    Input("status-interval", "n_intervals")
)
def check_api_status(n):
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=1)
        if response.status_code == 200:
            return "✅ API is running on port 5001", "success"
        else:
            return "⚠️ API returned non-200 status", "warning"
    except:
        return "❌ API is not running (start with: python3 src/api/flexible_variable_api.py)", "danger"

@app.callback(
    Output("results-display", "children"),
    [Input("btn-motor-state", "n_clicks"),
     Input("btn-position", "n_clicks"),
     Input("btn-current", "n_clicks"),
     Input("btn-debug", "n_clicks"),
     Input("btn-custom", "n_clicks")],
    State("custom-var-input", "value"),
    prevent_initial_call=True
)
def read_variable(motor_clicks, pos_clicks, current_clicks, debug_clicks, custom_clicks, custom_var):
    """Read variables when buttons are clicked"""
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        return "No data"
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Map button to variable
    variable_map = {
        "btn-motor-state": "motorVars_M1.motorState",
        "btn-position": "motorVars_M1.absPosition_rad", 
        "btn-current": "motorVars_M1.Idq_out_A.value[0]",
        "btn-debug": "debug_bypass.bypass_alignment_called",
        "btn-custom": custom_var
    }
    
    variable = variable_map.get(button_id)
    if not variable:
        return "No variable selected"
    
    # Call API
    try:
        response = requests.get(f"{API_URL}/api/read/{variable}", timeout=10)
        data = response.json()
        
        if data.get('success'):
            timestamp = datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S')
            return html.Div([
                html.H5(f"Variable: {data['variable']}"),
                html.H3(f"Value: {data['value']}", className="text-primary"),
                html.Small(f"Read at: {timestamp}")
            ])
        else:
            return html.Div([
                html.H5(f"Variable: {variable}"),
                html.P(f"Error: {data.get('error', 'Unknown error')}", className="text-danger")
            ])
            
    except requests.exceptions.Timeout:
        return html.Div([
            html.H5(f"Variable: {variable}"),
            html.P("Timeout: DSS script took too long", className="text-warning")
        ])
    except Exception as e:
        return html.Div([
            html.H5(f"Variable: {variable}"),
            html.P(f"Error: {str(e)}", className="text-danger")
        ])

if __name__ == "__main__":
    print("\n" + "="*60)
    print("API Test Dashboard")
    print("="*60)
    print("This dashboard tests the flexible variable API")
    print("Make sure the API is running first:")
    print("  python3 src/api/flexible_variable_api.py")
    print("\nDashboard will be available at: http://localhost:8052")
    print("="*60 + "\n")
    
    app.run_server(debug=True, port=8052)