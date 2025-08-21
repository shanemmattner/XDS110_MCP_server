"""Main XDS110 MCP Server implementation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ListResourcesResult,
    ListToolsResult,
    CallToolResult,
    ReadResourceResult,
)

from .gdb_interface.gdb_client import GDBClient
from .gdb_interface.openocd_manager import OpenOCDManager
from .knowledge.motor_control import MotorControlKnowledge
from .tools.variable_monitor import VariableMonitorTool
from .tools.memory_tools import MemoryTool
from .tools.analysis_tools import AnalysisTool
from .utils.config import Config
from .utils.logging import setup_logging


class XDS110MCPServer:
    """Main MCP server for XDS110 debugging."""
    
    def __init__(self, config_path: Path, debug: bool = False):
        """Initialize the XDS110 MCP server.
        
        Args:
            config_path: Path to configuration file
            debug: Enable debug logging
        """
        self.config = Config.load(config_path)
        self.debug = debug
        self.logger = setup_logging(debug)
        
        # Core components
        self.openocd_manager = OpenOCDManager(self.config.openocd)
        self.gdb_client = GDBClient(self.config.gdb)
        self.knowledge = MotorControlKnowledge()
        
        # MCP Tools
        self.variable_monitor = VariableMonitorTool(self.gdb_client, self.knowledge)
        self.memory_tool = MemoryTool(self.gdb_client, self.knowledge)
        self.analysis_tool = AnalysisTool(self.gdb_client, self.knowledge)
        
        # MCP Server
        self.server = Server("xds110-mcp-server")
        self._setup_handlers()
        
        self.logger.info("XDS110 MCP Server initialized")
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            """List available resources."""
            resources = [
                Resource(
                    uri="motor://variables",
                    name="Motor Control Variables",
                    description="Available motor control variables for monitoring"
                ),
                Resource(
                    uri="memory://layout", 
                    name="Memory Layout",
                    description="Target memory layout and structure definitions"
                ),
                Resource(
                    uri="knowledge://motor_control",
                    name="Motor Control Knowledge", 
                    description="Domain knowledge for motor control debugging"
                ),
            ]
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Read a specific resource."""
            if uri == "motor://variables":
                variables = await self.knowledge.get_available_variables()
                content = json.dumps(variables, indent=2)
            elif uri == "memory://layout":
                layout = await self.knowledge.get_memory_layout()
                content = json.dumps(layout, indent=2)
            elif uri == "knowledge://motor_control":
                knowledge = await self.knowledge.get_motor_control_info()
                content = json.dumps(knowledge, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")
            
            return ReadResourceResult(
                contents=[TextContent(type="text", text=content)]
            )
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available MCP tools."""
            tools = [
                Tool(
                    name="read_variables",
                    description="Read current values of motor control variables",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "variables": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of variable names to read"
                            },
                            "format": {
                                "type": "string", 
                                "enum": ["json", "table"],
                                "default": "json",
                                "description": "Output format"
                            }
                        },
                        "required": ["variables"]
                    }
                ),
                Tool(
                    name="monitor_variables",
                    description="Start continuous monitoring with change detection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "variables": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Variables to monitor"
                            },
                            "duration": {
                                "type": "number",
                                "default": 10.0,
                                "description": "Monitoring duration in seconds"
                            },
                            "threshold": {
                                "type": "number", 
                                "default": 0.01,
                                "description": "Change detection threshold"
                            }
                        },
                        "required": ["variables"]
                    }
                ),
                Tool(
                    name="write_memory",
                    description="Write values to memory addresses",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "Memory address (hex format)"
                            },
                            "value": {
                                "type": ["number", "array"],
                                "description": "Value(s) to write"
                            },
                            "size": {
                                "type": "integer",
                                "default": 1,
                                "description": "Size in bytes"
                            }
                        },
                        "required": ["address", "value"]
                    }
                ),
                Tool(
                    name="analyze_motor_state",
                    description="Analyze current motor control state",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "focus_area": {
                                "type": "string",
                                "enum": ["alignment", "current_control", "position", "faults"],
                                "description": "Area to focus analysis on"
                            }
                        }
                    }
                ),
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "read_variables":
                    result = await self.variable_monitor.read_variables(
                        variables=arguments["variables"],
                        format=arguments.get("format", "json")
                    )
                elif name == "monitor_variables":
                    result = await self.variable_monitor.monitor_variables(
                        variables=arguments["variables"],
                        duration=arguments.get("duration", 10.0),
                        threshold=arguments.get("threshold", 0.01)
                    )
                elif name == "write_memory":
                    result = await self.memory_tool.write_memory(
                        address=arguments["address"],
                        value=arguments["value"], 
                        size=arguments.get("size", 1)
                    )
                elif name == "analyze_motor_state":
                    result = await self.analysis_tool.analyze_motor_state(
                        focus_area=arguments.get("focus_area")
                    )
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(
                    content=[TextContent(type="text", text=str(result))]
                )
                
            except Exception as e:
                self.logger.error(f"Tool call error ({name}): {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {e}")],
                    isError=True
                )
    
    async def initialize_hardware(self) -> bool:
        """Initialize hardware connections."""
        try:
            # Start OpenOCD
            self.logger.info("Starting OpenOCD...")
            if not await self.openocd_manager.start():
                self.logger.error("Failed to start OpenOCD")
                return False
            
            # Connect GDB client
            self.logger.info("Connecting GDB client...")
            if not await self.gdb_client.connect():
                self.logger.error("Failed to connect GDB client")
                return False
            
            # Validate target connection
            self.logger.info("Validating target connection...")
            if not await self.gdb_client.validate_connection():
                self.logger.error("Target validation failed")
                return False
            
            self.logger.info("Hardware initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Hardware initialization error: {e}")
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up XDS110 MCP Server...")
        
        try:
            if hasattr(self, 'gdb_client'):
                await self.gdb_client.disconnect()
            
            if hasattr(self, 'openocd_manager'):
                await self.openocd_manager.stop()
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
        
        self.logger.info("Cleanup complete")
    
    async def run(self):
        """Run the MCP server."""
        try:
            # Initialize hardware
            if not await self.initialize_hardware():
                raise RuntimeError("Hardware initialization failed")
            
            # Run MCP server
            self.logger.info("Starting MCP server...")
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, write_stream,
                    InitializationOptions(
                        server_name="xds110-mcp-server",
                        server_version="0.1.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        
        except Exception as e:
            self.logger.error(f"Server run error: {e}")
            raise
        
        finally:
            await self.cleanup()