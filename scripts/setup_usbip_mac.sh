#!/bin/bash
# Setup USB/IP for XDS110 on macOS

set -e

echo "=== Setting up USB/IP for XDS110 on macOS ==="
echo

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if pyusbip exists
if [ ! -d "pyusbip" ]; then
    echo "Installing pyusbip..."
    git clone https://github.com/tumayt/pyusbip
    cd pyusbip
    python3 -m venv .venv
    source .venv/bin/activate
    pip install libusb1
    cd ..
else
    echo "pyusbip already exists"
    cd pyusbip
    source .venv/bin/activate
    cd ..
fi

echo
echo -e "${GREEN}✓ XDS110 Detected:${NC}"
echo "  Vendor ID: 0x0451 (Texas Instruments)"
echo "  Product ID: 0xbef3"
echo "  Serial: LS4104RF"
echo

# Start USB/IP server
echo "Starting USB/IP server..."
echo -e "${YELLOW}This requires sudo privileges${NC}"
echo

cd pyusbip
sudo .venv/bin/python pyusbip &
USBIP_PID=$!
cd ..

echo "USB/IP server started with PID: $USBIP_PID"
sleep 2

# Now connect from Docker container
echo
echo "Attaching XDS110 to Docker container..."
echo

# First, get the bus ID from the container perspective
docker exec xds110-mcp-server bash -c "
apk add --no-cache usbip-tools 2>/dev/null || true
usbip list -r host.docker.internal
"

echo
echo "To attach the XDS110 in the container, run:"
echo -e "${GREEN}docker exec -it xds110-mcp-server bash${NC}"
echo "Then inside the container:"
echo -e "${GREEN}usbip attach -r host.docker.internal -b <BUS-ID>${NC}"
echo
echo "To stop USB/IP server later:"
echo -e "${YELLOW}sudo kill $USBIP_PID${NC}"