# XDS110 Connection Status on macOS

## Current Situation (2025-08-25)

### ✅ What's Working:
1. **XDS110 Hardware Detected**
   - Device: XDS110 (03.00.00.32) Embed with CMSIS-DAP
   - Serial: LS4104RF
   - USB VID: 0x0451, PID: 0xbef3
   - macOS detects it via system_profiler

2. **Docker Integration**
   - Successfully created Docker containers with USB support
   - Host bridge running on port 5555 provides XDS110 status to containers
   - Containers can query XDS110 presence

3. **Software Installed**
   - Code Composer Studio 20.1.0 at /Applications/ti/ccs2010/
   - UniFlash with dslite CLI tool installed via Homebrew
   - OpenOCD installed (but doesn't support C2000)

### ❌ Connection Issues:
1. **DSS (Debug Server Scripting)**
   - Error: `libti_xpcom.dylib` cannot load
   - Library is x86_64, needs Rosetta 2 but still fails
   - This is a known macOS compatibility issue

2. **DSLite/UniFlash**
   - Error -260: "An attempt to connect to the XDS110 failed"
   - Same error from xds110reset utility
   - Likely USB permission or driver issue on macOS

3. **OpenOCD**
   - Cannot connect: C2000/C28x architecture not supported
   - Only supports ARM, RISC-V, etc., not TI's proprietary DSP

## Target Information: TMS320F280039C

### Uptime Counter Location:
- **Address**: `0x00000C00` (CPU Timer 0 Counter Register)
- **Name**: TIM register
- **Size**: 32-bit counter
- **Frequency**: 100 MHz (100,000,000 increments/second)
- **Calculation**: Uptime = TIM / 100,000,000 seconds

### Other Important Registers:
- `0x00000C02`: PRD - Timer Period Register
- `0x00000C04`: TCR - Timer Control Register
- `0x0000700A`: PLLSTS - PLL Status (clock info)
- `0x00000882`: PARTIDL - Device ID Low
- `0x00000884`: REVID - Device Revision

## Possible Solutions:

### 1. macOS System Preferences
- Check Security & Privacy → Privacy → Developer Tools
- May need to allow Terminal/dslite USB access
- Restart after granting permissions

### 2. Use Code Composer Studio GUI
- Open CCS IDE directly
- Create new target configuration for XDS110
- Use Memory Browser to read address 0x00000C00

### 3. Virtual Machine Approach
- Install Ubuntu/Windows VM
- Pass through XDS110 USB to VM
- TI tools work better on Linux/Windows

### 4. Alternative Debug Tools
- J-Link with J-Link GDB Server (if it supports C2000)
- Segger tools might have better macOS support

## Commands That Should Work (Once Connected):

### Reading Uptime:
```javascript
// DSS JavaScript (if it worked)
debugSession.memory.readWord(0, 0x00000C00)
```

```bash
# DSLite (if it connected)
dslite --config TMS320F280039C_LaunchPad.ccxml \
       --core 0 \
       --memory-read 0x00000C00 4
```

```gdb
# GDB (if connected)
x/1wx 0x00000C00
```

## Current Workaround:
The XDS110 host bridge at port 5555 confirms the hardware is present and provides USB info to Docker containers. However, actual debugging requires resolving the macOS USB/driver issues with TI's tools.

## Next Steps:
1. Try CCS GUI directly for memory browsing
2. Check macOS security settings for USB permissions
3. Consider Linux VM for reliable debugging
4. Contact TI support about macOS compatibility