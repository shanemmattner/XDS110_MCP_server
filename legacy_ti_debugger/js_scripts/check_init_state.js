// Check initialization state and try to find any non-zero values
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Checking Initialization State ===");
    
    var debugSession = null;
    
    try {
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        ds.setConfig("TMS320F280039C_LaunchPad.ccxml");
        debugSession = ds.openSession("*", "C28xx_CPU1");
        debugSession.target.connect();
        debugSession.memory.loadProgram("Flash_lib_DRV8323RH_3SC/obake_firmware.out");
        debugSession.target.halt();
        
        print("\n=== CHECKING ALL POSSIBLE VARIABLES ===");
        
        // Check initialization flags
        var initVars = [
            "motorVars_M1.needsInit",
            "motorVars_M1.isCalibrated",
            "motorVars_M1.runMotor",
            "motorVars_M1.faultMtrNow",
            "motorVars_M1.faultMtrNow.all",
            "motorVars_M1.faultMtrNow.bit.needsCalibration",
            "motorVars_M1.enableFlag",
            "motorVars_M1.flagEnableRunAndIdentify",
            "motorVars_M1.flagRunIdentAndOnLine"
        ];
        
        print("\nChecking initialization flags:");
        for (var i = 0; i < initVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(initVars[i]);
                print("  " + initVars[i] + " = " + value);
            } catch (e) {
                // Variable doesn't exist
            }
        }
        
        // Try to read raw memory at known locations
        print("\n=== READING RAW MEMORY ===");
        
        // Read memory starting from different addresses
        var addresses = [0xD3C0, 0xD000, 0xC000, 0x20000, 0x3F8000];
        
        for (var j = 0; j < addresses.length; j++) {
            try {
                print("\nMemory at 0x" + addresses[j].toString(16) + ":");
                var memData = debugSession.memory.readData(0, addresses[j], 8);
                var nonZeroFound = false;
                for (var k = 0; k < memData.length; k++) {
                    if (memData[k] != 0) {
                        print("  [+" + k + "]: 0x" + memData[k].toString(16) + " (" + memData[k] + ")");
                        nonZeroFound = true;
                    }
                }
                if (!nonZeroFound) {
                    print("  All zeros");
                }
            } catch (e) {
                print("  Could not read: " + e.message);
            }
        }
        
        // Try to manually start the motor
        print("\n=== ATTEMPTING TO INITIALIZE MOTOR ===");
        
        // Try setting run motor flag
        try {
            debugSession.expression.evaluate("motorVars_M1.runMotor = 1");
            print("Set runMotor = 1");
        } catch (e) {
            print("Could not set runMotor: " + e.message);
        }
        
        // Try setting enable flag
        try {
            debugSession.expression.evaluate("motorVars_M1.enableFlag = 1");
            print("Set enableFlag = 1");
        } catch (e) {
            print("Could not set enableFlag: " + e.message);
        }
        
        // Try to write to debug_bypass directly
        print("\n=== WRITING TO DEBUG_BYPASS ===");
        try {
            // Write 1 to debug_enabled at 0xD3C0
            var data = [1];
            debugSession.memory.writeData(0, 0xD3C0, data);
            print("Wrote 1 to 0xD3C0 (debug_enabled)");
            
            // Read it back
            var readback = debugSession.memory.readData(0, 0xD3C0, 1);
            print("Readback: " + readback[0]);
        } catch (e) {
            print("Could not write to debug_bypass: " + e.message);
        }
        
        // Resume and let it run briefly
        print("\n=== RESUMING AND READING AFTER 2 SECONDS ===");
        debugSession.target.runAsynch();
        Thread.sleep(2000);
        debugSession.target.halt();
        
        // Read values after running
        print("\nValues after running:");
        var checkVars = [
            "motorVars_M1.motorState",
            "motorVars_M1.angleENC_rad",
            "motorVars_M1.absPosition_rad",
            "motorVars_M1.speed_Hz",
            "motorVars_M1.Idq_out_A.value[0]",
            "motorVars_M1.Idq_out_A.value[1]"
        ];
        
        var anyNonZero = false;
        for (var i = 0; i < checkVars.length; i++) {
            try {
                var value = debugSession.expression.evaluate(checkVars[i]);
                if (value != 0) {
                    print("✓ NON-ZERO: " + checkVars[i] + " = " + value);
                    anyNonZero = true;
                } else {
                    print("  " + checkVars[i] + " = " + value);
                }
            } catch (e) {
                // Skip
            }
        }
        
        if (!anyNonZero) {
            print("\n⚠️  All motor variables are still zero.");
            print("This could mean:");
            print("  1. Motor needs physical initialization sequence");
            print("  2. Motor needs calibration (commands 64-67)");
            print("  3. Motor power supply is not connected");
            print("  4. Safety interlocks are preventing operation");
        }
        
    } catch (e) {
        print("Error: " + e.message);
    } finally {
        if (debugSession != null) {
            debugSession.terminate();
        }
    }
}

main();