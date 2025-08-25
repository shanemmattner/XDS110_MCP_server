# XDS110 MCP Server - Complete Debugging Setup Guide

## Executive Summary
Successfully established connection to TMS320F280039C (C2000 series MCU) via XDS110 debug probe using TI's Debug Server Scripting (DSS). OpenOCD does NOT support C2000/C28x architecture - must use TI's proprietary tools.

## Critical Discovery: OpenOCD Cannot Debug C2000 MCUs

### The Problem
- **Initial Error**: `Unknown target type c2000` when running OpenOCD
- **Root Cause**: OpenOCD does not have support for TI's proprietary C28x DSP architecture
- **Failed Workarounds**:
  - Tried using `cortex_m` target type as fallback - architecturally incompatible
  - Modified configuration to use SWD with DAP - still incompatible with C28x core
  - OpenOCD 0.12.0 only supports ARM cores (Cortex-M, Cortex-A, etc.), not TI C28x DSP

### The Solution
Use TI's Debug Server Scripting (DSS) from Code Composer Studio installation instead of OpenOCD.

## Hardware Detection & Verification

### 1. XDS110 USB Detection
```bash
lsusb | grep "0451:bef3"
# Output: Bus 003 Device 026: ID 0451:bef3 Texas Instruments, Inc. CC1352R1 Launchpad
```
✅ Hardware successfully detected on USB bus

### 2. Required Software
- **Code Composer Studio (CCS)**: Found at `/opt/ti/ccs1240/`
- **DSS (Debug Server Scripting)**: Located at `/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh`
- **Required Version**: CCS 12.4.0 or compatible

## Complete Setup Process

### Step 1: Obtain Required Files

#### CCXML Configuration File
- **Source**: `~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml`
- **Destination**: `legacy_ti_debugger/TMS320F280039C_LaunchPad.ccxml`
- **Purpose**: Defines connection between XDS110 and TMS320F280039C target

#### Firmware Binary
- **Source**: `~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out`
- **Destination**: `legacy_ti_debugger/Flash_lib_DRV8323RH_3SC/obake_firmware.out`
- **Purpose**: Motor control firmware for the target MCU

### Step 2: Working DSS Connection Process

#### Successful Connection Script
Location: `legacy_ti_debugger/js_scripts/connect_target_v2.js`

Key connection sequence:
1. Create Debug Server instance
2. Load CCXML configuration
3. Open session with "C28xx_CPU1" target
4. Connect to target
5. GEL scripts automatically initialize RAM and DCSM

#### Working Command
```bash
cd legacy_ti_debugger
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/connect_target_v2.js
```

#### Expected Output
```
=== TI DSS Connection Script v2 ===
Setting CCXML configuration...
Attempting to open session...
Opened session with C28xx_CPU1
Connecting to target...
C28xx_CPU1: GEL Output: RAM initialization done
C28xx_CPU1: GEL Output: Memory Map Initialization Complete
C28xx_CPU1: GEL Output: ... DCSM Initialization Done ...
Connected successfully!
```

### Step 3: Reading Motor Variables

#### ⚠️ CRITICAL: MUST LOAD FIRMWARE FIRST!

**IMPORTANT DISCOVERY (2025-08-25)**: The motorVars_M1 structure only exists after loading the Obake firmware!

#### Correct Sequence for Reading Non-Zero Values:
1. Connect to target
2. **LOAD FIRMWARE** (critical step!)
3. Let target run briefly
4. Halt and read values

#### Working Script That Gets Non-Zero Values:
```bash
cd legacy_ti_debugger
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/check_init_state.js
```

#### Successfully Read Variables (WITH NON-ZERO VALUES!)
- `motorVars_M1.absPosition_rad` - **5 radians (286.48°)** ✅ NON-ZERO!
- `motorVars_M1.angleFOC_rad` - Field-oriented control electrical angle
- `motorVars_M1.angleENC_rad` - Encoder mechanical angle  
- `motorVars_M1.motorState` - Current motor state (0=IDLE)
- `motorVars_M1.speed_Hz` - Motor speed in Hz
- `motorVars_M1.Idq_out_A.value[0]` - D-axis current
- `motorVars_M1.Idq_out_A.value[1]` - Q-axis current
- `motorVars_M1.Vab_out_V.value[0/1]` - Alpha/Beta voltages

## Troubleshooting Guide

### Issue 1: OpenOCD "Unknown target type c2000"
**Error**: `configs/xds110_f28039.cfg:23: Error: Unknown target type c2000`
**Solution**: Cannot use OpenOCD with C2000. Must use TI DSS instead.

