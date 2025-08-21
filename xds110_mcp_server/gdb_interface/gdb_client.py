"""GDB client for communicating with OpenOCD."""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Union
import json

from ..utils.config import GDBConfig


class GDBClient:
    """GDB client for embedded debugging via OpenOCD."""
    
    def __init__(self, config: GDBConfig):
        """Initialize GDB client.
        
        Args:
            config: GDB configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.sequence_num = 0
    
    async def connect(self) -> bool:
        """Connect to GDB server (OpenOCD).
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            if self.connected:
                self.logger.warning("Already connected to GDB server")
                return True
            
            for attempt in range(self.config.retry_attempts):
                try:
                    self.logger.info(f"Connecting to GDB server at {self.config.host}:{self.config.port} (attempt {attempt + 1})")
                    
                    self.reader, self.writer = await asyncio.wait_for(
                        asyncio.open_connection(self.config.host, self.config.port),
                        timeout=self.config.timeout
                    )
                    
                    # Test connection with a simple command
                    response = await self._send_command("info target")
                    if response is not None:
                        self.connected = True
                        self.logger.info("Connected to GDB server successfully")
                        return True
                    
                except (ConnectionRefusedError, asyncio.TimeoutError, OSError) as e:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay)
                    continue
            
            self.logger.error(f"Failed to connect after {self.config.retry_attempts} attempts")
            return False
            
        except Exception as e:
            self.logger.error(f"Error connecting to GDB server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from GDB server."""
        try:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
            
            self.reader = None
            self.writer = None
            self.connected = False
            self.logger.info("Disconnected from GDB server")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate that we can communicate with the target.
        
        Returns:
            True if target is accessible, False otherwise
        """
        try:
            if not self.connected:
                return False
            
            # Try to get target info
            response = await self._send_command("info target")
            if response is None:
                return False
            
            # Try to read a simple memory location
            response = await self._send_command("x/1wx 0x0")
            return response is not None
            
        except Exception as e:
            self.logger.error(f"Target validation error: {e}")
            return False
    
    async def read_variable(self, variable_name: str) -> Optional[Any]:
        """Read a variable value.
        
        Args:
            variable_name: Name of the variable to read
            
        Returns:
            Variable value or None if error
        """
        try:
            # Use GDB's print command
            response = await self._send_command(f"print {variable_name}")
            if response is None:
                return None
            
            # Parse the response to extract the value
            return self._parse_variable_value(response, variable_name)
            
        except Exception as e:
            self.logger.error(f"Error reading variable {variable_name}: {e}")
            return None
    
    async def read_multiple_variables(self, variable_names: List[str]) -> Dict[str, Any]:
        """Read multiple variables efficiently.
        
        Args:
            variable_names: List of variable names to read
            
        Returns:
            Dictionary of variable names to values
        """
        results = {}
        
        for var_name in variable_names:
            value = await self.read_variable(var_name)
            results[var_name] = value
        
        return results
    
    async def read_memory(self, address: str, size: int = 1, format: str = "x") -> Optional[List[int]]:
        """Read memory at specified address.
        
        Args:
            address: Memory address (hex string like "0x1000")
            size: Number of units to read
            format: GDB format (x=hex, d=decimal, u=unsigned, etc.)
            
        Returns:
            List of memory values or None if error
        """
        try:
            # Use GDB's examine command
            response = await self._send_command(f"x/{size}{format} {address}")
            if response is None:
                return None
            
            # Parse memory values from response
            return self._parse_memory_response(response)
            
        except Exception as e:
            self.logger.error(f"Error reading memory at {address}: {e}")
            return None
    
    async def write_memory(self, address: str, values: Union[int, List[int]], size: int = 1) -> bool:
        """Write values to memory.
        
        Args:
            address: Memory address (hex string)
            values: Value or list of values to write
            size: Size of each value in bytes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(values, int):
                values = [values]
            
            # Convert values to appropriate format based on size
            if size == 1:
                format_char = "c"
            elif size == 2:
                format_char = "h"  
            elif size == 4:
                format_char = "w"
            else:
                self.logger.error(f"Unsupported memory write size: {size}")
                return False
            
            success = True
            current_addr = int(address, 16)
            
            for value in values:
                cmd = f"set *({format_char} *){hex(current_addr)} = {value}"
                response = await self._send_command(cmd)
                if response is None:
                    success = False
                    break
                current_addr += size
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error writing memory at {address}: {e}")
            return False
    
    async def set_breakpoint(self, address: str, condition: Optional[str] = None) -> Optional[int]:
        """Set a breakpoint.
        
        Args:
            address: Address or function name
            condition: Optional condition for conditional breakpoint
            
        Returns:
            Breakpoint number or None if failed
        """
        try:
            if condition:
                cmd = f"break {address} if {condition}"
            else:
                cmd = f"break {address}"
            
            response = await self._send_command(cmd)
            if response is None:
                return None
            
            # Extract breakpoint number from response
            match = re.search(r'Breakpoint (\d+)', response)
            if match:
                return int(match.group(1))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error setting breakpoint at {address}: {e}")
            return None
    
    async def remove_breakpoint(self, breakpoint_num: int) -> bool:
        """Remove a breakpoint.
        
        Args:
            breakpoint_num: Breakpoint number to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self._send_command(f"delete {breakpoint_num}")
            return response is not None
            
        except Exception as e:
            self.logger.error(f"Error removing breakpoint {breakpoint_num}: {e}")
            return False
    
    async def continue_execution(self) -> bool:
        """Continue target execution.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = await self._send_command("continue")
            return response is not None
            
        except Exception as e:
            self.logger.error(f"Error continuing execution: {e}")
            return False
    
    async def halt_execution(self) -> bool:
        """Halt target execution.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Send Ctrl+C to interrupt
            if self.writer:
                self.writer.write(b'\x03')
                await self.writer.drain()
                
                # Wait for response
                await asyncio.sleep(0.1)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error halting execution: {e}")
            return False
    
    async def _send_command(self, command: str) -> Optional[str]:
        """Send a command to GDB and get response.
        
        Args:
            command: GDB command to send
            
        Returns:
            Response string or None if error
        """
        try:
            if not self.connected or not self.writer:
                self.logger.error("Not connected to GDB server")
                return None
            
            # Send command
            full_command = f"{command}\n"
            self.writer.write(full_command.encode())
            await self.writer.drain()
            
            # Read response with timeout
            response = await asyncio.wait_for(
                self._read_response(), 
                timeout=self.config.timeout
            )
            
            return response
            
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout waiting for response to: {command}")
            return None
        except Exception as e:
            self.logger.error(f"Error sending command '{command}': {e}")
            return None
    
    async def _read_response(self) -> str:
        """Read response from GDB server.
        
        Returns:
            Response string
        """
        if not self.reader:
            raise RuntimeError("No reader available")
        
        response_lines = []
        
        while True:
            line = await self.reader.readline()
            if not line:
                break
            
            line = line.decode().strip()
            if line == "(gdb)":  # GDB prompt indicates end of response
                break
            
            if line:  # Skip empty lines
                response_lines.append(line)
        
        return "\n".join(response_lines)
    
    def _parse_variable_value(self, response: str, variable_name: str) -> Any:
        """Parse variable value from GDB response.
        
        Args:
            response: GDB response string
            variable_name: Variable name for context
            
        Returns:
            Parsed value
        """
        try:
            # Look for patterns like "$1 = 42" or "$1 = 3.14"
            match = re.search(r'\$\d+\s*=\s*(.+)', response)
            if not match:
                return None
            
            value_str = match.group(1).strip()
            
            # Try to parse as number
            try:
                if '.' in value_str:
                    return float(value_str)
                else:
                    return int(value_str, 0)  # Auto-detect base
            except ValueError:
                # Return as string if not a number
                return value_str.strip('"\'')
                
        except Exception as e:
            self.logger.error(f"Error parsing value for {variable_name}: {e}")
            return None
    
    def _parse_memory_response(self, response: str) -> List[int]:
        """Parse memory values from GDB examine response.
        
        Args:
            response: GDB examine response
            
        Returns:
            List of integer values
        """
        values = []
        
        try:
            # Look for hex patterns like "0x1234" 
            hex_pattern = r'0x([0-9a-fA-F]+)'
            matches = re.findall(hex_pattern, response)
            
            for match in matches:
                values.append(int(match, 16))
                
        except Exception as e:
            self.logger.error(f"Error parsing memory response: {e}")
        
        return values