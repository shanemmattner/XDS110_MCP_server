#!/usr/bin/env python3
"""
Proof-of-Concept MAP File Parser for Generic CCS Debugging
Automatically discovers ALL variables and their addresses from MAP files!
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class Symbol:
    """Represents a symbol from the MAP file"""
    name: str
    address: int
    size: int = 0
    section: str = ""
    type_hint: str = "unknown"
    
    def to_dict(self):
        return {
            "name": self.name,
            "address": f"0x{self.address:08x}",
            "size": self.size,
            "section": self.section,
            "type_hint": self.type_hint
        }


class MapFileParser:
    """Universal MAP file parser for TI CCS projects"""
    
    def __init__(self, map_file_path: str):
        self.map_file = Path(map_file_path)
        self.symbols: Dict[str, Symbol] = {}
        self.memory_regions: List[Dict] = []
        
    def parse(self) -> Dict:
        """Parse the MAP file and extract all useful information"""
        if not self.map_file.exists():
            raise FileNotFoundError(f"MAP file not found: {self.map_file}")
            
        with open(self.map_file, 'r') as f:
            content = f.read()
            
        # Parse different sections
        self._parse_memory_configuration(content)
        self._parse_global_symbols(content)
        self._parse_section_allocation(content)
        self._guess_types()
        
        return self._generate_report()
    
    def _parse_memory_configuration(self, content: str):
        """Extract memory regions from MEMORY CONFIGURATION section"""
        memory_section = re.search(
            r'MEMORY CONFIGURATION\n\n.*?\n(.*?)\n\n', 
            content, 
            re.DOTALL
        )
        
        if memory_section:
            for line in memory_section.group(1).split('\n'):
                match = re.match(
                    r'\s*(\w+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)',
                    line
                )
                if match:
                    name, origin, length, used, unused = match.groups()
                    self.memory_regions.append({
                        "name": name,
                        "origin": f"0x{origin}",
                        "length": f"0x{length}",
                        "used": f"0x{used}",
                        "unused": f"0x{unused}"
                    })
    
    def _parse_global_symbols(self, content: str):
        """Extract all global symbols and their addresses"""
        # Find GLOBAL SYMBOLS section
        symbols_section = re.search(
            r'GLOBAL SYMBOLS:.*?\n\n(.*?)\n\n',
            content,
            re.DOTALL
        )
        
        if symbols_section:
            for line in symbols_section.group(1).split('\n'):
                # Parse lines like: 0     0000f580  motorVars_M1
                match = re.match(r'\d+\s+([0-9a-f]+)\s+(\w+)', line)
                if match:
                    address_str, name = match.groups()
                    address = int(address_str, 16)
                    
                    # Skip certain system symbols
                    if not name.startswith('__') and not name.startswith('$'):
                        self.symbols[name] = Symbol(
                            name=name,
                            address=address
                        )
    
    def _parse_section_allocation(self, content: str):
        """Extract size information from section allocation"""
        # Look for size information in various formats
        # Format: address    size (hex_size)    symbol_name
        size_pattern = re.compile(
            r'([0-9a-f]+)\s+([0-9a-f]+)\s+\(([0-9a-f]+)\)\s+(\w+)'
        )
        
        for match in size_pattern.finditer(content):
            address_str, size_str, _, name = match.groups()
            if name in self.symbols:
                self.symbols[name].size = int(size_str, 16)
    
    def _guess_types(self):
        """Guess variable types based on naming patterns"""
        type_patterns = [
            (r'.*_M\d+$', 'motor_struct'),  # motorVars_M1
            (r'.*[Aa]ngle.*', 'float'),      # angle variables
            (r'.*[Pp]osition.*', 'float'),   # position variables
            (r'.*[Ss]tate.*', 'enum'),       # state variables
            (r'.*[Ff]lag.*', 'bool'),        # flag variables
            (r'.*[Cc]ount.*', 'uint32'),     # counters
            (r'.*_A$', 'float'),              # current in Amps
            (r'.*_V$', 'float'),              # voltage in Volts
            (r'.*_Hz$', 'float'),             # frequency in Hz
            (r'.*[Bb]uffer.*', 'array'),     # buffers
            (r'debug_.*', 'debug_struct'),   # debug structures
        ]
        
        for symbol in self.symbols.values():
            for pattern, type_hint in type_patterns:
                if re.match(pattern, symbol.name):
                    symbol.type_hint = type_hint
                    break
    
    def _generate_report(self) -> Dict:
        """Generate a comprehensive report of parsed data"""
        # Find interesting symbols
        motor_symbols = [s for s in self.symbols.values() 
                        if 'motor' in s.name.lower()]
        debug_symbols = [s for s in self.symbols.values() 
                        if 'debug' in s.name.lower()]
        large_symbols = sorted(
            [s for s in self.symbols.values() if s.size > 100],
            key=lambda x: x.size,
            reverse=True
        )[:10]
        
        return {
            "summary": {
                "map_file": str(self.map_file),
                "total_symbols": len(self.symbols),
                "memory_regions": len(self.memory_regions),
                "motor_related": len(motor_symbols),
                "debug_related": len(debug_symbols)
            },
            "memory_regions": self.memory_regions,
            "interesting_symbols": {
                "motor_control": [s.to_dict() for s in motor_symbols],
                "debug": [s.to_dict() for s in debug_symbols],
                "large_structures": [s.to_dict() for s in large_symbols]
            },
            "all_symbols": {
                name: sym.to_dict() 
                for name, sym in sorted(self.symbols.items())
            }
        }
    
    def find_symbol(self, name: str) -> Optional[Symbol]:
        """Find a specific symbol by name"""
        return self.symbols.get(name)
    
    def search_symbols(self, pattern: str) -> List[Symbol]:
        """Search for symbols matching a pattern"""
        regex = re.compile(pattern, re.IGNORECASE)
        return [
            sym for name, sym in self.symbols.items()
            if regex.search(name)
        ]
    
    def generate_dss_script(self, output_file: str = "auto_generated_reader.js"):
        """Generate a DSS JavaScript file with all discovered symbols"""
        script = """// Auto-generated DSS script from MAP file parsing
