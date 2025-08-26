#!/usr/bin/env python3
"""
Callbacks for Generic DSP Debug Dashboard
Handles all interactive functionality
"""

from dash import callback, Input, Output, State, ALL, MATCH, callback_context
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import base64
import io
import re
from typing import Dict, List, Any, Optional, Tuple
import logging
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq

logger = logging.getLogger(__name__)

# Import data store from main dashboard
from generic_dsp_dashboard import data_store

# Variable categories for generic DSP applications
VARIABLE_CATEGORIES = {
    "control": r".*(?:ctrl|control|pid|loop|feedback).*",
    "adc_dac": r".*(?:adc|dac|analog|conv).*",
    "pwm": r".*(?:pwm|duty|pulse).*",
    "comm": r".*(?:spi|uart|can|i2c|serial|comm).*",
    "dsp": r".*(?:fft|filter|buffer|dma|fifo).*",
    "power": r".*(?:voltage|current|power|vdc|idc|vbus).*",
    "status": r".*(?:state|status|flag|error|fault).*",
}

# ============================================================================
# Variable Watch Callbacks
# ============================================================================

@callback(
    [Output("search-results", "children"),
     Output("watch-count", "children")],
    [Input("var-search-btn", "n_clicks"),
     Input("category-filter", "value")],
    [State("var-search-input", "value")]
)
def search_variables(n_clicks, categories, search_pattern):
    """Search for variables based on pattern and categories"""
    if not n_clicks:
        return [], "0"
    
    results = []
    all_vars = list(data_store.variables.keys())
    
    # Filter by search pattern
    if search_pattern:
        try:
            pattern = re.compile(search_pattern, re.IGNORECASE)
            filtered_vars = [v for v in all_vars if pattern.search(v)]
        except re.error:
            # If regex is invalid, do simple string search
            filtered_vars = [v for v in all_vars if search_pattern.lower() in v.lower()]
    else:
        filtered_vars = all_vars
    
    # Filter by categories
    category_vars = []
    for var in filtered_vars:
        for cat in categories:
            if cat in VARIABLE_CATEGORIES:
                cat_pattern = re.compile(VARIABLE_CATEGORIES[cat], re.IGNORECASE)
                if cat_pattern.search(var):
                    category_vars.append(var)
                    break
    
    # Create checklist for results
    if category_vars:
        results = dbc.Checklist(
            id="search-results-checklist",
            options=[{"label": var, "value": var} for var in category_vars[:50]],
            value=[],
            inline=False
        )
    else:
        results = html.Div("No variables found matching criteria", className="text-muted")
    
    return results, str(len(category_vars))

@callback(
    Output("watch-table", "data"),
    [Input("add-to-watch-btn", "n_clicks"),
     Input("clear-watch-btn", "n_clicks"),
     Input("update-interval", "n_intervals")],
    [State("search-results-checklist", "value"),
     State("watch-table", "data")]
)
def update_watch_table(add_clicks, clear_clicks, n_intervals, selected_vars, current_data):
    """Update the watch table with selected variables"""
    ctx = callback_context
    
    if not ctx.triggered:
        return current_data or []
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    # Clear watch table
    if trigger_id == "clear-watch-btn":
        return []
    
    # Add selected variables
    if trigger_id == "add-to-watch-btn" and selected_vars:
        current_data = current_data or []
        current_vars = [row["name"] for row in current_data]
        
        for var in selected_vars:
            if var not in current_vars:
                # Get metadata
                meta = data_store.metadata.get(var, {})
                
                current_data.append({
                    "name": var,
                    "value": 0,
                    "hex": "0x0",
                    "binary": "0b0",
                    "unit": meta.get("unit", ""),
                    "address": f"0x{meta.get('address', 0):04X}",
                    "delta": 0,
                    "trend": ""
                })
    
    # Update values on interval
    if trigger_id == "update-interval" and current_data:
        for row in current_data:
            var_name = row["name"]
            old_value = row.get("value", 0)
            new_value = data_store.get_latest(var_name)
            
            if new_value is not None:
                row["value"] = f"{new_value:.4f}" if isinstance(new_value, float) else str(new_value)
                
                # Format hex and binary
                try:
                    int_val = int(float(new_value))
                    row["hex"] = f"0x{int_val:04X}"
                    row["binary"] = f"{int_val:016b}"
                except:
                    pass
                
                # Calculate delta
                try:
                    delta = float(new_value) - float(old_value)
                    row["delta"] = f"{delta:+.4f}" if delta != 0 else ""
                except:
                    row["delta"] = ""
                
                # Create trend sparkline
                _, values = data_store.get_history(var_name, 10)
                if len(values) > 1:
                    from generic_dsp_dashboard import create_sparkline
                    row["trend"] = create_sparkline(values, width=20)
    
    return current_data

