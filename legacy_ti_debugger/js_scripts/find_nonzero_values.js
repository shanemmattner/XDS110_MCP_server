// DSS script to find non-zero values in the processor
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Searching for Non-Zero Values in Processor ===");
    
    var debugSession = null;
    
    try {
        // Get the Debug Server
        var ds = ScriptingEnvironment.instance().getServer("DebugServer.1");
        
        // Set the configuration file
        ds.setConfig("TMS320F280039C_LaunchPad.ccxml");
        
        // Open session
        debugSession = ds.openSession("*", "C28xx_CPU1");
        
        // Connect to target
        debugSession.target.connect();
        print("Connected to target");
        
        // DON'T load firmware - read what's already running
        print("Reading current state (not loading firmware)...");
        
        // Halt target for reading
        debugSession.target.halt();
        print("Target halted\n");
        
        print("=== SEARCHING FOR NON-ZERO VALUES ===\n");
        
        // List of all known variables to check
        var variablesToCheck = [
            // Position and angle variables
            "motorVars_M1.angleENC_rad",
            "motorVars_M1.absPosition_rad",
            "motorVars_M1.angleFOC_rad",
            
            // Motor state
            "motorVars_M1.motorState",
            "motorVars_M1.enableSpeedCtrl",
            "motorVars_M1.reversePhases",
            
            // Current variables
            "motorVars_M1.Idq_out_A.value[0]",
            "motorVars_M1.Idq_out_A.value[1]",
            "motorVars_M1.IsRef_A",
            "motorVars_M1.fluxCurrent_A",
            
            // Try possible voltage variables
            "motorVars_M1.VdcBus_V",
            "motorVars_M1.Vbus_V",
            "motorVars_M1.Vdq_out_V.value[0]",
            "motorVars_M1.Vdq_out_V.value[1]",
            
            // Speed variables
            "motorVars_M1.speed_Hz",
            "motorVars_M1.speed_RPM",
            "motorVars_M1.speedRef_Hz",
            
            // Control flags
            "motorVars_M1.needsInit",
            "motorVars_M1.runMotor",
            "motorVars_M1.isCalibrated"
        ];
        
        var nonZeroFound = false;
        
        for (var i = 0; i < variablesToCheck.length; i++) {
            try {
                var value = debugSession.expression.evaluate(variablesToCheck[i]);
                if (value != 0 && value != null) {
                    print("✓ NON-ZERO: " + variablesToCheck[i] + " = " + value);
                    nonZeroFound = true;
                } else if (value == 0) {
                    print("  zero:     " + variablesToCheck[i] + " = " + value);
                }
            } catch (e) {
                // Variable doesn't exist, skip silently
            }
        }
        
        if (!nonZeroFound) {
            print("\nNo non-zero values found in standard variables.");
            print("Checking memory directly...\n");
            
            // Try reading memory at known addresses
            print("Reading memory at debug_bypass address (0xD3C0):");
            try {
                var memData = debugSession.memory.readData(0, 0xD3C0, 16);
                print("Memory at 0xD3C0: ");
                var hasNonZero = false;
                for (var j = 0; j < memData.length; j++) {
                    if (memData[j] != 0) hasNonZero = true;
                    print("  [" + j + "]: 0x" + memData[j].toString(16));
                }
                if (hasNonZero) {
                    print("✓ Found non-zero bytes in debug_bypass memory!");
                }
            } catch (e) {
                print("Could not read memory at 0xD3C0: " + e.message);
            }
        }
        
        print("\n=== CHECKING SYSTEM REGISTERS ===");
        
        // Try to read PC (Program Counter) - should never be 0
        try {
            var pc = debugSession.expression.evaluate("PC");
            print("Program Counter (PC): 0x" + pc.toString(16) + " (" + pc + ")");
            if (pc != 0) {
                print("✓ PC is non-zero - processor is loaded with code");
            }
        } catch (e) {
            print("Could not read PC: " + e.message);
        }
        
        // Try to read SP (Stack Pointer)
        try {
            var sp = debugSession.expression.evaluate("SP");
            print("Stack Pointer (SP): 0x" + sp.toString(16) + " (" + sp + ")");
        } catch (e) {
            print("Could not read SP: " + e.message);
        }
        
        print("\n=== ATTEMPTING LIVE MONITORING (without resume) ===");
        print("Reading 5 times to check if values change while halted...");
        
        for (var iter = 0; iter < 5; iter++) {
            Thread.sleep(500);  // Wait 500ms
            try {
                var angleENC = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");
                var motorState = debugSession.expression.evaluate("motorVars_M1.motorState");
                print("Iteration " + (iter+1) + ": angleENC=" + angleENC + ", motorState=" + motorState);
            } catch (e) {
                print("Iteration " + (iter+1) + ": Error reading");
            }
        }
        
        // Try to resume and read again
        print("\n=== RESUMING TARGET AND READING ===");
        debugSession.target.runAsynch();
        print("Target resumed");
        
        Thread.sleep(1000);  // Wait 1 second
        
        // Halt again to read
        debugSession.target.halt();
        print("Target halted again");
        
        // Read after resume
        print("\nValues after resume:");
        for (var i = 0; i < 5; i++) {
            try {
                var value = debugSession.expression.evaluate(variablesToCheck[i]);
                print(variablesToCheck[i] + " = " + value);
            } catch (e) {
                // Skip
            }
        }
        
    } catch (e) {
        print("Error: " + e.message);
    } finally {
        if (debugSession != null) {
            debugSession.terminate();
            print("\nSession terminated");
        }
    }
}

main();