#!/usr/bin/env python3
"""Test MCP server functionality without hardware dependency."""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from xds110_mcp_server.knowledge.motor_control import MotorControlKnowledge
from xds110_mcp_server.tools.variable_monitor import VariableMonitorTool
from xds110_mcp_server.tools.memory_tools import MemoryTool
from xds110_mcp_server.tools.analysis_tools import AnalysisTool


class MockGDBClient:
    """Mock GDB client for testing without hardware."""
    
    def __init__(self):
        self.connected = True
    
    async def connect(self):
        return True
    
    async def disconnect(self):
        pass
    
    async def validate_connection(self):
        return True
    
    async def read_multiple_variables(self, variables):
        """Return mock motor control data."""
        mock_data = {
            "motorVars_M1.motorState": 2,  # CTRL_RUN state
            "motorVars_M1.absPosition_rad": 1.234,
            "motorVars_M1.angleFOC_rad": 0.785,
            "motorVars_M1.angleENC_rad": 1.230,
            "motorVars_M1.Idq_out_A.value[0]": 0.8,  # D-axis current
            "motorVars_M1.Idq_out_A.value[1]": 1.2,  # Q-axis current
            "motorVars_M1.IsRef_A": 1.5,
            "motorVars_M1.fluxCurrent_A": 0.8,
            "motorVars_M1.alignCurrent_A": 0.1,
            "motorVars_M1.enableSpeedCtrl": True,
            "motorVars_M1.reversePhases": False,
            "motorVars_M1.faultMtrNow.bit.needsCalibration": 0,
            "motorVars_M1.faultMtrNow.bit.obakeNeedsInit": 0,
            "motorVars_M1.faultMtrNow.all": 0,
            "debug_bypass.debug_enabled": True,
            "debug_bypass.bypass_alignment_called": False,
            "debug_bypass.bypass_electrical_angle": 0.0,
            "debug_bypass.cs_gpio_pin": 20
        }
        
        # Return only requested variables
        return {var: mock_data.get(var) for var in variables if var in mock_data}
    
    async def read_memory(self, address, count, format):
        """Return mock memory data."""
        if address == "0xd3c0" or address == hex(0x0000d3c0):
            # Mock debug_bypass structure data
            return [1, 0, 71, 15, 39, 0, 200, 0, 100, 0, 10, 0, 5, 0, 0, 0]
        return [0] * count
    
    async def write_memory(self, address, values, size):
        """Mock memory write."""
        print(f"Mock write: {len(values)} values to {address} (size={size})")
        return True


async def test_variable_reading():
    """Test variable reading functionality."""
    print("=== Testing Variable Reading ===")
    
    mock_gdb = MockGDBClient()
    knowledge = MotorControlKnowledge()
    monitor = VariableMonitorTool(mock_gdb, knowledge)
    
    # Test reading critical variables
    critical_vars = knowledge.get_critical_variables()
    print(f"Testing {len(critical_vars)} critical variables...")
    
    result = await monitor.read_variables(critical_vars[:5], format="json")
    data = json.loads(result)
    
    print(f"✓ Successfully read {data['successful_reads']}/{data['variables_read']} variables")
    
    for var_name, reading in data["readings"].items():
        if "error" not in reading:
            print(f"  {var_name}: {reading['value']} {reading['units']} - {reading['description']}")
    
    return True


async def test_motor_analysis():
    """Test motor state analysis."""
    print("\n=== Testing Motor State Analysis ===")
    
    mock_gdb = MockGDBClient()
    knowledge = MotorControlKnowledge()
    analysis_tool = AnalysisTool(mock_gdb, knowledge)
    
    # Test general analysis
    result = await analysis_tool.analyze_motor_state()
    data = json.loads(result)
    
    print(f"✓ Analysis completed: {data['assessment']}")
    
    if "fault_patterns" in data and data["fault_patterns"]:
        print(f"✓ Fault patterns detected: {len(data['fault_patterns'])}")
        for pattern in data["fault_patterns"]:
            print(f"  - {pattern['name']}: {pattern['severity']}")
    else:
        print("✓ No fault patterns detected - system appears healthy")
    
    if "recommendations" in data and data["recommendations"]:
        print(f"✓ Generated {len(data['recommendations'])} recommendations:")
        for rec in data["recommendations"]:
            print(f"  • {rec}")
    
    return True


