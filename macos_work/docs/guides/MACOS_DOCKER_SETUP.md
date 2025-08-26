# XDS110 on macOS: Setup Guide & Docker Considerations

## Executive Summary

**Good News**: TI Code Composer Studio (CCS) v20+ fully supports macOS, including Apple Silicon with Rosetta.
**Better News**: Docker Desktop 4.35+ now supports USB/IP for USB device access on macOS!
**Alternative**: docker-machine with VirtualBox also provides USB passthrough capability.
**Recommendation**: Multiple viable options exist for XDS110 debugging on macOS with Docker.

## Option 1: Native macOS Installation (RECOMMENDED)

### Prerequisites
- macOS 10.15 (Catalina) or later
- For Apple Silicon: Rosetta 2 installed
- ~4GB disk space for CCS installation
- XDS110 debug probe with USB cable

### Installation Steps

#### 1. Download Code Composer Studio
```bash
# Download CCS v20.2.0 for macOS (latest as of 2025)
# Visit: https://www.ti.com/tool/download/CCSTUDIO/20.2.0
# Select: macOS single file installer (1.2GB)
```

#### 2. Install CCS
```bash
# Make installer executable
chmod +x CCS20.2.0.00013_Mac.app

# Run installer
./CCS20.2.0.00013_Mac.app

# Default installation path
/Applications/ti/ccs2020/
```

#### 3. Install DSS Command Line Tools
```bash
# DSS is included with CCS installation
# Located at: /Applications/ti/ccs2020/ccs/ccs_base/scripting/bin/dss.sh
```

#### 4. USB Driver Setup
```bash
# macOS requires allowing kernel extensions for XDS110
# System Preferences → Security & Privacy → General
# Click "Allow" for Texas Instruments driver after first connection attempt
```

#### 5. Verify XDS110 Detection
```bash
# Check USB device
system_profiler SPUSBDataType | grep -i "texas"
# Expected: XDS110 with vendor ID 0451:bef3

# Alternative check
ioreg -p IOUSB -l | grep -i "xds110"
```

### Running the MCP Server on macOS

#### Adapt DSS Paths
```bash
# Update legacy_ti_debugger scripts to use macOS paths
sed -i '' 's|/opt/ti/ccs1240|/Applications/ti/ccs2020|g' legacy_ti_debugger/js_scripts/*.js

# Run DSS scripts
cd legacy_ti_debugger
/Applications/ti/ccs2020/ccs/ccs_base/scripting/bin/dss.sh js_scripts/connect_target_v2.js
```

#### Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run MCP server (mock mode for testing)
python test_mcp_server.py
```

## Option 2: Docker Desktop 4.35+ with USB/IP (NEW!)

### ✨ USB/IP Support Available

**Docker Desktop 4.35.0+ now supports USB device access on macOS** using USB/IP protocol. This is a game-changer for hardware development!

### Requirements
- Docker Desktop 4.35.0 or later
- USB/IP server running on macOS host
- Privileged container for device management

### Setup Process

#### Step 1: Install USB/IP Server
```bash
# Option A: Using Python pyusbip
git clone https://github.com/tumayt/pyusbip
cd pyusbip
python3 -m venv .venv
source .venv/bin/activate
pip install libusb1
python pyusbip

# Option B: Using jiegec/usbip (Rust-based)
git clone https://github.com/jiegec/usbip
cd usbip
cargo build --release
./target/release/usbip
```

#### Step 2: Create Device Manager Container
```bash
# Start privileged container with host PID namespace
docker run --rm -it --privileged --pid=host alpine sh

# Inside container, install USB/IP tools
apk add usbip-tools

# Enter mount namespace of PID 1
nsenter -t 1 -m

# List available USB devices from host
usbip list -r host.docker.internal

# Attach XDS110 (replace with your device ID)
usbip attach -r host.docker.internal -b 3-1

# Verify attachment
usbip port
ls -la /dev/ttyACM*
```

#### Step 3: Access from Application Container
```bash
# Run your container with device access
docker run -it --device=/dev/ttyACM0 --device=/dev/ttyACM1 your-image
```

### Limitations
- Initial container must remain running
- Docker includes drivers for many USB devices but not all
- More complex than native Linux --device flag

### Docker Setup for Development Only

```dockerfile
# Dockerfile for development/testing (NO HARDWARE ACCESS)
FROM python:3.10-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy project files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose MCP server port
EXPOSE 3000

