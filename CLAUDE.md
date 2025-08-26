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

### ⚠️ CRITICAL: OpenOCD Cannot Debug C2000/C28x
OpenOCD does NOT support TI's proprietary C28x DSP architecture. Must use TI Debug Server Scripting (DSS) instead.

## Architecture

### Core Components

1. **MCP Server** (`xds110_mcp_server/server.py`): Main server handling MCP protocol and tool orchestration
2. **TI DSS Interface** (`legacy_ti_debugger/framework/ti_dss_adapter.py`): Manages DSS JavaScript execution
3. **DSS Scripts** (`legacy_ti_debugger/js_scripts/`): JavaScript scripts for C28x debugging
4. **Motor Knowledge** (`xds110_mcp_server/knowledge/motor_control.py`): Domain expertise for motor control
5. **Generic CCS Support** (`src/generic/`): MAP file parser for auto-discovery of variables

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
- Reading motor control variables with non-zero values
- CCXML configuration from Obake firmware
- DSS JavaScript scripts for C28x debugging
- MAP file parsing for variable auto-discovery

### ⚠️ Critical Requirements
- **CCS Installation**: Required at `/opt/ti/ccs1240/`
- **Firmware Loading**: motorVars_M1 only exists after loading firmware
- **DSS Only**: OpenOCD cannot debug C2000/C28x - use TI DSS exclusively

### In Progress
- Full MCP server implementation with DSS backend
- Plotly Dash UI for real-time visualization
- Generic CCS project support via MAP file parsing

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

## UI Architecture

Plotly Dash interface (`src/ui/`):
- Real-time variable monitoring dashboard
- Interactive 3D motor position visualization
- MCP-Dash bridge for LLM interaction
- WebSocket support for live updates