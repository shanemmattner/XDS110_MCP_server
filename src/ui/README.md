# XDS110 Plotly Dash Dashboard

A real-time web-based debugging interface for TI C2000 DSP applications using XDS110 debug probe.

## Quick Start

### Prerequisites

1. **Code Composer Studio** installed at `/opt/ti/ccs1240/ccs` (or specify different path)
2. **Python packages**:
```bash
pip install dash plotly pandas numpy scipy
```

3. **Your project files**:
   - `.ccxml` file - Target configuration
   - `.map` file - Symbol addresses  
   - `.out` file - Binary to load (optional)

### Running the Dashboard

```bash
# Basic usage - connects and loads binary
python run_dashboard.py \
    --ccxml /path/to/your/project.ccxml \
    --map /path/to/your/project.map \
    --binary /path/to/your/project.out

# Without loading binary (if already programmed)
python run_dashboard.py \
    --ccxml /path/to/your/project.ccxml \
    --map /path/to/your/project.map

# Custom port
python run_dashboard.py \
    --ccxml project.ccxml \
    --map project.map \
    --port 8080
```

### Example with actual project

```bash
# For the Obake motor controller project
python run_dashboard.py \
    --ccxml ~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml \
    --map ~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.map \
    --binary ~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out
```

## Features

### 1. Real-Time Variable Monitoring
- Select any variables from your MAP file
- Monitor multiple variables simultaneously  
- 5Hz default update rate (configurable)
- See current values in monospace display

### 2. Live Plotting
- Time-series plots of selected variables
- Last 30 seconds of data shown
- Multiple variables on same plot
- Auto-scaling axes

### 3. Variable Write
- Write values to any variable
- Immediate feedback on success/failure
- Useful for tuning parameters

### 4. Zero Configuration
- Automatically discovers all variables from MAP file
- No need to hardcode addresses
- Works with ANY C2000 project

## How It Works

1. **MAP File Parsing**: Extracts all symbol names and addresses
2. **TI DSS Connection**: Uses TI's Debug Server Scripting to connect to XDS110
3. **Real-Time Monitoring**: Polls selected variables at specified rate
4. **Web Interface**: Plotly Dash provides interactive web UI
5. **Data Bridge**: Manages data flow between hardware and UI

## Architecture

```
┌─────────────────┐
│   Web Browser   │
│  (Plotly Dash)  │
└────────┬────────┘
         │ HTTP
┌────────▼────────┐
│  run_dashboard  │
│     (Python)    │
└────────┬────────┘
         │
┌────────▼────────┐
│ XDS110Interface │
│  (DSS Scripts)  │
└────────┬────────┘
         │ USB
┌────────▼────────┐
│    XDS110       │
│  Debug Probe    │
└────────┬────────┘
         │ SWD/JTAG
┌────────▼────────┐
│   C2000 Target  │
└─────────────────┘
```

## Files

- `run_dashboard.py` - Main entry point, simple dashboard
- `xds110_dash_connector.py` - Hardware interface via TI DSS
- `generic_dsp_dashboard.py` - Full-featured dashboard (advanced)
- `dashboard_callbacks.py` - Dash callbacks for full dashboard
- `dsp_utilities.py` - DSP analysis tools (FFT, filters, etc.)

## Troubleshooting

### "DSS not found"
Make sure CCS is installed at `/opt/ti/ccs1240/ccs` or modify the path in `xds110_dash_connector.py`

### "Connection timeout"
- Check XDS110 is connected: `lsusb | grep "0451:bef3"`
- Ensure target is powered
- Try resetting the XDS110

### "Variable not found"
- Variable might be optimized out - check MAP file
- Variable might be in different section - check compiler settings

### No data showing
- Make sure binary is loaded (use --binary flag)
- Check that variables exist in memory
- Try reading known addresses first

## Advanced Usage

### Custom Update Rates
Modify in `run_dashboard.py`:
```python
start_monitoring(selected_vars, rate_hz=10)  # 10Hz instead of 5Hz
```

### Memory Regions
The MAP file parser extracts memory regions. Access them via:
```python
xds110.map_symbols  # Dictionary of all symbols
```

### Using the Full Dashboard
For advanced features (FFT, filters, memory view):
```python
python generic_dsp_dashboard.py
```

## Extending

### Add Custom Analysis
In your callbacks:
```python
from dsp_utilities import DSPAnalyzer

# Calculate THD
thd = DSPAnalyzer.calculate_thd(signal_data, fs=10000)

# Design filter
b, a = DSPAnalyzer.design_iir_filter('lowpass', cutoff=1000, fs=10000)
```

### Add New Plots
Modify `update_display` callback to add different plot types:
- FFT spectrum
- XY plots  
- Histograms
- 3D plots

## Performance

- Default 5Hz monitoring rate works well
- Can achieve 10Hz with fewer variables
- Network latency adds ~10-50ms
- DSS script execution: ~50-100ms per call

## License

Part of XDS110_MCP_server project