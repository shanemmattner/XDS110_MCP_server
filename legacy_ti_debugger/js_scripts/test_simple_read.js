// Simple test script to read basic memory
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Simple Memory Test ===");
    
    var debugSession = null;
    
    try {
        // Connect
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        print("Connected to target");
        
        // Try to read a simple memory location
        try {
            // Read from data RAM at 0x0000C000 (a safe location)
            var value = debugSession.memory.readWord(0, 0x0000C000);
            print("SUCCESS: Memory at 0xC000 = " + value);
        } catch (e) {
            print("ERROR: Cannot read memory - " + e.message);
        }
        
        // Try to read program counter
        try {
            var pc = debugSession.expression.evaluate("PC");
            print("SUCCESS: PC = " + pc);
        } catch (e) {
            print("ERROR: Cannot read PC - " + e.message);
        }
        
        print("=== Test Complete ===");
        
    } catch (e) {
        print("Connection Error: " + e.message);
    } finally {
        if (debugSession != null) {
            try {
                debugSession.target.disconnect();
                debugSession.terminate();
            } catch (e) {}
        }
    }
}

main();