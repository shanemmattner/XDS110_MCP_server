// DSS script to read motor variables - with absolute paths
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Reading Motor Variables (Absolute Paths) ===");
    
    var debugSession = null;
    
    try {
        // Get the Debug Server and connect with absolute path
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/TMS320F280039C_LaunchPad.ccxml");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        print("Connected to target");
        
        // Load our firmware with absolute path
        print("Loading firmware...");
        try {
            debugSession.memory.loadProgram("/home/shane/Desktop/skip_repos/skip/robot/core/embedded/firmware/obake/Flash_lib_DRV8323RH_3SC/obake_firmware.out");
            print("Firmware loaded");
        } catch (e) {
            print("Could not load firmware (may already be loaded): " + e.message);
        }
        
        // Halt target to read variables
        try {
            debugSession.target.halt();
            print("Target halted");
        } catch (e) {
            print("Could not halt target: " + e.message);
        }
        
        print("=== Quick Variable Test ===");
        
        // Start with simple base variables
        var baseVars = [
            "motorVars_M1",
            "debug_bypass", 
            "systemVars",
            "controlVars"
        ];
        
        for (var i = 0; i < baseVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(baseVars[i]);
                print("BASE:" + baseVars[i] + " = " + value);
            } catch (e) {
                print("BASE_ERROR:" + baseVars[i] + " - " + e.message);
            }
        }
        
        print("=== Motor Control Variables ===");
        
        // Test structured variables
        var motorVars = [
            "motorVars_M1.motorState",
            "motorVars_M1.absPosition_rad",
            "motorVars_M1.angleENC_rad", 
            "motorVars_M1.angleFOC_rad"
        ];
        
        for (var i = 0; i < motorVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(motorVars[i]);
                print("MOTOR:" + motorVars[i] + " = " + value);
            } catch (e) {
                print("MOTOR_ERROR:" + motorVars[i] + " - " + e.message);
            }
        }
        
        print("=== Current Control Variables ===");
        var currentVars = [
            "motorVars_M1.Idq_out_A.value[0]",
            "motorVars_M1.Idq_out_A.value[1]",
            "motorVars_M1.IsRef_A"
        ];
        
        for (var i = 0; i < currentVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(currentVars[i]);
                print("CURRENT:" + currentVars[i] + " = " + value);
            } catch (e) {
                print("CURRENT_ERROR:" + currentVars[i] + " - " + e.message);
            }
        }
        
        print("=== Debug Variables ===");
        var debugVars = [
            "debug_bypass.bypass_alignment_called",
            "debug_bypass.bypass_electrical_angle",
            "debug_bypass.cs_gpio_pin"
        ];
        
        for (var i = 0; i < debugVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(debugVars[i]);
                print("DEBUG:" + debugVars[i] + " = " + value);
            } catch (e) {
                print("DEBUG_ERROR:" + debugVars[i] + " - " + e.message);
            }
        }
        
        print("=== FAST READ TEST - 10 rapid reads ===");
        
        // Test rapid reading of motorState
        var startTime = java.lang.System.currentTimeMillis();
        
        for (var i = 0; i < 10; i++) {
            try {
                var motorState = debugSession.expression.evaluate("motorVars_M1.motorState");
                var readTime = java.lang.System.currentTimeMillis();
                print("FAST_READ[" + i + "]:" + motorState + " (t=" + (readTime - startTime) + "ms)");
            } catch (e) {
                print("FAST_ERROR[" + i + "]:" + e.message);
            }
        }
        
        var totalTime = java.lang.System.currentTimeMillis() - startTime;
        print("TOTAL_TIME:" + totalTime + "ms for 10 reads (avg:" + (totalTime/10) + "ms/read)");
        
        print("=== Variable Reading Complete ===");
        
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
            } catch (e) {
                print("Error during cleanup: " + e.message);
            }
        }
    }
}

main();