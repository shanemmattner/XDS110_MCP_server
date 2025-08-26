#!/bin/bash
# Wrapper to run DSS with proper environment on macOS using Rosetta 2

# Set up CCS paths
export CCS_BASE=/Applications/ti/ccs2010/ccs/ccs_base
export DEBUGSERVER_BIN=$CCS_BASE/DebugServer/bin

# Set library paths for macOS
export DYLD_LIBRARY_PATH=$DEBUGSERVER_BIN:$CCS_BASE/common/lib:$DYLD_LIBRARY_PATH
export DYLD_FALLBACK_LIBRARY_PATH=$DEBUGSERVER_BIN:$CCS_BASE/common/lib

# Set @rpath for dynamic libraries
export DYLD_FRAMEWORK_PATH=$CCS_BASE/DebugServer/bin

echo "=== DSS Rosetta Wrapper ==="
echo "CCS_BASE: $CCS_BASE"
echo "DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"
echo "Architecture: x86_64 (via Rosetta 2)"
echo

# Change to the legacy_ti_debugger directory
cd /Users/shanemattner/Desktop/XDS110_MCP_server/legacy_ti_debugger

# Try to run DSS with x86_64 architecture
echo "Attempting connection to XDS110..."
arch -x86_64 $CCS_BASE/scripting/bin/dss.sh js_scripts/connect_target_v2.js 2>&1

# If that fails, try a simpler test
if [ $? -ne 0 ]; then
    echo
    echo "Connection failed. Trying simple version check..."
    arch -x86_64 $CCS_BASE/scripting/bin/dss.sh -v 2>&1
fi