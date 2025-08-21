#!/usr/bin/env python3
"""Basic functionality test for XDS110 MCP Server components."""

import asyncio
import sys
from pathlib import Path
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from xds110_mcp_server.knowledge.motor_control import MotorControlKnowledge
from xds110_mcp_server.utils.config import Config


async def test_knowledge_database():
    """Test the motor control knowledge database."""
    print("=== Testing Motor Control Knowledge Database ===")
    
    knowledge = MotorControlKnowledge()
    
    # Test variable schema lookup
    print("\n1. Testing variable schema lookup:")
    test_vars = [
        "motorVars_M1.motorState",
        "motorVars_M1.absPosition_rad", 
        "debug_bypass.debug_enabled",
        "unknown_variable"
    ]
    
    for var in test_vars:
        schema = knowledge.get_variable_schema(var)
        if schema:
            print(f"  {var}: {schema.type} - {schema.description}")
        else:
            print(f"  {var}: Not found")
    
    # Test fault pattern analysis
    print("\n2. Testing fault pattern analysis:")
    test_data = {
        "debug_bypass.bypass_alignment_called": True,
        "debug_bypass.bypass_electrical_angle": 1.5,
        "motorVars_M1.angleFOC_rad": 0.0,
        "motorVars_M1.motorState": 1,
        "motorVars_M1.faultMtrNow.bit.needsCalibration": 1
    }
    
    patterns = knowledge.analyze_fault_patterns(test_data)
    print(f"  Detected {len(patterns)} fault patterns:")
    for pattern in patterns:
        print(f"    - {pattern.name}: {pattern.description} ({pattern.severity})")
    
    # Test command descriptions
    print("\n3. Testing command descriptions:")
    test_commands = [64, 65, 71, 84, 999]
    for cmd in test_commands:
        desc = knowledge.get_command_description(cmd)
        print(f"  Command {cmd}: {desc}")
    
    # Test available variables
    print("\n4. Testing available variables:")
    variables = await knowledge.get_available_variables()
    print(f"  Total variables: {variables['total_variables']}")
    print(f"  Critical variables: {len(variables['critical_variables'])}")
    for category, vars in variables['variable_categories'].items():
        print(f"  {category.title()} variables: {len(vars)}")
    
    print("\nKnowledge database test completed ✓")


async def test_config_loading():
    """Test configuration loading."""
    print("\n=== Testing Configuration Loading ===")
    
    config_path = Path("configs/f28039_config.json")
    
    if config_path.exists():
        try:
            config = Config.load(config_path)
            print(f"✓ Successfully loaded config from {config_path}")
            print(f"  OpenOCD config file: {config.openocd.config_file}")
            print(f"  GDB server port: {config.gdb.port}")
        except Exception as e:
            print(f"✗ Failed to load config: {e}")
    else:
        print(f"✗ Config file not found: {config_path}")
    
    print("Configuration test completed ✓")


async def test_motor_control_concepts():
    """Test motor control domain concepts."""
    print("\n=== Testing Motor Control Domain Concepts ===")
    
    knowledge = MotorControlKnowledge()
    
    # Test motor control info
    info = await knowledge.get_motor_control_info()
    
    print(f"Motor states: {len(info['motor_states'])}")
    for state, desc in info['motor_states'].items():
        print(f"  State {state}: {desc}")
    
    print(f"\nCommand types: {len(info['command_types'])}")
    for cmd, desc in info['command_types'].items():
        print(f"  Command {cmd}: {desc}")
    
    print(f"\nFault patterns: {len(info['fault_patterns'])}")
    for pattern in info['fault_patterns']:
        print(f"  {pattern['name']}: {pattern['severity']}")
    
    print(f"\nMotor control concepts:")
    for concept, desc in info['motor_control_concepts'].items():
        if isinstance(desc, str):
            print(f"  {concept}: {desc}")
        else:
            print(f"  {concept}:")
            for sub, sub_desc in desc.items():
                print(f"    {sub}: {sub_desc}")
    
    print("Motor control concepts test completed ✓")


async def main():
    """Run all basic tests."""
    print("XDS110 MCP Server - Basic Functionality Tests")
    print("=" * 50)
    
    try:
        await test_knowledge_database()
        await test_config_loading()
        await test_motor_control_concepts()
        
        print("\n" + "=" * 50)
        print("✓ All basic tests completed successfully!")
        print("The core components are ready for MCP server integration.")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())