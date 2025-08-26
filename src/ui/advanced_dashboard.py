#!/usr/bin/env python3
"""
Advanced XDS110 Dashboard with drag-and-drop interface and struct field expansion
Much better UI for motor debugging with live updating values
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL, MATCH
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import argparse
from pathlib import Path
import sys
import logging
from datetime import datetime
import json

# Import our legacy dashboard connector
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

# Create Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title="XDS110 Advanced Debug Dashboard")

# Predefined struct field mappings for common motor structures
STRUCT_FIELDS = {
    'motorVars_M1': [
        'motorVars_M1.motorState',
        'motorVars_M1.absPosition_rad',
        'motorVars_M1.angleENC_rad',
        'motorVars_M1.angleFOC_rad',
        'motorVars_M1.enableSpeedCtrl',
        'motorVars_M1.fluxCurrent_A',
        'motorVars_M1.reversePhases',
        'motorVars_M1.Idq_out_A.value[0]',  # D-axis current
        'motorVars_M1.Idq_out_A.value[1]',  # Q-axis current
        'motorVars_M1.IsRef_A'
    ],
    'debug_bypass': [
        'debug_bypass.bypass_alignment_called',
        'debug_bypass.bypass_electrical_angle', 
        'debug_bypass.bypass_quad_position',
        'debug_bypass.cs_gpio_pin',
        'debug_bypass.bypass_mechanical_diff'
    ],
    'motorHandle_M1': [
        'motorHandle_M1.motorState',
        'motorHandle_M1.position_rad',
        'motorHandle_M1.current_A'
    ]
}

def create_variable_card(var_name, is_struct=False):
    """Create a card for a variable with expand button if it's a struct"""
    
    card_content = [
        dbc.CardBody([
            html.H6(var_name, className="card-title mb-2"),
            html.Div(id={'type': 'variable-value', 'index': var_name}, 
                    children="Not monitored", 
                    className="text-muted small")
        ])
    ]
    
    if is_struct and var_name in STRUCT_FIELDS:
        card_content.append(
            dbc.CardFooter([
                dbc.Button("Expand Fields", 
                          id={'type': 'expand-btn', 'index': var_name},
                          size="sm", 
                          color="info",
                          outline=True)
            ])
        )
    
    return dbc.Card(
        card_content,
        id={'type': 'var-card', 'index': var_name},
        className="mb-2 variable-card",
        style={"cursor": "grab", "minHeight": "100px"}
    )

