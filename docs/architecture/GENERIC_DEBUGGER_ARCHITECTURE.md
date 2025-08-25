# Generic CCS Debugger Architecture - Creative Solution

## 🎯 Core Insight: Use MAP + ELF Files for Complete Auto-Discovery!

### The MAP File Gold Mine
From analyzing `obake_firmware.map`, we found:
- **debug_bypass at 0x0000f2a2** (not 0xd3c0 as hardcoded!)
- **motorVars_M1 at 0x0000f580**
- Complete symbol table with addresses and sizes
- Memory layout and regions

## 🚀 Creative Generic Architecture

### 1. Project Wizard (Zero Configuration!)
```bash
xds110-mcp init /path/to/your/CCS/project/
```

This automatically:
1. Finds `.ccxml` file in project
2. Locates `.out` and `.map` files
3. Parses MAP for all symbols
4. Extracts debug info from ELF
5. Creates project profile

### 2. Smart Variable Discovery System

#### A. MAP File Parser
```python
class MapFileParser:
    def parse(self, map_file):
        symbols = {}
        # Extract from GLOBAL SYMBOLS section
        # Example: 0000f580  motorVars_M1
        for line in map_content:
            if match := re.match(r'([0-9a-f]+)\s+(\w+)\s+(\w+)', line):
                address, size, name = match.groups()
                symbols[name] = {
                    'address': int(address, 16),
                    'size': int(size, 16) if size else 0,
                    'type': 'unknown'  # Will enhance from ELF
                }
        return symbols
```

#### B. ELF DWARF Parser (for types)
```python
class ElfDebugParser:
    def extract_types(self, elf_file):
        # Use pyelftools to read DWARF debug info
        # Gets structure definitions, member offsets, types
        return type_info
```

#### C. Live Symbol Browser
```javascript
// Auto-generated from MAP parsing
var symbols = {
    "motorVars_M1": {"address": 0x0000f580, "type": "struct", "size": 982},
    "debug_bypass": {"address": 0x0000f2a2, "type": "struct", "size": 60},
    // ... hundreds more auto-discovered
};

// Browse and read ANY symbol
function browseSymbols(pattern) {
    return Object.keys(symbols).filter(s => s.match(pattern));
}
```

### 3. Interactive Variable Explorer

#### Web-Based UI (Optional)
```python
from flask import Flask, jsonify
import dash
import plotly

class VariableExplorer:
    def __init__(self, project):
        self.symbols = MapFileParser().parse(project.map_file)
        
    def search(self, pattern):
        # Fuzzy search through thousands of symbols
        return fuzzy_match(pattern, self.symbols)
    
    def watch(self, symbol_names):
        # Real-time monitoring of selected symbols
        return self.dss.read_continuous(symbol_names)
```

### 4. Pattern-Based Variable Discovery

#### Smart Patterns
```yaml
# patterns.yaml - Reusable across projects
motor_control:
  - pattern: ".*motor.*|.*angle.*|.*position.*"
    category: "Motor Variables"
  
sensor_data:
  - pattern: ".*adc.*|.*sensor.*|.*temp.*"
    category: "Sensor Readings"

control_loops:
  - pattern: ".*pid.*|.*controller.*|.*feedback.*"
    category: "Control Systems"

communication:
  - pattern: ".*uart.*|.*spi.*|.*i2c.*|.*can.*"
    category: "Communication"
```

### 5. Dynamic Type Reconstruction

```python
class TypeReconstructor:
    def analyze_memory_pattern(self, address, size):
        # Read memory and guess type based on patterns
        data = read_memory(address, size)
        
        if all(0 <= b <= 127 for b in data):
            return "likely_string"
        elif size == 4:
            as_float = struct.unpack('f', data)[0]
            if -1000 < as_float < 1000:
                return "likely_float"
        elif size % 4 == 0:
            return "likely_struct"
```

### 6. Project Profiles (Shareable!)

```json
{
  "project": {
    "name": "obake_motor_control",
    "device": "TMS320F280039C",
    "auto_discovered": {
      "ccxml": "TMS320F280039C_LaunchPad.ccxml",
      "binary": "obake_firmware.out",
      "map_file": "obake_firmware.map",
      "symbols_count": 1847
    }
  },
  "watched_variables": [
    {
      "name": "motorVars_M1",
      "address": "0x0000f580",
      "type": "struct",
      "interesting_members": [
        ".absPosition_rad",
        ".motorState",
        ".angleENC_rad"
      ]
    }
  ],
  "memory_regions": [
    {"name": "RAMM0S", "start": "0x00000128", "size": "0x000002d8"},
    {"name": "FLASH", "start": "0x00080000", "size": "0x00010000"}
  ]
}
```

### 7. AI-Assisted Variable Discovery

```python
class AIVariableAnalyzer:
    def suggest_interesting_variables(self, symbols, project_type):
        # Use LLM to analyze symbol names and suggest what to monitor
        prompt = f"""
        Project type: {project_type}
        Available symbols: {symbols[:100]}
        
        Suggest the most important variables to monitor.
        """
        return llm.complete(prompt)
```

