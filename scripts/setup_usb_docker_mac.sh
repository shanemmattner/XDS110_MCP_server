#!/bin/bash
# Setup script for USB access in Docker on macOS

set -e

echo "=== XDS110 Docker USB Setup for macOS ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if XDS110 is connected
echo "Checking for XDS110 debug probe..."
if system_profiler SPUSBDataType | grep -q "0451:bef3\|Texas Instruments"; then
    echo -e "${GREEN}✓ XDS110 detected${NC}"
else
    echo -e "${YELLOW}⚠ XDS110 not detected. Please connect your XDS110 debug probe.${NC}"
    echo "  Looking for vendor ID 0451:bef3"
fi

# Check Docker version
echo
echo "Checking Docker version..."
DOCKER_VERSION=$(docker --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
echo "Docker version: $DOCKER_VERSION"

# Parse version
MAJOR=$(echo $DOCKER_VERSION | cut -d. -f1)
MINOR=$(echo $DOCKER_VERSION | cut -d. -f2)

# Check if version supports USB/IP (4.35.0+)
if [ "$MAJOR" -gt 4 ] || ([ "$MAJOR" -eq 4 ] && [ "$MINOR" -ge 35 ]); then
    echo -e "${GREEN}✓ Docker Desktop supports USB/IP (version 4.35.0+)${NC}"
    USB_IP_SUPPORTED=true
else
    echo -e "${YELLOW}⚠ Docker Desktop version $DOCKER_VERSION may not support USB/IP${NC}"
    echo "  USB/IP requires Docker Desktop 4.35.0 or later"
    USB_IP_SUPPORTED=false
fi

# Option 1: Try USB/IP approach
if [ "$USB_IP_SUPPORTED" = true ]; then
    echo
    echo "=== Option 1: USB/IP Setup ==="
    echo "To use USB/IP, you need to:"
    echo "1. Install a USB/IP server on macOS host"
    echo "2. Run the Docker container with privileged mode"
    echo
    echo "Install pyusbip (Python USB/IP server):"
    echo -e "${YELLOW}git clone https://github.com/tumayt/pyusbip${NC}"
    echo -e "${YELLOW}cd pyusbip && python3 -m venv .venv${NC}"
    echo -e "${YELLOW}source .venv/bin/activate && pip install libusb1${NC}"
    echo -e "${YELLOW}sudo python pyusbip${NC}"
fi

# Option 2: docker-machine with VirtualBox
echo
echo "=== Option 2: docker-machine with VirtualBox ==="
echo "Check if docker-machine is installed..."
if command -v docker-machine &> /dev/null; then
    echo -e "${GREEN}✓ docker-machine is installed${NC}"
    
    # Check for existing machine
    if docker-machine ls | grep -q "default"; then
        echo "Found existing docker-machine 'default'"
        echo "To enable USB:"
        echo -e "${YELLOW}docker-machine stop default${NC}"
        echo -e "${YELLOW}vboxmanage modifyvm default --usbxhci on${NC}"
        echo -e "${YELLOW}vboxmanage usbfilter add 0 --target default --name XDS110 --vendorid 0x0451 --productid 0xbef3${NC}"
        echo -e "${YELLOW}docker-machine start default${NC}"
        echo -e "${YELLOW}eval \$(docker-machine env default)${NC}"
    fi
else
    echo "docker-machine not found. Install with:"
    echo -e "${YELLOW}brew install docker-machine virtualbox virtualbox-extension-pack${NC}"
fi

# Build and run options
echo
echo "=== Building and Running ==="
echo
echo "To build the Docker image:"
echo -e "${GREEN}docker-compose build${NC}"
echo
echo "To run with USB support (privileged mode):"
echo -e "${GREEN}docker-compose up -d${NC}"
echo
echo "To access the container:"
echo -e "${GREEN}docker exec -it xds110-mcp-server bash${NC}"
echo
echo "Inside container, check USB devices:"
echo -e "${GREEN}lsusb | grep 0451:bef3${NC}"
echo -e "${GREEN}ls -la /dev/ttyACM*${NC}"

# Test build
echo
read -p "Do you want to build the Docker image now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building Docker image..."
    docker-compose build
    echo -e "${GREEN}✓ Build complete${NC}"
    
    echo
    read -p "Do you want to start the container? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting container..."
        docker-compose up -d
        echo -e "${GREEN}✓ Container started${NC}"
        
        echo
        echo "Checking USB access in container..."
        docker exec xds110-mcp-server bash -c "lsusb 2>/dev/null | grep -i '0451:bef3' || echo 'XDS110 not visible in container yet'"
        
        echo
        echo "To attach to container:"
        echo -e "${GREEN}docker exec -it xds110-mcp-server bash${NC}"
    fi
fi

echo
echo "=== Setup Complete ==="
echo "For detailed instructions, see: docs/guides/MACOS_DOCKER_SETUP.md"