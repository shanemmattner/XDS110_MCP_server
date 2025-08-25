// DSS script to read encoder position and voltage values
importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);
importPackage(Packages.java.lang);

function main() {
    print("=== Reading Encoder and Voltage Sensor Data ===");
    
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
        
        // Load firmware
        debugSession.memory.loadProgram("Flash_lib_DRV8323RH_3SC/obake_firmware.out");
        print("Firmware loaded");
        
        // Halt target for reading
        debugSession.target.halt();
        print("Target halted\n");
        
        print("=== ENCODER POSITION DATA ===");
        
        // Read encoder position variables
        try {
            var angleENC = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");
            print("Encoder Angle (rad):      " + angleENC);
        } catch (e) {
            print("angleENC_rad not available: " + e.message);
        }
        
        try {
            var absPosition = debugSession.expression.evaluate("motorVars_M1.absPosition_rad");
            print("Absolute Position (rad):  " + absPosition);
        } catch (e) {
            print("absPosition_rad not available: " + e.message);
        }
        
        try {
            var angleFOC = debugSession.expression.evaluate("motorVars_M1.angleFOC_rad");
            print("FOC Electrical Angle (rad): " + angleFOC);
        } catch (e) {
            print("angleFOC_rad not available: " + e.message);
        }
        
        // Try to read encoder counts if available
        try {
            var encoderCounts = debugSession.expression.evaluate("motorVars_M1.encoderCounts");
            print("Encoder Counts:           " + encoderCounts);
        } catch (e) {
            // Encoder counts might not be in this structure
        }
        
        print("\n=== VOLTAGE MEASUREMENTS ===");
        
        // Read bus voltage
        try {
            var vbus = debugSession.expression.evaluate("motorVars_M1.VdcBus_V");
            print("DC Bus Voltage (V):       " + vbus);
        } catch (e) {
            // Try alternative name
            try {
                var vbus = debugSession.expression.evaluate("motorVars_M1.Vbus_V");
                print("DC Bus Voltage (V):       " + vbus);
            } catch (e2) {
                print("DC Bus voltage not available");
            }
        }
        
        // Read phase voltages
        try {
            var vAlpha = debugSession.expression.evaluate("motorVars_M1.Vab_out_V.value[0]");
            var vBeta = debugSession.expression.evaluate("motorVars_M1.Vab_out_V.value[1]");
            print("V_alpha (V):              " + vAlpha);
            print("V_beta (V):               " + vBeta);
        } catch (e) {
            // Try alternative names
            try {
                var vd = debugSession.expression.evaluate("motorVars_M1.Vdq_out_V.value[0]");
                var vq = debugSession.expression.evaluate("motorVars_M1.Vdq_out_V.value[1]");
                print("V_d (V):                  " + vd);
                print("V_q (V):                  " + vq);
            } catch (e2) {
                print("Phase voltages not available");
            }
        }
        
        print("\n=== CURRENT MEASUREMENTS ===");
        
        // Read phase currents
        try {
            var id = debugSession.expression.evaluate("motorVars_M1.Idq_out_A.value[0]");
            var iq = debugSession.expression.evaluate("motorVars_M1.Idq_out_A.value[1]");
            print("I_d (A):                  " + id);
            print("I_q (A):                  " + iq);
        } catch (e) {
            print("Current measurements not available");
        }
        
        print("\n=== MOTOR STATE INFO ===");
        
        // Read motor state
        try {
            var motorState = debugSession.expression.evaluate("motorVars_M1.motorState");
            var stateStr = "";
            switch(motorState) {
                case 0: stateStr = "IDLE"; break;
                case 1: stateStr = "ALIGNMENT"; break;
                case 2: stateStr = "CTRL_RUN"; break;
                case 3: stateStr = "CL_RUNNING"; break;
                default: stateStr = "UNKNOWN";
            }
            print("Motor State:              " + motorState + " (" + stateStr + ")");
        } catch (e) {
            print("Motor state not available");
        }
        
        // Read speed if available
        try {
            var speed = debugSession.expression.evaluate("motorVars_M1.speed_Hz");
            print("Motor Speed (Hz):         " + speed);
        } catch (e) {
            try {
                var speedRPM = debugSession.expression.evaluate("motorVars_M1.speed_RPM");
                print("Motor Speed (RPM):        " + speedRPM);
            } catch (e2) {
                // Speed not available
            }
        }
        
        print("\n=== CONTINUOUS MONITORING (5 readings, 1 second apart) ===");
        
        // Monitor encoder position changes
        for (var i = 0; i < 5; i++) {
            Thread.sleep(1000);  // Wait 1 second
            
            try {
                var angleENC = debugSession.expression.evaluate("motorVars_M1.angleENC_rad");
                var absPos = debugSession.expression.evaluate("motorVars_M1.absPosition_rad");
                var id = debugSession.expression.evaluate("motorVars_M1.Idq_out_A.value[0]");
                var iq = debugSession.expression.evaluate("motorVars_M1.Idq_out_A.value[1]");
                
                print("Reading " + (i+1) + ": Enc=" + angleENC.toFixed(4) + " rad, Pos=" + 
                      absPos.toFixed(4) + " rad, Id=" + id.toFixed(3) + " A, Iq=" + iq.toFixed(3) + " A");
            } catch (e) {
                print("Reading " + (i+1) + ": Error - " + e.message);
            }
        }
        
        // Resume target
        debugSession.target.runAsynch();
        print("\nTarget resumed");
        
    } catch (e) {
        print("Error: " + e.message);
        e.printStackTrace();
    } finally {
        if (debugSession != null) {
            debugSession.terminate();
            print("Session terminated");
        }
    }
}

main();