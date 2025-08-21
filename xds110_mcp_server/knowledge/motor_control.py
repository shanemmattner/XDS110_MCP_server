"""Motor control domain knowledge database.

This module contains comprehensive knowledge about motor control systems,
specifically for TI F280039C-based PMSM motor control applications.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class VariableSchema:
    """Schema for a motor control variable."""
    name: str
    type: str
    description: str
    units: str = ""
    enum_values: Optional[Dict[str, str]] = None
    valid_range: Optional[tuple] = None
    critical: bool = False


@dataclass
class FaultPattern:
    """Pattern for identifying motor control faults."""
    name: str
    description: str
    conditions: List[Dict[str, Any]]
    severity: str  # "critical", "warning", "info"
    recommendations: List[str]


class MotorControlKnowledge:
    """Domain knowledge database for motor control systems."""
    
    def __init__(self):
        """Initialize motor control knowledge database."""
        self._variable_schemas = self._build_variable_schemas()
        self._fault_patterns = self._build_fault_patterns()
        self._command_types = self._build_command_types()
        self._motor_states = self._build_motor_states()
    
    def get_variable_schema(self, variable_name: str) -> Optional[VariableSchema]:
        """Get schema for a variable.
        
        Args:
            variable_name: Variable name
            
        Returns:
            Variable schema or None if not found
        """
        return self._variable_schemas.get(variable_name)
    
    def get_all_variables(self) -> Dict[str, VariableSchema]:
        """Get all known variable schemas.
        
        Returns:
            Dictionary of variable schemas
        """
        return self._variable_schemas.copy()
    
    def get_fault_patterns(self) -> List[FaultPattern]:
        """Get all known fault patterns.
        
        Returns:
            List of fault patterns
        """
        return self._fault_patterns
    
    def get_command_description(self, cmd_value: int) -> str:
        """Get description for a command value.
        
        Args:
            cmd_value: Command value
            
        Returns:
            Command description
        """
        return self._command_types.get(cmd_value, f"Unknown command ({cmd_value})")
    
    def get_motor_state_description(self, state_value: int) -> str:
        """Get description for motor state value.
        
        Args:
            state_value: Motor state value
            
        Returns:
            State description
        """
        return self._motor_states.get(state_value, f"Unknown state ({state_value})")
    
    def _build_variable_schemas(self) -> Dict[str, VariableSchema]:
        """Build variable schemas from legacy ti_debugger knowledge."""
        schemas = {}
        
        # Motor state variables
        schemas["motorVars_M1.motorState"] = VariableSchema(
            name="motorVars_M1.motorState",
            type="uint8_t",
            description="Current motor control state",
            enum_values={
                "0": "IDLE - Motor stopped, no control active",
                "1": "ALIGNMENT - Motor performing alignment procedure", 
                "2": "CTRL_RUN - Motor control active but not closed loop",
                "3": "CL_RUNNING - Closed loop control active"
            },
            critical=True
        )
        
        # Position variables
        schemas["motorVars_M1.absPosition_rad"] = VariableSchema(
            name="motorVars_M1.absPosition_rad",
            type="float32",
            description="Absolute motor position from encoder",
            units="radians",
            valid_range=(-6.28, 6.28),
            critical=True
        )
        
        schemas["motorVars_M1.angleFOC_rad"] = VariableSchema(
            name="motorVars_M1.angleFOC_rad", 
            type="float32",
            description="Field-oriented control electrical angle",
            units="radians",
            valid_range=(0, 6.28),
            critical=True
        )
        
        schemas["motorVars_M1.angleENC_rad"] = VariableSchema(
            name="motorVars_M1.angleENC_rad",
            type="float32", 
            description="Encoder mechanical angle",
            units="radians",
            valid_range=(-6.28, 6.28),
            critical=True
        )
        
        # Current control variables
        schemas["motorVars_M1.Idq_out_A.value[0]"] = VariableSchema(
            name="motorVars_M1.Idq_out_A.value[0]",
            type="float32",
            description="D-axis current (flux current component)",
            units="A",
            valid_range=(-10.0, 10.0),
            critical=True
        )
        
        schemas["motorVars_M1.Idq_out_A.value[1]"] = VariableSchema(
            name="motorVars_M1.Idq_out_A.value[1]",
            type="float32",
            description="Q-axis current (torque current component)",
            units="A", 
            valid_range=(-10.0, 10.0),
            critical=True
        )
        
        schemas["motorVars_M1.IsRef_A"] = VariableSchema(
            name="motorVars_M1.IsRef_A",
            type="float32",
            description="Current reference magnitude",
            units="A",
            valid_range=(0.0, 10.0)
        )
        
        schemas["motorVars_M1.fluxCurrent_A"] = VariableSchema(
            name="motorVars_M1.fluxCurrent_A",
            type="float32", 
            description="Flux current setting for motor torque capability",
            units="A",
            valid_range=(0.0, 5.0),
            critical=True
        )
        
        schemas["motorVars_M1.alignCurrent_A"] = VariableSchema(
            name="motorVars_M1.alignCurrent_A",
            type="float32",
            description="Current used during motor alignment",
            units="A", 
            valid_range=(0.0, 1.0)
        )
        
        # Control flags
        schemas["motorVars_M1.enableSpeedCtrl"] = VariableSchema(
            name="motorVars_M1.enableSpeedCtrl",
            type="bool",
            description="Speed control loop enable flag",
            enum_values={"0": "Disabled", "1": "Enabled"}
        )
        
        schemas["motorVars_M1.reversePhases"] = VariableSchema(
            name="motorVars_M1.reversePhases",
            type="bool",
            description="Motor phase reversal flag",
            enum_values={"0": "Normal", "1": "Reversed"}
        )
        
        # Fault status variables
        schemas["motorVars_M1.faultMtrNow.bit.needsCalibration"] = VariableSchema(
            name="motorVars_M1.faultMtrNow.bit.needsCalibration",
            type="bool",
            description="Motor calibration required flag",
            enum_values={"0": "Calibrated", "1": "Needs Calibration"},
            critical=True
        )
        
        schemas["motorVars_M1.faultMtrNow.bit.obakeNeedsInit"] = VariableSchema(
            name="motorVars_M1.faultMtrNow.bit.obakeNeedsInit",
            type="bool", 
            description="Motor initialization required flag",
            enum_values={"0": "Initialized", "1": "Needs Initialization"},
            critical=True
        )
        
        schemas["motorVars_M1.faultMtrNow.all"] = VariableSchema(
            name="motorVars_M1.faultMtrNow.all",
            type="uint16_t",
            description="Complete fault status word",
            critical=True
        )
        
        # Debug bypass variables
        schemas["debug_bypass.debug_enabled"] = VariableSchema(
            name="debug_bypass.debug_enabled",
            type="bool",
            description="Debug bypass system enabled flag",
            enum_values={"0": "Disabled", "1": "Enabled"},
            critical=True
        )
        
        schemas["debug_bypass.bypass_alignment_called"] = VariableSchema(
            name="debug_bypass.bypass_alignment_called",
            type="bool",
            description="Bypass alignment procedure was called",
            enum_values={"0": "Not Called", "1": "Called"}
        )
        
        schemas["debug_bypass.bypass_electrical_angle"] = VariableSchema(
            name="debug_bypass.bypass_electrical_angle", 
            type="float32",
            description="Calculated electrical angle from bypass alignment",
            units="radians",
            valid_range=(0, 6.28)
        )
        
        schemas["debug_bypass.cs_gpio_pin"] = VariableSchema(
            name="debug_bypass.cs_gpio_pin",
            type="uint8_t",
            description="Chip select GPIO pin for encoder selection",
            enum_values={
                "20": "Absolute encoder (AMS AS5048A)",
                "21": "Quadrature encoder"
            }
        )
        
        return schemas
    
    def _build_fault_patterns(self) -> List[FaultPattern]:
        """Build fault pattern recognition database."""
        patterns = []
        
        # Motor humming during bypass alignment
        patterns.append(FaultPattern(
            name="motor_humming_bypass_alignment",
            description="Motor hums but doesn't spin during bypass alignment",
            conditions=[
                {"variable": "debug_bypass.bypass_alignment_called", "value": True},
                {"variable": "debug_bypass.bypass_electrical_angle", "operator": "!=", "value": 0.0},
                {"variable": "motorVars_M1.angleFOC_rad", "value": 0.0},
                {"variable": "motorVars_M1.motorState", "value": 1}
            ],
            severity="warning",
            recommendations=[
                "Initialize FOC angle with bypass electrical angle value",
                "Check if motor alignment current is appropriate (typically 0.1A)",
                "Verify encoder selection (pin 20 for absolute, pin 21 for quadrature)"
            ]
        ))
        
        # Calibration required fault
        patterns.append(FaultPattern(
            name="calibration_required", 
            description="Motor requires calibration before operation",
            conditions=[
                {"variable": "motorVars_M1.faultMtrNow.bit.needsCalibration", "value": 1}
            ],
            severity="critical",
            recommendations=[
                "Run calibration sequence (commands 64-67) before attempting motor control",
                "Ensure motor is mechanically free to move during calibration",
                "Verify encoder connections and functionality"
            ]
        ))
        
        # Initialization required fault  
        patterns.append(FaultPattern(
            name="initialization_required",
            description="Motor system requires initialization",
            conditions=[
                {"variable": "motorVars_M1.faultMtrNow.bit.obakeNeedsInit", "value": 1}
            ],
            severity="critical", 
            recommendations=[
                "Send initialization command (command 84) to clear needsInit flag",
                "Verify system startup sequence completed properly",
                "Check for hardware initialization issues"
            ]
        ))
        
        # No current command
        patterns.append(FaultPattern(
            name="no_current_command",
            description="Motor will not move - no current being commanded",
            conditions=[
                {"variable": "motorVars_M1.Idq_out_A.value[0]", "value": 0.0},
                {"variable": "motorVars_M1.Idq_out_A.value[1]", "value": 0.0},
                {"variable": "motorVars_M1.motorState", "operator": ">=", "value": 2}
            ],
            severity="warning",
            recommendations=[
                "Enable debug bypass mode (debug_bypass.debug_enabled = 1)",
                "Set appropriate command in debug_bypass.command structure",
                "Verify flux current setting (motorVars_M1.fluxCurrent_A > 0)"
            ]
        ))
        
        # Encoder inconsistency
        patterns.append(FaultPattern(
            name="encoder_position_inconsistency",
            description="Absolute and incremental encoders show different positions",
            conditions=[
                {"variable": "motorVars_M1.absPosition_rad", "operator": "diff", "compare_to": "motorVars_M1.angleENC_rad", "threshold": 0.1}
            ],
            severity="warning",
            recommendations=[
                "Check encoder calibration and zero position",
                "Verify encoder mechanical coupling",
                "Recalibrate encoder offset if necessary"
            ]
        ))
        
        return patterns
    
    def _build_command_types(self) -> Dict[int, str]:
        """Build command type descriptions."""
        return {
            64: "Calibrate absolute position - Set encoder zero reference",
            65: "Calibrate torque offset - Determine motor torque constant", 
            66: "Calibrate motor ADC - Calibrate current measurement offsets",
            67: "Calibrate motor direction - Determine motor rotation direction",
            71: "Position control command - Move to specific position",
            84: "Initialization command - Initialize motor control system"
        }
    
    def _build_motor_states(self) -> Dict[int, str]:
        """Build motor state descriptions."""
        return {
            0: "IDLE - Motor stopped, all control loops disabled",
            1: "ALIGNMENT - Motor performing alignment procedure to determine rotor position",
            2: "CTRL_RUN - Motor control active, current control enabled", 
            3: "CL_RUNNING - Closed loop position/speed control active"
        }
    
    def analyze_fault_patterns(self, variable_data: Dict[str, Any]) -> List[FaultPattern]:
        """Analyze variable data against known fault patterns.
        
        Args:
            variable_data: Current variable readings
            
        Returns:
            List of matching fault patterns
        """
        matching_patterns = []
        
        for pattern in self._fault_patterns:
            if self._pattern_matches(pattern, variable_data):
                matching_patterns.append(pattern)
        
        return matching_patterns
    
    def _pattern_matches(self, pattern: FaultPattern, variable_data: Dict[str, Any]) -> bool:
        """Check if a fault pattern matches current data.
        
        Args:
            pattern: Fault pattern to check
            variable_data: Current variable readings
            
        Returns:
            True if pattern matches
        """
        try:
            for condition in pattern.conditions:
                var_name = condition["variable"]
                current_value = variable_data.get(var_name)
                
                if current_value is None:
                    return False  # Can't evaluate without data
                
                # Handle different comparison operators
                operator = condition.get("operator", "==")
                expected_value = condition["value"]
                
                if operator == "==":
                    if current_value != expected_value:
                        return False
                elif operator == "!=":
                    if current_value == expected_value:
                        return False
                elif operator == ">=":
                    if not (current_value >= expected_value):
                        return False
                elif operator == "<=":
                    if not (current_value <= expected_value):
                        return False
                elif operator == "diff":
                    # Special case for comparing two variables
                    compare_var = condition.get("compare_to")
                    threshold = condition.get("threshold", 0.01)
                    compare_value = variable_data.get(compare_var)
                    
                    if compare_value is None:
                        return False
                    
                    if abs(float(current_value) - float(compare_value)) < threshold:
                        return False
            
            # All conditions matched
            return True
            
        except Exception:
            return False
    
    def get_critical_variables(self) -> List[str]:
        """Get list of critical variables for monitoring.
        
        Returns:
            List of critical variable names
        """
        return [name for name, schema in self._variable_schemas.items() if schema.critical]
    
    def get_variable_info(self, variable_name: str) -> Dict[str, Any]:
        """Get comprehensive variable information.
        
        Args:
            variable_name: Variable name
            
        Returns:
            Variable information dictionary
        """
        schema = self.get_variable_schema(variable_name)
        if schema:
            return {
                "type": schema.type,
                "description": schema.description,
                "units": schema.units,
                "enum_values": schema.enum_values or {},
                "valid_range": schema.valid_range,
                "critical": schema.critical
            }
        else:
            return {
                "type": "unknown",
                "description": f"Motor control variable: {variable_name}",
                "units": "",
                "enum_values": {},
                "valid_range": None,
                "critical": False
            }
    
    async def get_available_variables(self) -> Dict[str, Any]:
        """Get list of available motor control variables.
        
        Returns:
            Dictionary of available variables with metadata
        """
        return {
            "total_variables": len(self._variable_schemas),
            "critical_variables": [name for name, schema in self._variable_schemas.items() if schema.critical],
            "variable_categories": {
                "position": [name for name in self._variable_schemas.keys() if "position" in name.lower() or "angle" in name.lower()],
                "current": [name for name in self._variable_schemas.keys() if "current" in name.lower() or "Idq" in name],
                "state": [name for name in self._variable_schemas.keys() if "state" in name.lower() or "enable" in name.lower()],
                "faults": [name for name in self._variable_schemas.keys() if "fault" in name.lower()],
                "debug": [name for name in self._variable_schemas.keys() if "debug" in name.lower() or "bypass" in name.lower()]
            },
            "all_variables": list(self._variable_schemas.keys())
        }
    
    async def get_memory_layout(self) -> Dict[str, Any]:
        """Get target memory layout information.
        
        Returns:
            Memory layout information
        """
        return {
            "target_device": "TMS320F280039C",
            "memory_regions": {
                "flash": {
                    "start_address": "0x00080000",
                    "size": "0x20000",
                    "description": "Program Flash Memory"
                },
                "ram": {
                    "start_address": "0x00000000", 
                    "size": "0x8000",
                    "description": "Data RAM"
                },
                "debug_bypass": {
                    "start_address": "0x0000d3c0",
                    "size": "68",
                    "description": "Debug bypass structure for motor control",
                    "fields": {
                        "debug_enabled": {"offset": 0, "size": 1, "type": "bool"},
                        "command.cmd": {"offset": 2, "size": 1, "type": "uint8_t"},
                        "command.pos": {"offset": 3, "size": 2, "type": "int16_t", "scale": 1000},
                        "command.max_current_ma": {"offset": 5, "size": 2, "type": "uint16_t"},
                        "command.kp": {"offset": 7, "size": 2, "type": "int16_t", "scale": 100},
                        "command.ki": {"offset": 9, "size": 2, "type": "int16_t", "scale": 1000},
                        "command.kd": {"offset": 11, "size": 2, "type": "int16_t", "scale": 1000}
                    }
                }
            }
        }
    
    async def get_motor_control_info(self) -> Dict[str, Any]:
        """Get comprehensive motor control domain knowledge.
        
        Returns:
            Motor control domain knowledge
        """
        return {
            "motor_states": self._motor_states,
            "command_types": self._command_types,
            "fault_patterns": [
                {
                    "name": pattern.name,
                    "description": pattern.description,
                    "severity": pattern.severity,
                    "conditions": pattern.conditions,
                    "recommendations": pattern.recommendations
                } for pattern in self._fault_patterns
            ],
            "critical_variables": self.get_critical_variables(),
            "motor_control_concepts": {
                "FOC": "Field-Oriented Control - Advanced motor control technique using d-q axis transformation",
                "alignment": "Process to determine rotor position for accurate field orientation",
                "bypass_alignment": "Fast alignment using precalculated electrical angle to skip delay",
                "encoder_types": {
                    "absolute": "Encoder providing absolute position reference (AS5048A on pin 20)",
                    "quadrature": "Incremental encoder providing relative position (on pin 21)"
                },
                "current_control": {
                    "d_axis": "Flux current component - controls motor magnetization",
                    "q_axis": "Torque current component - controls actual motor torque"
                }
            }
        }