#!/usr/bin/env python3
"""
XDS110 Dash Connector - Direct integration between Plotly Dash and XDS110 hardware
Connects to TI DSS for real hardware debugging with web UI
"""

import subprocess
import json
import time
import threading
import queue
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from collections import deque
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XDS110Interface:
    """Direct interface to XDS110 hardware via TI DSS"""
    
    def __init__(self, ccs_path: str = "/opt/ti/ccs1240/ccs"):
        self.ccs_path = Path(ccs_path)
        self.dss_path = self.ccs_path / "ccs_base" / "scripting" / "bin" / "dss.sh"
        
        if not self.dss_path.exists():
            raise FileNotFoundError(f"DSS not found at {self.dss_path}")
        
        self.connected = False
        self.session = None
        self.map_symbols = {}  # Symbol table from MAP file
        self.data_queue = queue.Queue()
        self.monitor_thread = None
        self.monitoring = False
        
    def load_map_file(self, map_file_path: str) -> Dict:
        """Parse MAP file to get symbol addresses"""
        symbols = {}
        
        try:
            with open(map_file_path, 'r') as f:
                content = f.read()
                
            # Look for GLOBAL SYMBOLS section - TI format has "page address name"
            import re
            # Match format: page_num  hex_address  symbol_name
            symbol_pattern = re.compile(r'^\s*\d+\s+([0-9a-f]+)\s+(\w+)', re.MULTILINE | re.IGNORECASE)
            
            for match in symbol_pattern.finditer(content):
                address_str, name = match.groups()
                address = int(address_str, 16)
                symbols[name] = address
                
            logger.info(f"Loaded {len(symbols)} symbols from MAP file")
            self.map_symbols = symbols
            
        except Exception as e:
            logger.error(f"Failed to parse MAP file: {e}")
            
        return symbols
    
    def connect(self, ccxml_path: str, binary_path: Optional[str] = None) -> bool:
        """Connect to target using CCXML configuration"""
        
        # Create JavaScript for DSS to connect
        js_script = f"""
// Auto-generated DSS connection script
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

// Get the Debug Server using ScriptingEnvironment.instance()
var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");

// Configure target
ds.setConfig("{ccxml_path}");

// Open a debug session for C28x CPU1 specifically
var debugSession = ds.openSession(".*C28xx_CPU1");

// Connect to target
debugSession.target.connect();

// Load binary if provided
{"debugSession.memory.loadProgram('" + binary_path + "');" if binary_path else ""}

// Run target briefly to initialize
debugSession.target.runAsynch();
Thread.sleep(1000);
debugSession.target.halt();

print("CONNECTED:SUCCESS");
"""
        
        # Save script temporarily
        script_path = Path("/tmp/connect_xds110.js")
        script_path.write_text(js_script)
        
        try:
            # Execute DSS script
            result = subprocess.run(
                [str(self.dss_path), str(script_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "CONNECTED:SUCCESS" in result.stdout:
                self.connected = True
                logger.info("Successfully connected to XDS110")
                return True
            else:
                logger.error(f"Connection failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Connection timeout")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def read_variable(self, variable_name: str) -> Optional[float]:
        """Read a single variable from target"""
        if not self.connected:
            logger.error("Not connected to target")
            return None
        
        # Check if we have the symbol
        address = self.map_symbols.get(variable_name)
        if address is None:
            logger.warning(f"Variable {variable_name} not found in MAP file")
            return None
        
        # Create JavaScript to read variable
        js_script = f"""
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);

var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
var debugSession = ds.openSession(".*C28xx_CPU1");

// Read from address
var value = debugSession.memory.readData(0, 0x{address:08X}, 32);
print("VALUE:" + value);
"""
        
        script_path = Path(f"/tmp/read_{variable_name}.js")
        script_path.write_text(js_script)
        
        try:
            result = subprocess.run(
                [str(self.dss_path), str(script_path)],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Parse value from output
            for line in result.stdout.split('\n'):
                if line.startswith("VALUE:"):
                    value_str = line.replace("VALUE:", "").strip()
                    try:
                        return float(value_str)
                    except ValueError:
                        return None
                        
        except Exception as e:
            logger.error(f"Read error for {variable_name}: {e}")
            
        return None
    
    def read_multiple(self, variable_names: List[str]) -> Dict[str, Any]:
        """Read multiple variables in one DSS call (more efficient)"""
        if not self.connected:
            return {}
        
        results = {}
        
        # Build JavaScript to read all variables at once
        js_lines = [
            "importPackage(Packages.com.ti.debug.engine.scripting);",
            "importPackage(Packages.com.ti.ccstudio.scripting.environment);",
            "",
            "var ds = ScriptingEnvironment.instance().getServer('DebugServer.1');",
            "var debugSession = ds.openSession('.*');",
            ""
        ]
        
        for var_name in variable_names:
            address = self.map_symbols.get(var_name)
            if address:
                js_lines.append(f"var val_{var_name} = debugSession.memory.readData(0, 0x{address:08X}, 32);")
                js_lines.append(f"print('VAR:{var_name}=' + val_{var_name});")
        
        js_script = '\n'.join(js_lines)
        script_path = Path("/tmp/read_multiple.js")
        script_path.write_text(js_script)
        
        try:
            result = subprocess.run(
                [str(self.dss_path), str(script_path)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Parse all values
            for line in result.stdout.split('\n'):
                if line.startswith("VAR:"):
                    parts = line[4:].split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0]
                        try:
                            value = float(parts[1])
                            results[var_name] = value
                        except ValueError:
                            pass
                            
        except Exception as e:
            logger.error(f"Batch read error: {e}")
            
        return results
    
    def start_monitoring(self, variables: List[str], interval: float = 0.1):
        """Start monitoring variables in background thread"""
        if self.monitoring:
            logger.warning("Already monitoring")
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    # Read all variables
                    values = self.read_multiple(variables)
                    
                    if values:
                        # Add timestamp and push to queue
                        values['timestamp'] = datetime.now().timestamp()
                        self.data_queue.put(values)
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                    time.sleep(1)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Started monitoring {len(variables)} variables at {1/interval:.1f} Hz")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Stopped monitoring")
    
    def get_latest_data(self) -> Optional[Dict]:
        """Get latest data from queue (non-blocking)"""
        try:
            # Get all available data and return the most recent
            latest = None
            while not self.data_queue.empty():
                latest = self.data_queue.get_nowait()
            return latest
        except queue.Empty:
            return None
    
    def write_variable(self, variable_name: str, value: float) -> bool:
        """Write value to variable"""
        if not self.connected:
            return False
        
        address = self.map_symbols.get(variable_name)
        if address is None:
            logger.warning(f"Variable {variable_name} not found")
            return False
        
        # Create write script
        js_script = f"""
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);

var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
var debugSession = ds.openSession(".*C28xx_CPU1");

// Write value
debugSession.memory.writeData(0, 0x{address:08X}, {int(value)}, 32);
print("WRITE:SUCCESS");
"""
        
        script_path = Path(f"/tmp/write_{variable_name}.js")
        script_path.write_text(js_script)
        
        try:
            result = subprocess.run(
                [str(self.dss_path), str(script_path)],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            return "WRITE:SUCCESS" in result.stdout
            
        except Exception as e:
            logger.error(f"Write error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from target"""
        self.stop_monitoring()
        
        if self.connected:
            # Create disconnect script
            js_script = """
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);

var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
var debugSession = ds.openSession(".*C28xx_CPU1");

debugSession.target.disconnect();
"""
            
            script_path = Path("/tmp/disconnect_xds110.js")
            script_path.write_text(js_script)
            
            try:
                subprocess.run(
                    [str(self.dss_path), str(script_path)],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            
            self.connected = False
            logger.info("Disconnected from XDS110")


class DashDataBridge:
    """Bridge between XDS110 and Dash dashboard"""
    
    def __init__(self, xds110: XDS110Interface, max_history: int = 1000):
        self.xds110 = xds110
        self.max_history = max_history
        self.data_history = {}  # {variable: deque of (timestamp, value)}
        self.update_thread = None
        self.running = False
        
    def initialize_variables(self, variables: List[str]):
        """Initialize history storage for variables"""
        for var in variables:
            if var not in self.data_history:
                self.data_history[var] = deque(maxlen=self.max_history)
    
    def start_update_loop(self, variables: List[str], interval: float = 0.1):
        """Start updating data for dashboard"""
        if self.running:
            return
        
        self.running = True
        self.initialize_variables(variables)
        
        # Start XDS110 monitoring
        self.xds110.start_monitoring(variables, interval)
        
        def update_loop():
            while self.running:
                # Get latest data from XDS110
                data = self.xds110.get_latest_data()
                
                if data:
                    timestamp = data.get('timestamp', time.time())
                    
                    # Update history for each variable
                    for var in variables:
                        if var in data:
                            self.data_history[var].append((timestamp, data[var]))
                
                time.sleep(interval / 2)  # Check twice as fast as update rate
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        logger.info(f"Started dashboard update loop")
    
    def stop_update_loop(self):
        """Stop update loop"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=2)
        self.xds110.stop_monitoring()
    
    def get_current_values(self) -> Dict[str, float]:
        """Get current value for all variables"""
        values = {}
        for var, history in self.data_history.items():
            if history:
                values[var] = history[-1][1]  # Latest value
        return values
    
    def get_history(self, variable: str, duration_sec: Optional[int] = None) -> tuple:
        """Get historical data for variable"""
        if variable not in self.data_history:
            return [], []
        
        history = list(self.data_history[variable])
        
        if duration_sec and history:
            cutoff = time.time() - duration_sec
            history = [(t, v) for t, v in history if t >= cutoff]
        
        if history:
            timestamps, values = zip(*history)
            return list(timestamps), list(values)
        
        return [], []
    
    def clear_history(self, variable: Optional[str] = None):
        """Clear history for variable or all variables"""
        if variable:
            if variable in self.data_history:
                self.data_history[variable].clear()
        else:
            for var_history in self.data_history.values():
                var_history.clear()


# Global instance for use in Dash callbacks
xds110 = None
dash_bridge = None

def initialize_hardware(ccxml_path: str, map_file: str, binary_path: Optional[str] = None):
    """Initialize XDS110 hardware connection"""
    global xds110, dash_bridge
    
    try:
        # Create XDS110 interface
        xds110 = XDS110Interface()
        
        # Load MAP file
        symbols = xds110.load_map_file(map_file)
        logger.info(f"Loaded {len(symbols)} symbols")
        
        # Connect to hardware
        if xds110.connect(ccxml_path, binary_path):
            # Create bridge for Dash
            dash_bridge = DashDataBridge(xds110)
            logger.info("Hardware initialized successfully")
            return True
        else:
            logger.error("Failed to connect to hardware")
            return False
            
    except Exception as e:
        logger.error(f"Hardware initialization failed: {e}")
        return False

def get_available_variables() -> List[str]:
    """Get list of available variables from MAP file"""
    if xds110:
        return list(xds110.map_symbols.keys())
    return []

def start_monitoring(variables: List[str], rate_hz: float = 10):
    """Start monitoring selected variables"""
    if dash_bridge:
        interval = 1.0 / rate_hz
        dash_bridge.start_update_loop(variables, interval)
        return True
    return False

def stop_monitoring():
    """Stop monitoring"""
    if dash_bridge:
        dash_bridge.stop_update_loop()

def get_current_data() -> Dict[str, float]:
    """Get current values for dashboard display"""
    if dash_bridge:
        return dash_bridge.get_current_values()
    return {}

def get_variable_history(variable: str, duration: Optional[int] = None) -> tuple:
    """Get historical data for plotting"""
    if dash_bridge:
        return dash_bridge.get_history(variable, duration)
    return [], []

def write_value(variable: str, value: float) -> bool:
    """Write value to target"""
    if xds110:
        return xds110.write_variable(variable, value)
    return False

def disconnect():
    """Disconnect from hardware"""
    if xds110:
        xds110.disconnect()