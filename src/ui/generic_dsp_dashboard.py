#!/usr/bin/env python3
"""
Generic DSP Debug Dashboard - Universal interface for any C2000/DSP application
Adapted from proven Plotly Dash design patterns with enhanced features
"""

import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import base64
import io
import os
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import logging
from pathlib import Path

# Platform-specific update rates (from original design)
if os.name == 'nt':  # Windows
    UI_UPDATE_INTERVAL = 500    # 2Hz for stability
    PLOT_UPDATE_INTERVAL = 1000  # 1Hz
else:  # Linux/Mac
    UI_UPDATE_INTERVAL = 100    # 10Hz
    PLOT_UPDATE_INTERVAL = 200  # 5Hz

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                title="DSP Debug Dashboard")

# Global data storage
class DSPDataStore:
    """Thread-safe data storage for DSP variables"""
    
    def __init__(self, max_history=10000):
        self.max_history = max_history
        self.variables = {}  # {name: deque of (timestamp, value)}
        self.metadata = {}   # {name: {address, type, unit, description}}
        self.memory_map = {} # Memory regions from MAP file
        self.triggers = []   # Active triggers
        self.profiles = {}   # Saved variable profiles
        
    def add_variable(self, name: str, address: int, var_type: str = "unknown"):
        """Register a new variable for tracking"""
        if name not in self.variables:
            self.variables[name] = deque(maxlen=self.max_history)
            self.metadata[name] = {
                "address": address,
                "type": var_type,
                "unit": self._guess_unit(name),
                "description": self._guess_description(name)
            }
    
    def update(self, name: str, value: float, timestamp: float = None):
        """Update variable value"""
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        
        if name not in self.variables:
            self.add_variable(name, 0)  # Auto-register
        
        self.variables[name].append((timestamp, value))
    
    def get_latest(self, name: str) -> Optional[float]:
        """Get most recent value"""
        if name in self.variables and self.variables[name]:
            return self.variables[name][-1][1]
        return None
    
    def get_history(self, name: str, duration_sec: Optional[int] = None) -> Tuple[List, List]:
        """Get historical data for plotting"""
        if name not in self.variables:
            return [], []
        
        data = list(self.variables[name])
        if not data:
            return [], []
        
        if duration_sec:
            cutoff = datetime.now().timestamp() - duration_sec
            data = [(t, v) for t, v in data if t >= cutoff]
        
        if data:
            timestamps, values = zip(*data)
            return list(timestamps), list(values)
        return [], []
    
    def _guess_unit(self, name: str) -> str:
        """Guess unit from variable name"""
        name_lower = name.lower()
        if any(x in name_lower for x in ['current', 'i_', '_a']):
            return 'A'
        elif any(x in name_lower for x in ['voltage', 'v_', '_v']):
            return 'V'
        elif any(x in name_lower for x in ['freq', 'hz']):
            return 'Hz'
        elif any(x in name_lower for x in ['angle', 'phase', 'theta']):
            return 'rad'
        elif any(x in name_lower for x in ['temp']):
            return '°C'
        elif any(x in name_lower for x in ['power', 'p_']):
            return 'W'
        elif any(x in name_lower for x in ['speed', 'rpm']):
            return 'RPM'
        elif any(x in name_lower for x in ['duty']):
            return '%'
        return ''
    
    def _guess_description(self, name: str) -> str:
        """Generate description from variable name"""
        # Convert snake_case or camelCase to readable
        import re
        # Handle snake_case
        desc = name.replace('_', ' ')
        # Handle camelCase
        desc = re.sub(r'(?<!^)(?=[A-Z])', ' ', desc)
        return desc.title()

# Global data store instance
data_store = DSPDataStore()

