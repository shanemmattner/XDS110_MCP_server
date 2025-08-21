#!/usr/bin/env python3
"""
TI DSS Debug Adapter - Implementation of Generic Debug Interface for TI Debug Server Scripting

This adapter wraps our existing TI DSS JavaScript infrastructure with the generic
debug interface, allowing it to work with the LLM debugging framework.
"""

import asyncio
import json
import subprocess
import tempfile
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from debug_interface import (
    GenericDebugInterface, VariableInfo, VariableType, TargetState, DebugEvent
)


class TIDSSAdapter(GenericDebugInterface):
    """
    TI DSS implementation of the generic debug interface.
    
    This adapter leverages our existing JavaScript DSS scripts and wraps them
    with the standardized Python interface for LLM consumption.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize TI DSS adapter
        
        Args:
            config: Configuration dictionary containing:
                - dss_path: Path to DSS executable
                - ccxml_path: Path to target configuration file
                - firmware_path: Path to firmware file
                - script_dir: Directory containing our JavaScript scripts
        """
        super().__init__(config)
        
        self.dss_path = config.get('dss_path', '/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh')
        self.ccxml_path = config.get('ccxml_path', 'TMS320F280039C_LaunchPad.ccxml')
        self.firmware_path = config.get('firmware_path', 'Flash_lib_DRV8323RH_3SC/obake_firmware.out')
        self.script_dir = Path(config.get('script_dir', '.'))
        self.js_scripts_dir = self.script_dir / "js_scripts"
        
        # Define known motor control variables with metadata
        self._known_variables = self._initialize_variable_schema()
    
    def _initialize_variable_schema(self) -> Dict[str, VariableInfo]:
        """Initialize the schema of known motor control variables"""
        return {
            'motorVars_M1.angleFOC_rad': VariableInfo(
                name='motorVars_M1.angleFOC_rad',
                type=VariableType.FLOAT,
                description='Field-oriented control angle in radians',
                valid_range=(0.0, 6.28)
            ),
            'motorVars_M1.angleENC_rad': VariableInfo(
                name='motorVars_M1.angleENC_rad',
                type=VariableType.FLOAT,
                description='Encoder electrical angle in radians',
                valid_range=(0.0, 6.28)
            ),
            'motorVars_M1.absPosition_rad': VariableInfo(
                name='motorVars_M1.absPosition_rad',
                type=VariableType.FLOAT,
                description='Absolute encoder position in radians'
            ),
            'motorVars_M1.motorState': VariableInfo(
                name='motorVars_M1.motorState',
                type=VariableType.ENUM,
                description='Motor state machine',
                enum_values={0: 'IDLE', 1: 'ALIGNMENT', 2: 'CTRL_RUN', 3: 'CL_RUNNING'}
            ),
            'motorVars_M1.enableSpeedCtrl': VariableInfo(
                name='motorVars_M1.enableSpeedCtrl',
                type=VariableType.BOOL,
                description='Speed control enable flag'
            ),
            'motorVars_M1.fluxCurrent_A': VariableInfo(
                name='motorVars_M1.fluxCurrent_A',
                type=VariableType.FLOAT,
                description='Flux current setting in Amperes'
            ),
            'motorVars_M1.Idq_out_A.value[0]': VariableInfo(
                name='motorVars_M1.Idq_out_A.value[0]',
                type=VariableType.FLOAT,
                description='D-axis current command in Amperes'
            ),
            'motorVars_M1.Idq_out_A.value[1]': VariableInfo(
                name='motorVars_M1.Idq_out_A.value[1]',
                type=VariableType.FLOAT,
                description='Q-axis current command in Amperes'
            ),
            'debug_bypass.bypass_alignment_called': VariableInfo(
                name='debug_bypass.bypass_alignment_called',
                type=VariableType.BOOL,
                description='Flag indicating bypass alignment was executed'
            ),
            'debug_bypass.bypass_electrical_angle': VariableInfo(
                name='debug_bypass.bypass_electrical_angle',
                type=VariableType.FLOAT,
                description='Calculated electrical angle during bypass',
                valid_range=(0.0, 6.28)
            ),
            'debug_bypass.cs_gpio_pin': VariableInfo(
                name='debug_bypass.cs_gpio_pin',
                type=VariableType.ENUM,
                description='Current encoder pin selection',
                enum_values={20: 'ABSOLUTE', 21: 'QUADRATURE'}
            )
        }
    
    async def _execute_dss_script(self, script_content: str) -> tuple[bool, str]:
        """
        Execute a DSS JavaScript script and return results
        
        Args:
            script_content: JavaScript code to execute
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            # Execute DSS script
            result = await asyncio.create_subprocess_exec(
                self.dss_path, '-f', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.script_dir.parent.parent  # Change to firmware root
            )
            
            stdout, stderr = await result.communicate()
            
            # Clean up temporary file
            os.unlink(script_path)
            
            success = result.returncode == 0
            output = stdout.decode('utf-8') if stdout else stderr.decode('utf-8')
            
            return success, output
            
        except Exception as e:
            return False, f"Error executing DSS script: {str(e)}"
    
    def _generate_connection_script(self) -> str:
        """Generate JavaScript for target connection"""
        return f'''
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {{
    var debugSession = null;
    
    try {{
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{self.ccxml_path}");
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        print("CONNECTION_SUCCESS");
        
    }} catch (e) {{
        print("CONNECTION_ERROR: " + e.message);
    }} finally {{
        if (debugSession != null) {{
            try {{
                debugSession.target.disconnect();
                debugSession.terminate();
            }} catch (e) {{}}
        }}
    }}
}}

main();
'''
    
    def _generate_variable_read_script(self, variables: List[str]) -> str:
        """Generate JavaScript for reading variables"""
        variables_js = json.dumps(variables)
        
        return f'''
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {{
    var debugSession = null;
    
    try {{
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{self.ccxml_path}");
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Load firmware if needed
        debugSession.memory.loadProgram("{self.firmware_path}");
        debugSession.target.halt();
        
        var variables = {variables_js};
        
        for (var i = 0; i < variables.length; i++) {{
            try {{
                var value = debugSession.expression.evaluate(variables[i]);
                print(variables[i] + " = " + value);
            }} catch (e) {{
                print("Error reading " + variables[i] + ": " + e.message);
            }}
        }}
        
    }} catch (e) {{
        print("SCRIPT_ERROR: " + e.message);
    }} finally {{
        if (debugSession != null) {{
            try {{
                debugSession.target.disconnect();
                debugSession.terminate();
            }} catch (e) {{}}
        }}
    }}
}}

main();
'''
    
    def _generate_target_control_script(self, action: str) -> str:
        """Generate JavaScript for target control (halt/resume/reset)"""
        return f'''
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {{
    var debugSession = null;
    
    try {{
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{self.ccxml_path}");
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        {"debugSession.target.halt();" if action == "halt" else ""}
        {"debugSession.target.runAsynch();" if action == "resume" else ""}
        {"debugSession.target.reset();" if action == "reset" else ""}
        
        print("{action.upper()}_SUCCESS");
        
    }} catch (e) {{
        print("{action.upper()}_ERROR: " + e.message);
    }} finally {{
        if (debugSession != null) {{
            try {{
                debugSession.target.disconnect();
                debugSession.terminate();
            }} catch (e) {{}}
        }}
    }}
}}

main();
'''
    
    async def connect(self) -> bool:
        """Connect to TI target via DSS"""
        script = self._generate_connection_script()
        success, output = await self._execute_dss_script(script)
        
        if success and "CONNECTION_SUCCESS" in output:
            self.connected = True
            self.target_state = TargetState.HALTED
            self._emit_event(DebugEvent("connection", asyncio.get_event_loop().time(), 
                                      {"status": "connected", "target": "TMS320F280039C"}))
            return True
        else:
            self.connected = False
            self.target_state = TargetState.ERROR
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from TI target"""
        self.connected = False
        self.target_state = TargetState.DISCONNECTED
        self._emit_event(DebugEvent("disconnection", asyncio.get_event_loop().time(), 
                                  {"status": "disconnected"}))
        return True
    
    async def get_target_state(self) -> TargetState:
        """Get current target state"""
        return self.target_state
    
    async def halt_target(self) -> bool:
        """Halt target execution"""
        script = self._generate_target_control_script("halt")
        success, output = await self._execute_dss_script(script)
        
        if success and "HALT_SUCCESS" in output:
            self.target_state = TargetState.HALTED
            return True
        return False
    
    async def resume_target(self) -> bool:
        """Resume target execution"""
        script = self._generate_target_control_script("resume")
        success, output = await self._execute_dss_script(script)
        
        if success and "RESUME_SUCCESS" in output:
            self.target_state = TargetState.RUNNING
            return True
        return False
    
    async def reset_target(self, halt_after_reset: bool = True) -> bool:
        """Reset the target"""
        script = self._generate_target_control_script("reset")
        success, output = await self._execute_dss_script(script)
        
        if success and "RESET_SUCCESS" in output:
            self.target_state = TargetState.HALTED if halt_after_reset else TargetState.RUNNING
            return True
        return False
    
    async def load_firmware(self, firmware_path: str) -> bool:
        """Load firmware to target"""
        # Update firmware path for future operations
        self.firmware_path = firmware_path
        
        # For now, firmware loading is integrated into variable reading
        # In a full implementation, this would be a separate operation
        return True
    
    async def read_variable(self, variable_name: str) -> Optional[Any]:
        """Read a single variable"""
        result = await self.read_multiple_variables([variable_name])
        return result.get(variable_name)
    
    async def read_multiple_variables(self, variable_names: List[str]) -> Dict[str, Any]:
        """Read multiple variables efficiently"""
        script = self._generate_variable_read_script(variable_names)
        success, output = await self._execute_dss_script(script)
        
        if success:
            # Parse the output from our existing JavaScript scripts
            # They output in format "variable_name = value"
            results = {}
            
            for line in output.split('\n'):
                line = line.strip()
                if ' = ' in line and not line.startswith('Error'):
                    try:
                        var_name, value_str = line.split(' = ', 1)
                        var_name = var_name.strip()
                        value_str = value_str.strip()
                        
                        # Convert string values to appropriate types
                        if value_str.lower() in ['true', 'false']:
                            value = value_str.lower() == 'true'
                        elif value_str.replace('.', '').replace('-', '').isdigit():
                            value = float(value_str) if '.' in value_str else int(value_str)
                        else:
                            value = value_str
                        
                        results[var_name] = value
                        
                    except ValueError:
                        continue
            
            return results
        
        return {}
    
    async def write_variable(self, variable_name: str, value: Any) -> bool:
        """Write a variable to target (not implemented in current DSS scripts)"""
        # TODO: Implement variable writing in DSS JavaScript
        print(f"Variable writing not yet implemented for TI DSS adapter")
        return False
    
    async def read_memory(self, address: int, size: int) -> Optional[bytes]:
        """Read memory from target (not implemented in current DSS scripts)"""
        # TODO: Implement memory reading in DSS JavaScript
        print(f"Memory reading not yet implemented for TI DSS adapter")
        return None
    
    async def write_memory(self, address: int, data: bytes) -> bool:
        """Write memory to target (not implemented in current DSS scripts)"""
        # TODO: Implement memory writing in DSS JavaScript
        print(f"Memory writing not yet implemented for TI DSS adapter")
        return False
    
    async def get_available_variables(self) -> List[VariableInfo]:
        """Get list of available variables"""
        return list(self._known_variables.values())
    
    def get_variable_info(self, variable_name: str) -> Optional[VariableInfo]:
        """Get information about a specific variable"""
        return self._known_variables.get(variable_name)
    
    def is_variable_known(self, variable_name: str) -> bool:
        """Check if a variable is in our known schema"""
        return variable_name in self._known_variables
    
    async def validate_connection(self) -> Dict[str, Any]:
        """
        Validate connection and get basic system information
        
        Returns:
            Dictionary with connection validation results
        """
        if not self.connected:
            await self.connect()
        
        # Read key variables to validate the connection
        test_variables = [
            'motorVars_M1.motorState',
            'motorVars_M1.absPosition_rad',
            'debug_bypass.cs_gpio_pin'
        ]
        
        results = await self.read_multiple_variables(test_variables)
        
        return {
            'connected': self.connected,
            'target_state': self.target_state.value,
            'test_variables': results,
            'variable_count': len([v for v in results.values() if v is not None])
        }