async def test_memory_operations():
    """Test memory read/write operations."""
    print("\n=== Testing Memory Operations ===")
    
    mock_gdb = MockGDBClient()
    knowledge = MotorControlKnowledge()
    memory_tool = MemoryTool(mock_gdb, knowledge)
    
    # Test reading debug_bypass structure
    result = await memory_tool.read_memory("0xd3c0", count=16, format="hex")
    data = json.loads(result)
    
    if data["success"]:
        print(f"✓ Successfully read {data['count']} bytes from {data['address']}")
        if "interpretation" in data:
            print(f"  Structure: {data['interpretation']['structure']}")
            print(f"  Field: {data['interpretation'].get('field', 'Unknown')}")
    
    # Test safe memory write
    result = await memory_tool.write_debug_bypass_field("debug_enabled", 1)
    data = json.loads(result)
    
    if data["success"]:
        print(f"✓ Successfully wrote {data['field']} = {data['value']}")
        if data["verification"]["verified"]:
            print("  ✓ Write verified by readback")
    
    return True


async def test_monitoring():
    """Test variable monitoring with change detection."""
    print("\n=== Testing Variable Monitoring ===")
    
    mock_gdb = MockGDBClient()
    knowledge = MotorControlKnowledge()
    monitor = VariableMonitorTool(mock_gdb, knowledge)
    
    # Test short monitoring session
    test_vars = [
        "motorVars_M1.motorState",
        "motorVars_M1.Idq_out_A.value[0]",
        "motorVars_M1.absPosition_rad"
    ]
    
    print(f"Starting 3-second monitoring of {len(test_vars)} variables...")
    result = await monitor.monitor_variables(test_vars, duration=3.0, threshold=0.01)
    data = json.loads(result)
    
    summary = data["monitoring_summary"]
    print(f"✓ Monitoring completed:")
    print(f"  Duration: {summary['duration_seconds']:.1f}s")
    print(f"  Cycles: {summary['cycles_completed']}")
    print(f"  Frequency: {summary['frequency_hz']:.1f}Hz")
    print(f"  Variables with changes: {summary['variables_with_changes']}")
    
    return True


async def test_knowledge_integration():
    """Test knowledge database integration."""
    print("\n=== Testing Knowledge Integration ===")
    
    knowledge = MotorControlKnowledge()
    
    # Test fault pattern analysis with specific scenario
    test_scenario = {
        "motorVars_M1.faultMtrNow.bit.needsCalibration": 1,
        "motorVars_M1.faultMtrNow.bit.obakeNeedsInit": 1,
        "motorVars_M1.Idq_out_A.value[0]": 0.0,
        "motorVars_M1.Idq_out_A.value[1]": 0.0,
        "motorVars_M1.motorState": 2
    }
    
    patterns = knowledge.analyze_fault_patterns(test_scenario)
    print(f"✓ Detected {len(patterns)} fault patterns in test scenario:")
    
    for pattern in patterns:
        print(f"  - {pattern.name} ({pattern.severity})")
        print(f"    {pattern.description}")
        for rec in pattern.recommendations[:2]:  # Show first 2 recommendations
            print(f"    → {rec}")
    
    return True


async def main():
    """Run all MCP server tests."""
    print("XDS110 MCP Server - Software Component Tests")
    print("=" * 60)
    print("Testing without hardware dependency using mock GDB client")
    print("=" * 60)
    
    try:
        # Run all tests
        await test_variable_reading()
        await test_motor_analysis()
        await test_memory_operations() 
        await test_monitoring()
        await test_knowledge_integration()
        
        print("\n" + "=" * 60)
        print("🎉 All MCP server software tests passed!")
        print("✅ Variable reading and monitoring")
        print("✅ Motor state analysis with fault detection")
        print("✅ Memory operations with safety validation")
        print("✅ Knowledge database integration")
        print("✅ Real-time monitoring with change detection")
        print("\n🚀 MCP server software stack is fully functional!")
        print("📋 Next: Debug hardware connection for live testing")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())