### Issue 2: OpenOCD Cortex-M Workaround Fails
**Error**: `target requires -dap parameter instead of -chain-position`
**Why it fails**: C28x is not an ARM core, cannot masquerade as Cortex-M

### Issue 3: DSS "Cannot find function listSessions"
**Error**: In `detect_probe.js` script
**Solution**: Use `connect_target_v2.js` which has correct API calls

### Issue 4: DSS Connection Conflict
**Error**: `Error -260 @ 0x0: An attempt to connect to the XDS110 failed`
**Cause**: Previous DSS session still active
**Solution**: Only one DSS connection allowed at a time, close CCS or other DSS sessions

### Issue 5: Missing CCXML File
**Error**: Configuration file not found
**Solution**: Copy from Obake firmware directory or create new one in CCS

## Architecture Incompatibility Details

### Why OpenOCD Doesn't Work
1. **C28x vs ARM**: TMS320F280039C uses TI's proprietary C28x DSP core
2. **Instruction Set**: C28x has unique instruction set, not ARM Thumb/Thumb2
3. **Debug Interface**: Uses TI's proprietary debug architecture, not ARM CoreSight
4. **Memory Architecture**: Different memory model than ARM cores

### OpenOCD Supported Targets (for reference)
- ARM Cortex-M (M0, M0+, M1, M3, M4, M7, M23, M33)
- ARM Cortex-A/R
- RISC-V
- MIPS
- AVR
- **NOT SUPPORTED**: TI C2000/C28x, TI MSP430, TI C6000 DSPs

## Migration Path for MCP Server

### Current Problem
The MCP server (`xds110_mcp_server/`) is designed around OpenOCD which cannot debug C2000.

### Recommended Solution
1. Keep using `legacy_ti_debugger/` with DSS for actual hardware debugging
2. Or modify MCP server to call DSS JavaScript scripts instead of OpenOCD
3. Or use the DSS Python API if available (investigate `/opt/ti/ccs1240/ccs/ccs_base/scripting/examples/python/`)

### Working Implementation Path
```
User Request → MCP Server → DSS JavaScript Script → XDS110 → TMS320F280039C
                    ↓
              Parse Output
                    ↓
              Return to User
```

## File Structure After Setup
```
legacy_ti_debugger/
├── TMS320F280039C_LaunchPad.ccxml  # CCXML configuration (from Obake)
├── Flash_lib_DRV8323RH_3SC/
│   └── obake_firmware.out          # Motor control firmware
├── js_scripts/
│   ├── connect_target_v2.js        # ✅ Working connection script
│   ├── read_motor_vars_v1.js       # ✅ Working variable reader
│   ├── debug_motor_vars.js         # Debug script (connection conflicts)
│   ├── detect_probe.js             # Has API issues
│   ├── load_and_debug.js           # Firmware loader
│   └── monitor_alignment.js        # Motor alignment monitor
├── framework/
│   └── ti_dss_adapter.py           # Python wrapper for DSS (incomplete)
└── motor_control.py                 # Motor control logic

configs/
├── xds110_f28039.cfg                # OpenOCD config (DOES NOT WORK)
├── f28039_config.json               # MCP server config
└── motor_variables.json             # Variable definitions
```

## Key Commands Reference

### Test Hardware Connection
```bash
lsusb | grep "0451:bef3"
```

### Run DSS Scripts
```bash
cd /home/shane/shane/XDS110_MCP_server/legacy_ti_debugger
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/connect_target_v2.js
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/read_motor_vars_v1.js
```

### Test MCP Server (Mock Mode)
```bash
python3 test_mcp_server.py  # Works without hardware
```

## Important Memory Addresses
- `0x0000d3c0`: debug_bypass structure base address (if present in firmware)
- Motor variables accessed via `motorVars_M1` structure
- Current control via `Idq_out_A` structure

## Next Steps
1. Continue using DSS scripts for hardware debugging
2. Consider implementing Python wrapper around DSS for better integration
3. Document motor control sequences and state transitions
4. Test motor control commands (64-67 for calibration, 84 for init, etc.)

## Validation Checklist
- [x] XDS110 detected on USB bus
- [x] CCS/DSS installation verified
- [x] CCXML configuration file obtained
- [x] Firmware binary available
- [x] DSS connection established
- [x] Motor variables successfully read
- [ ] Motor control commands tested
- [ ] Real-time monitoring implemented

---
**Document Created**: 2025-08-25
**Hardware**: XDS110 + TMS320F280039C LaunchPad
**Firmware**: Obake Motor Control
**Key Learning**: OpenOCD cannot debug TI C2000 MCUs - must use TI DSS