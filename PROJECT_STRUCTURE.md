# Project Structure

```
XDS110_MCP_server/
│
├── 📄 README.md                    # Main project documentation
├── 📄 PRD_GENERIC.md              # Product Requirements (Generic Architecture)
├── 📄 PRD.md                      # Product Requirements (Original/Legacy)
├── 📄 CLAUDE.md                   # AI Assistant Instructions
├── 📄 LICENSE                     # MIT License
├── 📄 requirements.txt            # Python dependencies
├── 📄 pyproject.toml             # Project configuration
│
├── 📁 src/                        # Source code
│   ├── 📁 generic/               # Generic debugger implementation
│   │   ├── map_parser_poc.py    # MAP file parser
│   │   └── xds110_generic_cli.py # Generic CLI interface
│   │
│   └── 📁 examples/              # Example files
│       ├── generic_project_config.yaml
│       ├── auto_discovered_symbols.js
│       └── map_analysis_report.json
│
├── 📁 xds110_mcp_server/          # MCP Server Implementation
│   ├── __init__.py
│   ├── server.py                 # Main MCP server
│   │
│   ├── 📁 gdb_interface/         # GDB/OpenOCD interface (legacy)
│   │   ├── gdb_client.py
│   │   └── openocd_manager.py
│   │
│   ├── 📁 knowledge/             # Domain knowledge
│   │   └── motor_control.py     # Motor control expertise
│   │
│   ├── 📁 tools/                 # MCP tools
│   │   ├── analysis_tools.py
│   │   ├── memory_tools.py
│   │   └── variable_monitor.py
│   │
│   └── 📁 utils/                 # Utilities
│       ├── config.py
│       └── logging.py
│
├── 📁 legacy_ti_debugger/         # TI DSS Implementation (Working!)
│   ├── TMS320F280039C_LaunchPad.ccxml
│   ├── 📁 Flash_lib_DRV8323RH_3SC/
│   │   └── obake_firmware.out   # Motor control firmware
│   │
│   ├── 📁 js_scripts/            # DSS JavaScript scripts
│   │   ├── connect_target_v2.js # Connection script
│   │   ├── read_sensors.js      # Sensor reading
│   │   ├── monitor_encoder.js   # Encoder monitoring
│   │   ├── check_init_state.js  # ✅ Gets non-zero values!
│   │   └── find_nonzero_values.js
│   │
│   └── 📁 framework/             # Python DSS wrapper
│       └── ti_dss_adapter.py
│
├── 📁 configs/                    # Configuration files
│   ├── f28039_config.json       # Target config
│   ├── motor_variables.json     # Variable definitions
│   └── xds110_f28039.cfg       # OpenOCD config (doesn't work)
│
├── 📁 docs/                       # Documentation
│   ├── README.md                 # Documentation index
│   │
│   ├── 📁 guides/                # User guides
│   │   ├── QUICK_REFERENCE.md
│   │   ├── DEBUGGING_SETUP_GUIDE.md
│   │   └── SUCCESS_PROCESS_DOCUMENTATION.md
│   │
│   ├── 📁 architecture/          # Architecture docs
│   │   ├── GENERIC_DEBUGGER_ARCHITECTURE.md
│   │   └── GENERIC_CCS_COMPATIBILITY_PLAN.md
│   │
│   └── 📁 legacy/                # Historical docs
│       ├── PROJECT_STATUS.md
│       └── TESTING_RESULTS.md
│
├── 📁 tests/                      # Test files
│   ├── test_mcp_server.py
│   ├── test_basic.py
│   └── test_knowledge_only.py
│
└── 📁 scripts/                    # Utility scripts
    └── (empty - for future tools)
```

## Key Directories Explained

### `/src/generic/` 🌟 NEW!
The future of the project - generic debugging tools that work with ANY CCS project:
- `map_parser_poc.py` - Parses MAP files to discover all symbols
- `xds110_generic_cli.py` - Zero-config CLI interface

### `/legacy_ti_debugger/` ✅ WORKING!
Contains the WORKING TI DSS implementation:
- Successfully connects via XDS110
- Reads real values (found 5 radians in encoder!)
- JavaScript scripts that actually work with C2000

### `/xds110_mcp_server/` 🚧 IN PROGRESS
MCP protocol server implementation:
- Currently hardcoded for motor control
- Needs refactoring to use generic approach
- OpenOCD doesn't work with C2000!

### `/docs/` 📚
Complete documentation:
- `guides/` - How to use the system
- `architecture/` - System design and future plans
- `legacy/` - Historical development docs

## Important Files

### Critical Discoveries
- `docs/guides/SUCCESS_PROCESS_DOCUMENTATION.md` - How we got non-zero readings!
- `docs/architecture/GENERIC_DEBUGGER_ARCHITECTURE.md` - The universal solution

### Working Scripts
- `legacy_ti_debugger/js_scripts/check_init_state.js` - ✅ Reads real values!
- `src/generic/map_parser_poc.py` - Discovers 1000+ variables automatically

## Next Steps for Contributors

1. **Integrate MAP parser** with MCP server
2. **Replace hardcoded variables** with auto-discovered ones
3. **Create web UI** for variable exploration
4. **Add ELF parser** for type information
5. **Build plugin system** for domain-specific tools

## Quick Start for New Contributors

```bash
# See the generic approach in action
python src/generic/map_parser_poc.py

# Try the CLI demo
python src/generic/xds110_generic_cli.py demo

# Read the success story
cat docs/guides/SUCCESS_PROCESS_DOCUMENTATION.md
```