"""Configuration management utilities."""

import json
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class HardwareConfig:
    debug_probe: str
    target_mcu: str
    usb_vendor_id: str
    usb_product_id: str
    firmware_min_version: str


@dataclass  
class OpenOCDConfig:
    executable: str
    config_file: str
    gdb_port: int
    tcl_port: int
    telnet_port: int
    max_connections: int
    log_level: str


@dataclass
class GDBConfig:
    host: str
    port: int
    timeout: float
    retry_attempts: int
    retry_delay: float


@dataclass
class Config:
    """Main configuration class."""
    hardware: HardwareConfig
    openocd: OpenOCDConfig
    gdb: GDBConfig
    target: Dict[str, Any]
    monitoring: Dict[str, Any]
    logging: Dict[str, Any]
    
    @classmethod
    def load(cls, config_path: Path) -> "Config":
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return cls(
            hardware=HardwareConfig(**data["hardware"]),
            openocd=OpenOCDConfig(**data["openocd"]),
            gdb=GDBConfig(**data["gdb"]),
            target=data["target"],
            monitoring=data["monitoring"],
            logging=data["logging"]
        )