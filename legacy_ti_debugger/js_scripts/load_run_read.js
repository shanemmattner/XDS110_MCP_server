// Load firmware, run it, and read variables
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
        
        // Load firmware
        print("Loading firmware...");
        debugSession.memory.loadProgram("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out");
        print("Firmware loaded");
        
        // Run the firmware
        print("Running firmware...");
        debugSession.target.runAsynch();
        
        // Let it run for a bit
        java.lang.Thread.sleep(500);
        
        // Halt to read
        debugSession.target.halt();
        print("Halted for reading");
        
        // Try to read motor variables
        var varsToRead = [
            "motorVars_M1",
            "motorVars_M1.motorState", 
            "motorVars_M1.absPosition_rad",
            "motorVars_M1.angleENC_rad"
        ];
        
        for (var i = 0; i < varsToRead.length; i++) {
            try {
                var value = debugSession.expression.evaluate(varsToRead[i]);
                print("SUCCESS: " + varsToRead[i] + " = " + value);
            } catch (e) {
                print("ERROR: " + varsToRead[i] + " - " + e.message);
            }
        }
        
        // Also read raw encoder
        try {
            var encoderVal = debugSession.memory.readWord(0, 0x5100);
            print("RAW_ENCODER: 0x5100 = " + encoderVal);
        } catch (e) {
            print("ENCODER_ERROR: " + e.message);
        }
        
    } catch (e) {
        print("Script error: " + e.message);
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