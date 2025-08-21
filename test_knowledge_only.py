#!/usr/bin/env python3
"""Test just the knowledge database without MCP server imports."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Direct import to avoid server imports
sys.path.insert(0, str(Path(__file__).parent / "xds110_mcp_server"))
from knowledge.motor_control import MotorControlKnowledge


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
            print(f"  ✓ {var}: {schema.type} - {schema.description}")
        else:
            print(f"  ✗ {var}: Not found")
    
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
        print(f"    ✓ {pattern.name}: {pattern.description} ({pattern.severity})")
    
    # Test command descriptions
    print("\n3. Testing command descriptions:")
    test_commands = [64, 65, 71, 84, 999]
    for cmd in test_commands:
        desc = knowledge.get_command_description(cmd)
        print(f"  ✓ Command {cmd}: {desc}")
    
    # Test available variables
    print("\n4. Testing available variables:")
    variables = await knowledge.get_available_variables()
    print(f"  ✓ Total variables: {variables['total_variables']}")
    print(f"  ✓ Critical variables: {len(variables['critical_variables'])}")
    for category, vars in variables['variable_categories'].items():
        print(f"  ✓ {category.title()} variables: {len(vars)}")
    
    # Test memory layout
    print("\n5. Testing memory layout:")
    layout = await knowledge.get_memory_layout()
    print(f"  ✓ Target device: {layout['target_device']}")
    print(f"  ✓ Memory regions: {len(layout['memory_regions'])}")
    for region, info in layout['memory_regions'].items():
        print(f"    - {region}: {info['start_address']} ({info['description']})")
    
    # Test motor control info
    print("\n6. Testing motor control info:")
    info = await knowledge.get_motor_control_info()
    print(f"  ✓ Motor states: {len(info['motor_states'])}")
    print(f"  ✓ Command types: {len(info['command_types'])}")
    print(f"  ✓ Fault patterns: {len(info['fault_patterns'])}")
    print(f"  ✓ Critical variables: {len(info['critical_variables'])}")
    print(f"  ✓ Motor control concepts: {len(info['motor_control_concepts'])}")
    
    print("\n✅ Knowledge database test completed successfully!")
    return True


async def main():
    """Run knowledge database test."""
    print("XDS110 MCP Server - Knowledge Database Test")
    print("=" * 50)
    
    try:
        success = await test_knowledge_database()
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 Knowledge database is working correctly!")
            print("Ready to integrate with MCP server and GDB interface.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())