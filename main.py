#!/usr/bin/env python3
"""Main entry point for XDS110 MCP Server."""

import asyncio
import sys
from pathlib import Path
import argparse

from xds110_mcp_server.server import XDS110MCPServer


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="XDS110 MCP Server - LLM Co-Debugger for TI Embedded Systems")
    parser.add_argument(
        "--config", 
        type=Path, 
        default=Path("configs/f28039_config.json"),
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Validate config file exists
    if not args.config.exists():
        print(f"Error: Configuration file not found: {args.config}")
        print(f"Available configs:")
        config_dir = Path("configs")
        if config_dir.exists():
            for config_file in config_dir.glob("*.json"):
                print(f"  {config_file}")
        sys.exit(1)
    
    try:
        # Create and run the server
        server = XDS110MCPServer(args.config, debug=args.debug)
        await server.run()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())