#!/bin/bash
# Start API Server for XDS110 Testing

echo "Starting XDS110 Debug API Server"
echo "==============================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "API Endpoints:"
echo "  GET  /api/health                    - Health check"
echo "  POST /api/connect                   - Connect to hardware"
echo "  GET  /api/status                    - System status"
echo "  GET  /api/variables                 - List all variables"
echo "  GET  /api/variables/search?q=motor  - Search variables"
echo "  GET  /api/variables/<name>/read     - Read variable"
echo "  POST /api/variables/<name>/write    - Write variable"
echo "  POST /api/monitoring/start          - Start monitoring"
echo "  GET  /api/monitoring/data           - Get monitoring data"
echo ""
echo "Test commands:"
echo "  python3 test_api.py                - Run API tests"
echo "  python3 api_variable_test.py       - Systematic variable testing"
echo "  curl http://localhost:5000/api/health"
echo ""
echo "Starting server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python3 api_server.py