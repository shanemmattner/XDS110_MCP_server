"""Analysis and diagnostic tools for motor control debugging."""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..gdb_interface.gdb_client import GDBClient
from ..knowledge.motor_control import MotorControlKnowledge


class AnalysisTool:
    """Tool for motor control analysis and diagnostics."""
    
    def __init__(self, gdb_client: GDBClient, knowledge: Optional[MotorControlKnowledge] = None):
        """Initialize analysis tool.
        
        Args:
            gdb_client: GDB client for communication
            knowledge: Domain knowledge database
        """
        self.gdb_client = gdb_client
        self.knowledge = knowledge or MotorControlKnowledge()
        self.logger = logging.getLogger(__name__)
    
    async def analyze_motor_state(self, focus_area: Optional[str] = None) -> str:
        """Analyze current motor control state with domain expertise.
        
        Args:
            focus_area: Specific area to focus on ("alignment", "current_control", "position", "faults")
            
        Returns:
            JSON analysis results with findings and recommendations
        """
        try:
            self.logger.info(f"Starting motor state analysis (focus: {focus_area or 'general'})")
            
            # Gather comprehensive motor data
            motor_data = await self._gather_motor_data(focus_area)
            
            # Analyze different aspects
            analysis_results = {
                "timestamp": datetime.now().isoformat(),
                "focus_area": focus_area or "general",
                "motor_data": motor_data,
                "analysis": {}
            }
            
            if focus_area == "alignment" or focus_area is None:
                analysis_results["analysis"]["alignment"] = await self._analyze_alignment(motor_data)
            
            if focus_area == "current_control" or focus_area is None:
                analysis_results["analysis"]["current_control"] = await self._analyze_current_control(motor_data)
            
            if focus_area == "position" or focus_area is None:
                analysis_results["analysis"]["position"] = await self._analyze_position_control(motor_data)
            
            if focus_area == "faults" or focus_area is None:
                analysis_results["analysis"]["faults"] = await self._analyze_faults(motor_data)
            
            # Add fault pattern analysis
            analysis_results["fault_patterns"] = await self._analyze_fault_patterns(motor_data)
            
            # Generate overall assessment and recommendations
            analysis_results["assessment"] = await self._generate_assessment(analysis_results["analysis"])
            analysis_results["recommendations"] = await self._generate_recommendations(analysis_results["analysis"], analysis_results["fault_patterns"])
            
            return json.dumps(analysis_results, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error during motor state analysis: {e}")
            return json.dumps({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _gather_motor_data(self, focus_area: Optional[str]) -> Dict[str, Any]:
        """Gather relevant motor control data for analysis.
        
        Args:
            focus_area: Focus area to determine which variables to read
            
        Returns:
            Motor data dictionary
        """
        # Core variables always needed
        core_variables = [
            "motorVars_M1.motorState",
            "motorVars_M1.absPosition_rad", 
            "motorVars_M1.angleFOC_rad",
            "motorVars_M1.angleENC_rad",
            "motorVars_M1.enableSpeedCtrl",
            "motorVars_M1.Idq_out_A.value[0]",  # D-axis current
            "motorVars_M1.Idq_out_A.value[1]",  # Q-axis current
        ]
        
        # Additional variables based on focus area
        additional_variables = []
        
        if focus_area == "alignment" or focus_area is None:
            additional_variables.extend([
                "debug_bypass.bypass_alignment_called",
                "debug_bypass.bypass_electrical_angle",
                "debug_bypass.cs_gpio_pin",
                "motorVars_M1.alignCurrent_A",
                "motorVars_M1.fluxCurrent_A"
            ])
        
        if focus_area == "current_control" or focus_area is None:
            additional_variables.extend([
                "motorVars_M1.IsRef_A",
                "motorVars_M1.fluxCurrent_A",
                "motorVars_M1.reversePhases"
            ])
        
        if focus_area == "faults" or focus_area is None:
            additional_variables.extend([
                "motorVars_M1.faultMtrNow.bit.needsCalibration",
                "motorVars_M1.faultMtrNow.bit.obakeNeedsInit",
                "motorVars_M1.faultMtrNow.all"
            ])
        
        all_variables = core_variables + additional_variables
        
        # Read all variables
        readings = await self.gdb_client.read_multiple_variables(all_variables)
        
        # Add debug_bypass structure data
        debug_bypass_data = await self._read_debug_bypass_structure()
        readings.update(debug_bypass_data)
        
        return readings
    
    async def _read_debug_bypass_structure(self) -> Dict[str, Any]:
        """Read debug_bypass structure data directly from memory.
        
        Returns:
            Debug bypass structure data
        """
        try:
            base_addr = 0x0000d3c0
            
            # Read first 16 bytes of debug_bypass structure
            raw_data = await self.gdb_client.read_memory(hex(base_addr), 16, "x")
            
            if raw_data:
                return {
                    "debug_bypass_raw": raw_data,
                    "debug_bypass.debug_enabled": raw_data[0] if len(raw_data) > 0 else None,
                    "debug_bypass.command.cmd": raw_data[2] if len(raw_data) > 2 else None,
                    "debug_bypass.command.pos": self._decode_int16_le(raw_data[3:5]) if len(raw_data) > 4 else None,
                    "debug_bypass.command.max_current_ma": self._decode_uint16_le(raw_data[5:7]) if len(raw_data) > 6 else None,
                    "debug_bypass.command.kp": self._decode_int16_le(raw_data[7:9]) if len(raw_data) > 8 else None,
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error reading debug_bypass structure: {e}")
            return {}
    
    def _decode_int16_le(self, bytes_data: List[int]) -> int:
        """Decode little-endian 16-bit signed integer."""
        if len(bytes_data) >= 2:
            value = bytes_data[0] | (bytes_data[1] << 8)
            # Convert to signed
            if value > 32767:
                value -= 65536
            return value
        return 0
    
    def _decode_uint16_le(self, bytes_data: List[int]) -> int:
        """Decode little-endian 16-bit unsigned integer."""
        if len(bytes_data) >= 2:
            return bytes_data[0] | (bytes_data[1] << 8)
        return 0
    
    async def _analyze_alignment(self, motor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze motor alignment status and issues.
        
        Args:
            motor_data: Motor control data
            
        Returns:
            Alignment analysis results
        """
        analysis = {
            "status": "unknown",
            "issues": [],
            "insights": []
        }
        
        try:
            motor_state = motor_data.get("motorVars_M1.motorState", 0)
            bypass_called = motor_data.get("debug_bypass.bypass_alignment_called", False)
            electrical_angle = motor_data.get("debug_bypass.bypass_electrical_angle")
            cs_pin = motor_data.get("debug_bypass.cs_gpio_pin")
            angle_foc = motor_data.get("motorVars_M1.angleFOC_rad")
            
            # Analyze motor state
            if motor_state == 0:
                analysis["status"] = "idle"
                analysis["insights"].append("Motor is in IDLE state - not attempting alignment")
            elif motor_state == 1:
                analysis["status"] = "aligning"
                analysis["insights"].append("Motor is currently in ALIGNMENT state")
            elif motor_state in [2, 3]:
                analysis["status"] = "aligned"
                analysis["insights"].append("Motor has completed alignment and is in running state")
            
            # Check for bypass alignment issues
            if bypass_called:
                analysis["insights"].append("Bypass alignment was called - skipping normal alignment delay")
                
                if electrical_angle is not None:
                    analysis["insights"].append(f"Bypass calculated electrical angle: {electrical_angle:.3f} rad")
                else:
                    analysis["issues"].append("Bypass alignment called but electrical angle not calculated")
                
                if cs_pin == 20:
                    analysis["insights"].append("Using absolute encoder (pin 20)")
                elif cs_pin == 21:
                    analysis["insights"].append("Using quadrature encoder (pin 21)")
                else:
                    analysis["issues"].append(f"Unexpected encoder pin selection: {cs_pin}")
                    
                # Check if FOC angle is properly set
                if angle_foc == 0.0 and electrical_angle != 0.0:
                    analysis["issues"].append("FOC angle is 0 but bypass calculated non-zero electrical angle - potential initialization issue")
            
            # Check alignment current
            align_current = motor_data.get("motorVars_M1.alignCurrent_A")
            if align_current is not None:
                if align_current == 0.0 and motor_state == 1:
                    analysis["issues"].append("Motor in alignment state but alignment current is 0")
                elif align_current > 0.1:
                    analysis["issues"].append(f"High alignment current: {align_current:.3f}A")
            
        except Exception as e:
            analysis["issues"].append(f"Analysis error: {e}")
        
        return analysis
    
    async def _analyze_current_control(self, motor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current control system status.
        
        Args:
            motor_data: Motor control data
            
        Returns:
            Current control analysis results
        """
        analysis = {
            "status": "unknown", 
            "issues": [],
            "insights": []
        }
        
        try:
            d_current = motor_data.get("motorVars_M1.Idq_out_A.value[0]", 0)
            q_current = motor_data.get("motorVars_M1.Idq_out_A.value[1]", 0)
            current_ref = motor_data.get("motorVars_M1.IsRef_A", 0)
            flux_current = motor_data.get("motorVars_M1.fluxCurrent_A", 0)
            
            # Analyze current levels
            current_magnitude = (d_current**2 + q_current**2)**0.5
            
            if current_magnitude == 0:
                analysis["status"] = "no_current"
                analysis["issues"].append("No current command - motor will not move")
            elif current_magnitude < 0.01:
                analysis["status"] = "low_current"
                analysis["insights"].append(f"Very low current magnitude: {current_magnitude:.4f}A")
            else:
                analysis["status"] = "active"
                analysis["insights"].append(f"Current magnitude: {current_magnitude:.3f}A")
            
            # Check D/Q current balance
            if abs(d_current) > 0.001:
                analysis["insights"].append(f"D-axis current: {d_current:.3f}A (flux/torque capability)")
            if abs(q_current) > 0.001:
                analysis["insights"].append(f"Q-axis current: {q_current:.3f}A (actual torque)")
            
            # Check flux current setting
            if flux_current == 0:
                analysis["issues"].append("Flux current is 0 - motor may not have torque capability")
            elif flux_current != d_current and abs(d_current) > 0.001:
                analysis["insights"].append(f"Flux current setting ({flux_current:.3f}A) differs from D-axis command ({d_current:.3f}A)")
            
            # Check for current reference issues
            if current_ref != current_magnitude and current_magnitude > 0.001:
                ratio = current_ref / current_magnitude if current_magnitude > 0 else 0
                analysis["insights"].append(f"Current reference vs magnitude ratio: {ratio:.2f}")
                
        except Exception as e:
            analysis["issues"].append(f"Analysis error: {e}")
        
        return analysis
    
    async def _analyze_position_control(self, motor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze position control performance.
        
        Args:
            motor_data: Motor control data
            
        Returns:
            Position control analysis results
        """
        analysis = {
            "status": "unknown",
            "issues": [],
            "insights": []
        }
        
        try:
            abs_position = motor_data.get("motorVars_M1.absPosition_rad")
            angle_foc = motor_data.get("motorVars_M1.angleFOC_rad")
            angle_enc = motor_data.get("motorVars_M1.angleENC_rad")
            
            # Check position consistency
            if abs_position is not None and angle_enc is not None:
                position_diff = abs(abs_position - angle_enc)
                if position_diff > 0.1:  # > ~6 degrees
                    analysis["issues"].append(f"Large difference between absolute position ({abs_position:.3f}) and encoder angle ({angle_enc:.3f})")
                else:
                    analysis["insights"].append("Absolute position and encoder angle are consistent")
            
            # Check FOC angle initialization
            if angle_foc is not None:
                if angle_foc == 0.0:
                    analysis["insights"].append("FOC angle is 0 - may indicate uninitialized state")
                else:
                    analysis["insights"].append(f"FOC angle: {angle_foc:.3f} rad")
            
            # Analyze debug_bypass position command if present
            debug_pos = motor_data.get("debug_bypass.command.pos")
            if debug_pos is not None:
                # Convert from scaled integer (pos * 1000)
                pos_radians = debug_pos / 1000.0
                analysis["insights"].append(f"Debug bypass position target: {pos_radians:.3f} rad")
                
                if abs_position is not None:
                    position_error = abs_position - pos_radians
                    analysis["insights"].append(f"Position error: {position_error:.3f} rad")
            
        except Exception as e:
            analysis["issues"].append(f"Analysis error: {e}")
        
        return analysis
    
    async def _analyze_faults(self, motor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fault conditions and system health.
        
        Args:
            motor_data: Motor control data
            
        Returns:
            Fault analysis results
        """
        analysis = {
            "status": "unknown",
            "issues": [],
            "insights": [],
            "active_faults": []
        }
        
        try:
            needs_calibration = motor_data.get("motorVars_M1.faultMtrNow.bit.needsCalibration")
            needs_init = motor_data.get("motorVars_M1.faultMtrNow.bit.obakeNeedsInit")
            fault_all = motor_data.get("motorVars_M1.faultMtrNow.all")
            
            # Check calibration status
            if needs_calibration == 1:
                analysis["active_faults"].append("Motor needs calibration")
                analysis["issues"].append("System requires calibration before operation")
            elif needs_calibration == 0:
                analysis["insights"].append("Motor calibration is complete")
            
            # Check initialization status
            if needs_init == 1:
                analysis["active_faults"].append("Motor needs initialization")
                analysis["issues"].append("System requires initialization command")
            elif needs_init == 0:
                analysis["insights"].append("Motor initialization is complete")
            
            # Analyze overall fault word
            if fault_all is not None:
                if fault_all == 0:
                    analysis["status"] = "healthy"
                    analysis["insights"].append("No active faults detected")
                else:
                    analysis["status"] = "faulted"
                    analysis["insights"].append(f"Fault word: 0x{fault_all:x}")
                    # Could add more detailed fault bit analysis here
            
            # Determine overall system health
            if len(analysis["active_faults"]) == 0:
                analysis["status"] = "healthy"
            else:
                analysis["status"] = "requires_attention"
                
        except Exception as e:
            analysis["issues"].append(f"Analysis error: {e}")
        
        return analysis
    
    async def _analyze_fault_patterns(self, motor_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze motor data against known fault patterns.
        
        Args:
            motor_data: Motor control data
            
        Returns:
            List of matching fault patterns with details
        """
        try:
            matching_patterns = self.knowledge.analyze_fault_patterns(motor_data)
            
            pattern_results = []
            for pattern in matching_patterns:
                pattern_results.append({
                    "name": pattern.name,
                    "description": pattern.description,
                    "severity": pattern.severity,
                    "recommendations": pattern.recommendations
                })
            
            return pattern_results
            
        except Exception as e:
            self.logger.error(f"Error analyzing fault patterns: {e}")
            return []
    
    async def _generate_assessment(self, analysis: Dict[str, Any]) -> str:
        """Generate overall assessment from analysis results.
        
        Args:
            analysis: Analysis results dictionary
            
        Returns:
            Overall assessment string
        """
        try:
            assessments = []
            
            # Check each analysis area
            for area, results in analysis.items():
                if isinstance(results, dict) and "status" in results:
                    status = results["status"]
                    issues = len(results.get("issues", []))
                    
                    if status in ["healthy", "active", "aligned"]:
                        assessments.append(f"{area.title()}: OK")
                    elif status in ["requires_attention", "faulted"]:
                        assessments.append(f"{area.title()}: ISSUES ({issues} problems)")
                    else:
                        assessments.append(f"{area.title()}: {status.upper()}")
            
            if not assessments:
                return "Analysis completed - see detailed results for findings"
            
            return " | ".join(assessments)
            
        except Exception as e:
            return f"Assessment generation error: {e}"
    
    async def _generate_recommendations(self, analysis: Dict[str, Any], fault_patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on analysis results.
        
        Args:
            analysis: Analysis results dictionary
            fault_patterns: Detected fault patterns
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        try:
            # First add recommendations from fault patterns (domain knowledge)
            for pattern in fault_patterns:
                if pattern["severity"] == "critical":
                    recommendations.extend([f"CRITICAL: {rec}" for rec in pattern["recommendations"]])
                else:
                    recommendations.extend(pattern["recommendations"])
            
            # Check for common patterns and generate specific recommendations
            
            # Fault-based recommendations
            fault_analysis = analysis.get("faults", {})
            if "Motor needs calibration" in fault_analysis.get("active_faults", []):
                recommendations.append("Run calibration sequence (commands 64-67) before attempting motor control")
            
            if "Motor needs initialization" in fault_analysis.get("active_faults", []):
                recommendations.append("Send initialization command (command 84) to clear needsInit flag")
            
            # Current control recommendations
            current_analysis = analysis.get("current_control", {})
            if current_analysis.get("status") == "no_current":
                recommendations.append("Enable current control - check if debug_bypass.debug_enabled = 1 and proper command is set")
            
            # Alignment recommendations
            alignment_analysis = analysis.get("alignment", {})
            alignment_issues = alignment_analysis.get("issues", [])
            
            for issue in alignment_issues:
                if "FOC angle is 0 but bypass calculated non-zero" in issue:
                    recommendations.append("Initialize FOC angle with bypass electrical angle value to fix motor humming")
                elif "alignment current is 0" in issue:
                    recommendations.append("Set appropriate alignment current (typically 0.1A) for proper motor alignment")
            
            # Position control recommendations
            position_analysis = analysis.get("position", {})
            for issue in position_analysis.get("issues", []):
                if "Large difference between absolute position" in issue:
                    recommendations.append("Check encoder calibration - absolute and incremental encoders show different positions")
            
            # General recommendations if no specific ones found
            if not recommendations:
                total_issues = sum(len(results.get("issues", [])) for results in analysis.values() if isinstance(results, dict))
                if total_issues > 0:
                    recommendations.append("Multiple issues detected - review detailed analysis for specific problems")
                else:
                    recommendations.append("System appears healthy - monitor for any parameter drift or performance changes")
            
        except Exception as e:
            recommendations.append(f"Recommendation generation error: {e}")
        
        return recommendations