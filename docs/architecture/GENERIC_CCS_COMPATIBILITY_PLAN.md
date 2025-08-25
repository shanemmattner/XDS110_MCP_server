# Generic CCS Project Compatibility Plan

## Current State: Project-Specific (Obake Motor Control)

### Hardcoded Elements Found (214+ occurrences):

#### 1. **Target Configuration**
- ❌ **Hardcoded**: `TMS320F280039C_LaunchPad.ccxml`
- ❌ **Hardcoded**: Target name `C28xx_CPU1`
- ❌ **Hardcoded**: MCU type `TMS320F280039C`

#### 2. **Firmware/Binary**
- ❌ **Hardcoded**: `obake_firmware.out`
- ❌ **Hardcoded**: Path `Flash_lib_DRV8323RH_3SC/`

#### 3. **Variable Names**
- ❌ **Hardcoded**: `motorVars_M1` structure
- ❌ **Hardcoded**: Motor-specific variables (angleENC_rad, absPosition_rad, etc.)
- ❌ **Hardcoded**: Memory address `0x0000d3c0` for debug_bypass

#### 4. **Domain Knowledge**
- ❌ **Hardcoded**: Motor control states (IDLE, ALIGNMENT, CTRL_RUN, CL_RUNNING)
- ❌ **Hardcoded**: Motor control concepts (FOC, encoder calibration, etc.)

## What Needs to Change for Generic CCS Support

### 1. Configuration-Driven Approach

Create a project configuration file:
```json
{
  "project_name": "generic_project",
  "target": {
    "ccxml_file": "path/to/target.ccxml",
    "cpu_name": "C28xx_CPU1",  // or "Cortex_M4", "MSP430", etc.
    "device": "TMS320F280039C"  // or any TI device
  },
  "firmware": {
    "binary_path": "path/to/firmware.out",
    "load_on_connect": true
  },
  "variables": [
    {
      "name": "myStruct.field1",
      "type": "float32",
      "description": "Custom variable"
    }
  ],
  "memory_regions": {
    "debug_area": "0x0000d3c0",
    "custom_region": "0x20000000"
  }
}
```

### 2. Generic Variable Discovery

Instead of hardcoding variable names:
```javascript
// Current (Obake-specific):
var value = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");

// Generic approach:
function readVariables(debugSession, variableList) {
    variableList.forEach(function(varName) {
        try {
            var value = debugSession.expression.evaluate(varName);
            print(varName + " = " + value);
        } catch (e) {
            // Variable doesn't exist
        }
    });
}
```

### 3. Symbol Table Reading

Add capability to read symbols from ELF file:
```javascript
// Read all available symbols from loaded binary
var symbols = debugSession.symbol.list();
// Or from ELF file analysis
var symbols = parseELF("firmware.out");
```

### 4. Generic JavaScript Templates

Create template scripts:
```javascript
// generic_read_variables.js
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);

function main() {
    // Load configuration
    var config = loadConfig("project_config.json");
    
    var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
    ds.setConfig(config.target.ccxml_file);
    
    var debugSession = ds.openSession("*", config.target.cpu_name);
    debugSession.target.connect();
    
    if (config.firmware.load_on_connect) {
        debugSession.memory.loadProgram(config.firmware.binary_path);
    }
    
    // Read configured variables
    config.variables.forEach(function(varDef) {
        try {
            var value = debugSession.expression.evaluate(varDef.name);
            print(varDef.name + " = " + value);
        } catch (e) {
            print(varDef.name + " not found");
        }
    });
}
```

### 5. MCP Server Modifications

#### Current Structure (Motor-Specific):
```
xds110_mcp_server/
├── knowledge/
│   └── motor_control.py  # Motor-specific domain knowledge
├── tools/
│   ├── variable_monitor.py  # Hardcoded motorVars_M1
│   └── memory_tools.py  # Hardcoded addresses
```

#### Generic Structure Needed:
```
xds110_mcp_server/
├── core/
│   ├── dss_interface.py  # Generic DSS wrapper
│   ├── symbol_reader.py  # ELF/symbol table parser
│   └── config_loader.py  # Project configuration
├── plugins/
│   ├── motor_control/  # Optional motor-specific plugin
│   ├── generic/  # Generic variable reader
│   └── custom/  # User-defined plugins
├── tools/
│   ├── variable_monitor.py  # Config-driven variables
│   └── memory_tools.py  # Config-driven addresses
```

## Implementation Steps for Generic Support

### Phase 1: Configuration System
1. Create JSON schema for project configuration
2. Add config loader to read project settings
3. Update all scripts to use configuration

### Phase 2: Generic DSS Interface
1. Create generic JavaScript templates
2. Remove hardcoded variable names
3. Add symbol discovery capability

### Phase 3: Plugin Architecture
1. Move motor-specific code to optional plugin
2. Create generic variable reading interface
3. Allow custom domain plugins

### Phase 4: Auto-Discovery
1. Implement ELF file parsing for symbol extraction
2. Add CCXML auto-detection from CCS workspace
3. Create project import wizard

## Example: Using with Different Projects

### Example 1: MSP430 Temperature Sensor
```json
{
  "project_name": "temp_sensor",
  "target": {
    "ccxml_file": "MSP430F5529.ccxml",
    "cpu_name": "MSP430",
    "device": "MSP430F5529"
  },
  "firmware": {
    "binary_path": "temp_sensor.out"
  },
  "variables": [
    "temperature_celsius",
    "adc_reading",
    "sensor_status"
  ]
}
```

### Example 2: ARM Cortex-M4 IoT Device
```json
{
  "project_name": "iot_device",
  "target": {
    "ccxml_file": "CC2642R1F.ccxml",
    "cpu_name": "Cortex_M4",
    "device": "CC2642R1F"
  },
  "firmware": {
    "binary_path": "iot_firmware.out"
  },
  "variables": [
    "wifi_status",
    "packet_count",
    "rssi_value"
  ]
}
```

## Backwards Compatibility

Keep motor control as a plugin:
```bash
# Generic usage
xds110-mcp --config my_project.json

# With motor control plugin
xds110-mcp --config my_project.json --plugin motor_control
```

## Estimated Effort

- **Configuration System**: 2-3 days
- **Generic DSS Interface**: 3-4 days
- **Plugin Architecture**: 4-5 days
- **Auto-Discovery**: 3-4 days
- **Testing & Documentation**: 2-3 days

**Total**: ~2-3 weeks for full generic support

## Recommendation

Currently, this tool is **NOT generic enough** for smooth use with any CCS project. To make it generic:

1. **Immediate fix** (1-2 days): Add configuration file support for CCXML and firmware paths
2. **Short-term** (1 week): Create generic variable reading scripts
3. **Long-term** (2-3 weeks): Full plugin architecture with auto-discovery

Without these changes, each new project requires:
- Manual script modification
- Hardcoding new variable names
- Creating project-specific JavaScript files
- Updating Python code with new structures

This is manageable for 2-3 projects but becomes unmaintainable beyond that.