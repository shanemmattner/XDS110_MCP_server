// Fast variable reading script for API
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    var debugSession = null;
    
    try {
        // Connect quickly
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Always try to load firmware (it's fast if already loaded)
        try {
            debugSession.memory.loadProgram("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out");
            // Run the firmware briefly to initialize variables
            debugSession.target.runAsynch();
            java.lang.Thread.sleep(200);
            debugSession.target.halt();
        } catch (e) {
            // Firmware may already be loaded - try to halt anyway
            try {
                debugSession.target.halt();
            } catch (e2) {}
        }
        
        // Read variables passed as arguments
        var args = arguments;
        for (var i = 0; i < args.length; i++) {
            var varName = args[i];
            if (varName == "--load-firmware") continue; // Skip flag if present
            try {
                var value = debugSession.expression.evaluate(varName);
                // Force more precision for floating point values
                if (value.toString().indexOf('.') !== -1 || varName.indexOf('Position') !== -1 || varName.indexOf('angle') !== -1) {
                    // For position/angle values, print with more precision
                    print("VAR_READ:" + varName + "=" + java.text.DecimalFormat("0.######").format(value));
                } else {
                    print("VAR_READ:" + varName + "=" + value);
                }
            } catch (e) {
                // Try reading as memory address if variable fails
                try {
                    if (varName.startsWith("0x")) {
                        var addr = parseInt(varName, 16);
                        var memValue = debugSession.memory.readWord(0, addr);
                        print("VAR_READ:" + varName + "=" + memValue);
                    } else {
                        print("VAR_ERROR:" + varName + "=" + e.message);
                    }
                } catch (e2) {
                    print("VAR_ERROR:" + varName + "=" + e.message);
                }
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

// Call main with command line arguments
main.apply(this, arguments);