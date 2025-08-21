// DSS script to read motor variables - fixed version
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Reading Motor Variables ===");
    
    var debugSession = null;
    
    try {
        // Get the Debug Server and connect
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("TMS320F280039C_LaunchPad.ccxml");
        
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        print("Connected to target");
        
        // Load our firmware if it's not already loaded
        print("Loading firmware...");
        try {
            debugSession.memory.loadProgram("Flash_lib_DRV8323RH_3SC/obake_firmware.out");
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
        
        print("=== Reading Motor Control Variables ===");
        
        // List of variables to read
        var motorVars = [
            "motorVars_M1.angleFOC_rad",
            "motorVars_M1.angleENC_rad", 
            "motorVars_M1.absPosition_rad",
            "motorVars_M1.motorState",
            "motorVars_M1.enableSpeedCtrl",
            "motorVars_M1.fluxCurrent_A",
            "motorVars_M1.reversePhases"
        ];
        
        for (var i = 0; i < motorVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(motorVars[i]);
                print(motorVars[i] + " = " + value);
            } catch (e) {
                print("Error reading " + motorVars[i] + ": " + e.message);
            }
        }
        
        print("=== Reading Current Control Variables ===");
        var currentVars = [
            "motorVars_M1.Idq_out_A.value[0]",
            "motorVars_M1.Idq_out_A.value[1]",
            "motorVars_M1.IsRef_A"
        ];
        
        for (var i = 0; i < currentVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(currentVars[i]);
                print(currentVars[i] + " = " + value);
            } catch (e) {
                print("Error reading " + currentVars[i] + ": " + e.message);
            }
        }
        
        print("=== Reading Bypass Debug Variables ===");
        var bypassVars = [
            "debug_bypass.bypass_alignment_called",
            "debug_bypass.bypass_electrical_angle",
            "debug_bypass.bypass_quad_position",
            "debug_bypass.cs_gpio_pin",
            "debug_bypass.bypass_mechanical_diff"
        ];
        
        for (var i = 0; i < bypassVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(bypassVars[i]);
                print(bypassVars[i] + " = " + value);
            } catch (e) {
                print("Error reading " + bypassVars[i] + ": " + e.message);
            }
        }
        
        print("=== Reading Hardware Registers ===");
        try {
            // Try to read EQEP registers directly
            var eqepBase = 0x5700;
            var qposcnt = debugSession.memory.readWord(0, eqepBase + 0x00);
            var qposinit = debugSession.memory.readWord(0, eqepBase + 0x04); 
            var qposmax = debugSession.memory.readWord(0, eqepBase + 0x08);
            
            print("EQEP1 QPOSCNT (Position Count): " + qposcnt);
            print("EQEP1 QPOSINIT (Initial Position): " + qposinit);
            print("EQEP1 QPOSMAX (Max Position): " + qposmax);
            
        } catch (e) {
            print("Error reading EQEP registers: " + e.message);
        }
        
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