#!/bin/bash
# Generic dashboard starter - works with any C2000 project

echo "=========================================="
echo "XDS110 Generic DSP Debug Dashboard"
echo "=========================================="

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 --project PROJECT_DIR [OPTIONS]

Required:
  --project DIR      Path to CCS project directory

Options:
  --port PORT        Web server port (default: 8050)
  --host HOST        Web server host (default: 0.0.0.0)
  --no-binary        Don't load binary (use if already programmed)
  --ccxml FILE       Specific CCXML file (auto-detected if not specified)
  --map FILE         Specific MAP file (auto-detected if not specified)
  --binary FILE      Specific binary file (auto-detected if not specified)
  
Examples:
  # Auto-detect all files in project
  $0 --project ~/my_project
  
  # Specify port
  $0 --project ~/my_project --port 8080
  
  # Don't load binary
  $0 --project ~/my_project --no-binary
  
  # Specify exact files
  $0 --project ~/my_project --ccxml config.ccxml --map output.map

EOF
    exit 1
}

# Default values
PROJECT_DIR=""
PORT=8050
HOST="0.0.0.0"
LOAD_BINARY=true
CCXML=""
MAP_FILE=""
BINARY=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_DIR="$2"
            shift 2
            ;;
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
        --ccxml)
            CCXML="$2"
            shift 2
            ;;
        --map)
            MAP_FILE="$2"
            shift 2
            ;;
        --binary)
            BINARY="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            ;;
    esac
done

# Check required argument
if [ -z "$PROJECT_DIR" ]; then
    echo "❌ ERROR: --project is required"
    echo ""
    show_usage
fi

# Expand project directory path
PROJECT_DIR=$(realpath "$PROJECT_DIR" 2>/dev/null)
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ ERROR: Project directory not found: $PROJECT_DIR"
    exit 1
fi

echo "Project directory: $PROJECT_DIR"
echo ""

# Auto-detect files if not specified
echo "Scanning project files..."

# Find CCXML
if [ -z "$CCXML" ]; then
    CCXML=$(find "$PROJECT_DIR" -name "*.ccxml" -type f | head -1)
    if [ -z "$CCXML" ]; then
        echo "❌ ERROR: No CCXML file found in project"
        echo "  Please specify with --ccxml"
        exit 1
    fi
fi
echo "✅ CCXML: $(basename $CCXML)"

# Find MAP file
if [ -z "$MAP_FILE" ]; then
    MAP_FILE=$(find "$PROJECT_DIR" -name "*.map" -type f | head -1)
    if [ -z "$MAP_FILE" ]; then
        echo "❌ ERROR: No MAP file found in project"
        echo "  Please build your project first or specify with --map"
        exit 1
    fi
fi
echo "✅ MAP: $(basename $MAP_FILE)"

# Find binary (if loading)
if [ "$LOAD_BINARY" = true ] && [ -z "$BINARY" ]; then
    BINARY=$(find "$PROJECT_DIR" -name "*.out" -type f | grep -v "_linkInfo" | head -1)
    if [ -z "$BINARY" ]; then
        echo "⚠️  WARNING: No .out file found"
        echo "  Will attempt to connect without loading binary"
        LOAD_BINARY=false
    else
        echo "✅ Binary: $(basename $BINARY)"
    fi
fi

# Check XDS110
echo ""
echo "Checking XDS110 connection..."
if lsusb | grep -q "0451:bef3"; then
    echo "✅ XDS110 detected"
else
    echo "⚠️  WARNING: XDS110 not detected"
    echo "  Make sure the debug probe is connected"
    echo ""
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python dependencies
echo ""
echo "Checking Python dependencies..."
python3 -c "import dash, plotly" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip install dash plotly pandas numpy scipy
fi

# Extract some info from MAP file
echo ""
echo "Analyzing MAP file..."
SYMBOL_COUNT=$(grep -E '^\s*[0-9a-f]+\s+\w+\s*$' "$MAP_FILE" | wc -l)
echo "  Found approximately $SYMBOL_COUNT symbols"

# Show some example variables
echo "  Sample variables:"
grep -E '^\s*[0-9a-f]+\s+\w+\s*$' "$MAP_FILE" | head -5 | while read addr name rest; do
    echo "    - $name @ $addr"
done

# Start dashboard
echo ""
echo "=========================================="
echo "Starting dashboard..."
echo "URL: http://localhost:$PORT"
echo "=========================================="
echo ""
echo "Tips:"
echo "  1. Select variables from dropdown to monitor"
echo "  2. Click 'Start Monitoring' to begin"
echo "  3. Use write feature to change values"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$SCRIPT_DIR"

# Build command
CMD="python3 run_dashboard.py --ccxml \"$CCXML\" --map \"$MAP_FILE\" --port $PORT --host $HOST"

if [ "$LOAD_BINARY" = true ]; then
    CMD="$CMD --binary \"$BINARY\""
fi

# Run dashboard
eval $CMD