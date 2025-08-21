// Monitor motor alignment process in real-time
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Motor Alignment Monitoring Script ===");
    
    var debugSession = null;
    
    try {
        // Connect to target
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("TMS320F280039C_LaunchPad.ccxml");
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        
        // Load firmware
        debugSession.memory.loadProgram("Flash_lib_DRV8323RH_3SC/obake_firmware.out");
        print("Firmware loaded, starting execution...");
        
        // Run firmware to let it initialize
        debugSession.target.runAsynch();
        
        // Wait for initialization
        java.lang.Thread.sleep(3000);
        print("Initialization period complete, starting monitoring...");
        
        // Monitor variables during alignment
        for (var cycle = 0; cycle < 20; cycle++) {
            try {
                // Halt to read variables
                debugSession.target.halt();
                
                // Read key variables
                var motorState = debugSession.expression.evaluate("motorVars_M1.motorState");
                var angleFOC = debugSession.expression.evaluate("motorVars_M1.angleFOC_rad");
                var angleENC = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");
                var absPos = debugSession.expression.evaluate("motorVars_M1.absPosition_rad");
                var bypassCalled = debugSession.expression.evaluate("debug_bypass.bypass_alignment_called");
                var csPin = debugSession.expression.evaluate("debug_bypass.cs_gpio_pin");
                var idqD = debugSession.expression.evaluate("motorVars_M1.Idq_out_A.value[0]");
                var idqQ = debugSession.expression.evaluate("motorVars_M1.Idq_out_A.value[1]");
                
                print("=== Cycle " + cycle + " ===");
                print("Motor State: " + motorState + " (0=STOP_IDLE, 1=ALIGNMENT, 2=CTRL_RUN, 3=CL_RUNNING)");
                print("angleFOC_rad: " + angleFOC);
                print("angleENC_rad: " + angleENC);
                print("absPosition_rad: " + absPos);
                print("bypass_called: " + bypassCalled);
                print("cs_gpio_pin: " + csPin + " (20=absolute, 21=quadrature)");
                print("Idq d-axis: " + idqD);
                print("Idq q-axis: " + idqQ);
                print("");
                
                // If motor is in alignment, monitor more closely
                if (motorState == 1) {
                    print("*** MOTOR IS IN ALIGNMENT STATE ***");
                    
                    // Read alignment-specific variables
                    try {
                        var alignCurrent = debugSession.expression.evaluate("motorVars_M1.alignCurrent_A");
                        var fluxCurrent = debugSession.expression.evaluate("motorVars_M1.fluxCurrent_A");
                        var enableSpeedCtrl = debugSession.expression.evaluate("motorVars_M1.enableSpeedCtrl");
                        
                        print("Alignment current: " + alignCurrent);
                        print("Flux current: " + fluxCurrent);
                        print("Speed ctrl enabled: " + enableSpeedCtrl);
                    } catch (e) {
                        print("Error reading alignment variables: " + e.message);
                    }
                }
                
                // Resume execution
                debugSession.target.runAsynch();
                
                // Wait between readings
                java.lang.Thread.sleep(500);
                
            } catch (e) {
                print("Error in cycle " + cycle + ": " + e.message);
                // Try to resume anyway
                try {
                    debugSession.target.runAsynch();
                } catch (e2) {}
            }
        }
        
        print("=== Monitoring Complete ===");
        
        // Final halt and read
        debugSession.target.halt();
        print("=== Final State ===");
        var finalState = debugSession.expression.evaluate("motorVars_M1.motorState");
        var finalAngleFOC = debugSession.expression.evaluate("motorVars_M1.angleFOC_rad");
        var finalAngleENC = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");
        var finalBypass = debugSession.expression.evaluate("debug_bypass.bypass_alignment_called");
        
        print("Final Motor State: " + finalState);
        print("Final angleFOC_rad: " + finalAngleFOC);
        print("Final angleENC_rad: " + finalAngleENC);
        print("Final bypass called: " + finalBypass);
        
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