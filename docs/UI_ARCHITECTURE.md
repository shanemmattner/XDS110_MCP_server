# UI Architecture: Plotly Dash + MCP Integration

## Overview

A hybrid approach combining:
- **MCP Server**: LLM interaction and intelligent debugging
- **Plotly Dash**: Interactive UI for human visualization and control
- **WebSocket Bridge**: Real-time data streaming between components

This gives us the best of both worlds: AI-powered debugging AND human-friendly visualization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Browser                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Plotly Dash Web Interface                      │  │
│  │  • Real-time plots                                        │  │
│  │  • Variable watch                                         │  │
│  │  • Memory viewer                                          │  │
│  │  • DSP analysis tools                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    WebSocket (real-time)
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     Backend Server                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   Dash Server    │←→│  Data Broker     │←→│  MCP Server  │  │
│  │  (Port 8050)     │  │  (Redis/Memory)  │  │  (Port 3000) │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                              │                       │          │
│                              └───────┬───────────────┘          │
│                                      │                          │
│                         ┌────────────▼────────────┐             │
│                         │   TI DSS Interface      │             │
│                         │  (JavaScript Bridge)    │             │
│                         └────────────┬────────────┘             │
└─────────────────────────────────────┼───────────────────────────┘
                                      │
                          ┌───────────▼───────────┐
                          │   XDS110 → Target     │
                          └───────────────────────┘
```

## Key Features

### 1. Generic DSP Debugging (Not Motor-Specific)

```python
# Generic variable categories for ANY C2000 application
VARIABLE_CATEGORIES = {
    "control": {
        "pattern": r".*ctrl.*|.*control.*|.*pid.*",
        "description": "Control loop variables"
    },
    "signal": {
        "pattern": r".*adc.*|.*dac.*|.*pwm.*",
        "description": "Signal I/O variables"
    },
    "state": {
        "pattern": r".*state.*|.*mode.*|.*status.*",
        "description": "State machines and status"
    },
    "communication": {
        "pattern": r".*spi.*|.*uart.*|.*can.*|.*i2c.*",
        "description": "Communication interfaces"
    },
    "dsp": {
        "pattern": r".*fft.*|.*filter.*|.*buffer.*",
        "description": "DSP processing variables"
    },
    "power": {
        "pattern": r".*voltage.*|.*current.*|.*power.*",
        "description": "Power measurements"
    },
    "timing": {
        "pattern": r".*timer.*|.*counter.*|.*freq.*",
        "description": "Timing and frequency"
    },
    "math": {
        "pattern": r".*sin.*|.*cos.*|.*angle.*|.*phase.*",
        "description": "Mathematical computations"
    }
}
```

### 2. Plotly Dash UI Components

#### Real-Time Plotting
```python
# Multiple plot types for different DSP applications
PLOT_TYPES = {
    "time_series": "Standard time domain plot",
    "xy_plot": "Phase plots, Lissajous figures",
    "fft": "Frequency spectrum analysis",
    "waterfall": "Spectrogram over time",
    "3d_surface": "2D signal visualization",
    "polar": "Phasor diagrams",
    "histogram": "Statistical distribution",
    "heatmap": "Correlation matrices"
}
```

#### Interactive Variable Watch
- Auto-discovered from MAP file
- Grouped by category
- Real-time updates with sparklines
- Export to CSV/JSON

#### Memory Visualization
- Hex/ASCII/Float viewer
- Memory map with usage visualization
- Diff view for changes
- Breakpoint-like triggers

#### DSP Analysis Tools
- FFT with windowing options
- Digital filter design (IIR/FIR)
- Auto-correlation/cross-correlation
- THD calculation
- SNR measurement
- Generate C code for filters

### 3. MCP + UI Integration

The MCP server exposes UI-specific tools:

```json
{
  "tools": [
    {
      "name": "start_ui_session",
      "description": "Start interactive debugging UI",
      "returns": "URL to Dash interface"
    },
    {
      "name": "add_plot",
      "description": "Add variable to real-time plot",
      "parameters": {
        "variable": "string",
        "plot_type": "string",
        "window_size": "number"
      }
    },
    {
      "name": "set_trigger",
      "description": "Set conditional trigger for debugging",
      "parameters": {
        "variable": "string",
        "condition": "string",
        "action": "string"
      }
    },
    {
      "name": "export_data",
      "description": "Export debugging session data",
      "parameters": {
        "format": "csv|json|matlab|numpy",
        "variables": ["array of strings"]
      }
    }
  ]
}
```

### 4. WebSocket Real-Time Updates

```javascript
// WebSocket protocol for real-time streaming
{
  "type": "variable_update",
  "data": {
    "timestamp": 1234567890.123,
    "variables": {
      "adc_result": 2048,
      "pwm_duty": 0.75,
      "state_machine": 3
    }
  }
}

