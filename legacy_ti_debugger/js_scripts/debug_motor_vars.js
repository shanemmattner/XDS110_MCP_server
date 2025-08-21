// TI DSS script to read motor control variables
// This script connects to the target and reads key motor control variables

// Import DSS packages
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Motor Control Variable Debug Script ===");
    
    try {
        // Create the Debug Server
        print("Creating debug server...");
        var debugServer = ScriptingEnvironment.instance().getServer("DebugServer.1");
        
        // Set the configuration
        print("Setting CCXML configuration...");
        debugServer.setConfig("TMS320F280039C_LaunchPad.ccxml");
        
        // Connect to the target
        print("Connecting to target...");
        var debugSession = debugServer.openSession("TMS320F280039C_0");
        
        // Connect to target
        debugSession.target.connect();
        print("Connected to target successfully");
        
        // Check if target is running
        if (debugSession.target.isRunning()) {
            print("Target is running, halting...");
            debugSession.target.halt();
        }
        
        print("=== Reading Motor Control Variables ===");
        
        // Key motor control variables to read
        var variables = [
            "motorVars_M1.angleFOC_rad",
            "motorVars_M1.angleENC_rad", 
            "motorVars_M1.absPosition_rad",
            "motorVars_M1.motorState",
            "motorVars_M1.Idq_out_A.value[0]",
            "motorVars_M1.Idq_out_A.value[1]",
            "motorVars_M1.enableSpeedCtrl",
            "motorVars_M1.fluxCurrent_A",
            "motorVars_M1.reversePhases",
            "debug_bypass.bypass_alignment_called",
            "debug_bypass.bypass_electrical_angle",
            "debug_bypass.bypass_quad_position",
            "debug_bypass.cs_gpio_pin"
        ];
        
        // Read and display each variable
        for (var i = 0; i < variables.length; i++) {
            try {
                var varName = variables[i];
                var value = debugSession.expression.evaluate(varName);
                print(varName + " = " + value);
            } catch (e) {
                print("Error reading " + variables[i] + ": " + e.message);
            }
        }
        
        print("=== Reading Encoder State ===");
        
        // Try to read encoder position from hardware registers
        try {
            var eqepBase = 0x5700; // EQEP1 base address for F280039C
            var eqepPos = debugSession.memory.readWord(0, eqepBase + 0x00); // QPOSCNT register
            var eqepInit = debugSession.memory.readWord(0, eqepBase + 0x04); // QPOSINIT register
            print("EQEP Position Count: " + eqepPos);
            print("EQEP Initial Position: " + eqepInit);
        } catch (e) {
            print("Error reading EQEP registers: " + e.message);
        }
        
        print("=== Debug Complete ===");
        
    } catch (e) {
        print("Error: " + e.message);
        print("Stack trace: " + e.stack);
    } finally {
        // Clean up
        try {
            if (debugSession) {
                debugSession.terminate();
            }
        } catch (e) {
            print("Error during cleanup: " + e.message);
        }
    }
}

// Run the main function
main();