# ============================================================================
# Plotting Callbacks
# ============================================================================

@callback(
    Output("plot-variables", "options"),
    [Input("watch-table", "data")]
)
def update_plot_variable_options(watch_data):
    """Update available variables for plotting"""
    if not watch_data:
        return []
    
    return [{"label": row["name"], "value": row["name"]} for row in watch_data]

@callback(
    Output("main-plot", "figure"),
    [Input("update-plot-btn", "n_clicks"),
     Input("plot-interval", "n_intervals")],
    [State("plot-variables", "value"),
     State("plot-type", "value"),
     State("time-window", "value")]
)
def update_main_plot(update_clicks, n_intervals, variables, plot_type, time_window):
    """Update the main plot based on selected variables and type"""
    if not variables:
        return go.Figure().add_annotation(
            text="Select variables to plot",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Create appropriate plot based on type
    if plot_type == "time":
        return create_time_series_plot(variables, time_window)
    elif plot_type == "xy":
        return create_xy_plot(variables)
    elif plot_type == "fft":
        return create_fft_plot(variables)
    elif plot_type == "hist":
        return create_histogram(variables)
    elif plot_type == "heat":
        return create_heatmap(variables)
    elif plot_type == "3d":
        return create_3d_plot(variables)
    
    return go.Figure()

def create_time_series_plot(variables: List[str], time_window: int) -> go.Figure:
    """Create time series plot for selected variables"""
    fig = make_subplots(
        rows=len(variables), 
        cols=1,
        subplot_titles=variables,
        vertical_spacing=0.1 / len(variables) if len(variables) > 1 else 0.1
    )
    
    for i, var in enumerate(variables):
        timestamps, values = data_store.get_history(var, time_window if time_window > 0 else None)
        
        if timestamps and values:
            # Convert timestamps to relative time
            if timestamps:
                start_time = timestamps[0]
                rel_times = [(t - start_time) for t in timestamps]
            else:
                rel_times = []
            
            meta = data_store.metadata.get(var, {})
            unit = meta.get("unit", "")
            
            fig.add_trace(
                go.Scatter(
                    x=rel_times,
                    y=values,
                    mode='lines',
                    name=var,
                    line=dict(width=2)
                ),
                row=i+1, col=1
            )
            
            fig.update_xaxes(title_text="Time (s)", row=i+1, col=1)
            fig.update_yaxes(title_text=f"Value ({unit})" if unit else "Value", row=i+1, col=1)
    
    fig.update_layout(
        height=300 * len(variables),
        showlegend=True,
        title_text="Time Series Data"
    )
    
    return fig

def create_fft_plot(variables: List[str]) -> go.Figure:
    """Create FFT spectrum plot for selected variables"""
    fig = go.Figure()
    
    for var in variables:
        _, values = data_store.get_history(var)
        
        if values and len(values) > 1:
            # Perform FFT
            n = len(values)
            fs = 10  # Assume 10Hz sampling rate (can be made configurable)
            
            yf = fft(values)
            xf = fftfreq(n, 1/fs)
            
            # Take positive frequencies only
            xf_pos = xf[:n//2]
            yf_pos = 2.0/n * np.abs(yf[:n//2])
            
            fig.add_trace(
                go.Scatter(
                    x=xf_pos,
                    y=yf_pos,
                    mode='lines',
                    name=f"{var} FFT"
                )
            )
    
    fig.update_layout(
        title="FFT Spectrum Analysis",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Magnitude",
        yaxis_type="log",
        showlegend=True
    )
    
    return fig

def create_xy_plot(variables: List[str]) -> go.Figure:
    """Create XY plot (first vs second variable)"""
    if len(variables) < 2:
        return go.Figure().add_annotation(
            text="Select at least 2 variables for XY plot",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig = go.Figure()
    
    _, x_values = data_store.get_history(variables[0])
    _, y_values = data_store.get_history(variables[1])
    
    # Ensure equal length
    min_len = min(len(x_values), len(y_values))
    x_values = x_values[-min_len:]
    y_values = y_values[-min_len:]
    
    if x_values and y_values:
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='markers+lines',
                name=f"{variables[1]} vs {variables[0]}",
                marker=dict(size=5)
            )
        )
    
    fig.update_layout(
        title=f"XY Plot: {variables[1]} vs {variables[0]}",
        xaxis_title=variables[0],
        yaxis_title=variables[1]
    )
    
    return fig

def create_histogram(variables: List[str]) -> go.Figure:
    """Create histogram for selected variables"""
    fig = go.Figure()
    
    for var in variables:
        _, values = data_store.get_history(var)
        
        if values:
            fig.add_trace(
                go.Histogram(
                    x=values,
                    name=var,
                    opacity=0.7,
                    nbinsx=30
                )
            )
    
    fig.update_layout(
        title="Value Distribution Histogram",
        xaxis_title="Value",
        yaxis_title="Count",
        barmode='overlay',
        showlegend=True
    )
    
    return fig

def create_heatmap(variables: List[str]) -> go.Figure:
    """Create correlation heatmap for selected variables"""
    if len(variables) < 2:
        return go.Figure().add_annotation(
            text="Select at least 2 variables for heatmap",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Get data for all variables
    data_matrix = []
    for var in variables:
        _, values = data_store.get_history(var)
        if values:
            data_matrix.append(values[-100:])  # Last 100 points
    
    if data_matrix:
        # Calculate correlation matrix
        corr_matrix = np.corrcoef(data_matrix)
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix,
            x=variables,
            y=variables,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
        ))
        
        fig.update_layout(
            title="Variable Correlation Heatmap",
            xaxis_title="Variables",
            yaxis_title="Variables"
        )
    else:
        fig = go.Figure()
    
    return fig

def create_3d_plot(variables: List[str]) -> go.Figure:
    """Create 3D plot for first three variables"""
    if len(variables) < 3:
        return go.Figure().add_annotation(
            text="Select at least 3 variables for 3D plot",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig = go.Figure()
    
    _, x_values = data_store.get_history(variables[0])
    _, y_values = data_store.get_history(variables[1])
    _, z_values = data_store.get_history(variables[2])
    
    # Ensure equal length
    min_len = min(len(x_values), len(y_values), len(z_values))
    x_values = x_values[-min_len:]
    y_values = y_values[-min_len:]
    z_values = z_values[-min_len:]
    
    if x_values and y_values and z_values:
        fig.add_trace(
            go.Scatter3d(
                x=x_values,
                y=y_values,
                z=z_values,
                mode='markers+lines',
                marker=dict(size=4),
                line=dict(width=2),
                name='3D Trajectory'
            )
        )
    
    fig.update_layout(
        title=f"3D Plot: {variables[0]}, {variables[1]}, {variables[2]}",
        scene=dict(
            xaxis_title=variables[0],
            yaxis_title=variables[1],
            zaxis_title=variables[2]
        )
    )
    
    return fig

# ============================================================================
# DSP Analysis Callbacks
# ============================================================================

@callback(
    Output("dsp-signal-select", "options"),
    [Input("watch-table", "data")]
)
def update_dsp_signal_options(watch_data):
    """Update available signals for DSP analysis"""
    if not watch_data:
        return []
    
    return [{"label": row["name"], "value": row["name"]} for row in watch_data]

@callback(
    [Output("time-domain-plot", "figure"),
     Output("freq-domain-plot", "figure"),
     Output("signal-stats-display", "children")],
    [Input("analyze-signal-btn", "n_clicks")],
    [State("dsp-signal-select", "value"),
     State("dsp-analysis-options", "value")]
)
def analyze_dsp_signal(n_clicks, signal_name, analysis_options):
    """Perform DSP analysis on selected signal"""
    if not n_clicks or not signal_name:
        empty_fig = go.Figure()
        return empty_fig, empty_fig, "Select a signal to analyze"
    
    # Get signal data
    timestamps, values = data_store.get_history(signal_name)
    
    if not values or len(values) < 2:
        empty_fig = go.Figure()
        return empty_fig, empty_fig, "Insufficient data for analysis"
    
    # Time domain plot
    time_fig = go.Figure()
    time_fig.add_trace(
        go.Scatter(
            x=list(range(len(values))),
            y=values,
            mode='lines',
            name=signal_name
        )
    )
    time_fig.update_layout(
        title=f"Time Domain - {signal_name}",
        xaxis_title="Sample",
        yaxis_title="Value"
    )
    
    # Frequency domain plot
    freq_fig = go.Figure()
    if "fft" in analysis_options:
        n = len(values)
        fs = 10  # Sampling frequency (configurable)
        
        yf = fft(values)
        xf = fftfreq(n, 1/fs)
        
        # Positive frequencies only
        xf_pos = xf[:n//2]
        yf_pos = 2.0/n * np.abs(yf[:n//2])
        
        freq_fig.add_trace(
            go.Scatter(
                x=xf_pos,
                y=yf_pos,
                mode='lines',
                name='FFT Magnitude'
            )
        )
        freq_fig.update_layout(
            title="Frequency Domain (FFT)",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Magnitude"
        )
    
    # Statistics
    from generic_dsp_dashboard import analyze_signal
    stats = analyze_signal(np.array(values))
    
    stats_display = dbc.Table([
        html.Tbody([
            html.Tr([html.Td("Mean:"), html.Td(f"{stats['mean']:.4f}")]),
            html.Tr([html.Td("Std Dev:"), html.Td(f"{stats['std']:.4f}")]),
            html.Tr([html.Td("RMS:"), html.Td(f"{stats['rms']:.4f}")]),
            html.Tr([html.Td("Peak-to-Peak:"), html.Td(f"{stats['peak_to_peak']:.4f}")]),
            html.Tr([html.Td("Crest Factor:"), html.Td(f"{stats['crest_factor']:.2f}")]),
            html.Tr([html.Td("Dominant Freq:"), html.Td(f"{stats['dominant_freq']:.2f} Hz")]),
            html.Tr([html.Td("THD:"), html.Td(f"{stats['thd']:.2f}%")]),
            html.Tr([html.Td("SNR:"), html.Td(f"{stats['snr_db']:.2f} dB")]),
        ])
    ], bordered=True, hover=True, size="sm")
    
    return time_fig, freq_fig, stats_display

# ============================================================================
# Filter Design Callbacks
# ============================================================================

@callback(
    [Output("filter-response-plot", "figure"),
     Output("filter-coeffs", "data")],
    [Input("design-filter-btn", "n_clicks")],
    [State("filter-type", "value"),
     State("filter-order", "value"),
     State("filter-cutoff", "value"),
     State("filter-implementation", "value")]
)
def design_digital_filter(n_clicks, ftype, order, cutoff, implementation):
    """Design digital filter and show response"""
    if not n_clicks:
        return go.Figure(), None
    
    fs = 10000  # Sampling frequency (Hz)
    nyquist = fs / 2
    
    # Normalize cutoff frequency
    if cutoff >= nyquist:
        cutoff = nyquist * 0.9
    
    wn = cutoff / nyquist
    
    # Design filter based on implementation
    if implementation == "butter":
        b, a = scipy_signal.butter(order, wn, btype=ftype)
    elif implementation == "cheby":
        b, a = scipy_signal.cheby1(order, 0.5, wn, btype=ftype)  # 0.5 dB ripple
    else:  # FIR
        b = scipy_signal.firwin(order * 10 + 1, wn, window='hamming')
        a = [1.0]
    
    # Calculate frequency response
    w, h = scipy_signal.freqz(b, a, fs=fs, worN=2048)
    
    # Create subplots for magnitude and phase
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Magnitude Response", "Phase Response"),
        vertical_spacing=0.15
    )
    
    # Magnitude plot
    fig.add_trace(
        go.Scatter(
            x=w,
            y=20 * np.log10(np.abs(h)),
            mode='lines',
            name='Magnitude (dB)'
        ),
        row=1, col=1
    )
    
    # Phase plot
    fig.add_trace(
        go.Scatter(
            x=w,
            y=np.unwrap(np.angle(h)) * 180 / np.pi,
            mode='lines',
            name='Phase (degrees)'
        ),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Frequency (Hz)", row=2, col=1)
    fig.update_yaxes(title_text="Magnitude (dB)", row=1, col=1)
    fig.update_yaxes(title_text="Phase (degrees)", row=2, col=1)
    
    fig.update_layout(
        title=f"{ftype.title()} Filter - Order {order}, Cutoff {cutoff} Hz",
        showlegend=False,
        height=500
    )
    
    # Store coefficients
    coeffs = {
        "b": b.tolist(),
        "a": a.tolist(),
        "fs": fs,
        "type": ftype,
        "order": order,
        "cutoff": cutoff
    }
    
    return fig, json.dumps(coeffs)

@callback(
    Output("download-component", "data"),
    [Input("gen-c-code-btn", "n_clicks")],
    [State("filter-coeffs", "data")]
)
def generate_filter_c_code(n_clicks, coeffs_json):
    """Generate C code for the designed filter"""
    if not n_clicks or not coeffs_json:
        return None
    
    coeffs = json.loads(coeffs_json)
    b = coeffs["b"]
    a = coeffs["a"]
    
    # Generate C code
    c_code = f"""// Digital Filter Implementation
// Type: {coeffs['type']}, Order: {coeffs['order']}, Cutoff: {coeffs['cutoff']} Hz
// Sampling Frequency: {coeffs['fs']} Hz

#define FILTER_ORDER {len(b)-1}

// Filter coefficients (b - numerator)
const float b_coeffs[{len(b)}] = {{
    {', '.join([f'{c:.6f}f' for c in b])}
}};

// Filter coefficients (a - denominator)
const float a_coeffs[{len(a)}] = {{
    {', '.join([f'{c:.6f}f' for c in a])}
}};

// Filter state variables
float x_history[{len(b)}] = {{0}};
float y_history[{len(a)}] = {{0}};

float apply_filter(float input) {{
    // Shift input history
    for(int i = {len(b)-1}; i > 0; i--) {{
        x_history[i] = x_history[i-1];
    }}
    x_history[0] = input;
    
    // Calculate output
    float output = 0;
    
    // FIR part (b coefficients)
    for(int i = 0; i < {len(b)}; i++) {{
        output += b_coeffs[i] * x_history[i];
    }}
    
    // IIR part (a coefficients)
    for(int i = 1; i < {len(a)}; i++) {{
        output -= a_coeffs[i] * y_history[i-1];
    }}
    
    // Normalize by a[0]
    output /= a_coeffs[0];
    
    // Shift output history
    for(int i = {len(a)-2}; i > 0; i--) {{
        y_history[i] = y_history[i-1];
    }}
    y_history[0] = output;
    
    return output;
}}
"""
    
    return dict(content=c_code, filename="digital_filter.c")

# ============================================================================
# Memory View Callbacks
# ============================================================================

@callback(
    Output("memory-display", "children"),
    [Input("read-mem-btn", "n_clicks")],
    [State("mem-address", "value"),
     State("mem-length", "value"),
     State("mem-format", "value")]
)
def read_memory_display(n_clicks, address_str, length, format_type):
    """Read and display memory content"""
    if not n_clicks:
        return "Click 'Read Memory' to display content"
    
    try:
        # Parse address
        if address_str.startswith("0x"):
            address = int(address_str, 16)
        else:
            address = int(address_str)
    except:
        return "Invalid address format"
    
    # Simulate memory read (replace with actual DSS read)
    # For now, generate sample data
    memory_data = [i % 256 for i in range(address, address + length)]
    
    # Format output based on selected format
    if format_type == "hex":
        lines = []
        for i in range(0, length, 16):
            addr = address + i
            hex_vals = " ".join([f"{memory_data[j]:02X}" if j < len(memory_data) else "  " 
                               for j in range(i, i+16)])
            ascii_vals = "".join([chr(memory_data[j]) if 32 <= memory_data[j] < 127 else "." 
                                 for j in range(i, min(i+16, len(memory_data)))])
            lines.append(f"{addr:08X}: {hex_vals:48s} |{ascii_vals}|")
        return "\n".join(lines)
    
    elif format_type == "dec":
        lines = []
        for i in range(0, length, 8):
            addr = address + i
            dec_vals = " ".join([f"{memory_data[j]:3d}" if j < len(memory_data) else "   " 
                               for j in range(i, i+8)])
            lines.append(f"{addr:08X}: {dec_vals}")
        return "\n".join(lines)
    
    elif format_type == "float":
        lines = []
        for i in range(0, length, 4):
            addr = address + i
            if i+3 < len(memory_data):
                # Convert 4 bytes to float (simplified)
                val = (memory_data[i] << 24) | (memory_data[i+1] << 16) | \
                      (memory_data[i+2] << 8) | memory_data[i+3]
                # This is a simplified conversion - actual implementation would use struct.unpack
                float_val = val / 1000000.0
                lines.append(f"{addr:08X}: {float_val:.6f}")
        return "\n".join(lines)
    
    elif format_type == "ascii":
        ascii_str = "".join([chr(b) if 32 <= b < 127 else "." for b in memory_data])
        return ascii_str
    
    elif format_type == "bin":
        lines = []
        for i in range(0, min(length, 32), 4):  # Limit binary display
            addr = address + i
            bin_vals = " ".join([f"{memory_data[j]:08b}" if j < len(memory_data) else "" 
                               for j in range(i, i+4)])
            lines.append(f"{addr:08X}: {bin_vals}")
        return "\n".join(lines)
    
    return "Unknown format"

# ============================================================================
# Configuration Callbacks
# ============================================================================

@callback(
    Output("map-info", "children"),
    [Input("map-upload", "contents")],
    [State("map-upload", "filename")]
)
def process_map_file(contents, filename):
    """Process uploaded MAP file"""
    if not contents:
        return "No file uploaded"
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        content = decoded.decode('utf-8')
        
        # Parse MAP file (simplified)
        symbols_found = 0
        memory_regions = 0
        
        # Look for symbol definitions
        for line in content.split('\n'):
            if re.match(r'\s*0x[0-9a-fA-F]+\s+\w+', line):
                symbols_found += 1
        
        # Simulate adding to data store
        # In real implementation, would parse and add to data_store
        
        return dbc.Alert([
            html.H6(f"MAP File: {filename}"),
            html.P(f"Symbols found: {symbols_found}"),
            html.P(f"File size: {len(decoded)} bytes")
        ], color="success")
        
    except Exception as e:
        return dbc.Alert(f"Error processing file: {str(e)}", color="danger")

@callback(
    Output("profile-settings", "children"),
    [Input("profile-select", "value")]
)
def load_profile_settings(profile):
    """Load settings for selected profile"""
    profiles = {
        "generic": {
            "description": "General purpose DSP debugging",
            "auto_watch": ["state", "error", "status"],
            "update_rate": 500,
        },
        "power": {
            "description": "Power converter debugging",
            "auto_watch": ["vdc", "idc", "pwm_duty", "fault"],
            "update_rate": 200,
        },
        "motor": {
            "description": "Motor control debugging",
            "auto_watch": ["position", "velocity", "current", "state"],
            "update_rate": 100,
        },
        "signal": {
            "description": "Signal processing",
            "auto_watch": ["adc", "dac", "filter", "fft"],
            "update_rate": 100,
        },
        "comm": {
            "description": "Communication debugging",
            "auto_watch": ["uart", "spi", "can", "i2c"],
            "update_rate": 1000,
        }
    }
    
    if profile in profiles:
        settings = profiles[profile]
        return dbc.Card([
            dbc.CardBody([
                html.P(settings["description"]),
                html.Hr(),
                html.H6("Auto-watch patterns:"),
                html.Ul([html.Li(p) for p in settings["auto_watch"]]),
                html.P(f"Update rate: {settings['update_rate']}ms")
            ])
        ])
    
    return "Select a profile to view settings"

@callback(
    [Output("connection-indicator", "style"),
     Output("connection-status", "children")],
    [Input("connect-btn", "n_clicks"),
     Input("disconnect-btn", "n_clicks")],
    [State("dss-host", "value"),
     State("dss-port", "value")]
)
def handle_connection(connect_clicks, disconnect_clicks, host, port):
    """Handle connection to DSS/MCP server"""
    ctx = callback_context
    
    if not ctx.triggered:
        return {"color": "red", "fontSize": "20px"}, "Disconnected"
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "connect-btn":
        # Simulate connection (replace with actual connection logic)
        # In real implementation, would connect to MCP server
        return {"color": "green", "fontSize": "20px"}, f"Connected to {host}:{port}"
    
    elif trigger_id == "disconnect-btn":
        return {"color": "red", "fontSize": "20px"}, "Disconnected"
    
    return {"color": "red", "fontSize": "20px"}, "Disconnected"

# ============================================================================
# Export Callbacks
# ============================================================================

@callback(
    Output("download-component", "data", allow_duplicate=True),
    [Input("export-btn", "n_clicks")],
    [State("export-options", "value"),
     State("export-format", "value"),
     State("watch-table", "data")],
    prevent_initial_call=True
)
def export_data(n_clicks, options, format_type, watch_data):
    """Export data in selected format"""
    if not n_clicks or not watch_data:
        return None
    
    if format_type == "csv":
        # Create CSV data
        df = pd.DataFrame(watch_data)
        csv_string = df.to_csv(index=False)
        return dict(content=csv_string, filename=f"dsp_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    elif format_type == "json":
        # Create JSON data
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "variables": watch_data,
            "metadata": {
                "export_options": options,
                "num_variables": len(watch_data)
            }
        }
        json_string = json.dumps(export_data, indent=2)
        return dict(content=json_string, filename=f"dsp_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    return None