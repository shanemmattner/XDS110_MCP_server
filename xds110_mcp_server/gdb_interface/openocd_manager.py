"""OpenOCD process management and control."""

import asyncio
import logging
import subprocess
import signal
from pathlib import Path
from typing import Optional, Dict, Any
import time

from ..utils.config import OpenOCDConfig


class OpenOCDManager:
    """Manages OpenOCD process for XDS110 debugging."""
    
    def __init__(self, config: OpenOCDConfig):
        """Initialize OpenOCD manager.
        
        Args:
            config: OpenOCD configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        
    async def start(self) -> bool:
        """Start OpenOCD process.
        
        Returns:
            True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                self.logger.warning("OpenOCD already running")
                return True
            
            # Check if OpenOCD executable exists
            if not Path(self.config.executable).exists():
                self.logger.error(f"OpenOCD executable not found: {self.config.executable}")
                return False
            
            # Check if config file exists
            config_path = Path(self.config.config_file)
            if not config_path.exists():
                self.logger.error(f"OpenOCD config file not found: {config_path}")
                return False
            
            # Build command
            cmd = [
                self.config.executable,
                "-f", str(config_path),
                "-c", f"gdb_port {self.config.gdb_port}",
                "-c", f"tcl_port {self.config.tcl_port}",
                "-c", f"telnet_port {self.config.telnet_port}",
                # gdb_max_connections is not supported in OpenOCD 0.12
                # "-c", f"gdb_max_connections {self.config.max_connections}",
            ]
            
            self.logger.info(f"Starting OpenOCD: {' '.join(cmd)}")
            
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                preexec_fn=None if hasattr(signal, 'SIGTERM') else None
            )
            
            # Wait a moment for startup
            await asyncio.sleep(2.0)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                self.logger.error(f"OpenOCD failed to start:")
                self.logger.error(f"stdout: {stdout}")
                self.logger.error(f"stderr: {stderr}")
                return False
            
            # Test connection by checking if ports are accessible
            if not await self._test_ports():
                self.logger.error("OpenOCD ports not accessible after startup")
                await self.stop()
                return False
            
            self.is_running = True
            self.logger.info("OpenOCD started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start OpenOCD: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop OpenOCD process.
        
        Returns:
            True if stopped successfully, False otherwise  
        """
        try:
            if not self.is_running or self.process is None:
                self.logger.info("OpenOCD not running")
                return True
            
            self.logger.info("Stopping OpenOCD...")
            
            # Try graceful shutdown first
            self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    asyncio.create_task(self._wait_for_process()), 
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("OpenOCD didn't stop gracefully, killing...")
                self.process.kill()
                await asyncio.create_task(self._wait_for_process())
            
            self.process = None
            self.is_running = False
            self.logger.info("OpenOCD stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping OpenOCD: {e}")
            return False
    
    async def restart(self) -> bool:
        """Restart OpenOCD process.
        
        Returns:
            True if restarted successfully, False otherwise
        """
        self.logger.info("Restarting OpenOCD...")
        await self.stop()
        await asyncio.sleep(1.0)
        return await self.start()
    
    async def is_healthy(self) -> bool:
        """Check if OpenOCD is running and healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.is_running or self.process is None:
            return False
        
        # Check if process is still alive
        if self.process.poll() is not None:
            self.logger.warning("OpenOCD process died")
            self.is_running = False
            return False
        
        # Check if ports are still accessible
        return await self._test_ports()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get OpenOCD status information.
        
        Returns:
            Status dictionary
        """
        status = {
            "running": self.is_running,
            "process_alive": self.process is not None and self.process.poll() is None,
            "gdb_port": self.config.gdb_port,
            "tcl_port": self.config.tcl_port,
            "telnet_port": self.config.telnet_port,
            "max_connections": self.config.max_connections
        }
        
        if self.is_running:
            status["healthy"] = await self.is_healthy()
            status["ports_accessible"] = await self._test_ports()
        
        return status
    
    async def _test_ports(self) -> bool:
        """Test if OpenOCD ports are accessible.
        
        Returns:
            True if ports are accessible, False otherwise
        """
        try:
            # Test GDB port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('localhost', self.config.gdb_port),
                timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            return True
            
        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            return False
        except Exception as e:
            self.logger.debug(f"Port test error: {e}")
            return False
    
    async def _wait_for_process(self):
        """Wait for process to exit (async version of process.wait())."""
        if self.process is None:
            return
        
        while self.process.poll() is None:
            await asyncio.sleep(0.1)
    
    def __del__(self):
        """Cleanup on destruction."""
        if self.process is not None:
            try:
                self.process.terminate()
            except:
                pass