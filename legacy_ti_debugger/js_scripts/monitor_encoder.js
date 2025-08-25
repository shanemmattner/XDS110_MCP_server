// Monitor encoder position changes in real-time
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Real-Time Encoder Monitoring ===");
    
    var debugSession = null;
    
    try {
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("TMS320F280039C_LaunchPad.ccxml");
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        debugSession.memory.loadProgram("Flash_lib_DRV8323RH_3SC/obake_firmware.out");
        
        print("Connected and firmware loaded");
        print("Monitoring encoder position...");
        print("(Manually rotate the motor shaft to see changes)\n");
        
        // Resume target to let it run
        debugSession.target.runAsynch();
        print("Target running - reading live values\n");
        
        var lastAbsPos = null;
        var lastEncAngle = null;
        var lastFocAngle = null;
        
        print("Time     | Abs Position | Encoder Angle | FOC Angle | Delta Pos");
        print("---------|--------------|---------------|-----------|----------");
        
        // Monitor for 30 iterations
        for (var i = 0; i < 30; i++) {
            Thread.sleep(500);  // Read every 500ms
            
            try {
                // Use refresh to get live values while running
                debugSession.target.refresh();
                
                var absPos = debugSession.expression.evaluate("motorVars_M1.absPosition_rad");
                var encAngle = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");
                var focAngle = debugSession.expression.evaluate("motorVars_M1.angleFOC_rad");
                var motorState = debugSession.expression.evaluate("motorVars_M1.motorState");
                
                // Calculate delta
                var delta = 0;
                if (lastAbsPos != null) {
                    delta = absPos - lastAbsPos;
                }
                
                // Format time
                var timeStr = (i * 0.5).toFixed(1) + "s";
                while (timeStr.length < 7) timeStr += " ";
                
                // Print values - highlight if changed
                var line = timeStr + "  | ";
                
                // Absolute position
                var absPosStr = absPos.toFixed(4);
                if (lastAbsPos != null && Math.abs(absPos - lastAbsPos) > 0.001) {
                    absPosStr = ">" + absPosStr + "<";  // Highlight changes
                }
                while (absPosStr.length < 12) absPosStr += " ";
                line += absPosStr + " | ";
                
                // Encoder angle
                var encAngleStr = encAngle.toFixed(4);
                if (lastEncAngle != null && Math.abs(encAngle - lastEncAngle) > 0.001) {
                    encAngleStr = ">" + encAngleStr + "<";
                }
                while (encAngleStr.length < 13) encAngleStr += " ";
                line += encAngleStr + " | ";
                
                // FOC angle
                var focAngleStr = focAngle.toFixed(4);
                if (lastFocAngle != null && Math.abs(focAngle - lastFocAngle) > 0.001) {
                    focAngleStr = ">" + focAngleStr + "<";
                }
                while (focAngleStr.length < 9) focAngleStr += " ";
                line += focAngleStr + " | ";
                
                // Delta
                if (delta != 0) {
                    line += delta.toFixed(4);
                }
                
                print(line);
                
                // Check for motor state changes
                if (motorState != 0) {
                    var stateStr = "";
                    switch(motorState) {
                        case 1: stateStr = "ALIGNMENT"; break;
                        case 2: stateStr = "CTRL_RUN"; break;
                        case 3: stateStr = "CL_RUNNING"; break;
                    }
                    if (stateStr != "") {
                        print("         *** Motor State Changed: " + stateStr + " ***");
                    }
                }
                
                // Update last values
                lastAbsPos = absPos;
                lastEncAngle = encAngle;
                lastFocAngle = focAngle;
                
            } catch (e) {
                print("Read error at " + (i * 0.5) + "s: " + e.message);
            }
        }
        
        // Final summary
        debugSession.target.halt();
        Thread.sleep(100);
        
        print("\n=== FINAL READINGS ===");
        var finalAbsPos = debugSession.expression.evaluate("motorVars_M1.absPosition_rad");
        var finalEncAngle = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");
        var finalSpeed = debugSession.expression.evaluate("motorVars_M1.speed_Hz");
        
        print("Final Absolute Position: " + finalAbsPos + " radians");
        print("Final Encoder Angle: " + finalEncAngle + " radians");
        print("Final Speed: " + finalSpeed + " Hz");
        
        // Convert to degrees for easier understanding
        print("\nIn degrees:");
        print("  Absolute Position: " + (finalAbsPos * 180 / Math.PI).toFixed(2) + "°");
        print("  Encoder Angle: " + (finalEncAngle * 180 / Math.PI).toFixed(2) + "°");
        
    } catch (e) {
        print("Error: " + e.message);
    } finally {
        if (debugSession != null) {
            debugSession.terminate();
        }
    }
}

main();