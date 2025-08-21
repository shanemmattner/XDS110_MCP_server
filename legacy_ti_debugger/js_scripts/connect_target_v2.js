// DSS script based on TI documentation examples
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== TI DSS Connection Script v2 ===");
    
    var debugSession = null;
    
    try {
        // Get the Debug Server
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        
        // Set the configuration file
        print("Setting CCXML configuration...");
        ds.setConfig("TMS320F280039C_LaunchPad.ccxml");
        
        // Try different session opening approaches
        print("Attempting to open session...");
        
        // Method 1: Try specific CPU name
        try {
            debugSession = ds.openSession("*", "C28xx_CPU1");
            print("Opened session with C28xx_CPU1");
        } catch (e) {
            print("Failed to open with C28xx_CPU1: " + e.message);
            
            // Method 2: Try wildcard only
            try {
                debugSession = ds.openSession("*");
                print("Opened session with wildcard");
            } catch (e2) {
                print("Failed to open with wildcard: " + e2.message);
                
                // Method 3: Try specific target name from CCXML
                try {
                    debugSession = ds.openSession("Texas Instruments XDS110 USB Debug Probe_0/TMS320F280039C_0");
                    print("Opened session with full path");
                } catch (e3) {
                    print("Failed to open with full path: " + e3.message);
                    throw new Error("Could not open any session");
                }
            }
        }
        
        // Connect to target - this is critical!
        print("Connecting to target...");
        debugSession.target.connect();
        print("Connected successfully!");
        
        // Check target status
        if (debugSession.target.isConnected()) {
            print("Target is connected");
            
            if (debugSession.target.isRunning()) {
                print("Target is running - halting...");
                debugSession.target.halt();
            } else {
                print("Target is halted");
            }
            
            // Try to read a simple register
            try {
                var pc = debugSession.memory.readRegister("PC");
                print("Program Counter: 0x" + pc.toString(16));
            } catch (e) {
                print("Could not read PC register: " + e.message);
            }
            
        } else {
            print("Target connection failed!");
        }
        
    } catch (e) {
        print("Error: " + e.message);
        if (e.javaException) {
            e.javaException.printStackTrace();
        }
    } finally {
        if (debugSession != null) {
            try {
                debugSession.target.disconnect();
                debugSession.terminate();
                print("Session terminated");
            } catch (e) {
                print("Error during cleanup: " + e.message);
            }
        }
    }
}

main();