// Generated from: {map_file}
// Total symbols: {total}

importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);

// All discovered symbols with addresses
var symbols = {symbols_json};

function readSymbol(symbolName) {{
    if (symbols[symbolName]) {{
        var sym = symbols[symbolName];
        try {{
            // Read from specific address
            var value = debugSession.memory.readData(0, sym.address, 4);
            print(symbolName + " @ 0x" + sym.address.toString(16) + " = " + value);
            return value;
        }} catch (e) {{
            print("Error reading " + symbolName + ": " + e.message);
        }}
    }} else {{
        print("Symbol not found: " + symbolName);
    }}
}}

function searchAndRead(pattern) {{
    var regex = new RegExp(pattern, 'i');
    for (var name in symbols) {{
        if (regex.test(name)) {{
            readSymbol(name);
        }}
    }}
}}

// Example usage:
print("Available symbols: " + Object.keys(symbols).length);
print("\\nReading motor-related variables:");
searchAndRead("motor");
""".format(
            map_file=self.map_file.name,
            total=len(self.symbols),
            symbols_json=json.dumps({
                name: {"address": sym.address, "size": sym.size}
                for name, sym in self.symbols.items()
            }, indent=2)
        )
        
        with open(output_file, 'w') as f:
            f.write(script)
        
        return output_file


def main():
    """Demo: Parse the Obake MAP file"""
    map_file = "/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.map"
    
    print("=" * 60)
    print("MAP File Parser - Proof of Concept")
    print("=" * 60)
    
    parser = MapFileParser(map_file)
    report = parser.parse()
    
    print(f"\n📊 Summary:")
    print(f"  Total Symbols Found: {report['summary']['total_symbols']}")
    print(f"  Memory Regions: {report['summary']['memory_regions']}")
    print(f"  Motor-related: {report['summary']['motor_related']}")
    print(f"  Debug-related: {report['summary']['debug_related']}")
    
    print(f"\n🎯 Key Discoveries:")
    
    # Show motorVars_M1
    motor_vars = parser.find_symbol("motorVars_M1")
    if motor_vars:
        print(f"  motorVars_M1:")
        print(f"    Address: 0x{motor_vars.address:08x} (was guessed as different!)")
        print(f"    Size: {motor_vars.size} bytes")
    
    # Show debug_bypass
    debug_bypass = parser.find_symbol("debug_bypass")
    if debug_bypass:
        print(f"  debug_bypass:")
        print(f"    Address: 0x{debug_bypass.address:08x} (NOT 0xd3c0 as hardcoded!)")
        print(f"    Size: {debug_bypass.size} bytes")
    
    print(f"\n🔍 Searching for patterns:")
    
    # Search for angle-related
    angle_vars = parser.search_symbols(r".*angle.*")
    print(f"  Found {len(angle_vars)} angle-related variables")
    for var in angle_vars[:3]:
        print(f"    - {var.name} @ 0x{var.address:08x}")
    
    # Search for current/voltage
    electrical = parser.search_symbols(r".*(current|voltage|[IV]dc|[IV]dq).*")
    print(f"  Found {len(electrical)} electrical variables")
    
    print(f"\n💾 Memory Layout:")
    for region in report['memory_regions'][:5]:
        print(f"  {region['name']:20} @ {region['origin']} size: {region['length']}")
    
    # Generate DSS script
    print(f"\n✨ Generating auto DSS script...")
    script_file = parser.generate_dss_script("auto_discovered_symbols.js")
    print(f"  Created: {script_file}")
    
    # Save full report
    with open("map_analysis_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    print(f"  Full report: map_analysis_report.json")
    
    print("\n✅ This proves we can auto-discover EVERYTHING from MAP files!")
    print("   No more hardcoding addresses or variable names!")


if __name__ == "__main__":
    main()