# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

XDS110 MCP Server enables LLMs to act as co-debuggers for Texas Instruments embedded systems, providing real-time variable monitoring, memory manipulation, and motor control analysis. The server auto-discovers 1000+ variables from CCS MAP files, requiring zero manual configuration.

**Key Hardware**: TI XDS110 Debug Probe + TMS320F280039C microcontroller (C2000 series) + DRV8323RH motor driver

## Commands

### Development & Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test MCP server without hardware (mock mode)
python test_mcp_server.py

# Test knowledge base only
python test_knowledge_only.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m xds110_mcp_server

# Format code
black xds110_mcp_server/

# Type checking
mypy xds110_mcp_server/
```

### Hardware Connection

```bash
# Check XDS110 detection
lsusb | grep "0451:bef3"
# Expected: Bus XXX Device XXX: ID 0451:bef3 Texas Instruments, Inc.

# Connect using TI DSS (WORKING METHOD)
cd legacy_ti_debugger
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/connect_target_v2.js

# Read motor variables (firmware must be loaded)
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/read_motor_vars_v1.js

# Check initialization state (loads firmware and reads values)
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/check_init_state.js
```

### Dashboard Interface

```bash
# Start dashboard with legacy connector (WORKING SOLUTION)
cd src/ui
python3 run_dashboard.py --ccxml "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml" --map "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.map" --binary "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out" --port 8051