def create_dashboard_layout():
    """Create the main dashboard layout"""
    
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1("DSP Debug Dashboard", className="text-primary"),
                html.P("Universal debugging interface for C2000/DSP applications", 
                       className="text-muted")
            ], width=9),
            dbc.Col([
                html.Div([
                    html.Span("●", id="connection-indicator", 
                             style={"color": "red", "fontSize": "20px"}),
                    html.Span(" Status: ", className="ms-2"),
                    html.Span("Disconnected", id="connection-status"),
                ], className="text-end mt-3"),
            ], width=3),
        ], className="mb-4"),
        
        # Main Tabs
        dbc.Tabs([
            # Variable Watch Tab
            dbc.Tab(label="Variable Watch", tab_id="watch-tab", children=[
                dbc.Row([
                    # Variable Search Panel
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Variable Search"),
                            dbc.CardBody([
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="var-search-input",
                                        placeholder="Search variables (regex supported)...",
                                        value=""
                                    ),
                                    dbc.Button("Search", id="var-search-btn", 
                                             color="primary", outline=True),
                                ], className="mb-3"),
                                
                                # Category filters
                                dbc.Label("Filter by Category:"),
                                dbc.Checklist(
                                    id="category-filter",
                                    options=[
                                        {"label": "Control", "value": "control"},
                                        {"label": "ADC/DAC", "value": "adc_dac"},
                                        {"label": "PWM", "value": "pwm"},
                                        {"label": "Communication", "value": "comm"},
                                        {"label": "DSP", "value": "dsp"},
                                        {"label": "Power", "value": "power"},
                                        {"label": "Status", "value": "status"},
                                    ],
                                    value=["control", "adc_dac"],
                                    inline=True,
                                    className="mb-3"
                                ),
                                
                                # Search results
                                html.Div(id="search-results", className="mb-3"),
                                
                                dbc.ButtonGroup([
                                    dbc.Button("Add Selected", id="add-to-watch-btn", 
                                             color="success", size="sm"),
                                    dbc.Button("Clear Watch", id="clear-watch-btn", 
                                             color="danger", size="sm"),
                                ])
                            ])
                        ])
                    ], width=4),
                    
                    # Watch Table
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                "Watching Variables",
                                dbc.Badge(id="watch-count", children="0", 
                                        className="ms-2", color="primary")
                            ]),
                            dbc.CardBody([
                                dash_table.DataTable(
                                    id="watch-table",
                                    columns=[
                                        {"name": "Variable", "id": "name", "type": "text"},
                                        {"name": "Value", "id": "value", "type": "numeric"},
                                        {"name": "Hex", "id": "hex", "type": "text"},
                                        {"name": "Binary", "id": "binary", "type": "text"},
                                        {"name": "Unit", "id": "unit", "type": "text"},
                                        {"name": "Address", "id": "address", "type": "text"},
                                        {"name": "Δ", "id": "delta", "type": "numeric"},
                                        {"name": "Trend", "id": "trend", "type": "text", 
                                         "presentation": "markdown"},
                                    ],
                                    data=[],
                                    editable=False,
                                    row_selectable="multi",
                                    selected_rows=[],
                                    style_cell={'textAlign': 'left', 'fontSize': '14px'},
                                    style_data_conditional=[
                                        {
                                            'if': {'column_id': 'delta', 
                                                  'filter_query': '{delta} > 0'},
                                            'color': 'green',
                                        },
                                        {
                                            'if': {'column_id': 'delta', 
                                                  'filter_query': '{delta} < 0'},
                                            'color': 'red',
                                        }
                                    ],
                                    page_size=20,
                                    sort_action="native",
                                    filter_action="native",
                                )
                            ])
                        ])
                    ], width=8)
                ], className="mb-3"),
                
                # Update Controls
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Label("Update Rate:"),
                                dbc.RadioItems(
                                    id="update-rate",
                                    options=[
                                        {"label": "10 Hz", "value": 100},
                                        {"label": "5 Hz", "value": 200},
                                        {"label": "2 Hz", "value": 500},
                                        {"label": "1 Hz", "value": 1000},
                                        {"label": "Manual", "value": 0},
                                    ],
                                    value=500,
                                    inline=True,
                                ),
                                dbc.Button("Read Now", id="read-now-btn", 
                                         color="primary", className="ms-3"),
                            ])
                        ])
                    ])
                ])
            ]),
            
            # Real-Time Plotting Tab
            dbc.Tab(label="Real-Time Plots", tab_id="plot-tab", children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Plot Configuration"),
                            dbc.CardBody([
                                dbc.Label("Variables to Plot:"),
                                dcc.Dropdown(
                                    id="plot-variables",
                                    options=[],
                                    multi=True,
                                    placeholder="Select variables...",
                                    className="mb-3"
                                ),
                                
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Plot Type:"),
                                        dbc.Select(
                                            id="plot-type",
                                            options=[
                                                {"label": "Time Series", "value": "time"},
                                                {"label": "XY Plot", "value": "xy"},
                                                {"label": "FFT Spectrum", "value": "fft"},
                                                {"label": "Histogram", "value": "hist"},
                                                {"label": "Heatmap", "value": "heat"},
                                                {"label": "3D Surface", "value": "3d"},
                                            ],
                                            value="time"
                                        )
                                    ], width=6),
                                    dbc.Col([
                                        dbc.Label("Time Window:"),
                                        dbc.Select(
                                            id="time-window",
                                            options=[
                                                {"label": "10 seconds", "value": 10},
                                                {"label": "30 seconds", "value": 30},
                                                {"label": "1 minute", "value": 60},
                                                {"label": "5 minutes", "value": 300},
                                                {"label": "All data", "value": 0},
                                            ],
                                            value=30
                                        )
                                    ], width=6)
                                ], className="mb-3"),
                                
                                dbc.ButtonGroup([
                                    dbc.Button("Update Plot", id="update-plot-btn", 
                                             color="primary"),
                                    dbc.Button("Clear Data", id="clear-plot-btn", 
                                             color="warning"),
                                    dbc.Button("Export", id="export-plot-btn", 
                                             color="info"),
                                ])
                            ])
                        ])
                    ], width=3),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(
                                    id="main-plot",
                                    figure=go.Figure(),
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'toImageButtonOptions': {
                                            'format': 'png',
                                            'filename': 'dsp_plot',
                                            'height': 600,
                                            'width': 1200,
                                        }
                                    },
                                    style={'height': '600px'}
                                )
                            ])
                        ])
                    ], width=9)
                ])
            ]),
            
            # DSP Analysis Tab
            dbc.Tab(label="DSP Analysis", tab_id="dsp-tab", children=[
                dbc.Row([
                    # Signal Selection
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Signal Analysis"),
                            dbc.CardBody([
                                dbc.Label("Select Signal:"),
                                dcc.Dropdown(
                                    id="dsp-signal-select",
                                    options=[],
                                    placeholder="Choose signal to analyze...",
                                    className="mb-3"
                                ),
                                
                                # Analysis Options
                                html.H6("Analysis Options:", className="mt-3"),
                                dbc.Checklist(
                                    id="dsp-analysis-options",
                                    options=[
                                        {"label": "FFT Analysis", "value": "fft"},
                                        {"label": "Statistics", "value": "stats"},
                                        {"label": "Autocorrelation", "value": "autocorr"},
                                        {"label": "Power Spectrum", "value": "power"},
                                        {"label": "THD Analysis", "value": "thd"},
                                        {"label": "SNR Calculation", "value": "snr"},
                                    ],
                                    value=["fft", "stats"],
                                    className="mb-3"
                                ),
                                
                                dbc.Button("Analyze", id="analyze-signal-btn", 
                                         color="primary", className="w-100")
                            ])
                        ])
                    ], width=3),
                    
                    # Analysis Results
                    dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Time Domain"),
                                    dbc.CardBody([
                                        dcc.Graph(id="time-domain-plot", 
                                                style={'height': '300px'})
                                    ])
                                ])
                            ], width=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Frequency Domain"),
                                    dbc.CardBody([
                                        dcc.Graph(id="freq-domain-plot", 
                                                style={'height': '300px'})
                                    ])
                                ])
                            ], width=6)
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Signal Statistics"),
                                    dbc.CardBody(id="signal-stats-display")
                                ])
                            ])
                        ])
                    ], width=9)
                ]),
                
                # Filter Design Section
                html.Hr(className="my-4"),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Digital Filter Design"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Filter Type:"),
                                        dbc.Select(
                                            id="filter-type",
                                            options=[
                                                {"label": "Low Pass", "value": "lowpass"},
                                                {"label": "High Pass", "value": "highpass"},
                                                {"label": "Band Pass", "value": "bandpass"},
                                                {"label": "Band Stop", "value": "bandstop"},
                                                {"label": "Notch", "value": "notch"},
                                            ],
                                            value="lowpass"
                                        )
                                    ], width=4),
                                    dbc.Col([
                                        dbc.Label("Order:"),
                                        dbc.Input(
                                            id="filter-order",
                                            type="number",
                                            value=4,
                                            min=1,
                                            max=20
                                        )
                                    ], width=4),
                                    dbc.Col([
                                        dbc.Label("Cutoff Freq (Hz):"),
                                        dbc.Input(
                                            id="filter-cutoff",
                                            type="number",
                                            value=1000,
                                            min=1
                                        )
                                    ], width=4)
                                ], className="mb-3"),
                                
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Implementation:"),
                                        dbc.RadioItems(
                                            id="filter-implementation",
                                            options=[
                                                {"label": "IIR (Butterworth)", "value": "butter"},
                                                {"label": "IIR (Chebyshev)", "value": "cheby"},
                                                {"label": "FIR (Window)", "value": "fir"},
                                            ],
                                            value="butter",
                                            inline=True
                                        )
                                    ])
                                ], className="mb-3"),
                                
                                dbc.ButtonGroup([
                                    dbc.Button("Design Filter", id="design-filter-btn", 
                                             color="primary"),
                                    dbc.Button("Apply to Signal", id="apply-filter-btn", 
                                             color="success"),
                                    dbc.Button("Generate C Code", id="gen-c-code-btn", 
                                             color="info"),
                                ])
                            ])
                        ])
                    ], width=6),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Filter Response"),
                            dbc.CardBody([
                                dcc.Graph(id="filter-response-plot", 
                                        style={'height': '400px'})
                            ])
                        ])
                    ], width=6)
                ])
            ]),
            
            # Memory View Tab
            dbc.Tab(label="Memory View", tab_id="memory-tab", children=[
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Memory Configuration"),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Label("Address (hex):"),
                                        dbc.Input(
                                            id="mem-address",
                                            value="0x0000",
                                            placeholder="0x0000"
                                        )
                                    ], width=6),
                                    dbc.Col([
                                        dbc.Label("Length:"),
                                        dbc.Input(
                                            id="mem-length",
                                            type="number",
                                            value=256,
                                            min=1,
                                            max=4096
                                        )
                                    ], width=6)
                                ], className="mb-3"),
                                
                                dbc.Label("Display Format:"),
                                dbc.RadioItems(
                                    id="mem-format",
                                    options=[
                                        {"label": "Hex", "value": "hex"},
                                        {"label": "Decimal", "value": "dec"},
                                        {"label": "Float", "value": "float"},
                                        {"label": "ASCII", "value": "ascii"},
                                        {"label": "Binary", "value": "bin"},
                                    ],
                                    value="hex",
                                    inline=True,
                                    className="mb-3"
                                ),
                                
                                dbc.Button("Read Memory", id="read-mem-btn", 
                                         color="primary", className="w-100")
                            ])
                        ])
                    ], width=3),
                    
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Memory Content"),
                            dbc.CardBody([
                                html.Pre(
                                    id="memory-display",
                                    children="Memory content will appear here...",
                                    style={
                                        "fontFamily": "monospace",
                                        "fontSize": "12px",
                                        "backgroundColor": "#f8f9fa",
                                        "padding": "15px",
                                        "height": "500px",
                                        "overflowY": "scroll"
                                    }
                                )
                            ])
                        ])
                    ], width=9)
                ])
            ]),
            
            # Configuration Tab
            dbc.Tab(label="Configuration", tab_id="config-tab", children=[
                dbc.Row([
                    # MAP File Upload
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Project Configuration"),
                            dbc.CardBody([
                                html.H6("MAP File Upload:"),
                                dcc.Upload(
                                    id="map-upload",
                                    children=dbc.Button(
                                        "Upload MAP File",
                                        color="secondary",
                                        className="w-100"
                                    ),
                                    multiple=False
                                ),
                                html.Div(id="map-info", className="mt-3"),
                                
                                html.Hr(),
                                
                                html.H6("Connection Settings:"),
                                dbc.InputGroup([
                                    dbc.InputGroupText("Host:"),
                                    dbc.Input(id="dss-host", value="localhost"),
                                ], className="mb-2"),
                                
                                dbc.InputGroup([
                                    dbc.InputGroupText("Port:"),
                                    dbc.Input(id="dss-port", type="number", value=8080),
                                ], className="mb-3"),
                                
                                dbc.ButtonGroup([
                                    dbc.Button("Connect", id="connect-btn", 
                                             color="success"),
                                    dbc.Button("Disconnect", id="disconnect-btn", 
                                             color="danger"),
                                ], className="w-100")
                            ])
                        ])
                    ], width=4),
                    
                    # Profile Management
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Application Profiles"),
                            dbc.CardBody([
                                html.H6("Select Profile:"),
                                dbc.Select(
                                    id="profile-select",
                                    options=[
                                        {"label": "Generic DSP", "value": "generic"},
                                        {"label": "Power Converter", "value": "power"},
                                        {"label": "Motor Control", "value": "motor"},
                                        {"label": "Signal Processing", "value": "signal"},
                                        {"label": "Communication", "value": "comm"},
                                        {"label": "Custom", "value": "custom"},
                                    ],
                                    value="generic",
                                    className="mb-3"
                                ),
                                
                                html.H6("Profile Settings:"),
                                html.Div(id="profile-settings", className="mb-3"),
                                
                                dbc.ButtonGroup([
                                    dbc.Button("Save Profile", id="save-profile-btn", 
                                             color="primary"),
                                    dbc.Button("Load Profile", id="load-profile-btn", 
                                             color="info"),
                                ])
                            ])
                        ])
                    ], width=4),
                    
                    # Export/Import
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader("Data Management"),
                            dbc.CardBody([
                                html.H6("Export Options:"),
                                dbc.Checklist(
                                    id="export-options",
                                    options=[
                                        {"label": "Variable Data", "value": "data"},
                                        {"label": "Configuration", "value": "config"},
                                        {"label": "Plots", "value": "plots"},
                                        {"label": "Analysis Results", "value": "analysis"},
                                    ],
                                    value=["data"],
                                    className="mb-3"
                                ),
                                
                                dbc.Label("Export Format:"),
                                dbc.RadioItems(
                                    id="export-format",
                                    options=[
                                        {"label": "CSV", "value": "csv"},
                                        {"label": "JSON", "value": "json"},
                                        {"label": "MATLAB", "value": "mat"},
                                        {"label": "HDF5", "value": "hdf5"},
                                    ],
                                    value="csv",
                                    inline=True,
                                    className="mb-3"
                                ),
                                
                                dbc.ButtonGroup([
                                    dbc.Button("Export", id="export-btn", 
                                             color="success"),
                                    dbc.Button("Import", id="import-btn", 
                                             color="primary"),
                                ], className="w-100")
                            ])
                        ])
                    ], width=4)
                ])
            ])
        ], id="main-tabs", active_tab="watch-tab"),
        
        # Hidden storage components
        dcc.Store(id="session-data", storage_type="session"),
        dcc.Store(id="plot-data", storage_type="memory"),
        dcc.Store(id="filter-coeffs", storage_type="memory"),
        
        # Download component
        dcc.Download(id="download-component"),
        
        # Update intervals
        dcc.Interval(
            id="update-interval",
            interval=UI_UPDATE_INTERVAL,
            n_intervals=0
        ),
        
        dcc.Interval(
            id="plot-interval",
            interval=PLOT_UPDATE_INTERVAL,
            n_intervals=0
        )
        
    ], fluid=True)