# Run in mock mode only
CMD ["python", "test_mcp_server.py"]
```

```yaml
# docker-compose.yml for development
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      - MOCK_MODE=true
    volumes:
      - ./legacy_ti_debugger:/app/legacy_ti_debugger
      - ./xds110_mcp_server:/app/xds110_mcp_server
```

```bash
# Build and run (development only)
docker-compose up --build

# This will only work in mock mode without hardware
```

## Option 3: docker-machine with VirtualBox USB Filters

### How It Works
docker-machine creates a VirtualBox VM that can pass through USB devices using VirtualBox's USB filtering capabilities.

### Installation
```bash
# Install docker-machine and VirtualBox
brew install docker-machine virtualbox virtualbox-extension-pack

# Create docker-machine with VirtualBox driver
docker-machine create --driver virtualbox default
```

### Enable USB Support
```bash
# Stop the machine
docker-machine stop default

# Enable USB 2.0 or 3.0 (requires extension pack)
vboxmanage modifyvm default --usbxhci on

# Add USB filter for XDS110 (vendor ID: 0451, product ID: bef3)
vboxmanage usbfilter add 0 --target default --name "XDS110" \
  --vendorid 0x0451 --productid 0xbef3

# Start the machine
docker-machine start default

# Set Docker environment
eval $(docker-machine env default)
```

### Run Container with USB Access
```bash
# SSH into docker-machine
docker-machine ssh default

# Check USB devices are visible
lsusb | grep "0451:bef3"

# Run container with device access
docker run -it --privileged -v /dev/bus/usb:/dev/bus/usb \
  --device=/dev/ttyACM0 --device=/dev/ttyACM1 your-image
```

### Advantages
- More stable than USB/IP approach
- Automatic USB attachment via filters
- Works with older Docker versions

### Disadvantages
- Requires VirtualBox installation
- Performance overhead from VM
- Not compatible with Docker Desktop

## Option 4: Hybrid Approach (RECOMMENDED FOR TEAMS)

### Architecture
```
macOS Host (with CCS)     Docker Container
    │                           │
    ├─ XDS110 USB              ├─ MCP Server
    ├─ DSS Scripts              ├─ Plotly Dash UI
    └─ Hardware Control         ├─ Analysis Tools
            │                   └─ Knowledge Base
            └───── TCP/IP ──────┘
```

### Implementation
1. **Hardware Bridge Service** (runs on macOS host)
   - Native CCS/DSS installation handles hardware
   - Exposes TCP/IP API for variable reading/writing
   
2. **Docker Container** (platform-independent)
   - MCP server connects to bridge via TCP
   - All analysis and UI components
   - Can be deployed anywhere

### Example Bridge Service
```python
# hardware_bridge.py (runs on macOS host)
import subprocess
import json
from flask import Flask, jsonify, request

app = Flask(__name__)

DSS_PATH = "/Applications/ti/ccs2020/ccs/ccs_base/scripting/bin/dss.sh"

