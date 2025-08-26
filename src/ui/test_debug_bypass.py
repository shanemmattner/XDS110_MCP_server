#!/usr/bin/env python3
"""
Test debug_bypass struct specifically
Examine the structure and try to read its fields
"""

import subprocess
from pathlib import Path
import json

def test_debug_bypass_struct():
    """Test reading debug_bypass struct and its fields"""
    
    print("Debug Bypass Struct Testing")
    print("==========================")
    
    # File paths
    obake_dir = Path.home() / "Desktop/skip_repos/skip/robot/core/embedded/firmware/obake"
    ccxml_path = obake_dir / "TMS320F280039C_LaunchPad.ccxml"
    binary_path = obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.out"
    
    # Get debug_bypass address from MAP file
    from xds110_dash_connector import XDS110Interface
    xds = XDS110Interface()
    symbols = xds.load_map_file(str(obake_dir / "Flash_lib_DRV8323RH_3SC/obake_firmware.map"))
    
    debug_bypass_addr = symbols.get('debug_bypass')
    if not debug_bypass_addr:
        print("❌ debug_bypass not found in MAP file")
        return
    
    print(f"debug_bypass address: 0x{debug_bypass_addr:08x}")
    
    # Create comprehensive DSS script to examine debug_bypass
    js_script = f"""
// Debug Bypass Structure Analysis
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {{
    print("=== Debug Bypass Structure Test ===");
    
    try {{
        // Connect to target
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("{ccxml_path}");
        
        var debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        debugSession.memory.loadProgram("{binary_path}");
        
        // Initialize target
        debugSession.target.runAsynch();
        Thread.sleep(2000);
        debugSession.target.halt();
        
        print("Target initialized successfully");
        
        // Test debug_bypass structure
        var base_addr = 0x{debug_bypass_addr:08X};
        print("DEBUG_BYPASS_BASE:0x" + base_addr.toString(16));
        
        // Try different approaches to read debug_bypass
        
        // Method 1: Direct expression
        try {{
            var bypass_value = debugSession.expression.evaluate("debug_bypass");
            print("EXPRESSION_SUCCESS:debug_bypass=" + bypass_value);
        }} catch (e) {{
            print("EXPRESSION_FAILED:debug_bypass:" + e.message);
        }}
        
        // Method 2: Read raw memory (32-bit words)
        print("MEMORY_DUMP_START");
        for (var i = 0; i < 16; i++) {{  // Read 16 words (64 bytes)
            try {{
                var addr = base_addr + (i * 4);
                var value = debugSession.memory.readData(0, addr, 32);
                print("MEM:0x" + addr.toString(16) + "=" + value);
            }} catch (e) {{
                print("MEM_FAILED:0x" + (base_addr + i*4).toString(16) + ":" + e.message);
            }}
        }}
        print("MEMORY_DUMP_END");
        
        // Method 3: Try to read as bytes
        print("BYTE_DUMP_START");
        try {{
            for (var i = 0; i < 64; i++) {{  // Read 64 bytes
                var addr = base_addr + i;
                var value = debugSession.memory.readData(0, addr, 8);  // 8-bit read
                print("BYTE:0x" + addr.toString(16) + "=" + value);
            }}
        }} catch (e) {{
            print("BYTE_READ_FAILED:" + e.message);
        }}
        print("BYTE_DUMP_END");
        
        // Method 4: Try to examine type information
        try {{
            var typeInfo = debugSession.symbol.getAddress("debug_bypass");
            print("SYMBOL_INFO:" + typeInfo);
        }} catch (e) {{
            print("SYMBOL_INFO_FAILED:" + e.message);
        }}
        
        // Method 5: Look for related symbols
        print("RELATED_SYMBOLS_START");
        try {{
            var symbols = ["debug_bypass_process", "motorVars_M1", "motorHandle_M1"];
            for (var s in symbols) {{
                var symbol = symbols[s];
                try {{
                    var value = debugSession.expression.evaluate(symbol);
                    print("RELATED:" + symbol + "=" + value);
                }} catch (e) {{
                    print("RELATED_FAILED:" + symbol + ":" + e.message);
                }}
            }}
        }} catch (e) {{
            print("RELATED_SYMBOLS_FAILED:" + e.message);
        }}
        print("RELATED_SYMBOLS_END");
        
        print("ANALYSIS_COMPLETE");
        
    }} catch (error) {{
        print("MAIN_ERROR:" + error.message);
        if (error.javaException) {{
            print("JAVA_EXCEPTION:" + error.javaException);
        }}
    }}
}}

main();
"""
    
    # Save and execute script
    script_path = Path("/tmp/test_debug_bypass.js")
    script_path.write_text(js_script)
    
    print(f"Executing DSS script: {script_path}")
    
    try:
        dss_path = Path("/opt/ti/ccs1240/ccs/ccs_base/scripting/bin/dss.sh")
        result = subprocess.run(
            [str(dss_path), str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("\nDSS Output:")
        print("-" * 40)
        
        # Parse and organize output
        memory_values = {}
        related_symbols = {}
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            
            if line.startswith("DEBUG_BYPASS_BASE:"):
                addr = line.split(':')[1]
                print(f"Base Address: {addr}")
                
            elif line.startswith("EXPRESSION_SUCCESS:"):
                expr = line[19:]  # Remove prefix
                print(f"✅ Expression: {expr}")
                
            elif line.startswith("EXPRESSION_FAILED:"):
                error = line[18:]
                print(f"❌ Expression failed: {error}")
                
            elif line.startswith("MEM:"):
                # Format: MEM:0xaddress=value
                parts = line[4:].split('=')
                if len(parts) == 2:
                    addr, value = parts
                    memory_values[addr] = value
                    print(f"Memory {addr} = {value}")
                    
            elif line.startswith("RELATED:"):
                # Format: RELATED:symbol=value
                parts = line[8:].split('=', 1)
                if len(parts) == 2:
                    symbol, value = parts
                    related_symbols[symbol] = value
                    print(f"✅ Related: {symbol} = {value}")
                    
            elif line.startswith("RELATED_FAILED:"):
                error = line[15:]
                print(f"❌ Related failed: {error}")
                
            elif "ERROR" in line or "FAILED" in line:
                print(f"❌ {line}")
            elif line.startswith("SUCCESS") or "successful" in line.lower():
                print(f"✅ {line}")
            elif line.strip() and not line.startswith(("MEMORY_", "BYTE_", "RELATED_")):
                print(f"ℹ️  {line}")
        
        # Show stderr if any
        if result.stderr:
            print(f"\nDSS Stderr:")
            print("-" * 40)
            for line in result.stderr.split('\n'):
                if line.strip() and "SLF4J" not in line:
                    print(f"⚠️  {line}")
        
        # Summary
        print(f"\nSummary:")
        print(f"Memory locations read: {len(memory_values)}")
        print(f"Related symbols found: {len(related_symbols)}")
        
        return {
            'memory_values': memory_values,
            'related_symbols': related_symbols,
            'base_address': f"0x{debug_bypass_addr:08x}"
        }
        
    except subprocess.TimeoutExpired:
        print("❌ DSS script timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return None

if __name__ == "__main__":
    test_debug_bypass_struct()