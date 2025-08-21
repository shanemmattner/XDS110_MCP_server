// Load firmware and read motor variables

importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Load Firmware and Debug Motor Variables ===");
    
    var debugSession = null;
    
    try {
        // Create debug server
        var debugServer = ScriptingEnvironment.instance().getServer("DebugServer.1");
        debugServer.setConfig("TMS320F280039C_LaunchPad.ccxml");
        
        // Open session
        print("Opening debug session...");
        debugSession = debugServer.openSession("*");
        
        // Connect to target
        print("Connecting to target...");
        debugSession.target.connect();
        
        // Reset target
        print("Resetting target...");
        debugSession.target.reset();
        
        // Load firmware
        print("Loading firmware...");
        var firmwarePath = "Flash_lib_DRV8323RH_3SC/obake_firmware.out";
        debugSession.memory.loadProgram(firmwarePath);
        
        // Run for a short time to let initialization happen
        print("Running target to initialize...");
        debugSession.target.run();
        
        // Wait a bit for initialization
        java.lang.Thread.sleep(2000);
        
        // Halt to read variables
        print("Halting target...");
        debugSession.target.halt();
        
        print("=== Reading Motor Variables ===");
        
        // Try to read some basic variables
        var basicVars = [
            "motorVars_M1",
            "debug_bypass"
        ];
        
        for (var i = 0; i < basicVars.length; i++) {
            try {
                var varName = basicVars[i];
                var addr = debugSession.symbol.getAddress(varName);
                print(varName + " address: 0x" + addr.toString(16));
            } catch (e) {
                print("Could not find symbol " + basicVars[i]);
            }
        }
        
        // Try to read specific motor control variables
        var motorVars = [
            "motorVars_M1.angleFOC_rad",
            "motorVars_M1.angleENC_rad",
            "motorVars_M1.motorState"
        ];
        
        for (var i = 0; i < motorVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(motorVars[i]);
                print(motorVars[i] + " = " + value);
            } catch (e) {
                print("Error reading " + motorVars[i] + ": " + e.message);
            }
        }
        
    } catch (e) {
        print("Error: " + e.message);
        if (e.javaException) {
            e.javaException.printStackTrace();
        }
    } finally {
        if (debugSession != null) {
            try {
                debugSession.terminate();
            } catch (e) {
                print("Error terminating session: " + e.message);
            }
        }
    }
}

main();