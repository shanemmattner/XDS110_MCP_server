"""Memory manipulation tools for MCP server."""

import json
import logging
from typing import Dict, List, Any, Union, Optional

from ..gdb_interface.gdb_client import GDBClient
from ..knowledge.motor_control import MotorControlKnowledge


class MemoryTool:
    """Tool for memory read/write operations."""
    
    def __init__(self, gdb_client: GDBClient, knowledge: Optional[MotorControlKnowledge] = None):
        """Initialize memory tool.
        
        Args:
            gdb_client: GDB client for communication
            knowledge: Domain knowledge database
        """
        self.gdb_client = gdb_client
        self.knowledge = knowledge or MotorControlKnowledge()
        self.logger = logging.getLogger(__name__)
        
        # Known safe memory regions (from legacy ti_debugger)
        self.safe_memory_regions = {
            "debug_bypass": {
                "base_address": 0x0000d3c0,
                "size": 68,
                "description": "Debug bypass structure for motor control"
            }
        }
    
    async def write_memory(self, address: str, value: Union[int, List[int]], size: int = 1) -> str:
        """Write values to memory address.
        
        Args:
            address: Memory address (hex string like "0x1000")
            value: Value or list of values to write  
            size: Size of each value in bytes (1, 2, or 4)
            
        Returns:
            JSON result of write operation
        """
        try:
            # Parse address
            addr_int = int(address, 16)
            
            # Safety check
            if not self._is_safe_address(addr_int, size):
                return json.dumps({
                    "success": False,
                    "error": f"Address {address} is not in safe memory region",
                    "safe_regions": list(self.safe_memory_regions.keys())
                })
            
            # Convert single value to list
            if isinstance(value, int):
                values = [value]
            else:
                values = value
            
            self.logger.info(f"Writing {len(values)} values to {address} (size={size})")
            
            # Perform write
            success = await self.gdb_client.write_memory(address, values, size)
            
            if success:
                # Verify write by reading back
                read_values = await self.gdb_client.read_memory(address, len(values), "x")
                
                result = {
                    "success": True,
                    "address": address,
                    "values_written": values,
                    "size_bytes": size,
                    "verification": {
                        "read_back_values": read_values,
                        "verified": read_values == values if read_values else False
                    }
                }
            else:
                result = {
                    "success": False,
                    "error": "GDB write command failed",
                    "address": address,
                    "attempted_values": values
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error writing memory at {address}: {e}")
            return json.dumps({
                "success": False, 
                "error": str(e),
                "address": address
            })
    
    async def read_memory(self, address: str, size: int = 1, count: int = 1, format: str = "hex") -> str:
        """Read memory at specified address.
        
        Args:
            address: Memory address (hex string)
            size: Size of each unit in bytes (1, 2, or 4)
            count: Number of units to read
            format: Output format ("hex", "decimal", "binary")
            
        Returns:
            JSON result of read operation
        """
        try:
            self.logger.info(f"Reading {count} units of size {size} from {address}")
            
            # Read memory
            values = await self.gdb_client.read_memory(address, count, "x")
            
            if values is not None:
                result = {
                    "success": True,
                    "address": address,
                    "size_bytes": size,
                    "count": count,
                    "values": self._format_values(values, format),
                    "raw_values": values
                }
                
                # Add interpretation if this is a known structure
                interpretation = await self._interpret_memory_region(address, values)
                if interpretation:
                    result["interpretation"] = interpretation
            else:
                result = {
                    "success": False,
                    "error": "Failed to read memory",
                    "address": address
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error reading memory at {address}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "address": address
            })
    
    async def write_debug_bypass_field(self, field_name: str, value: Union[int, float]) -> str:
        """Write to specific debug_bypass structure field.
        
        Args:
            field_name: Field name (e.g., "debug_enabled", "command.cmd", "command.pos")
            value: Value to write
            
        Returns:
            JSON result of write operation
        """
        try:
            # Get field information
            field_info = await self._get_debug_bypass_field_info(field_name)
            if not field_info:
                return json.dumps({
                    "success": False,
                    "error": f"Unknown debug_bypass field: {field_name}",
                    "available_fields": await self._get_debug_bypass_fields()
                })
            
            # Calculate address
            base_addr = 0x0000d3c0
            field_addr = base_addr + field_info["offset"]
            
            # Handle value encoding
            encoded_value = self._encode_field_value(value, field_info)
            
            self.logger.info(f"Writing {field_name} = {value} (encoded: {encoded_value}) to {hex(field_addr)}")
            
            # Write the value
            success = await self.gdb_client.write_memory(
                hex(field_addr), 
                encoded_value, 
                field_info["size"]
            )
            
            if success:
                # Read back for verification
                read_back = await self.gdb_client.read_memory(hex(field_addr), 1, "x")
                
                result = {
                    "success": True,
                    "field": field_name,
                    "value": value,
                    "encoded_value": encoded_value,
                    "address": hex(field_addr),
                    "size_bytes": field_info["size"],
                    "verification": {
                        "read_back": read_back[0] if read_back else None,
                        "verified": read_back[0] == encoded_value[0] if read_back and encoded_value else False
                    }
                }
            else:
                result = {
                    "success": False,
                    "error": "Write operation failed",
                    "field": field_name,
                    "address": hex(field_addr)
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error writing debug_bypass field {field_name}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "field": field_name
            })
    
    def _is_safe_address(self, address: int, size: int) -> bool:
        """Check if address is in a safe memory region.
        
        Args:
            address: Memory address as integer
            size: Size of write operation
            
        Returns:
            True if address is safe to write
        """
        for region_name, region in self.safe_memory_regions.items():
            start = region["base_address"]
            end = start + region["size"]
            
            if start <= address < end and (address + size) <= end:
                return True
        
        return False
    
    def _format_values(self, values: List[int], format: str) -> List[str]:
        """Format values according to specified format.
        
        Args:
            values: List of integer values
            format: Format type ("hex", "decimal", "binary")
            
        Returns:
            List of formatted value strings
        """
        if format == "hex":
            return [f"0x{val:x}" for val in values]
        elif format == "decimal":
            return [str(val) for val in values]
        elif format == "binary":
            return [f"0b{val:b}" for val in values]
        else:
            return [f"0x{val:x}" for val in values]  # Default to hex
    
    async def _interpret_memory_region(self, address: str, values: List[int]) -> Dict[str, Any]:
        """Interpret memory values if in a known structure.
        
        Args:
            address: Memory address
            values: Raw values read
            
        Returns:
            Interpretation dictionary or None
        """
        try:
            addr_int = int(address, 16)
            
            # Check if this is debug_bypass structure
            if addr_int >= 0x0000d3c0 and addr_int < 0x0000d3c0 + 68:
                offset = addr_int - 0x0000d3c0
                
                interpretation = {
                    "structure": "debug_bypass",
                    "base_address": "0x0000d3c0",
                    "offset": offset
                }
                
                # Add field-specific interpretation
                if offset == 0:  # debug_enabled
                    interpretation["field"] = "debug_enabled"
                    interpretation["meaning"] = "Debug bypass enabled" if values[0] else "Debug bypass disabled"
                elif offset == 2:  # command.cmd
                    interpretation["field"] = "command.cmd"
                    interpretation["command_type"] = self.knowledge.get_command_description(values[0])
                
                return interpretation
                
        except:
            pass
        
        return None
    
    
    async def _get_debug_bypass_field_info(self, field_name: str) -> Dict[str, Any]:
        """Get field information for debug_bypass structure.
        
        Args:
            field_name: Field name
            
        Returns:
            Field information dictionary or None
        """
        # Field layout from legacy ti_debugger (proven working)
        field_layout = {
            "debug_enabled": {"offset": 0, "size": 1, "type": "bool"},
            "command.cmd": {"offset": 2, "size": 1, "type": "uint8_t"},
            "command.pos": {"offset": 3, "size": 2, "type": "int16_t", "scale": 1000, "endian": "little"},
            "command.max_current_ma": {"offset": 5, "size": 2, "type": "uint16_t", "endian": "little"},
            "command.kp": {"offset": 7, "size": 2, "type": "int16_t", "scale": 100, "endian": "little"},
            "command.ki": {"offset": 9, "size": 2, "type": "int16_t", "scale": 1000, "endian": "little"},
            "command.kd": {"offset": 11, "size": 2, "type": "int16_t", "scale": 1000, "endian": "little"}
        }
        
        return field_layout.get(field_name)
    
    async def _get_debug_bypass_fields(self) -> List[str]:
        """Get list of available debug_bypass fields.
        
        Returns:
            List of field names
        """
        field_info = await self._get_debug_bypass_field_info("")  # Get all fields
        return [
            "debug_enabled", "command.cmd", "command.pos", 
            "command.max_current_ma", "command.kp", "command.ki", "command.kd"
        ]
    
    def _encode_field_value(self, value: Union[int, float], field_info: Dict[str, Any]) -> List[int]:
        """Encode value according to field specifications.
        
        Args:
            value: Raw value to encode
            field_info: Field information dictionary
            
        Returns:
            List of encoded bytes
        """
        try:
            # Apply scaling if specified
            if "scale" in field_info:
                scaled_value = int(value * field_info["scale"])
            else:
                scaled_value = int(value)
            
            # Handle different sizes
            if field_info["size"] == 1:
                return [scaled_value & 0xFF]
            elif field_info["size"] == 2:
                # Little endian encoding for 16-bit values
                if field_info.get("endian") == "little":
                    return [scaled_value & 0xFF, (scaled_value >> 8) & 0xFF]
                else:
                    return [(scaled_value >> 8) & 0xFF, scaled_value & 0xFF]
            else:
                return [scaled_value & 0xFF]  # Default to single byte
                
        except Exception as e:
            self.logger.error(f"Error encoding value {value}: {e}")
            return [0]