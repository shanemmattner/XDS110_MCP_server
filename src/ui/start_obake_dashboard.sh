#!/bin/bash
# Start XDS110 Dashboard for Obake Motor Controller Project

echo "=========================================="
echo "XDS110 Dashboard for Obake Motor Controller"
echo "=========================================="

# Define project paths
OBAKE_DIR="$HOME/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
CCXML="$OBAKE_DIR/TMS320F280039C_LaunchPad.ccxml"
MAP_FILE="$OBAKE_DIR/Flash_lib_DRV8323RH_3SC/obake_firmware.map"
BINARY="$OBAKE_DIR/Flash_lib_DRV8323RH_3SC/obake_firmware.out"

# Check if files exist
echo "Checking project files..."

if [ ! -f "$CCXML" ]; then
    echo "❌ ERROR: CCXML not found at: $CCXML"
    exit 1
fi
echo "✅ Found CCXML: $(basename $CCXML)"

if [ ! -f "$MAP_FILE" ]; then
    echo "❌ ERROR: MAP file not found at: $MAP_FILE"
    exit 1
fi
echo "✅ Found MAP file: $(basename $MAP_FILE)"

if [ ! -f "$BINARY" ]; then
    echo "❌ ERROR: Binary not found at: $BINARY"
    exit 1
fi
echo "✅ Found binary: $(basename $BINARY)"

# Check if XDS110 is connected
echo ""
echo "Checking XDS110 connection..."
if lsusb | grep -q "0451:bef3"; then
    echo "✅ XDS110 detected"
else
    echo "⚠️  WARNING: XDS110 not detected. Please connect the debug probe."
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for Python dependencies
echo ""
echo "Checking Python dependencies..."
python3 -c "import dash" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dash not installed. Installing..."
    pip install dash plotly pandas numpy scipy
fi

# Parse command line arguments
PORT=8050
HOST="0.0.0.0"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --no-binary)
            LOAD_BINARY=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--port PORT] [--host HOST] [--no-binary]"
            exit 1
            ;;
    esac
done

# Start the dashboard
echo ""
echo "=========================================="
echo "Starting dashboard..."
echo "URL: http://localhost:$PORT"
echo "=========================================="
echo ""
echo "Motor control variables available:"
echo "  - motorVars_M1.*"
echo "  - debug_bypass.*"
echo "  - controlVars.*"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the dashboard
cd "$SCRIPT_DIR"
if [ "$LOAD_BINARY" = false ]; then
    echo "Running without loading binary (assuming already programmed)..."
    python3 run_dashboard.py \
        --ccxml "$CCXML" \
        --map "$MAP_FILE" \
        --port $PORT \
        --host $HOST
else
    echo "Running with binary load..."
    python3 run_dashboard.py \
        --ccxml "$CCXML" \
        --map "$MAP_FILE" \
        --binary "$BINARY" \
        --port $PORT \
        --host $HOST
fi