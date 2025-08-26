#!/bin/bash
# Debug version of dashboard with full logging

echo "Starting XDS110 Dashboard Debug Mode"
echo "====================================="

# Create log directory
LOG_DIR="debug_logs"
mkdir -p "$LOG_DIR"

# Timestamp for log files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/dashboard_debug_$TIMESTAMP.log"

echo "Log file: $LOG_FILE"

# Run dashboard with full debug logging
export PYTHONUNBUFFERED=1

# Set script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting dashboard with debug logging..."
echo "Press Ctrl+C to stop"
echo ""

# Run dashboard and capture all output
python3 -u run_dashboard.py \
    --ccxml ~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml \
    --map ~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.map \
    --binary ~/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out \
    --port 8050 \
    --host 0.0.0.0 2>&1 | tee "$LOG_FILE"