// Batch updates for efficiency
{
  "type": "batch_update",
  "data": {
    "timestamp": 1234567890.123,
    "updates": [
      {"name": "buffer[0]", "value": 123},
      {"name": "buffer[1]", "value": 456},
      // ... up to 100 variables per batch
    ]
  }
}
```

## Implementation Examples

### Example 1: Power Converter Debugging

```python
# User asks LLM
"Monitor the DC bus voltage and show me any ripple above 5%"

# MCP Server responds and starts UI
mcp_server.start_ui_session()
mcp_server.add_plot("dc_bus_voltage", plot_type="time_series")
mcp_server.set_trigger("dc_bus_ripple", condition="> 0.05", action="alert")

# Dash UI automatically:
# - Opens in browser
# - Shows real-time voltage plot
# - Highlights when ripple exceeds threshold
# - Calculates FFT to show ripple frequency
```

### Example 2: Digital Filter Analysis

```python
# User asks LLM
"Analyze the performance of the FIR filter on channel 1"

# MCP Server + UI collaboration
mcp_server.start_ui_session()
mcp_server.add_plot("adc_ch1_raw", plot_type="time_series")
mcp_server.add_plot("filter_output", plot_type="time_series")
mcp_server.add_plot("filter_response", plot_type="fft")

# Dash UI shows:
# - Input signal
# - Filtered output
# - Frequency response
# - Phase delay
# - Filter coefficients
```

### Example 3: Communication Protocol Debugging

```python
# User asks LLM
"Debug the SPI communication timing"

# UI provides logic analyzer view
mcp_server.start_ui_session()
mcp_server.add_plot(["spi_clk", "spi_mosi", "spi_miso", "spi_cs"], 
                    plot_type="digital_timing")

# Dash UI shows:
# - Digital timing diagram
# - Decoded data packets
# - Timing violations highlighted
# - Bit rate analysis
```

## UI Features by Application Domain

### Power Electronics
- Voltage/current waveforms
- Power factor visualization
- Harmonic analysis
- Thermal monitoring

### Motor Control (if applicable)
- Park/Clarke transformations
- Current vector visualization
- Speed/position tracking
- Fault detection

### Signal Processing
- FFT/DFT analysis
- Filter response
- Windowing functions
- Correlation plots

### Communication Systems
- Eye diagrams
- Constellation plots
- BER visualization
- Protocol decoding

### Control Systems
- Step response
- Bode plots
- Root locus
- PID tuning interface

## Deployment Options

### 1. Local Development
```bash
# Start MCP server
python -m xds110_mcp_server

# Start Dash UI
python src/ui/dash_debug_interface.py

# Access at http://localhost:8050
```

### 2. Team Deployment
```yaml
# docker-compose.yml
services:
  mcp-server:
    image: xds110-mcp:latest
    ports:
      - "3000:3000"
  
  dash-ui:
    image: xds110-dash:latest
    ports:
      - "8050:8050"
    environment:
      - MCP_SERVER=http://mcp-server:3000
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 3. Cloud Deployment
- Host Dash on AWS/Azure/GCP
- WebSocket through CloudFlare
- Redis Cloud for data persistence
- VPN for secure hardware access

## Performance Considerations

### Data Streaming Optimization
```python
class DataStreamOptimizer:
    def __init__(self):
        self.batch_size = 100  # Variables per update
        self.update_rate = 10  # Hz
        self.compression = True  # Delta compression
        
    def optimize_for_bandwidth(self, bandwidth_kbps):
        """Adjust streaming based on available bandwidth"""
        if bandwidth_kbps < 100:
            self.batch_size = 20
            self.update_rate = 2
        elif bandwidth_kbps < 1000:
            self.batch_size = 50
            self.update_rate = 5
```

### UI Responsiveness
- Virtual scrolling for large variable lists
- Decimation for plotting (max 1000 points)
- Worker threads for FFT calculations
- Lazy loading of historical data

## Security

### Authentication
```python
# Dash app with authentication
import dash_auth

# Basic auth for development
auth = dash_auth.BasicAuth(
    app,
    {'debug_user': 'secure_password'}
)

# OAuth for production
from dash_auth import OAuth
auth = OAuth(app, config={
    'client_id': 'YOUR_CLIENT_ID',
    'client_secret': 'YOUR_SECRET'
})
```

### Data Security
- TLS for WebSocket connections
- Session tokens for MCP access
- Read-only mode by default
- Audit logging of all writes

## Benefits of This Approach

1. **Best of Both Worlds**: AI intelligence + Human visualization
2. **Generic**: Works for ANY C2000 application
3. **Scalable**: From single user to team deployment
4. **Extensible**: Easy to add new plot types and analyses
5. **Familiar**: Engineers know Plotly/Dash
6. **Real-time**: Sub-second update latency
7. **Collaborative**: Multiple users can view same session

## Next Steps

1. Implement WebSocket bridge between MCP and Dash
2. Create reusable Dash components for DSP debugging
3. Add export capabilities (CSV, MATLAB, NumPy)
4. Build filter design wizard
5. Add session recording/playback
6. Create plot templates for common scenarios

This architecture provides a powerful, generic debugging environment that combines the intelligence of LLMs with the visualization capabilities engineers need.