## 🛠️ Implementation: Complete Generic Tool

### Phase 1: Core Infrastructure (Week 1)
```python
# map_parser.py
class UniversalMapParser:
    """Parses TI, IAR, GCC, and Keil MAP formats"""
    
    def auto_detect_format(self, map_file):
        # Detect linker type from file header
        pass
    
    def extract_all_symbols(self):
        # Returns dict: name -> {address, size, section}
        pass

# elf_analyzer.py  
class ElfTypeExtractor:
    """Extracts type info from ELF DWARF sections"""
    
    def get_struct_layout(self, struct_name):
        # Returns member offsets and types
        pass

# project_scanner.py
class ProjectAutoSetup:
    """Scans CCS project and sets up everything"""
    
    def scan_project(self, project_path):
        # Finds all relevant files
        # Creates initial configuration
        pass
```

### Phase 2: Dynamic DSS Interface (Week 2)
```javascript
// generic_reader.js
function readAnyVariable(symbolName, address, type) {
    // No hardcoding - everything from config
    var value = debugSession.memory.readAddress(address, type.size);
    return parseByType(value, type);
}

// variable_browser.js
function findVariablesMatching(pattern) {
    // Search through ALL symbols from MAP
    return symbols.filter(s => s.name.match(pattern));
}
```

### Phase 3: Interactive Tools (Week 3)
```python
# CLI Interface
$ xds110-mcp explore
> search motor
Found 47 matches:
  motorVars_M1 (struct, 982 bytes) @ 0x0000f580
  motorVars_M1.motorState (uint16) @ 0x0000f580
  motorVars_M1.absPosition_rad (float) @ 0x0000f584
  ...
> watch motorVars_M1.absPosition_rad
Watching motorVars_M1.absPosition_rad...
  0.000s: 5.000 rad
  0.100s: 5.001 rad
  0.200s: 5.002 rad  [CHANGED]

# Web Interface
$ xds110-mcp serve --port 8080
Starting web interface at http://localhost:8080
```

## 🎮 Usage Examples

### Example 1: Any CCS Project (Zero Config)
```bash
# Just point at your project
$ xds110-mcp init ~/my_ccs_workspace/MyProject/
Found: MSP430F5529.ccxml
Found: my_project.out (247 KB)
Found: my_project.map (1,234 symbols)
Analyzing... Done!

$ xds110-mcp connect
Connected to MSP430F5529
1,234 variables available

$ xds110-mcp watch "temperature|humidity"
Watching 3 variables:
  temperature_celsius: 23.5°C
  humidity_percent: 45.2%
  temp_sensor_status: 0x01 (OK)
```

### Example 2: Pattern Discovery
```bash
$ xds110-mcp discover --patterns communication
Found communication-related variables:
  uart_tx_buffer[64] @ 0x2000
  uart_rx_count @ 0x2040
  spi_data_reg @ 0x4000
  i2c_slave_addr @ 0x4100
```

### Example 3: Memory Map Visualization
```bash
$ xds110-mcp memmap --visual
Memory Layout for TMS320F280039C:
[======FLASH======][==RAM==][PERIPHERALS][  UNUSED  ]
0x80000          0xC000  0x4000       0x48000
```

## 🚀 Key Advantages

1. **Zero Manual Configuration** - Everything auto-discovered
2. **Works with ANY CCS Project** - Not limited to motor control
3. **No Code Changes Required** - Just point at existing project
4. **Shareable Profiles** - Export/import project setups
5. **Type-Aware** - Understands structures from debug info
6. **Pattern-Based** - Find variables by category
7. **Real-Time Explorer** - Browse variables while running

## 📊 Comparison

| Feature | Current (Hardcoded) | New (Generic) |
|---------|-------------------|---------------|
| Setup Time | Hours per project | Seconds |
| Variables | ~20 hardcoded | 1000+ auto-discovered |
| Project Types | Motor control only | ANY CCS project |
| Configuration | Edit source code | None required |
| Symbol Discovery | Manual | Automatic from MAP |
| Type Information | Hardcoded | From ELF DWARF |
| Memory Layout | Guessed | Exact from MAP |

## 🎯 The Secret Sauce

The MAP file contains EVERYTHING we need:
- All symbol addresses (no more guessing!)
- Actual memory layout
- Function locations
- Variable sizes
- Section allocations

Combined with ELF DWARF debug info:
- Complete type definitions
- Structure member offsets
- Array dimensions
- Typedef expansions

This means we can debug ANY project without writing a single line of project-specific code!

## Next Steps

1. Build MAP file parser (2 days)
2. Create symbol database (1 day)
3. Generic DSS scripts (2 days)
4. Interactive explorer (3 days)
5. Pattern matching engine (1 day)
6. Web UI (optional, 3 days)

**Total: ~2 weeks for complete generic solution**

The best part? Once built, it works for EVERY CCS project ever created!