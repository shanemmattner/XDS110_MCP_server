// Simple script to detect if XDS110 probe is connected

importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);

function main() {
    print("=== Detecting Debug Probe ===");
    
    try {
        var debugServer = ScriptingEnvironment.instance().getServer("DebugServer.1");
        
        print("Setting CCXML configuration...");
        debugServer.setConfig("TMS320F280039C_LaunchPad.ccxml");
        
        print("Available sessions:");
        var sessions = debugServer.listSessions();
        for (var i = 0; i < sessions.length; i++) {
            print("Session " + i + ": " + sessions[i]);
        }
        
    } catch (e) {
        print("Error: " + e.message);
    }
}

main();