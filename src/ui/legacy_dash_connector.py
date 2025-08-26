#!/usr/bin/env python3
"""
Legacy Dashboard Connector - Uses the working legacy loop connector with dashboard interface
Provides the same interface as the original dashboard connector but uses proven legacy scripts internally
"""

import time
import threading
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import deque
from datetime import datetime

# Import our working legacy loop connector
from legacy_loop_connector import LegacyLoopConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegacyDashConnector:
    """
    Dashboard connector that uses the proven legacy loop approach
    Provides dashboard-compatible interface while using working legacy DSS scripts
    """
    
    def __init__(self, max_history: int = 1000):
        self.legacy_connector = None
        self.connected = False
        self.max_history = max_history
        
        # Data management for dashboard (separate from legacy connector's internal storage)
        self.data_history = {}  # {variable: deque of (timestamp, value)}
        self.current_values = {}  # {variable: latest_value}
        self.monitored_variables = []
        
        # Monitoring thread (our own, separate from legacy connector's)
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_rate = 2.0  # Hz - reasonable rate for legacy scripts
        
        logger.info("LegacyDashConnector initialized")
    
    def initialize_hardware(self, ccxml_path: str, map_file: str, binary_path: Optional[str] = None) -> bool:
        """Initialize hardware using legacy loop connector"""
        try:
            logger.info("Initializing hardware with legacy dashboard connector...")
            
            # Create LegacyLoopConnector instance (our proven working solution)
            self.legacy_connector = LegacyLoopConnector(ccxml_path, map_file, binary_path)
            
            # Test connection by running one cycle
            available_vars = self.get_available_variables()
            if not available_vars:
                logger.error("No variables found - initialization failed")
                return False
            
            # Test with simple motor variables that we know work
            test_vars = ['motorVars_M1.motorState']
            logger.info(f"Testing connection with: {test_vars}")
            
            test_results = self.legacy_connector.run_monitoring_cycle(test_vars)
            if test_results and any(v is not None for v in test_results.values()):
                logger.info(f"✅ Connection test successful - read {len(test_results)} variables")
                self.connected = True
                return True
            else:
                logger.error("❌ Connection test failed - could not read variables")
                return False
                
        except Exception as e:
            logger.error(f"Hardware initialization failed: {e}")
            return False
    
    def get_available_variables(self) -> List[str]:
        """Get list of available variables from MAP file"""
        if self.legacy_connector:
            return self.legacy_connector.get_available_variables()
        return []
    
    def start_monitoring(self, variables: List[str], rate_hz: float = 2.0) -> bool:
        """Start monitoring selected variables using legacy script cycles"""
        if not self.connected or not self.legacy_connector:
            logger.error("Cannot start monitoring - not connected")
            return False
        
        if self.monitoring:
            logger.warning("Already monitoring - stopping previous session")
            self.stop_monitoring()
        
        # Validate variables (handle structured names like motorVars_M1.motorState)
        valid_variables = []
        for var in variables:
            base_var = var.split('.')[0]
            available = self.legacy_connector.get_available_variables()
            if base_var in available:
                valid_variables.append(var)
        
        if not valid_variables:
            logger.error("No valid variables to monitor")
            return False
        
        # Initialize history storage
        for var in valid_variables:
            if var not in self.data_history:
                self.data_history[var] = deque(maxlen=self.max_history)
        
        self.monitored_variables = valid_variables
        self.monitor_rate = min(rate_hz, 2.0)  # Cap at 2Hz for legacy script reliability
        self.monitoring = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"✅ Started legacy dashboard monitoring: {len(valid_variables)} variables at {self.monitor_rate:.1f} Hz")
        return True
    
    def _monitor_loop(self):
        """Background monitoring loop using legacy script cycles"""
        interval = 1.0 / self.monitor_rate
        
        logger.info(f"Legacy dashboard monitor loop starting (interval: {interval:.2f}s)")
        
        cycle_count = 0
        while self.monitoring:
            try:
                start_time = time.time()
                cycle_count += 1
                
                # Use legacy connector to run one monitoring cycle
                results = self.legacy_connector.run_monitoring_cycle(self.monitored_variables)
                
                if results:
                    timestamp = datetime.now().timestamp()
                    
                    # Update current values and history
                    success_count = 0
                    for var_name, value in results.items():
                        if value is not None:
                            self.current_values[var_name] = value
                            
                            # Add to history
                            if var_name in self.data_history:
                                self.data_history[var_name].append((timestamp, value))
                            success_count += 1
                    
                    if success_count > 0:
                        logger.debug(f"Dashboard cycle {cycle_count}: {success_count}/{len(self.monitored_variables)} variables updated")
                    else:
                        logger.warning(f"Dashboard cycle {cycle_count}: No variables updated")
                else:
                    logger.warning(f"Dashboard cycle {cycle_count}: No data from legacy connector")
                
                # Maintain target rate
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Dashboard monitor loop cycle {cycle_count} error: {e}")
                time.sleep(2)  # Error recovery delay
        
        logger.info(f"Legacy dashboard monitor loop stopped after {cycle_count} cycles")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
                if self.monitor_thread.is_alive():
                    logger.warning("Dashboard monitor thread did not stop cleanly")
            logger.info("Legacy dashboard monitoring stopped")
    
    def get_current_data(self) -> Dict[str, float]:
        """Get current values for dashboard display"""
        return dict(self.current_values)  # Return copy
    
    def get_variable_history(self, variable: str, duration: Optional[int] = None) -> tuple:
        """Get historical data for plotting"""
        if variable not in self.data_history:
            return [], []
        
        history = list(self.data_history[variable])
        
        # Filter by duration if specified
        if duration and history:
            cutoff = time.time() - duration
            history = [(t, v) for t, v in history if t >= cutoff]
        
        if history:
            timestamps, values = zip(*history)
            return list(timestamps), list(values)
        
        return [], []
    
    def write_value(self, variable: str, value: float) -> bool:
        """Write value to target (not implemented yet)"""
        logger.warning("Write functionality not yet implemented in legacy dash connector")
        return False
    
    def disconnect(self):
        """Disconnect from hardware"""
        logger.info("Disconnecting legacy dashboard connector...")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Disconnect legacy connector
        if self.legacy_connector:
            self.legacy_connector.disconnect()
        
        # Clear data
        self.current_values.clear()
        self.data_history.clear()
        self.monitored_variables.clear()
        
        # Reset connection state
        self.connected = False
        self.legacy_connector = None
        
        logger.info("Legacy dashboard connector disconnected")


