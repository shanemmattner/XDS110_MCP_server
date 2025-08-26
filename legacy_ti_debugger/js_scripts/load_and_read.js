// Load firmware and then read variables
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    var debugSession = null;
    
    try {
        // Connect
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        print("Connected");
        
        // Load the firmware
        print("Loading firmware...");
        debugSession.memory.loadProgram("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out");
        print("Firmware loaded");
        
        // Run briefly then halt
        debugSession.target.runAsynch();
        java.lang.Thread.sleep(100);
        debugSession.target.halt();
        print("Target halted");
        
        // Now try to read motorVars_M1
        var args = arguments;
        for (var i = 0; i < args.length; i++) {
            var varName = args[i];
            try {
                var value = debugSession.expression.evaluate(varName);
                print("VAR_READ:" + varName + "=" + value);
            } catch (e) {
                print("VAR_ERROR:" + varName + "=" + e.message);
            }
        }
        
    } catch (e) {
        print("SCRIPT_ERROR:" + e.message);
    } finally {
        if (debugSession != null) {
            try {
                debugSession.target.disconnect();
                debugSession.terminate();
            } catch (e) {}
        }
    }
}

main.apply(this, arguments);