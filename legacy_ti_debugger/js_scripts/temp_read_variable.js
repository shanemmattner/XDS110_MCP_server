// Auto-generated DSS script for variable reading
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    var debugSession = null;
    var results = {};
    
    try {
        // Connect to target
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Load firmware if needed
        try {
            debugSession.memory.loadProgram("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out");
        } catch (e) {
            // Firmware may already be loaded
        }
        
        // Halt target for reading
        try {
            debugSession.target.halt();
        } catch (e) {
            // Target may already be halted
        }
        
        // Read requested variables

        try {
            var value = debugSession.expression.evaluate("motorVars_M1.motorState");
            print("VAR_READ:motorVars_M1.motorState=" + value);
        } catch (e) {
            print("VAR_ERROR:motorVars_M1.motorState=" + e.message);
        }

    } catch (e) {
        print("SCRIPT_ERROR:" + e.message);
    } finally {
        if (debugSession != null) {
            try {
                debugSession.target.disconnect();
                debugSession.terminate();
            } catch (e) {
                // Ignore cleanup errors
            }
        }
    }
}

main();