def create_monitoring_item(var_name, value=None):
    """Create a monitoring item in the right panel"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.H6(var_name, className="mb-1"),
                html.Div([
                    html.Span(id={'type': 'monitor-value', 'index': var_name}, 
                             children=f"{value:.6f}" if value is not None else "---",
                             className="badge bg-primary me-2"),
                    dbc.Button("Remove", 
                              id={'type': 'remove-btn', 'index': var_name},
                              size="sm", 
                              color="danger",
                              outline=True,
                              className="float-end")
                ], className="d-flex justify-content-between align-items-center")
            ])
        ])
    ], className="mb-2 monitor-card")

# Advanced layout with drag-and-drop
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🔧 XDS110 Advanced Debug Dashboard", className="text-center mb-4"),
            html.Div(id='connection-status', className='text-center mb-4'),
        ], width=12)
    ]),
    
    dbc.Row([
        # Left Panel - Available Variables
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📋 Available Variables")),
                dbc.CardBody([
                    dbc.InputGroup([
                        dbc.Input(id='variable-search', placeholder="Search variables...", type="text"),
                        dbc.Button("🔍", id='search-btn', color="secondary", outline=True)
                    ], className="mb-3"),
                    
                    html.Div(
                        id='available-variables',
                        style={
                            "height": "600px", 
                            "overflowY": "auto",
                            "border": "2px dashed #ccc",
                            "borderRadius": "5px",
                            "padding": "10px"
                        }
                    )
                ])
            ])
        ], width=6),
        
        # Right Panel - Monitored Variables  
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5("📊 Monitored Variables", className="mb-0"),
                        html.Div([
                            dbc.Button("▶ Start", id='start-monitoring-btn', color="success", size="sm", className="me-2"),
                            dbc.Button("⏹ Stop", id='stop-monitoring-btn', color="danger", size="sm", className="me-2"),
                            dbc.Button("🗑 Clear All", id='clear-all-btn', color="warning", size="sm")
                        ])
                    ], className="d-flex justify-content-between align-items-center")
                ]),
                dbc.CardBody([
                    html.Div(
                        id='monitored-variables',
                        children=[
                            html.Div("Drag variables here to start monitoring", 
                                   className="text-muted text-center p-4")
                        ],
                        style={
                            "minHeight": "300px",
                            "border": "2px dashed #28a745", 
                            "borderRadius": "5px",
                            "padding": "10px"
                        }
                    ),
                    
                    html.Hr(),
                    
                    # Monitoring Status
                    html.Div([
                        html.H6("Monitoring Status:"),
                        html.Div(id='monitoring-status', children="Stopped", className="badge bg-secondary")
                    ], className="mb-3"),
                    
                    # Rate Control
                    html.Div([
                        html.Label("Update Rate:"),
                        dcc.Slider(
                            id='rate-slider',
                            min=0.5,
                            max=5.0,
                            step=0.5,
                            value=1.0,
                            marks={i: f'{i}Hz' for i in [0.5, 1, 2, 3, 4, 5]},
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ])
                ])
            ])
        ], width=6)
    ], className="mb-4"),
    
    # Plot Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("📈 Real-Time Plots")),
                dbc.CardBody([
                    dcc.Graph(
                        id='live-plot',
                        figure={
                            'data': [],
                            'layout': {
                                'title': 'Real-Time Variable Data',
                                'xaxis': {'title': 'Time (s)'},
                                'yaxis': {'title': 'Value'},
                                'height': 400
                            }
                        }
                    )
                ])
            ])
        ], width=12)
    ]),
    
    # Hidden divs for state management
    html.Div(id='monitored-vars-state', style={'display': 'none'}, children='[]'),
    html.Div(id='monitoring-active', style={'display': 'none'}, children='false'),
    
    # Update interval
    dcc.Interval(
        id='update-interval',
        interval=1000,  # 1 second
        n_intervals=0
    ),
    
], fluid=True)

# Callbacks

@app.callback(
    [Output('connection-status', 'children'),
     Output('available-variables', 'children')],
    Input('update-interval', 'n_intervals')
)
def update_connection_and_variables(n):
    """Update connection status and available variables"""
    variables = get_available_variables()
    
    if variables:
        # Create priority grouping
        priority_vars = ['motorVars_M1', 'motorHandle_M1', 'debug_bypass', 'motor1_drive', 'motor_common']
        motor_vars = [v for v in variables if 'motor' in v.lower() and v not in priority_vars]
        debug_vars = [v for v in variables if 'debug' in v.lower() and v not in priority_vars]
        other_vars = [v for v in variables if v not in priority_vars and 'motor' not in v.lower() and 'debug' not in v.lower()]
        
        status = dbc.Alert(
            f"✅ Connected - {len(variables)} variables available",
            color="success"
        )
        
        var_cards = []
        
        # Priority variables section
        if any(v in variables for v in priority_vars):
            var_cards.append(html.H6("⭐ Priority Variables", className="text-info mt-3 mb-2"))
            for var in priority_vars:
                if var in variables:
                    is_struct = var in STRUCT_FIELDS
                    var_cards.append(create_variable_card(var, is_struct))
        
        # Motor variables section
        if motor_vars:
            var_cards.append(html.H6("🔧 Motor Variables", className="text-success mt-3 mb-2"))
            for var in motor_vars[:20]:  # Limit display
                var_cards.append(create_variable_card(var))
        
        # Debug variables section  
        if debug_vars:
            var_cards.append(html.H6("🐛 Debug Variables", className="text-warning mt-3 mb-2"))
            for var in debug_vars[:10]:  # Limit display
                var_cards.append(create_variable_card(var))
        
        # Other variables (limited)
        if other_vars:
            var_cards.append(html.H6("📦 Other Variables", className="text-secondary mt-3 mb-2"))
            for var in other_vars[:30]:  # Show first 30
                var_cards.append(create_variable_card(var))
        
        return status, var_cards
    else:
        return dbc.Alert("❌ Not connected", color="danger"), []

@app.callback(
    Output('available-variables', 'children', allow_duplicate=True),
    Input({'type': 'expand-btn', 'index': ALL}, 'n_clicks'),
    State('available-variables', 'children'),
    prevent_initial_call=True
)
def expand_struct_fields(n_clicks_list, current_children):
    """Expand struct fields when expand button is clicked"""
    if not any(n_clicks_list):
        return current_children
    
    ctx = callback_context
    if not ctx.triggered:
        return current_children
    
    # Find which expand button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    struct_name = eval(button_id)['index']
    
    if struct_name in STRUCT_FIELDS:
        # Add field cards after the struct card
        new_children = list(current_children) if current_children else []
        
        # Find position to insert fields
        insert_pos = len(new_children)
        for i, child in enumerate(new_children):
            if isinstance(child, dict) and child.get('props', {}).get('id', {}).get('index') == struct_name:
                insert_pos = i + 1
                break
        
        # Insert field cards
        field_cards = []
        field_cards.append(html.Div(f"🔽 {struct_name} fields:", className="text-muted small mt-2 mb-1"))
        
        for field in STRUCT_FIELDS[struct_name]:
            field_card = dbc.Card([
                dbc.CardBody([
                    html.H6(field.split('.')[-1], className="card-title mb-1 text-primary"),
                    html.Small(field, className="text-muted"),
                    html.Div(id={'type': 'variable-value', 'index': field}, 
                            children="Not monitored", 
                            className="text-muted small mt-1")
                ])
            ], 
            id={'type': 'var-card', 'index': field},
            className="mb-1 ms-3 variable-field-card",
            style={"cursor": "grab", "minHeight": "80px", "backgroundColor": "#f8f9fa"}
            )
            field_cards.append(field_card)
        
        # Insert field cards
        new_children[insert_pos:insert_pos] = field_cards
        return new_children
    
    return current_children

@app.callback(
    Output('monitored-variables', 'children'),
    [Input({'type': 'var-card', 'index': ALL}, 'n_clicks'),
     Input({'type': 'remove-btn', 'index': ALL}, 'n_clicks'),
     Input('clear-all-btn', 'n_clicks')],
    [State('monitored-vars-state', 'children')],
    prevent_initial_call=True
)
def manage_monitored_variables(var_clicks, remove_clicks, clear_clicks, monitored_state):
    """Handle adding/removing variables to/from monitoring panel"""
    ctx = callback_context
    if not ctx.triggered:
        return []
    
    # Parse current monitored variables
    try:
        monitored_vars = json.loads(monitored_state) if monitored_state != '[]' else []
    except:
        monitored_vars = []
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'var-card' in trigger_id:
        # Add variable to monitoring
        var_name = eval(trigger_id.split('.')[0])['index']
        if var_name not in monitored_vars:
            monitored_vars.append(var_name)
    
    elif 'remove-btn' in trigger_id:
        # Remove variable from monitoring
        var_name = eval(trigger_id.split('.')[0])['index']
        if var_name in monitored_vars:
            monitored_vars.remove(var_name)
    
    elif 'clear-all-btn' in trigger_id:
        # Clear all monitored variables
        monitored_vars = []
    
    # Create monitoring cards
    if monitored_vars:
        current_data = get_current_data()
        cards = []
        for var in monitored_vars:
            value = current_data.get(var)
            cards.append(create_monitoring_item(var, value))
        return cards
    else:
        return [html.Div("Drag variables here to start monitoring", 
                        className="text-muted text-center p-4")]

@app.callback(
    [Output('monitored-vars-state', 'children'),
     Output('monitoring-status', 'children'),
     Output('monitoring-status', 'className')],
    [Input({'type': 'var-card', 'index': ALL}, 'n_clicks'),
     Input({'type': 'remove-btn', 'index': ALL}, 'n_clicks'),
     Input('clear-all-btn', 'n_clicks'),
     Input('start-monitoring-btn', 'n_clicks'),
     Input('stop-monitoring-btn', 'n_clicks')],
    [State('monitored-vars-state', 'children'),
     State('rate-slider', 'value')],
    prevent_initial_call=True
)
def update_monitoring_state(var_clicks, remove_clicks, clear_clicks, start_clicks, stop_clicks, 
                           monitored_state, rate):
    """Update monitoring state and control monitoring"""
    ctx = callback_context
    if not ctx.triggered:
        return monitored_state, "Stopped", "badge bg-secondary"
    
    # Parse current monitored variables
    try:
        monitored_vars = json.loads(monitored_state) if monitored_state != '[]' else []
    except:
        monitored_vars = []
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'var-card' in trigger_id:
        # Add variable to monitoring
        var_name = eval(trigger_id.split('.')[0])['index']
        if var_name not in monitored_vars:
            monitored_vars.append(var_name)
    
    elif 'remove-btn' in trigger_id:
        # Remove variable from monitoring
        var_name = eval(trigger_id.split('.')[0])['index']
        if var_name in monitored_vars:
            monitored_vars.remove(var_name)
    
    elif 'clear-all-btn' in trigger_id:
        # Clear all monitored variables
        monitored_vars = []
        stop_monitoring()
    
    elif 'start-monitoring-btn' in trigger_id:
        # Start monitoring
        if monitored_vars:
            success = start_monitoring(monitored_vars, rate_hz=rate)
            if success:
                return json.dumps(monitored_vars), "Running", "badge bg-success"
            else:
                return json.dumps(monitored_vars), "Error", "badge bg-danger"
    
    elif 'stop-monitoring-btn' in trigger_id:
        # Stop monitoring
        stop_monitoring()
        return json.dumps(monitored_vars), "Stopped", "badge bg-secondary"
    
    return json.dumps(monitored_vars), "Ready", "badge bg-info"

@app.callback(
    [Output({'type': 'monitor-value', 'index': MATCH}, 'children') for _ in range(20)],  # Support up to 20 variables
    Input('update-interval', 'n_intervals'),
    State('monitored-vars-state', 'children'),
    prevent_initial_call=True
)
def update_monitored_values(n, monitored_state):
    """Update the values of monitored variables"""
    try:
        monitored_vars = json.loads(monitored_state) if monitored_state != '[]' else []
    except:
        monitored_vars = []
    
    if not monitored_vars:
        return ["---"] * 20
    
    current_data = get_current_data()
    results = []
    
    for var in monitored_vars:
        value = current_data.get(var)
        if value is not None:
            if isinstance(value, (int, float)):
                results.append(f"{value:.6f}")
            else:
                results.append(str(value))
        else:
            results.append("---")
    
    # Pad with "---" for unused slots
    while len(results) < 20:
        results.append("---")
    
    return results

@app.callback(
    Output('live-plot', 'figure'),
    Input('update-interval', 'n_intervals'),
    State('monitored-vars-state', 'children')
)
def update_plot(n, monitored_state):
    """Update the live plot"""
    try:
        monitored_vars = json.loads(monitored_state) if monitored_state != '[]' else []
    except:
        monitored_vars = []
    
    fig = go.Figure()
    
    if monitored_vars:
        for var in monitored_vars:
            timestamps, values = get_variable_history(var, duration=30)  # Last 30 seconds
            
            if timestamps and values:
                # Convert to relative time
                start_time = timestamps[0] if timestamps else 0
                rel_times = [(t - start_time) for t in timestamps]
                
                fig.add_trace(
                    go.Scatter(
                        x=rel_times,
                        y=values,
                        mode='lines+markers',
                        name=var.split('.')[-1] if '.' in var else var,  # Short name for legend
                        line={'width': 2}
                    )
                )
        
        fig.update_layout(
            title='Real-Time Variable Data',
            xaxis_title='Time (s)',
            yaxis_title='Value',
            hovermode='x unified',
            height=400,
            showlegend=True
        )
    else:
        fig.update_layout(
            title='Real-Time Variable Data (No variables selected)',
            xaxis_title='Time (s)',
            yaxis_title='Value',
            height=400
        )
    
    return fig

# Custom CSS for better styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .variable-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
                transition: all 0.2s ease-in-out;
            }
            .variable-field-card:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            }
            .monitor-card {
                border-left: 4px solid #28a745;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Advanced XDS110 Debug Dashboard')
    parser.add_argument('--ccxml', required=True, help='Path to CCXML configuration file')
    parser.add_argument('--map', required=True, help='Path to MAP file')
    parser.add_argument('--binary', help='Path to binary file to load (optional)')
    parser.add_argument('--port', type=int, default=8052, help='Dashboard port (default: 8052)')
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
        
        # Run the advanced dashboard
        logger.info(f"Starting advanced dashboard on http://{args.host}:{args.port}")
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