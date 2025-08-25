# XDS110 MCP Server - Quick Reference Card

## 🚀 Working Commands (Copy & Paste)

### Check Hardware
```bash
lsusb | grep "0451:bef3"
```

### Connect to Target & Read Variables (WITH NON-ZERO VALUES!)
```bash
cd /home/shane/shane/XDS110_MCP_server/legacy_ti_debugger

# ✅ USE THIS TO GET NON-ZERO VALUES (loads firmware first):
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/check_init_state.js

# Alternative scripts (may show zeros if firmware not loaded):
/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh js_scripts/read_motor_vars_v1.js
```

### Test Without Hardware
```bash
cd /home/shane/shane/XDS110_MCP_server
python3 test_mcp_server.py
```

## ⚠️ What NOT to Do
```bash
# THESE WILL NOT WORK - C2000 not supported by OpenOCD
python3 main.py --config configs/f28039_config.json  # ❌ FAILS
openocd -f configs/xds110_f28039.cfg                 # ❌ FAILS
```

## 📁 Key Files
- **CCXML Config**: `legacy_ti_debugger/TMS320F280039C_LaunchPad.ccxml`
- **Firmware**: `legacy_ti_debugger/Flash_lib_DRV8323RH_3SC/obake_firmware.out`
- **Working Scripts**: `legacy_ti_debugger/js_scripts/connect_target_v2.js`
- **Full Documentation**: `DEBUGGING_SETUP_GUIDE.md`

## 🔧 Required Software
- Code Composer Studio: `/opt/ti/ccs1240/`
- DSS Tool: `/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh`

## 📊 Motor Variables Successfully Read (WITH REAL VALUES!)
- `motorVars_M1.absPosition_rad` - **5 radians (286.48°)** ✅ NON-ZERO!
- `motorVars_M1.motorState` - 0=IDLE, 1=ALIGNMENT, 2=CTRL_RUN, 3=CL_RUNNING
- `motorVars_M1.angleFOC_rad` - FOC electrical angle
- `motorVars_M1.angleENC_rad` - Encoder angle
- `motorVars_M1.Idq_out_A.value[0]` - D-axis current
- `motorVars_M1.Idq_out_A.value[1]` - Q-axis current

## 🎯 Critical Discovery
**MUST LOAD FIRMWARE FIRST!** The motorVars_M1 structure doesn't exist until firmware is loaded.

## 🎯 Remember
**TI C2000/C28x requires TI's Debug Server Scripting (DSS), NOT OpenOCD!**