# Access dashboard at http://localhost:8051
```

### ⚠️ CRITICAL: OpenOCD Cannot Debug C2000/C28x
OpenOCD does NOT support TI's proprietary C28x DSP architecture. Must use TI Debug Server Scripting (DSS) instead.

## Architecture

### Core Components

1. **MCP Server** (`xds110_mcp_server/server.py`): Main server handling MCP protocol and tool orchestration
2. **TI DSS Interface** (`legacy_ti_debugger/framework/ti_dss_adapter.py`): Manages DSS JavaScript execution
3. **DSS Scripts** (`legacy_ti_debugger/js_scripts/`): JavaScript scripts for C28x debugging
4. **Motor Knowledge** (`xds110_mcp_server/knowledge/motor_control.py`): Domain expertise for motor control
5. **Generic CCS Support** (`src/generic/`): MAP file parser for auto-discovery of variables
6. **Dashboard Interface** (`src/ui/`): Plotly Dash web interface for real-time monitoring

### Dashboard Components (NEW)

- **Legacy Loop Connector** (`src/ui/legacy_loop_connector.py`): Uses proven legacy DSS scripts for continuous monitoring
- **Legacy Dashboard Connector** (`src/ui/legacy_dash_connector.py`): Dashboard interface using legacy connector
- **Dashboard Runner** (`src/ui/run_dashboard.py`): Main dashboard application with Plotly Dash UI
- **Alternative Connectors**: Single-session and unified connectors for different approaches

### MCP Tools Available

- **Variable Monitor** (`tools/variable_monitor.py`): Read/monitor ANY CCS project variables
- **Memory Tools** (`tools/memory_tools.py`): Direct memory read/write operations
- **Analysis Tools** (`tools/analysis_tools.py`): AI-powered motor state analysis
- **MAP Parser** (`src/generic/map_parser_poc.py`): Auto-discovers variables from CCS MAP files

### Key Variable Structures

- **motorVars_M1**: Main motor control structure (requires firmware load)
  - `.absPosition_rad`: Absolute position in radians
  - `.motorState`: Current motor state (0=IDLE, 1=ALIGNMENT, 2=CTRL_RUN, 3=CL_RUNNING)
  - `.Idq_out_A.value[0/1]`: D/Q axis currents
- **debug_bypass** (0x0000d3c0): Debug override structure (if present in firmware)

## Working Components

### ✅ Verified Working
- Hardware connection via TI DSS to TMS320F280039C
- Reading motor control variables with real values
- CCXML configuration from Obake firmware
- DSS JavaScript scripts for C28x debugging
- MAP file parsing for variable auto-discovery (924 variables discovered)
- Dashboard interface at http://localhost:8051 with legacy connector
- Real-time variable monitoring using legacy DSS script pattern
- Battery-connected encoder reading position data

### ⚠️ Critical Requirements
- **CCS Installation**: Required at `/opt/ti/ccs1240/`
- **Firmware Loading**: motorVars_M1 only exists after loading firmware
- **DSS Only**: OpenOCD cannot debug C2000/C28x - use TI DSS exclusively
- **Single DSS Session**: Each variable read cycle must use complete connect+read+disconnect pattern

### Working Dashboard Architecture
- **Legacy Script Pattern**: Each monitoring cycle runs complete DSS script (connect→read→disconnect)
- **Variable Discovery**: 924 variables auto-discovered from MAP file
- **Real Data Confirmed**: Successfully reading motorVars_M1.motorState, absPosition_rad, and Idq_out_A values
- **UI Interface**: Full Plotly Dash interface with variable selection, real-time plotting, and monitoring controls

### Known Issues & Solutions
- **DSS Session Persistence**: Cross-process variable reads fail - solved by using complete script cycles
- **Variable Name Resolution**: Structured variables (e.g., motorVars_M1.motorState) require base variable in MAP
- **Monitoring Rate**: Limited to ~2Hz for reliable DSS script execution
- **Variable Visibility**: Dashboard shows base variables from MAP, structured access requires manual entry

## Motor Control Domain Knowledge

### Motor States
- **IDLE (0)**: Motor stopped, ready for commands
- **ALIGNMENT (1)**: Initial rotor alignment procedure
- **CTRL_RUN (2)**: Control loop initialization
- **CL_RUNNING (3)**: Closed-loop operation

### Common Debugging Patterns
- **Motor Humming**: Check Idq_out_A values, verify current control initialization
- **Zero Variables**: Ensure firmware is loaded before reading motorVars_M1
- **Connection Issues**: Only one DSS session allowed, close CCS if running
- **Variable Not Found**: Check if base variable exists in MAP file for structured variables

## UI Architecture

Plotly Dash interface (`src/ui/`):
- Real-time variable monitoring dashboard
- Interactive 3D motor position visualization
- MCP-Dash bridge for LLM interaction
- WebSocket support for live updates
- Legacy DSS script integration for reliable data

### Current Status (Latest Update)
- **Dashboard**: ✅ Running on port 8051 (legacy), 8052 (API test dashboard)
- **Hardware**: ✅ Connected with XDS110 + TMS320F280039C
- **Variables**: ✅ 924 variables discovered from MAP
- **Data Flow**: ✅ Real motor data confirmed via legacy scripts
- **Battery**: ✅ Connected for encoder position reading
- **API Server**: ✅ Flexible REST API on port 5001 reading REAL hardware values
- **Absolute Encoder**: ✅ Successfully reading motorVars_M1.absPosition_rad with live values
- **Confirmed Working**: PC=4184996, Memory=49152, Encoder position changing (4→0→1 radians)
- **Issue**: Encoder precision showing exactly 1.0 radians (impossible - needs investigation)

## API System Architecture

### Flexible Variable API (Port 5001)
- **Endpoint**: `GET /api/read/<variable>` - Read any variable or memory address
- **Endpoint**: `POST /api/read` - Read multiple variables in one request
- **Backend**: Uses `api_read_variable.js` DSS script with command-line arguments
- **Performance**: 15-second timeout for DSS operations
- **Tested**: Successfully reading PC register and memory addresses

### Test Dashboard (Port 8052)
- Simple Dash interface for testing API
- Quick buttons for common variables
- Custom variable input field
- Real-time status indicator

## Next Steps
- Load firmware to enable motorVars_M1 variable reading
- Test structured variable access (motorVars_M1.motorState)
- Optimize DSS connection time for faster reads
- Add caching layer for frequently accessed variables