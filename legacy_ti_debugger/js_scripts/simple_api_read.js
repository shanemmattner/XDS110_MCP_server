// Simplified API read script - no firmware loading
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    var debugSession = null;
    
    try {
        // Quick connect
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Halt target
        try {
            debugSession.target.halt();
        } catch (e) {}
        
        // Read arguments
        var args = arguments;
        for (var i = 0; i < args.length; i++) {
            var varName = args[i];
            try {
                // Try as variable first
                var value = debugSession.expression.evaluate(varName);
                print("VAR_READ:" + varName + "=" + value);
            } catch (e) {
                // Try as memory address
                try {
                    if (varName.startsWith("0x") || varName.startsWith("0X")) {
                        var addr = parseInt(varName, 16);
                        var memValue = debugSession.memory.readWord(0, addr);
                        print("VAR_READ:" + varName + "=" + memValue);
                    } else {
                        print("VAR_ERROR:" + varName + "=Not found");
                    }
                } catch (e2) {
                    print("VAR_ERROR:" + varName + "=Error");
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

main.apply(this, arguments);