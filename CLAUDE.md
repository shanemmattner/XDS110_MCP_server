# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

XDS110 MCP Server enables LLMs to act as co-debuggers for Texas Instruments embedded systems, providing real-time variable monitoring, memory manipulation, and motor control analysis through OpenOCD proxy architecture.

**Key Hardware**: TI XDS110 Debug Probe + TMS320F280039C microcontroller + PMSM motor control

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

### Hardware Connection (TI DSS - Working Method)

```bash
# Check XDS110 detection
lsusb | grep "0451:bef3"
# Expected: Bus 003 Device 026: ID 0451:bef3 Texas Instruments, Inc.

# Connect and read variables using TI DSS (WORKING)
cd legacy_ti_debugger
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/connect_target_v2.js
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/read_motor_vars_v1.js
```

### ⚠️ CRITICAL: OpenOCD Does NOT Work with C2000
```bash
# DO NOT USE - OpenOCD cannot debug TI C2000/C28x MCUs
# openocd -f configs/xds110_f28039.cfg  # Will fail with "Unknown target type c2000"
```

## Architecture

### Core Components

1. **MCP Server** (`xds110_mcp_server/server.py`): Main server handling MCP protocol, tool registration, and orchestration
2. **OpenOCD Manager** (`gdb_interface/openocd_manager.py`): Manages OpenOCD process for multi-client debugging
3. **GDB Client** (`gdb_interface/gdb_client.py`): Communicates with target via GDB protocol
4. **Motor Knowledge** (`knowledge/motor_control.py`): Domain expertise for motor control, FOC principles, fault patterns

### MCP Tools Implementation

- **Variable Monitor** (`tools/variable_monitor.py`): Read/monitor motor control variables with change detection
- **Memory Tools** (`tools/memory_tools.py`): Direct memory read/write to debug_bypass structure (0x0000d3c0)
- **Analysis Tools** (`tools/analysis_tools.py`): AI-powered motor state analysis and fault diagnosis

### Critical Memory Addresses

- `0x0000d3c0`: debug_bypass structure base address
- Motor state variables accessed via motorVars_M1 structure
- Union structures require special handling for field access

## Development Status

### Working Components (from legacy_ti_debugger/)
- ✅ Hardware connection via TI DSS (NOT OpenOCD)
- ✅ Successfully reading motor control variables
- ✅ Motor control variable schemas and relationships
- ✅ CCXML configuration from Obake firmware
- ✅ DSS JavaScript scripts for C28x debugging
- Debug_bypass structure manipulation (needs firmware verification)
- Calibration sequences (commands 64-67)

### CRITICAL DISCOVERY (2025-08-25)
**OpenOCD does NOT support TI C2000/C28x MCUs**. Must use TI Debug Server Scripting (DSS) instead.
- Required: Code Composer Studio installation at `/opt/ti/ccs1240/`
- Working path: `legacy_ti_debugger/` with DSS JavaScript scripts
- See `DEBUGGING_SETUP_GUIDE.md` for complete setup instructions

### In Progress
- Migrating from OpenOCD to TI DSS for MCP server
- Full MCP protocol implementation with DSS backend
- Real-time variable monitoring with sub-100ms latency
- Session handoff with Code Composer Studio

## Motor Control Domain Knowledge

### Key Motor States
- IDLE (0): Motor stopped
- ALIGNMENT (1): Bypass alignment procedure  
- CTRL_RUN (2): Control initialization
- CL_RUNNING (3): Closed-loop running

### Common Issues & Solutions
- **Motor Humming**: Missing current control initialization in bypass alignment
- **Overcurrent Faults**: Check current limits and calibration values
- **Position Errors**: Verify encoder calibration (commands 64-67)

## Future Enhancements

Planned Plotly Dash dashboard for real-time visualization:
- Live motor state plots and 3D position visualization
- Interactive parameter tuning interface
- Code viewer with breakpoint integration
- Complete IDE replacement capability