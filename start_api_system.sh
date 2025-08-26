#!/bin/bash
# Start the flexible API system without affecting existing dashboards

echo "=================================="
echo "Starting Flexible Variable API System"
echo "=================================="
echo ""
echo "This will start:"
echo "  - API server on port 5001"
echo "  - Web interface on port 8053"  
echo "  - Test dashboard on port 8052"
echo ""
echo "Your existing dashboards remain available:"
echo "  - Legacy dashboard: port 8051"
echo "  - Working script dashboard: port 8055"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="
echo ""

# Function to kill all background processes on exit
cleanup() {
    echo -e "\n\nShutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Start API server
echo "Starting API server on port 5001..."
python3 src/api/flexible_variable_api.py &
sleep 2

# Start web interface server
echo "Starting web interface on port 8053..."
python3 src/api/serve_web_interface.py &
sleep 1

# Start test dashboard
echo "Starting test dashboard on port 8052..."
python3 src/ui/api_test_dashboard.py &

echo ""
echo "All services started!"
echo ""
echo "Access points:"
echo "  - API endpoint: http://localhost:5001/api/info"
echo "  - Web interface: http://localhost:8053/api_web_interface.html"
echo "  - Test dashboard: http://localhost:8052"
echo ""
echo "Your original dashboards are still available:"
echo "  - http://localhost:8051 (legacy dashboard)"
echo "  - http://localhost:8055 (working script dashboard)"
echo ""

# Wait for all background jobs
wait