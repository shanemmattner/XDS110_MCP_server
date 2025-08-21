"""XDS110 MCP Server - LLM Co-Debugger for TI Embedded Systems."""

__version__ = "0.1.0"
__author__ = "XDS110 MCP Server Contributors"
__description__ = "MCP server for TI embedded systems debugging via XDS110"

from .server import XDS110MCPServer

__all__ = ["XDS110MCPServer"]


def main():
    """Main entry point for the XDS110 MCP server."""
    import asyncio
    import argparse
    import sys
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="XDS110 MCP Server")
    parser.add_argument(
        "--config", 
        type=Path,
        default="configs/f28039_config.json",
        help="Configuration file path"
    )
    parser.add_argument(
        "--debug",
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if not args.config.exists():
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Create and run server
    server = XDS110MCPServer(config_path=args.config, debug=args.debug)
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()