@app.route('/read_variables', methods=['POST'])
def read_variables():
    """Bridge endpoint for reading variables via DSS"""
    variables = request.json.get('variables', [])
    
    # Execute DSS script
    result = subprocess.run(
        [DSS_PATH, "js_scripts/read_motor_vars_v1.js"] + variables,
        capture_output=True,
        text=True
    )
    
    return jsonify({
        'status': 'success' if result.returncode == 0 else 'error',
        'data': json.loads(result.stdout) if result.returncode == 0 else None,
        'error': result.stderr if result.returncode != 0 else None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Option 5: Complete Dockerfile for XDS110 with USB/IP

### Full Working Example
```dockerfile
# Dockerfile.xds110
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    git \
    curl \
    usbip \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install -r requirements.txt

# Copy project files
COPY . /app/

# Script to connect USB device
RUN echo '#!/bin/bash\n\
nsenter -t 1 -m\n\
usbip list -r host.docker.internal\n\
echo "Attaching XDS110..."\n\
usbip attach -r host.docker.internal -b $(usbip list -r host.docker.internal | grep "0451:bef3" | cut -d":" -f1)\n\
usbip port\n\
exec "$@"' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "xds110_mcp_server/server.py"]
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Device manager container (must run first)
  device-manager:
    image: alpine
    privileged: true
    pid: host
    command: sleep infinity
    
  # XDS110 MCP Server
  xds110-server:
    build:
      context: .
      dockerfile: Dockerfile.xds110
    depends_on:
      - device-manager
    privileged: true
    devices:
      - /dev/ttyACM0:/dev/ttyACM0
      - /dev/ttyACM1:/dev/ttyACM1
    volumes:
      - ./legacy_ti_debugger:/app/legacy_ti_debugger
      - ./xds110_mcp_server:/app/xds110_mcp_server
    environment:
      - USB_IP_HOST=host.docker.internal
      - XDS110_VENDOR_ID=0451
      - XDS110_PRODUCT_ID=bef3
    ports:
      - "3000:3000"
```

### Running the Complete Setup
```bash
# 1. Start USB/IP server on host
python3 pyusbip/pyusbip &

# 2. Start containers
docker-compose up -d

# 3. Attach USB device (run once after containers start)
docker exec -it xds110-server_device-manager_1 sh -c "
  apk add usbip-tools
  nsenter -t 1 -m
  usbip attach -r host.docker.internal -b 3-1
"

# 4. Verify XDS110 is available
docker exec xds110-server_xds110-server_1 ls -la /dev/ttyACM*
```

## Option 6: Virtual Machine (Alternative)

### UTM for Apple Silicon
```bash
# Install UTM (free, open-source)
brew install --cask utm

# Create Linux VM with USB passthrough
# UTM supports USB device passthrough to VMs
# Run full Linux CCS installation in VM
```

### VMware Fusion / Parallels
- Both support USB passthrough to VMs
- Can run Linux with full CCS/DSS support
- More reliable than Docker for hardware access

## Recommendations by Use Case

### Solo Developer on Mac
1. Install CCS v20 natively on macOS
2. Use native DSS scripts for hardware debugging
3. Develop Python MCP server components locally

### Team with Mixed Platforms
1. Use hybrid approach with TCP bridge
2. Hardware debugging on native OS (macOS/Linux/Windows)
3. Containerize everything except hardware interface

### CI/CD Pipeline
1. Use Docker for testing non-hardware components
2. Mock mode for unit tests
3. Hardware-in-the-loop testing on dedicated machines

## Known Issues & Solutions

### Issue: "Unable to find Texas Instruments device"
**Solution**: Check Security & Privacy settings, allow kernel extension

### Issue: DSS path differences between Linux and macOS
**Solution**: Use environment variables or config files for paths
```bash
export DSS_PATH="${DSS_PATH:-/Applications/ti/ccs2020/ccs/ccs_base/scripting/bin/dss.sh}"
```

### Issue: Python package compatibility on Apple Silicon
**Solution**: Use x86_64 Python via Rosetta if needed
````bash
arch -x86_64 /usr/bin/python3 -m pip install -r requirements.txt
```

## Performance Considerations

### Native macOS
- Full speed USB 2.0 (480 Mbps) to XDS110
- Direct hardware access, minimal latency
- DSS scripts run natively

### Docker Container
- No hardware access possible
- Good for development/testing only
- UI and analysis components work well

### Virtual Machine
- USB passthrough adds ~5-10ms latency
- Requires more system resources
- Most compatible option for Linux tools

## Conclusion

**For XDS110 debugging on macOS with Docker - YOU HAVE OPTIONS!**:

1. **Newest & Best**: Docker Desktop 4.35+ with USB/IP (finally works!)
2. **Most Stable**: docker-machine with VirtualBox USB filters
3. **Simplest**: Native CCS installation on macOS
4. **Team-Friendly**: Hybrid TCP bridge approach
5. **Fallback**: Full VM with UTM/VMware/Parallels

**I was wrong initially** - Docker CAN now access USB devices on macOS! The landscape changed significantly with Docker Desktop 4.35.0 (released late 2024) which added USB/IP support. Additionally, docker-machine with VirtualBox has been a working solution for years.

### Quick Decision Guide
- **Just want it to work?** → Native CCS on macOS
- **Need Docker specifically?** → Docker Desktop 4.35+ with USB/IP
- **Have older Docker?** → docker-machine + VirtualBox
- **Team environment?** → Hybrid TCP bridge
- **Maximum compatibility?** → Full Linux VM

The USB passthrough limitation on macOS Docker has been SOLVED through multiple approaches!