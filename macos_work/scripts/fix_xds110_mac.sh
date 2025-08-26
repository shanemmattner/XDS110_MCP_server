#!/bin/bash
# Script to fix XDS110 USB access on macOS

echo "=== XDS110 macOS Fix Script ==="
echo

# Check if XDS110 is visible to macOS
echo "1. Checking USB detection..."
if system_profiler SPUSBDataType | grep -q "XDS110"; then
    echo "   ✓ XDS110 detected by macOS"
    system_profiler SPUSBDataType | grep -A 5 "XDS110"
else
    echo "   ✗ XDS110 not detected"
    exit 1
fi

echo
echo "2. Checking for FTDI drivers that might interfere..."
if kextstat | grep -q "FTDI"; then
    echo "   ! FTDI drivers found - these can interfere with XDS110"
    echo "   To unload: sudo kextunload /System/Library/Extensions/FTDIUSBSerialDriver.kext"
else
    echo "   ✓ No FTDI drivers loaded"
fi

echo
echo "3. Creating libusb configuration for XDS110..."
# Create a libusb config that might help
cat > /tmp/xds110_libusb.conf << EOF
# XDS110 USB configuration
VENDOR_ID=0x0451
PRODUCT_ID=0xbef3
EOF
echo "   Created /tmp/xds110_libusb.conf"

echo
echo "4. Testing different dslite approaches..."

# Test 1: Without any port specification (let it auto-detect)
echo
echo "Test 1: Auto-detect mode"
cd /Users/shanemattner/Desktop/XDS110_MCP_server/legacy_ti_debugger
dslite --config TMS320F280039C_LaunchPad.ccxml --verbose --list-cores 2>&1 | head -20

# Test 2: Try with explicit timeout
echo
echo "Test 2: With timeout"
dslite --config TMS320F280039C_LaunchPad.ccxml --timeout 30 --list-cores 2>&1 | head -20

# Test 3: Try resetting USB
echo
echo "Test 3: After USB reset attempt"
echo "Attempting to reset USB subsystem..."
# This would need sudo, so just show the command
echo "Would run: sudo killall -STOP -c usbd"
echo "Would run: sudo killall -CONT -c usbd"

echo
echo "5. Alternative: Using OpenOCD with XDS110 driver..."
echo "Testing OpenOCD connection..."
cat > /tmp/xds110_openocd.cfg << 'EOF'
# Minimal XDS110 test config
adapter driver xds110
xds110 supply 3300
adapter speed 1000

# Try to connect
init
echo "XDS110 adapter initialized"
shutdown
EOF

openocd -f /tmp/xds110_openocd.cfg 2>&1 | head -20

echo
echo "6. Checking for Code Composer Studio processes..."
if pgrep -f "Code Composer" > /dev/null; then
    echo "   ! CCS is running - this might lock the XDS110"
    echo "   Try closing CCS and running again"
else
    echo "   ✓ CCS is not running"
fi

echo
echo "=== Diagnosis Complete ==="
echo
echo "Common solutions:"
echo "1. Close Code Composer Studio if running"
echo "2. Unplug and replug the XDS110"
echo "3. Check System Preferences → Security & Privacy → Privacy → Developer Tools"
echo "4. Try: sudo chmod 666 /dev/cu.* /dev/tty.* (if serial devices exist)"
echo "5. Install Rosetta 2 if on Apple Silicon: softwareupdate --install-rosetta"
echo
echo "The Error -260 typically means:"
echo "- USB permissions issue on macOS"
echo "- Another process has locked the device"
echo "- Driver conflict (FTDI vs XDS110)"
echo "- Need to allow app in Security preferences"