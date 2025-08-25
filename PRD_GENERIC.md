# Product Requirements Document
## XDS110 Universal Debugger - Generic CCS Project Debugging Solution

**Version:** 2.0  
**Date:** 2025-08-25  
**Status:** Architecture Redesign Complete

---

## 1. Executive Summary

The XDS110 Universal Debugger is a revolutionary zero-configuration debugging solution that works with ANY Texas Instruments Code Composer Studio project. By automatically parsing MAP files to discover all project symbols and their memory addresses, it eliminates the traditional need for project-specific configuration while providing access to thousands of variables through intelligent pattern-based search and real-time monitoring.

### Paradigm Shift
**From:** Hardcoded, project-specific debugging tools  
**To:** Universal, auto-discovering debugging interface

---

## 2. Problem Statement

### Current State Problems

1. **Manual Configuration Hell**
   - Each new project requires hours of setup
   - Variables must be manually identified and hardcoded
   - Memory addresses must be looked up and maintained
   - Scripts must be rewritten for each project

2. **Limited Variable Access**
   - Typically only 20-50 hardcoded variables accessible
   - Missing variables require code changes and recompilation
   - No way to explore unknown variables

3. **Project Lock-in**
   - Debugging tools are project-specific
   - Cannot easily switch between projects
   - Knowledge doesn't transfer between projects

4. **Discovery Limitations**
   - No way to know what variables exist
   - Cannot search for variables by pattern
   - Memory layout is opaque

### Specific Technical Challenges

- **Symbol Discovery**: MAP files contain all symbols but are never utilized
- **Address Resolution**: Hardcoded addresses often wrong (e.g., debug_bypass at 0xf2a2, not 0xd3c0)
- **Type Information**: Variable types must be manually specified
- **Scalability**: Current approach doesn't scale beyond 2-3 projects

---

## 3. Solution: Universal Auto-Discovery

### Core Innovation: MAP File Mining

```
Traditional Approach:          Universal Approach:
┌──────────────┐              ┌──────────────┐
│ Hardcode     │              │ Point to     │
│ Variables    │              │ Project Dir  │
└──────┬───────┘              └──────┬───────┘
       │                              │
       ▼                              ▼
┌──────────────┐              ┌──────────────┐
│ Edit Scripts │              │ Parse MAP    │
│ for Project  │              │ Automatically│
└──────┬───────┘              └──────┬───────┘
       │                              │
       ▼                              ▼
┌──────────────┐              ┌──────────────┐
│ Access ~20   │              │ Access 1000+ │
│ Variables    │              │ Variables    │
└──────────────┘              └──────────────┘
```

### Technical Architecture

#### 3.1 MAP File Parser
```python
class UniversalMapParser:
    """Extracts ALL symbols from any TI linker MAP file"""
    
    def parse(map_file) -> SymbolDatabase:
        - Extract global symbols with addresses
        - Parse memory regions and layout
        - Identify structure sizes
        - Build searchable database
        return {
            "motorVars_M1": {"address": 0xf580, "size": 982},
            "debug_bypass": {"address": 0xf2a2, "size": 970},
            # ... 1000+ more symbols
        }
```

#### 3.2 Pattern-Based Discovery
```python
def search_variables(pattern: str) -> List[Variable]:
    """Find variables using regex patterns"""
    
    # Examples:
    search(".*motor.*")     # Find all motor-related
    search(".*angle.*")     # Find all angle variables
    search(".*[IV]dc.*")    # Find voltage/current
    search(".*state.*")     # Find state machines
```

#### 3.3 Auto-Generated Access Scripts
```javascript
// Automatically generated from MAP parsing
var symbols = {
    "motorVars_M1": {"address": 0x0000f580, "size": 982},
    "debug_bypass": {"address": 0x0000f2a2, "size": 970},
    // ... all other symbols
};

function readAnyVariable(name) {
    return debugSession.memory.read(symbols[name].address);
}
```

---

## 4. User Requirements

### 4.1 Functional Requirements

#### Zero Configuration Setup
- **FR-1**: System SHALL auto-discover project files (.ccxml, .out, .map)
- **FR-2**: System SHALL work with ANY CCS project without modification
- **FR-3**: System SHALL complete setup in < 60 seconds

#### Variable Discovery
- **FR-4**: System SHALL discover 100% of symbols from MAP file
- **FR-5**: System SHALL support regex pattern searching
- **FR-6**: System SHALL show memory addresses for all symbols
- **FR-7**: System SHALL indicate symbol sizes when available

#### Real-Time Monitoring
- **FR-8**: System SHALL read any discovered variable
- **FR-9**: System SHALL support concurrent monitoring of multiple variables
- **FR-10**: System SHALL highlight value changes
- **FR-11**: System SHALL achieve ≥10Hz update rate

#### Universal Compatibility
- **FR-12**: System SHALL support all TI MCU families (C2000, MSP430, ARM)
- **FR-13**: System SHALL work with any MAP file format (TI, IAR, GCC)
- **FR-14**: System SHALL handle projects with 10-10,000 symbols

### 4.2 Non-Functional Requirements

#### Performance
- **NFR-1**: Symbol discovery SHALL complete in < 5 seconds for 5000 symbols
- **NFR-2**: Pattern search SHALL return results in < 100ms
- **NFR-3**: Variable read latency SHALL be < 50ms