# Global instances for dashboard compatibility
legacy_dash_connector = None

def initialize_hardware(ccxml_path: str, map_file: str, binary_path: Optional[str] = None) -> bool:
    """Initialize XDS110 hardware connection (dashboard interface)"""
    global legacy_dash_connector
    
    try:
        legacy_dash_connector = LegacyDashConnector()
        
        success = legacy_dash_connector.initialize_hardware(ccxml_path, map_file, binary_path)
        
        if success:
            logger.info("✅ Legacy dashboard connection established")
        else:
            logger.error("❌ Legacy dashboard connection failed")
            legacy_dash_connector = None
        
        return success
        
    except Exception as e:
        logger.error(f"Legacy dashboard initialization failed: {e}")
        legacy_dash_connector = None
        return False

def get_available_variables() -> List[str]:
    """Get list of available variables from MAP file (dashboard interface)"""
    if legacy_dash_connector:
        return legacy_dash_connector.get_available_variables()
    return []

def start_monitoring(variables: List[str], rate_hz: float = 2.0) -> bool:
    """Start monitoring selected variables (dashboard interface)"""
    if legacy_dash_connector:
        return legacy_dash_connector.start_monitoring(variables, rate_hz)
    return False

def stop_monitoring():
    """Stop monitoring (dashboard interface)"""
    if legacy_dash_connector:
        legacy_dash_connector.stop_monitoring()

def get_current_data() -> Dict[str, float]:
    """Get current values for dashboard display (dashboard interface)"""
    if legacy_dash_connector:
        return legacy_dash_connector.get_current_data()
    return {}

def get_variable_history(variable: str, duration: Optional[int] = None) -> tuple:
    """Get historical data for plotting (dashboard interface)"""
    if legacy_dash_connector:
        return legacy_dash_connector.get_variable_history(variable, duration)
    return [], []

def write_value(variable: str, value: float) -> bool:
    """Write value to target (dashboard interface)"""
    if legacy_dash_connector:
        return legacy_dash_connector.write_value(variable, value)
    return False

def disconnect():
    """Disconnect from hardware (dashboard interface)"""
    global legacy_dash_connector
    if legacy_dash_connector:
        legacy_dash_connector.disconnect()
        legacy_dash_connector = None


# Test function
def test_legacy_dash_connector():
    """Test the legacy dashboard connector"""
    print("Testing Legacy Dashboard Connector")
    print("=================================")
    
    # File paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    map_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    # Test initialization
    print("1. Testing hardware initialization...")
    if initialize_hardware(str(ccxml_path), str(map_path), str(binary_path)):
        print("✅ Hardware initialized")
        
        # Test variable discovery
        print("2. Testing variable discovery...")
        variables = get_available_variables()
        print(f"Found {len(variables)} variables")
        
        if variables:
            # Test monitoring with proven working variables
            print("3. Testing monitoring...")
            test_vars = [
                'motorVars_M1.motorState',
                'motorVars_M1.absPosition_rad',
                'motorVars_M1.Idq_out_A.value[0]'
            ]
            
            print(f"Starting monitoring for: {test_vars}")
            if start_monitoring(test_vars, rate_hz=1.0):  # 1 Hz for testing
                print("✅ Monitoring started")
                
                # Monitor for 10 seconds
                print("4. Monitoring data for 10 seconds...")
                for i in range(10):
                    time.sleep(1)
                    current_data = get_current_data()
                    if current_data:
                        print(f"  {i+1}s: {len(current_data)} variables with data")
                        for var, value in current_data.items():
                            print(f"    {var} = {value}")
                    else:
                        print(f"  {i+1}s: No current data")
                
                # Test history
                print("5. Testing history...")
                for var in test_vars:
                    timestamps, values = get_variable_history(var, duration=10)
                    print(f"  {var}: {len(timestamps)} history points")
                
                stop_monitoring()
                print("✅ Monitoring stopped")
            else:
                print("❌ Failed to start monitoring")
        
        disconnect()
        print("✅ Disconnected")
    else:
        print("❌ Hardware initialization failed")

if __name__ == "__main__":
    test_legacy_dash_connector()