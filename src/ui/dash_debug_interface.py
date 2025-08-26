#!/usr/bin/env python3
"""
Generic C2000 DSP Debug Interface - Web UI for real-time debugging
Works alongside MCP server for human + AI collaborative debugging
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio
import websocket
import threading
import json
from collections import deque
from typing import Dict, List, Any
import redis

# Initialize Dash app
app = dash.Dash(__name__, update_title=None)

# Data storage for real-time updates
class DataStore:
    def __init__(self, max_points=1000):
        self.max_points = max_points
        self.variables = {}  # {name: deque of (timestamp, value) tuples}
        self.variable_metadata = {}  # {name: {address, type, size, description}}
        self.memory_regions = []
        self.watchlist = []
        self.triggers = {}  # {name: {condition, action}}
        
    def add_variable(self, name: str, metadata: dict):
        """Add a variable to track"""
        if name not in self.variables:
            self.variables[name] = deque(maxlen=self.max_points)
            self.variable_metadata[name] = metadata
            
    def update_value(self, name: str, value: float, timestamp: float = None):
        """Update variable value"""
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        if name in self.variables:
            self.variables[name].append((timestamp, value))
            
    def get_latest(self, name: str):
        """Get latest value for a variable"""
        if name in self.variables and self.variables[name]:
            return self.variables[name][-1][1]
        return None
        
    def get_history(self, name: str, points: int = 100):
        """Get historical data for plotting"""
        if name in self.variables:
            data = list(self.variables[name])[-points:]
            if data:
                timestamps, values = zip(*data)
                return timestamps, values
        return [], []

# Global data store
data_store = DataStore()

# Layout
app.layout = html.Div([
    html.Div([
        html.H1("C2000 DSP Debug Interface", className="header-title"),
        html.Div([
            html.Span(id="connection-status", children="● Disconnected", 
                     style={"color": "red", "fontSize": "14px"}),
            html.Span(" | Device: ", style={"marginLeft": "20px"}),
            html.Span(id="device-info", children="Not Connected"),
        ], className="header-info")
    ], className="header"),
    
    dcc.Tabs(id="main-tabs", value="watch-tab", children=[
        
        # Variable Watch Tab
        dcc.Tab(label="Variable Watch", value="watch-tab", children=[
            html.Div([
                # Variable search and add
                html.Div([
                    dcc.Input(
                        id="variable-search",
                        type="text",
                        placeholder="Search variables (regex supported)...",
                        style={"width": "300px"}
                    ),
                    html.Button("Search", id="search-btn", n_clicks=0),
                    html.Button("Add to Watch", id="add-watch-btn", n_clicks=0),
                    html.Button("Clear Watch", id="clear-watch-btn", n_clicks=0),
                ], className="control-bar"),
                
                # Search results dropdown
                dcc.Dropdown(
                    id="search-results",
                    options=[],
                    multi=True,
                    placeholder="Select variables to watch...",
                    style={"marginTop": "10px"}
                ),
                
                # Watch table
                html.Div([
                    dash_table.DataTable(
                        id="watch-table",
                        columns=[
                            {"name": "Variable", "id": "name"},
                            {"name": "Value", "id": "value"},
                            {"name": "Hex", "id": "hex"},
                            {"name": "Binary", "id": "binary"},
                            {"name": "Address", "id": "address"},
                            {"name": "Type", "id": "type"},
                            {"name": "Change", "id": "change"},
                            {"name": "Sparkline", "id": "sparkline", "presentation": "markdown"},
                        ],
                        data=[],
                        editable=False,
                        row_selectable="multi",
                        selected_rows=[],
                        style_cell={'textAlign': 'left'},
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'change'},
                                'color': 'green',
                                'fontWeight': 'bold'
                            }
                        ],
                        style_cell_conditional=[
                            {'if': {'column_id': 'sparkline'}, 'width': '100px'},
                        ]
                    )
                ], style={"marginTop": "20px"}),
                
                # Update controls
                html.Div([
                    html.Label("Update Rate: "),
                    dcc.RadioItems(
                        id="update-rate",
                        options=[
                            {'label': '10 Hz', 'value': 100},
                            {'label': '5 Hz', 'value': 200},
                            {'label': '1 Hz', 'value': 1000},
                            {'label': '0.5 Hz', 'value': 2000},
                            {'label': 'Manual', 'value': 0},
                        ],
                        value=1000,
                        inline=True
                    ),
                    html.Button("Read Now", id="read-now-btn", n_clicks=0),
                ], className="update-controls", style={"marginTop": "20px"}),
            ])
        ]),
        
        # Real-time Plotting Tab
        dcc.Tab(label="Real-Time Plots", value="plot-tab", children=[
            html.Div([
                # Plot configuration
                html.Div([
                    dcc.Dropdown(
                        id="plot-variables",
                        options=[],
                        multi=True,
                        placeholder="Select variables to plot...",
                        style={"width": "500px", "display": "inline-block"}
                    ),
                    html.Button("Add Plot", id="add-plot-btn", n_clicks=0),
                    html.Button("Clear Plots", id="clear-plots-btn", n_clicks=0),
                    dcc.RadioItems(
                        id="plot-type",
                        options=[
                            {'label': 'Time Series', 'value': 'time'},
                            {'label': 'XY Plot', 'value': 'xy'},
                            {'label': 'FFT', 'value': 'fft'},
                            {'label': 'Histogram', 'value': 'hist'},
                        ],
                        value='time',
                        inline=True,
                        style={"marginLeft": "20px"}
                    ),
                ], className="control-bar"),
                
                # Plot grid
                html.Div(id="plot-container", children=[
                    dcc.Graph(id="main-plot", style={"height": "500px"}),
                ]),
                
                # Plot controls
                html.Div([
                    html.Label("Window: "),
                    dcc.Slider(
                        id="plot-window",
                        min=10,
                        max=1000,
                        value=100,
                        marks={10: '10', 50: '50', 100: '100', 500: '500', 1000: '1000'},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.Button("Pause", id="pause-plot-btn", n_clicks=0),
                    html.Button("Export CSV", id="export-csv-btn", n_clicks=0),
                ], style={"marginTop": "20px"}),
            ])
        ]),
        
        # Memory View Tab
        dcc.Tab(label="Memory View", value="memory-tab", children=[
            html.Div([
                html.Div([
                    html.Label("Address: "),
                    dcc.Input(
                        id="memory-address",
                        type="text",
                        placeholder="0x0000",
                        value="0x0000",
                        style={"width": "100px"}
                    ),
                    html.Label(" Length: ", style={"marginLeft": "20px"}),
                    dcc.Input(
                        id="memory-length",
                        type="number",
                        placeholder="256",
                        value=256,
                        style={"width": "100px"}
                    ),
                    html.Button("Read", id="read-memory-btn", n_clicks=0),
                    dcc.RadioItems(
                        id="memory-format",
                        options=[
                            {'label': 'Hex', 'value': 'hex'},
                            {'label': 'Decimal', 'value': 'dec'},
                            {'label': 'Float', 'value': 'float'},
                            {'label': 'ASCII', 'value': 'ascii'},
                        ],
                        value='hex',
                        inline=True,
                        style={"marginLeft": "20px"}
                    ),
                ], className="control-bar"),
                
                # Memory display
                html.Div(
                    id="memory-display",
                    children=[html.Pre("Memory content will appear here...")],
                    style={
                        "fontFamily": "monospace",
                        "backgroundColor": "#f0f0f0",
                        "padding": "10px",
                        "marginTop": "20px",
                        "height": "400px",
                        "overflowY": "scroll"
                    }
                ),
                
                # Memory map visualization
                html.Div([
                    html.H4("Memory Map"),
                    dcc.Graph(id="memory-map", style={"height": "200px"}),
                ], style={"marginTop": "20px"}),
            ])
        ]),
        
        # Triggers & Actions Tab
        dcc.Tab(label="Triggers & Actions", value="trigger-tab", children=[
            html.Div([
                html.H3("Conditional Triggers"),
                html.Div([
                    dcc.Input(
                        id="trigger-variable",
                        type="text",
                        placeholder="Variable name...",
                        style={"width": "200px"}
                    ),
                    dcc.Dropdown(
                        id="trigger-condition",
                        options=[
                            {'label': '>', 'value': '>'},
                            {'label': '<', 'value': '<'},
                            {'label': '==', 'value': '=='},
                            {'label': '!=', 'value': '!='},
                            {'label': 'changes', 'value': 'change'},
                        ],
                        value='>',
                        style={"width": "100px", "display": "inline-block", "marginLeft": "10px"}
                    ),
                    dcc.Input(
                        id="trigger-value",
                        type="number",
                        placeholder="Value...",
                        style={"width": "100px", "marginLeft": "10px"}
                    ),
                    dcc.Dropdown(
                        id="trigger-action",
                        options=[
                            {'label': 'Log', 'value': 'log'},
                            {'label': 'Alert', 'value': 'alert'},
                            {'label': 'Capture', 'value': 'capture'},
                            {'label': 'Stop', 'value': 'stop'},
                            {'label': 'Execute Script', 'value': 'script'},
                        ],
                        value='log',
                        style={"width": "150px", "display": "inline-block", "marginLeft": "10px"}
                    ),
                    html.Button("Add Trigger", id="add-trigger-btn", n_clicks=0),
                ], className="control-bar"),
                
                # Active triggers table
                html.Div([
                    html.H4("Active Triggers"),
                    dash_table.DataTable(
                        id="triggers-table",
                        columns=[
                            {"name": "Variable", "id": "variable"},
                            {"name": "Condition", "id": "condition"},
                            {"name": "Action", "id": "action"},
                            {"name": "Status", "id": "status"},
                            {"name": "Count", "id": "count"},
                        ],
                        data=[],
                        row_deletable=True,
                    )
                ], style={"marginTop": "20px"}),
                
                # Event log
                html.Div([
                    html.H4("Event Log"),
                    html.Div(
                        id="event-log",
                        children=[],
                        style={
                            "height": "200px",
                            "overflowY": "scroll",
                            "backgroundColor": "#f8f8f8",
                            "padding": "10px",
                            "fontFamily": "monospace",
                            "fontSize": "12px"
                        }
                    ),
                ], style={"marginTop": "20px"}),
            ])
        ]),
        
        # DSP Analysis Tab
        dcc.Tab(label="DSP Analysis", value="dsp-tab", children=[
            html.Div([
                html.H3("Signal Analysis Tools"),
                
                # Signal selection
                html.Div([
                    dcc.Dropdown(
                        id="dsp-signal",
                        options=[],
                        placeholder="Select signal for analysis...",
                        style={"width": "300px"}
                    ),
                    html.Button("Analyze", id="analyze-btn", n_clicks=0),
                ], className="control-bar"),
                
                # Analysis results grid
                html.Div([
                    html.Div([
                        html.H4("Time Domain"),
                        dcc.Graph(id="time-domain-plot", style={"height": "300px"}),
                    ], style={"width": "50%", "display": "inline-block"}),
                    
                    html.Div([
                        html.H4("Frequency Domain"),
                        dcc.Graph(id="freq-domain-plot", style={"height": "300px"}),
                    ], style={"width": "50%", "display": "inline-block"}),
                ]),
                
                # Statistics
                html.Div([
                    html.H4("Signal Statistics"),
                    html.Div(id="signal-stats", children=[
                        html.Table([
                            html.Tr([html.Td("Mean:"), html.Td("--")]),
                            html.Tr([html.Td("Std Dev:"), html.Td("--")]),
                            html.Tr([html.Td("RMS:"), html.Td("--")]),
                            html.Tr([html.Td("Peak-Peak:"), html.Td("--")]),
                            html.Tr([html.Td("THD:"), html.Td("--")]),
                            html.Tr([html.Td("SNR:"), html.Td("--")]),
                        ])
                    ], style={"marginTop": "20px"}),
                ]),
                
                # Digital filter design
                html.Div([
                    html.H4("Filter Design"),
                    html.Div([
                        dcc.Dropdown(
                            id="filter-type",
                            options=[
                                {'label': 'Low Pass', 'value': 'lowpass'},
                                {'label': 'High Pass', 'value': 'highpass'},
                                {'label': 'Band Pass', 'value': 'bandpass'},
                                {'label': 'Notch', 'value': 'notch'},
                            ],
                            value='lowpass',
                            style={"width": "150px", "display": "inline-block"}
                        ),
                        dcc.Input(
                            id="filter-cutoff",
                            type="number",
                            placeholder="Cutoff (Hz)",
                            style={"width": "120px", "marginLeft": "10px"}
                        ),
                        dcc.Input(
                            id="filter-order",
                            type="number",
                            placeholder="Order",
                            value=4,
                            style={"width": "80px", "marginLeft": "10px"}
                        ),
                        html.Button("Apply Filter", id="apply-filter-btn", n_clicks=0),
                        html.Button("Generate C Code", id="gen-code-btn", n_clicks=0),
                    ]),
                ], style={"marginTop": "30px"}),
            ])
        ]),
        
        # Configuration Tab
        dcc.Tab(label="Configuration", value="config-tab", children=[
            html.Div([
                html.H3("Connection Settings"),
                html.Div([
                    html.Label("DSS Host: "),
                    dcc.Input(
                        id="dss-host",
                        type="text",
                        value="localhost",
                        style={"width": "150px"}
                    ),
                    html.Label(" Port: ", style={"marginLeft": "20px"}),
                    dcc.Input(
                        id="dss-port",
                        type="number",
                        value=8080,
                        style={"width": "100px"}
                    ),
                    html.Button("Connect", id="connect-btn", n_clicks=0),
                    html.Button("Disconnect", id="disconnect-btn", n_clicks=0),
                ], style={"marginBottom": "20px"}),
                
                html.H3("Project Configuration"),
                html.Div([
                    html.Label("MAP File: "),
                    dcc.Upload(
                        id="map-upload",
                        children=html.Div(['Drag and Drop or ', html.A('Select MAP File')]),
                        style={
                            'width': '300px',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'display': 'inline-block'
                        },
                    ),
                    html.Div(id="map-info", style={"marginTop": "10px"}),
                ]),
                
                html.H3("Export Settings"),
                html.Div([
                    html.Button("Export Configuration", id="export-config-btn"),
                    html.Button("Import Configuration", id="import-config-btn"),
                    dcc.Download(id="download-config"),
                ]),
            ])
        ]),
    ]),
    
    # Hidden div to store data
    html.Div(id="hidden-data", style={"display": "none"}),
    
    # Interval component for updates
    dcc.Interval(
        id='interval-component',
        interval=1000,  # in milliseconds
        n_intervals=0
    ),
    
    # WebSocket status
    html.Div(id="ws-status", style={"display": "none"}),
])

# Callbacks
@app.callback(
    Output('watch-table', 'data'),
    Input('interval-component', 'n_intervals'),
    State('watch-table', 'data')
)
def update_watch_table(n, current_data):
    """Update watch table with latest values"""
    if not current_data:
        return []
    
    # Update values from data store
    for row in current_data:
        name = row['name']
        value = data_store.get_latest(name)
        if value is not None:
            old_value = row.get('value', 0)
            row['value'] = f"{value:.4f}" if isinstance(value, float) else str(value)
            row['hex'] = f"0x{int(value):04X}" if isinstance(value, (int, float)) else ""
            row['binary'] = f"{int(value):016b}" if isinstance(value, (int, float)) else ""
            
            # Calculate change
            if isinstance(value, (int, float)) and isinstance(old_value, (int, float)):
                change = value - float(old_value) if old_value else 0
                row['change'] = f"{change:+.4f}" if change != 0 else ""
            
            # Create sparkline
            _, values = data_store.get_history(name, 20)
            if values:
                sparkline = create_sparkline(values)
                row['sparkline'] = sparkline
    
    return current_data

@app.callback(
    Output('main-plot', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('plot-variables', 'value'),
     Input('plot-window', 'value'),
     Input('plot-type', 'value')],
)
def update_plot(n, variables, window, plot_type):
    """Update main plot"""
    if not variables:
        return go.Figure()
    
    fig = make_subplots(rows=len(variables), cols=1, 
                       subplot_titles=variables,
                       vertical_spacing=0.1)
    
    for i, var in enumerate(variables):
        timestamps, values = data_store.get_history(var, window)
        
        if plot_type == 'time':
            # Time series plot
            times = [(t - timestamps[0]) if timestamps else 0 for t in timestamps]
            fig.add_trace(
                go.Scatter(x=times, y=values, mode='lines', name=var),
                row=i+1, col=1
            )
            fig.update_xaxes(title_text="Time (s)", row=i+1, col=1)
            
        elif plot_type == 'fft':
            # FFT plot
            if values:
                fft_vals = np.fft.fft(values)
                fft_freq = np.fft.fftfreq(len(values))
                fig.add_trace(
                    go.Scatter(x=fft_freq[:len(fft_freq)//2], 
                             y=np.abs(fft_vals)[:len(fft_vals)//2],
                             mode='lines', name=var),
                    row=i+1, col=1
                )
                fig.update_xaxes(title_text="Frequency", row=i+1, col=1)
        
        elif plot_type == 'hist':
            # Histogram
            fig.add_trace(
                go.Histogram(x=values, name=var),
                row=i+1, col=1
            )
    
    fig.update_layout(height=500, showlegend=True)
    return fig

def create_sparkline(values):
    """Create ASCII sparkline from values"""
    if not values:
        return ""
    
    chars = "▁▂▃▄▅▆▇█"
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        return chars[4] * len(values)
    
    sparkline = ""
    for v in values[-20:]:  # Last 20 values
        index = int((v - min_val) / (max_val - min_val) * 7)
        sparkline += chars[min(index, 7)]
    
    return sparkline

# WebSocket connection for real-time data
def ws_client():
    """WebSocket client for real-time updates from DSS/MCP server"""
    ws_url = "ws://localhost:8081/realtime"
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            if data['type'] == 'variable_update':
                data_store.update_value(data['name'], data['value'])
            elif data['type'] == 'variable_discovered':
                data_store.add_variable(data['name'], data['metadata'])
        except Exception as e:
            print(f"WebSocket error: {e}")
    
    def on_error(ws, error):
        print(f"WebSocket error: {error}")
    
    def on_close(ws):
        print("WebSocket closed")
    
    def on_open(ws):
        print("WebSocket connected")
    
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

# Start WebSocket in background thread
ws_thread = threading.Thread(target=ws_client, daemon=True)
ws_thread.start()

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)