#### Usability
- **NFR-4**: No manual configuration files required
- **NFR-5**: Single command to start debugging
- **NFR-6**: Intuitive pattern matching syntax

#### Reliability
- **NFR-7**: Graceful handling of missing MAP files
- **NFR-8**: Accurate address resolution (100% from MAP)
- **NFR-9**: Connection recovery after disconnect

---

## 5. User Scenarios

### Scenario 1: New Project Setup
```bash
$ xds110-debug init ~/my_new_project/

[Automatic Discovery]
✓ Found: TMS320F280039C.ccxml
✓ Found: firmware.out (247 KB)
✓ Found: firmware.map (1,847 symbols)
✓ Ready to debug!

Time: 3 seconds (vs 2+ hours traditional)
```

### Scenario 2: Finding Unknown Variables
```bash
$ xds110-debug search ".*temper.*"

Found 5 temperature-related variables:
- temperature_celsius @ 0x2000 (float)
- temperature_raw @ 0x2004 (uint16)
- temperature_offset @ 0x2006 (int16)
- overtemperature_flag @ 0x2008 (bool)
- max_temperature_limit @ 0x200A (float)
```

### Scenario 3: Cross-Project Debugging
```bash
# Project A - Motor Control
$ xds110-debug quickstart ~/motor_project/
✓ 982 motor control variables available

# Project B - Sensor Network (different project!)
$ xds110-debug quickstart ~/sensor_project/
✓ 427 sensor variables available

# No reconfiguration needed!
```

---

## 6. Technical Specifications

### 6.1 MAP File Parsing

#### Input Format Support
- TI CCS Linker MAP files
- IAR Linker MAP files  
- GCC Linker MAP files
- Keil MDK MAP files

#### Extraction Capabilities
```
GLOBAL SYMBOLS section → Symbol names and addresses
SECTION ALLOCATION     → Symbol sizes
MEMORY CONFIGURATION   → Memory layout
```

### 6.2 Symbol Database Schema
```json
{
  "symbols": {
    "symbol_name": {
      "address": "0x0000f580",
      "size": 982,
      "section": ".ebss",
      "type_hint": "struct",
      "discovered_from": "MAP",
      "members": []  // Future: from DWARF
    }
  },
  "memory_regions": [...],
  "metadata": {
    "total_symbols": 1847,
    "map_file": "firmware.map",
    "parse_time_ms": 234
  }
}
```

### 6.3 Pattern Matching Engine

Supports full PCRE regex:
- `.*motor.*` - Contains "motor"
- `^uart_` - Starts with "uart_"  
- `.*_[IV]$` - Ends with _I or _V
- `(adc|dac)_.*` - ADC or DAC variables

---

## 7. Success Metrics

### Adoption Metrics
- **Time to First Debug**: < 60 seconds (vs hours)
- **Variables Accessible**: 1000+ (vs ~20)
- **Projects Supported**: ANY CCS project (vs single project)

### Technical Metrics
- **Symbol Discovery Rate**: 100% from MAP
- **Address Accuracy**: 100% (no guessing)
- **Setup Commands**: 1 (vs dozens)

### User Satisfaction
- **Configuration Required**: ZERO
- **Learning Curve**: < 5 minutes
- **Cross-Project Reuse**: 100%

---

## 8. Implementation Roadmap

### Phase 1: Core MAP Parser (Week 1)
- [x] MAP file parser implementation
- [x] Symbol database creation
- [x] Pattern search engine
- [x] Basic CLI interface

### Phase 2: DSS Integration (Week 2)
- [ ] Generic DSS script generation
- [ ] Auto-discovery of project files
- [ ] Real-time variable monitoring
- [ ] Connection management

### Phase 3: Advanced Features (Week 3)
- [ ] ELF/DWARF parser for types
- [ ] Web UI for visualization
- [ ] Export capabilities (CSV, JSON)
- [ ] Plugin architecture

### Phase 4: Production Ready (Week 4)
- [ ] Error handling and recovery
- [ ] Performance optimization
- [ ] Documentation completion
- [ ] Release packaging

---

## 9. Competitive Analysis

| Feature | Traditional Debugging | XDS110 Universal |
|---------|---------------------|------------------|
| Setup Time | Hours | Seconds |
| Configuration | Manual | Automatic |
| Variables | ~20 hardcoded | 1000+ discovered |
| Project Support | Single | Universal |
| Address Accuracy | Often wrong | 100% from MAP |
| Search | Not available | Pattern-based |
| Maintenance | High | Zero |

---

## 10. Risks and Mitigations

### Technical Risks
1. **MAP Format Changes**
   - Mitigation: Modular parser with format detection
   
2. **Large Symbol Count Performance**
   - Mitigation: Indexed database with caching

3. **Type Information Missing**
   - Mitigation: ELF/DWARF parser for complete types

### Adoption Risks
1. **User Skepticism** 
   - Mitigation: Live demos showing instant setup
   
2. **Legacy Tool Attachment**
   - Mitigation: Compatibility mode for gradual migration

---

## 11. Conclusion

The XDS110 Universal Debugger represents a paradigm shift in embedded debugging, moving from manual, project-specific configuration to automatic, universal discovery. By leveraging the untapped goldmine of MAP files, we can provide access to ALL project variables with zero configuration, making debugging accessible, efficient, and scalable across any number of projects.

**The future of debugging is universal, not project-specific.**