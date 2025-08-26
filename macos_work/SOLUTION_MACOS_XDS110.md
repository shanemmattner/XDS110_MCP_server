# XDS110 macOS Connection Issue - Error -260

## Problem Summary
The XDS110 debug probe is detected by macOS but TI tools (dslite, DSS, xdsdfu) cannot connect with Error -260. This is a **known macOS USB HID driver issue** affecting TI debug tools.

## Root Cause
macOS requires signed kernel extensions and specific USB permissions that the TI XDS110 drivers don't properly handle, especially on Apple Silicon (M1/M2/M3) Macs.

## Confirmed Status
- ✅ XDS110 hardware detected (VID: 0x0451, PID: 0xbef3, Serial: LS4104RF) 
- ✅ macOS sees device via system_profiler
- ❌ TI tools cannot connect (Error -260)
- ❌ xdsdfu cannot see device
- ❌ OpenOCD fails to connect
- ❌ DSLite/UniFlash fails

## The Uptime Counter You Want to Read
**Address**: `0x00000C00` (CPU Timer 0 Counter)
- 32-bit counter incrementing at 100 MHz
- Formula: Uptime seconds = value ÷ 100,000,000

## Working Solutions

### Option 1: Use a Raspberry Pi or Linux Machine
```bash
# On Linux, these commands would work:
sudo apt-get install uniflash
dslite --config TMS320F280039C_LaunchPad.ccxml --core 0 \
       --memory-read 0x00000C00 4
```

### Option 2: Windows Virtual Machine (Parallels/VMware)
1. Install Windows 10/11 in VM
2. Install TI CCS/UniFlash for Windows
3. Pass through XDS110 USB to VM
4. Use dslite normally

### Option 3: Linux Docker Container with USB Passthrough
```bash
# On a Linux host (not macOS Docker Desktop):
docker run --privileged -v /dev/bus/usb:/dev/bus/usb \
           ti-tools dslite --config config.ccxml
```

### Option 4: Code Composer Studio GUI (Sometimes Works)
1. Open CCS IDE on Mac
2. Create Debug Configuration
3. Use Memory Browser to view 0x00000C00
4. Note: GUI sometimes succeeds where CLI fails

## Why Command Line Fails on macOS

The issue stems from:
1. **USB HID Driver Conflicts**: macOS's strict USB security model
2. **Unsigned Kernel Extensions**: TI drivers aren't properly signed for macOS
3. **IOKit Permissions**: The ioctl calls TI tools make aren't allowed
4. **Apple Silicon Complications**: x86_64 emulation doesn't help with USB drivers

## What We Tried (All Failed)
- ✗ Running with sudo
- ✗ Using Rosetta 2 (arch -x86_64)
- ✗ Setting DYLD_LIBRARY_PATH
- ✗ Different dslite modes
- ✗ OpenOCD with XDS110 driver
- ✗ Resetting USB subsystem
- ✗ Installing/reinstalling UniFlash

## TI's Official Position
From TI E2E forums: "The tools team did find an issue with the FTDI drivers on Mac" and the recommended workaround is to use XDS110 instead of FTDI. However, even XDS110 has issues on newer macOS versions.

## Recommendation
**Use a Linux machine or VM for reliable TMS320F280039C debugging**. The macOS USB driver issues are unlikely to be fixed soon as TI prioritizes Windows and Linux support.

## Alternative: Remote Debugging
Set up a Raspberry Pi or Linux server with:
1. XDS110 connected via USB
2. OpenOCD or dslite server running
3. Access remotely from Mac via network

```bash
# On Linux server:
openocd -f xds110.cfg -c "bindto 0.0.0.0"

# On Mac:
telnet linux-server 4444
> mdw 0x00000C00 1
```

## The Bottom Line
Your XDS110 hardware is fine. Your TMS320F280039C is fine. The uptime counter is at 0x00000C00. But macOS USB driver issues prevent TI tools from connecting. Use Linux or Windows for actual debugging.