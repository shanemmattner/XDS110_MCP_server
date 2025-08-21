"""Variable monitoring tools for MCP server."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..gdb_interface.gdb_client import GDBClient
from ..knowledge.motor_control import MotorControlKnowledge


@dataclass
class VariableReading:
    """Single variable reading."""
    timestamp: datetime
    value: Any
    changed: bool = False


class VariableMonitorTool:
    """Tool for reading and monitoring motor control variables."""
    
    def __init__(self, gdb_client: GDBClient, knowledge: Optional[MotorControlKnowledge] = None):
        """Initialize variable monitor.
        
        Args:
            gdb_client: GDB client for communication
            knowledge: Domain knowledge database
        """
        self.gdb_client = gdb_client
        self.knowledge = knowledge or MotorControlKnowledge()
        self.logger = logging.getLogger(__name__)
        self.last_readings: Dict[str, Any] = {}
    
    async def read_variables(self, variables: List[str], format: str = "json") -> str:
        """Read current values of specified variables.
        
        Args:
            variables: List of variable names to read
            format: Output format ("json" or "table")
            
        Returns:
            Formatted variable readings
        """
        try:
            self.logger.info(f"Reading {len(variables)} variables")
            
            # Read all variables
            readings = await self.gdb_client.read_multiple_variables(variables)
            
            # Add metadata
            result = {
                "timestamp": datetime.now().isoformat(),
                "variables_read": len(variables),
                "successful_reads": len([v for v in readings.values() if v is not None]),
                "readings": {}
            }
            
            # Process each reading
            for var_name, value in readings.items():
                if value is not None:
                    # Get variable info from knowledge base
                    var_info = self.knowledge.get_variable_info(var_name)
                    
                    result["readings"][var_name] = {
                        "value": value,
                        "type": var_info.get("type", "unknown"),
                        "description": var_info.get("description", ""),
                        "units": var_info.get("units", "")
                    }
                    
                    # Add enum interpretation if available
                    if "enum_values" in var_info and isinstance(value, (int, float)):
                        enum_name = var_info["enum_values"].get(str(int(value)))
                        if enum_name:
                            result["readings"][var_name]["enum_value"] = enum_name
                else:
                    result["readings"][var_name] = {
                        "error": "Failed to read variable"
                    }
            
            if format == "table":
                return self._format_as_table(result["readings"])
            else:
                return json.dumps(result, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error reading variables: {e}")
            return json.dumps({"error": str(e)})
    
    async def monitor_variables(self, variables: List[str], duration: float = 10.0, 
                               threshold: float = 0.01) -> str:
        """Monitor variables with change detection.
        
        Args:
            variables: Variables to monitor
            duration: Monitoring duration in seconds
            threshold: Change detection threshold
            
        Returns:
            Monitoring results with detected changes
        """
        try:
            self.logger.info(f"Starting {duration}s monitoring of {len(variables)} variables")
            
            monitoring_data = []
            start_time = datetime.now()
            
            # Calculate monitoring frequency (5Hz default, max 10Hz)
            frequency = min(10.0, max(1.0, 50.0 / len(variables)))  # Adaptive frequency
            interval = 1.0 / frequency
            
            # Initial reading
            previous_readings = await self.gdb_client.read_multiple_variables(variables)
            
            elapsed = 0.0
            cycle = 0
            
            while elapsed < duration:
                cycle_start = datetime.now()
                
                # Read current values
                current_readings = await self.gdb_client.read_multiple_variables(variables)
                
                # Detect changes
                changes_detected = []
                for var_name in variables:
                    prev_val = previous_readings.get(var_name)
                    curr_val = current_readings.get(var_name)
                    
                    if prev_val is not None and curr_val is not None:
                        if self._value_changed(prev_val, curr_val, threshold):
                            changes_detected.append({
                                "variable": var_name,
                                "previous_value": prev_val,
                                "current_value": curr_val,
                                "change_magnitude": abs(float(curr_val) - float(prev_val)) if isinstance(curr_val, (int, float)) else 1
                            })
                
                # Record this cycle's data
                cycle_data = {
                    "cycle": cycle,
                    "timestamp": cycle_start.isoformat(),
                    "elapsed_seconds": elapsed,
                    "readings": current_readings,
                    "changes_detected": changes_detected
                }
                monitoring_data.append(cycle_data)
                
                # Log significant changes
                if changes_detected:
                    self.logger.info(f"Cycle {cycle}: {len(changes_detected)} changes detected")
                    for change in changes_detected:
                        var_info = self.knowledge.get_variable_info(change["variable"])
                        self.logger.info(f"  {change['variable']}: {change['previous_value']} → {change['current_value']} {var_info.get('units', '')}")
                
                previous_readings = current_readings
                cycle += 1
                
                # Wait for next cycle
                cycle_time = (datetime.now() - cycle_start).total_seconds()
                sleep_time = max(0, interval - cycle_time)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                elapsed = (datetime.now() - start_time).total_seconds()
            
            # Generate summary
            total_changes = sum(len(cycle["changes_detected"]) for cycle in monitoring_data)
            variables_with_changes = set()
            for cycle in monitoring_data:
                for change in cycle["changes_detected"]:
                    variables_with_changes.add(change["variable"])
            
            result = {
                "monitoring_summary": {
                    "duration_seconds": elapsed,
                    "cycles_completed": len(monitoring_data),
                    "frequency_hz": len(monitoring_data) / elapsed,
                    "variables_monitored": len(variables),
                    "total_changes_detected": total_changes,
                    "variables_with_changes": len(variables_with_changes),
                    "change_threshold": threshold
                },
                "variables_with_activity": list(variables_with_changes),
                "detailed_data": monitoring_data
            }
            
            self.logger.info(f"Monitoring complete: {total_changes} changes in {len(variables_with_changes)} variables")
            return json.dumps(result, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error during variable monitoring: {e}")
            return json.dumps({"error": str(e)})
    
    def _value_changed(self, prev_value: Any, curr_value: Any, threshold: float) -> bool:
        """Check if a value has changed significantly.
        
        Args:
            prev_value: Previous value
            curr_value: Current value  
            threshold: Change threshold
            
        Returns:
            True if value changed significantly
        """
        try:
            # Exact comparison for non-numeric types
            if not isinstance(prev_value, (int, float)) or not isinstance(curr_value, (int, float)):
                return prev_value != curr_value
            
            # Threshold comparison for numeric types
            if prev_value == 0:
                return abs(curr_value) > threshold
            
            relative_change = abs(curr_value - prev_value) / abs(prev_value)
            return relative_change > threshold
            
        except:
            # Fall back to exact comparison
            return prev_value != curr_value
    
    
    def _format_as_table(self, readings: Dict[str, Any]) -> str:
        """Format readings as a text table.
        
        Args:
            readings: Variable readings dictionary
            
        Returns:
            Formatted table string
        """
        try:
            lines = ["Variable Readings:", "=" * 50]
            
            for var_name, data in readings.items():
                if "error" in data:
                    lines.append(f"{var_name}: ERROR - {data['error']}")
                else:
                    value = data["value"]
                    units = data.get("units", "")
                    enum_val = data.get("enum_value", "")
                    
                    value_str = f"{value}"
                    if units:
                        value_str += f" {units}"
                    if enum_val:
                        value_str += f" ({enum_val})"
                    
                    lines.append(f"{var_name}: {value_str}")
                    if data.get("description"):
                        lines.append(f"  Description: {data['description']}")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error formatting table: {e}"