# Set the layout
app.layout = create_dashboard_layout

# Utility functions
def create_sparkline(values: List[float], width: int = 50) -> str:
    """Create ASCII sparkline visualization"""
    if not values or len(values) < 2:
        return ""
    
    chars = "▁▂▃▄▅▆▇█"
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        return chars[4] * min(len(values), width)
    
    # Take last 'width' values
    recent_values = values[-width:] if len(values) > width else values
    
    sparkline = ""
    for v in recent_values:
        index = int((v - min_val) / (max_val - min_val) * 7)
        sparkline += chars[min(index, 7)]
    
    return sparkline

def analyze_signal(signal: np.ndarray, fs: float = 10000) -> Dict:
    """Perform comprehensive signal analysis"""
    results = {}
    
    # Basic statistics
    results['mean'] = float(np.mean(signal))
    results['std'] = float(np.std(signal))
    results['rms'] = float(np.sqrt(np.mean(signal**2)))
    results['peak_to_peak'] = float(np.max(signal) - np.min(signal))
    results['crest_factor'] = float(np.max(np.abs(signal)) / results['rms']) if results['rms'] > 0 else 0
    
    # FFT
    n = len(signal)
    fft_vals = np.fft.fft(signal)
    fft_freq = np.fft.fftfreq(n, 1/fs)
    
    # Positive frequencies only
    pos_freq = fft_freq[:n//2]
    pos_fft = np.abs(fft_vals[:n//2])
    
    # Find dominant frequency
    dominant_idx = np.argmax(pos_fft[1:]) + 1  # Skip DC
    results['dominant_freq'] = float(pos_freq[dominant_idx])
    results['dominant_mag'] = float(pos_fft[dominant_idx])
    
    # THD calculation (simplified)
    if results['dominant_mag'] > 0:
        harmonics = []
        fundamental = results['dominant_freq']
        for h in range(2, 6):  # Check up to 5th harmonic
            h_freq = h * fundamental
            h_idx = np.argmin(np.abs(pos_freq - h_freq))
            if h_idx < len(pos_fft):
                harmonics.append(pos_fft[h_idx])
        
        thd = np.sqrt(np.sum(np.array(harmonics)**2)) / results['dominant_mag'] * 100
        results['thd'] = float(thd)
    else:
        results['thd'] = 0
    
    # SNR estimation (simplified)
    signal_power = results['dominant_mag']**2
    noise_power = np.var(signal)
    if noise_power > 0:
        results['snr_db'] = float(10 * np.log10(signal_power / noise_power))
    else:
        results['snr_db'] = float('inf')
    
    return results

# Callbacks will be added in a separate file for modularity
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)