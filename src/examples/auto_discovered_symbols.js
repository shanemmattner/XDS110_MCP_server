// Auto-generated DSS script from MAP file parsing
// Generated from: obake_firmware.map
// Total symbols: 445

importPackage(Packages.com.ti.debug.engine.scripting);
importPackage(Packages.com.ti.ccstudio.scripting.environment);

// All discovered symbols with addresses
var symbols = {
  "ADC_setOffsetTrimAll": {
    "address": 562267,
    "size": 0
  },
  "ADC_setVREF": {
    "address": 562345,
    "size": 0
  },
  "ANGLE_GEN_init": {
    "address": 563574,
    "size": 0
  },
  "ANGLE_GEN_setParams": {
    "address": 563172,
    "size": 0
  },
  "C": {
    "address": 561244,
    "size": 0
  },
  "CLARKE_init": {
    "address": 563651,
    "size": 0
  },
  "CLA_Main_Init": {
    "address": 552861,
    "size": 0
  },
  "CLA_Start_Tasks": {
    "address": 563271,
    "size": 0
  },
  "CLA_motorFastControl": {
    "address": 32768,
    "size": 0
  },
  "CLA_motorFastControlData_Init": {
    "address": 555806,
    "size": 0
  },
  "CLA_motorFastControl_Init": {
    "address": 36872,
    "size": 0
  },
  "CLA_runRuntimeMonitoring": {
    "address": 36110,
    "size": 0
  },
  "CLA_setTriggerSource": {
    "address": 561990,
    "size": 0
  },
  "CLAdiv": {
    "address": 36932,
    "size": 0
  },
  "CMPSS_configFilterHigh": {
    "address": 562370,
    "size": 0
  },
  "CMPSS_configFilterLow": {
    "address": 562395,
    "size": 0
  },
  "CPUTimer_setEmulationMode": {
    "address": 563580,
    "size": 0
  },
  "Cla1ProgLoadStart": {
    "address": 538100,
    "size": 0
  },
  "Cla1ProgRunStart": {
    "address": 32768,
    "size": 0
  },
  "Cla1Regs": {
    "address": 5120,
    "size": 80
  },
  "Device_enableAllPeripherals": {
    "address": 554357,
    "size": 0
  },
  "Device_init": {
    "address": 558445,
    "size": 0
  },
  "Device_initGPIO": {
    "address": 563035,
    "size": 0
  },
  "ENC_init": {
    "address": 559386,
    "size": 0
  },
  "ENC_setParams": {
    "address": 562445,
    "size": 0
  },
  "EPWM_setEmulationMode": {
    "address": 563334,
    "size": 0
  },
  "EST_Angle_init": {
    "address": 563655,
    "size": 0
  },
  "EST_Angle_setParams": {
    "address": 561325,
    "size": 0
  },
  "EST_Dir_init": {
    "address": 559965,
    "size": 0
  },
  "EST_Dir_resetHpFilters": {
    "address": 563051,
    "size": 0
  },
  "EST_Dir_resetLpFilters": {
    "address": 562018,
    "size": 0
  },
  "EST_Dir_setHpFilterParams": {
    "address": 557858,
    "size": 0
  },
  "EST_Dir_setLpFilterParams": {
    "address": 556243,
    "size": 0
  },
  "EST_Dir_setParams": {
    "address": 563282,
    "size": 0
  },
  "EST_Eab_init": {
    "address": 563659,
    "size": 0
  },
  "EST_Eab_setParams": {
    "address": 563483,
    "size": 0
  },
  "EST_Edq_init": {
    "address": 563663,
    "size": 0
  },
  "EST_Edq_setParams": {
    "address": 563616,
    "size": 0
  },
  "EST_Flux_ab_init": {
    "address": 562610,
    "size": 0
  },
  "EST_Flux_ab_resetDerFilters": {
    "address": 563067,
    "size": 0
  },
  "EST_Flux_ab_setDerFilterParams": {
    "address": 557932,
    "size": 0
  },
  "EST_Flux_ab_setParams": {
    "address": 563304,
    "size": 0
  },
  "EST_Flux_dq_init": {
    "address": 563667,
    "size": 0
  },
  "EST_Flux_dq_setParams": {
    "address": 563621,
    "size": 0
  },
  "EST_Flux_init": {
    "address": 563099,
    "size": 0
  },
  "EST_Flux_setParams": {
    "address": 557444,
    "size": 0
  },
  "EST_Flux_setWaitTimes": {
    "address": 563490,
    "size": 0
  },
  "EST_Flux_updateState": {
    "address": 559214,
    "size": 0
  },
  "EST_Freq_init": {
    "address": 562632,
    "size": 0
  },
  "EST_Freq_resetDerFilter": {
    "address": 563497,
    "size": 0
  },
  "EST_Freq_resetLpFilter": {
    "address": 563504,
    "size": 0
  },
  "EST_Freq_setDerFilterParams": {
    "address": 560869,
    "size": 0
  },
  "EST_Freq_setLpFilterParams": {
    "address": 560911,
    "size": 0
  },
  "EST_Freq_setParams": {
    "address": 557702,
    "size": 0
  },
  "EST_Iab_init": {
    "address": 562654,
    "size": 0
  },
  "EST_Iab_resetLpFilters": {
    "address": 560157,
    "size": 0
  },
  "EST_Iab_setLpFilterParams": {
    "address": 558006,
    "size": 0
  },
  "EST_Iab_setParams": {
    "address": 562676,
    "size": 0
  },
  "EST_Idq_init": {
    "address": 562698,
    "size": 0
  },
  "EST_Idq_resetLpFilters": {
    "address": 561363,
    "size": 0
  },
  "EST_Idq_setLpFilterParams": {
    "address": 558080,
    "size": 0
  },
  "EST_Idq_setParams": {
    "address": 562909,
    "size": 0
  },
  "EST_Ls_init": {
    "address": 563671,
    "size": 0
  },
  "EST_Ls_setParams": {
    "address": 558718,
    "size": 0
  },
  "EST_Ls_setWaitTimes": {
    "address": 563511,
    "size": 0
  },
  "EST_Ls_updateState": {
    "address": 559549,
    "size": 0
  },
  "EST_OneOverDcBus_init": {
    "address": 563114,
    "size": 0
  },
  "EST_OneOverDcBus_setParams": {
    "address": 561121,
    "size": 0
  },
  "EST_Rr_init": {
    "address": 563675,
    "size": 0
  },
  "EST_Rr_setParams": {
    "address": 562046,
    "size": 0
  },
  "EST_Rr_setWaitTimes": {
    "address": 563518,
    "size": 0
  },
  "EST_Rr_updateState": {
    "address": 559813,
    "size": 0
  },
  "EST_RsOnLine_init": {
    "address": 561162,
    "size": 0
  },
  "EST_RsOnLine_setLpFilterParams": {
    "address": 559093,
    "size": 0
  },
  "EST_RsOnLine_setParams": {
    "address": 558515,
    "size": 0
  },
  "EST_Rs_init": {
    "address": 563679,
    "size": 0
  },
  "EST_Rs_setParams": {
    "address": 562074,
    "size": 0
  },
  "EST_Rs_setWaitTimes": {
    "address": 563525,
    "size": 0
  },
  "EST_Rs_updateState": {
    "address": 559864,
    "size": 0
  },
  "EST_Traj_configure": {
    "address": 552590,
    "size": 0
  },
  "EST_Traj_init": {
    "address": 562102,
    "size": 0
  },
  "EST_Traj_run": {
    "address": 55619,
    "size": 0
  },
  "EST_Traj_setParams": {
    "address": 554975,
    "size": 0
  },
  "EST_Vab_init": {
    "address": 563683,
    "size": 0
  },
  "EST_Vab_setParams": {
    "address": 563626,
    "size": 0
  },
  "EST_Vdq_init": {
    "address": 562720,
    "size": 0
  },
  "EST_Vdq_resetLpFilters": {
    "address": 560953,
    "size": 0
  },
  "EST_Vdq_setLpFilterParams": {
    "address": 558154,
    "size": 0
  },
  "EST_Vdq_setParams": {
    "address": 562947,
    "size": 0
  },
  "EST_checkForErrors": {
    "address": 563775,
    "size": 0
  },
  "EST_computeLmag_H": {
    "address": 561842,
    "size": 0
  },
  "EST_computePower_W": {
    "address": 563343,
    "size": 0
  },
  "EST_computeTorque_Nm": {
    "address": 561285,
    "size": 0
  },
  "EST_configureTraj": {
    "address": 563532,
    "size": 0
  },
  "EST_configureTrajState": {
    "address": 53258,
    "size": 0
  },
  "EST_disable": {
    "address": 563687,
    "size": 0
  },
  "EST_disableTraj": {
    "address": 563539,
    "size": 0
  },
  "EST_doCurrentCtrl": {
    "address": 56097,
    "size": 0
  },
  "EST_doSpeedCtrl": {
    "address": 56075,
    "size": 0
  },
  "EST_getFASTVersion": {
    "address": 563778,
    "size": 0
  },
  "EST_getFe_rps": {
    "address": 563586,
    "size": 0
  },
  "EST_getFlag_bypassLockRotor": {
    "address": 563691,
    "size": 0
  },
  "EST_getFlag_enable": {
    "address": 563695,
    "size": 0
  },
  "EST_getFlag_enableRsRecalc": {
    "address": 563699,
    "size": 0
  },
  "EST_getFm_lp_Hz": {
    "address": 563144,
    "size": 0
  },
  "EST_getIdRated_A": {
    "address": 56116,
    "size": 0
  },
  "EST_getIntValue_Id_A": {
    "address": 56124,
    "size": 0
  },
  "EST_getIntValue_spd_Hz": {
    "address": 56107,
    "size": 0
  },
  "EST_getLs_d_H": {
    "address": 563379,
    "size": 0
  },
  "EST_getLs_q_H": {
    "address": 563387,
    "size": 0
  },
  "EST_getRoverL_rps": {
    "address": 563703,
    "size": 0
  },
  "EST_getRr_Ohm": {
    "address": 563395,
    "size": 0
  },
  "EST_getRsOnLine_Ohm": {
    "address": 563403,
    "size": 0
  },
  "EST_getRs_Ohm": {
    "address": 563411,
    "size": 0
  },
  "EST_getState": {
    "address": 56145,
    "size": 0
  },
  "EST_getTrajState": {
    "address": 563631,
    "size": 0
  },
  "EST_init": {
    "address": 554779,
    "size": 0
  },
  "EST_initEst": {
    "address": 562965,
    "size": 0
  },
  "EST_isEnabled": {
    "address": 56137,
    "size": 0
  },
  "EST_isError": {
    "address": 563419,
    "size": 0
  },
  "EST_isIdle": {
    "address": 563427,
    "size": 0
  },
  "EST_isLockRotor": {
    "address": 563435,
    "size": 0
  },
  "EST_isMotorIdentified": {
    "address": 563707,
    "size": 0
  },
  "EST_reset": {
    "address": 549498,
    "size": 0
  },
  "EST_resetCounter_isr": {
    "address": 563781,
    "size": 0
  },
  "EST_resetCounter_state": {
    "address": 563784,
    "size": 0
  },
  "EST_run": {
    "address": 54464,
    "size": 0
  },
  "EST_runTraj": {
    "address": 56131,
    "size": 0
  },
  "EST_setAngle_rad": {
    "address": 563352,
    "size": 0
  },
  "EST_setBemf_sf": {
    "address": 563211,
    "size": 0
  },
  "EST_setFlag_bypassLockRotor": {
    "address": 563711,
    "size": 0
  },
  "EST_setFlag_enable": {
    "address": 563715,
    "size": 0
  },
  "EST_setFlag_enableFluxControl": {
    "address": 563719,
    "size": 0
  },
  "EST_setFlag_enableForceAngle": {
    "address": 563723,
    "size": 0
  },
  "EST_setFlag_enableRsOnLine": {
    "address": 563727,
    "size": 0
  },
  "EST_setFlag_enableRsRecalc": {
    "address": 563731,
    "size": 0
  },
  "EST_setFlag_updateRs": {
    "address": 563735,
    "size": 0
  },
  "EST_setFluxBeta_lp": {
    "address": 561203,
    "size": 0
  },
  "EST_setFlux_ab_betaOmega_der": {
    "address": 562186,
    "size": 0
  },
  "EST_setFreqBetaOmega_der": {
    "address": 562130,
    "size": 0
  },
  "EST_setFreqBeta_lp": {
    "address": 562764,
    "size": 0
  },
  "EST_setFreqLFP_sf": {
    "address": 563129,
    "size": 0
  },
  "EST_setIab_beta_lp": {
    "address": 562785,
    "size": 0
  },
  "EST_setId_ref_A": {
    "address": 563592,
    "size": 0
  },
  "EST_setIdq_beta_lp": {
    "address": 562806,
    "size": 0
  },
  "EST_setIq_ref_A": {
    "address": 563598,
    "size": 0
  },
  "EST_setLs_d_H": {
    "address": 563443,
    "size": 0
  },
  "EST_setLs_q_H": {
    "address": 563451,
    "size": 0
  },
  "EST_setMotorParams": {
    "address": 563546,
    "size": 0
  },
  "EST_setNumIsrTicksPerEstTick": {
    "address": 563787,
    "size": 0
  },
  "EST_setOneOverFluxGain_sf": {
    "address": 563223,
    "size": 0
  },
  "EST_setParams": {
    "address": 542296,
    "size": 0
  },
  "EST_setRr_Ohm": {
    "address": 563459,
    "size": 0
  },
  "EST_setVdq_beta_lp": {
    "address": 562827,
    "size": 0
  },
  "EST_setWaitTimes": {
    "address": 563553,
    "size": 0
  },
  "EST_setupTrajState": {
    "address": 54936,
    "size": 0
  },
  "EST_updateState": {
    "address": 548251,
    "size": 0
  },
  "FILTER_FO_init": {
    "address": 563739,
    "size": 0
  },
  "FILTER_FO_setDenCoeffs": {
    "address": 563790,
    "size": 0
  },
  "FILTER_FO_setInitialConditions": {
    "address": 563604,
    "size": 0
  },
  "FILTER_FO_setNumCoeffs": {
    "address": 563636,
    "size": 0
  },
  "Fapi_GlobalInit": {
    "address": 58862,
    "size": 0
  },
  "Fapi_WriteReadBack": {
    "address": 58775,
    "size": 0
  },
  "Fapi_calculateFletcherChecksum": {
    "address": 58594,
    "size": 0
  },
  "Fapi_calculateOtpChecksum": {
    "address": 58830,
    "size": 0
  },
  "Fapi_checkFsmForReady": {
    "address": 58816,
    "size": 0
  },
  "Fapi_checkRegionForValue": {
    "address": 57954,
    "size": 0
  },
  "Fapi_configureFMAC": {
    "address": 58198,
    "size": 0
  },
  "Fapi_divideUnsignedLong": {
    "address": 58638,
    "size": 0
  },
  "Fapi_doBlankCheck": {
    "address": 57830,
    "size": 0
  },
  "Fapi_doVerify": {
    "address": 58801,
    "size": 0
  },
  "Fapi_flushPipeline": {
    "address": 58718,
    "size": 0
  },
  "Fapi_getFsmStatus": {
    "address": 58854,
    "size": 0
  },
  "Fapi_initializeAPI": {
    "address": 58495,
    "size": 0
  },
  "Fapi_isAddressEcc": {
    "address": 58682,
    "size": 0
  },
  "Fapi_isAddressValid": {
    "address": 58381,
    "size": 0
  },
  "Fapi_issueBankEraseCommand": {
    "address": 57655,
    "size": 0
  },
  "Fapi_issueFsmCommand": {
    "address": 58295,
    "size": 0
  },
  "Fapi_issueProgrammingCommand": {
    "address": 57039,
    "size": 0
  },
  "Fapi_loopRegionForValue": {
    "address": 58076,
    "size": 0
  },
  "Fapi_scaleCycleValues": {
    "address": 58843,
    "size": 0
  },
  "Fapi_setActiveFlashBank": {
    "address": 58440,
    "size": 0
  },
  "Fapi_setupBankSectorEnable": {
    "address": 58545,
    "size": 0
  },
  "Fapi_setupSectorsForWrite": {
    "address": 58747,
    "size": 0
  },
  "Flash_initModule": {
    "address": 55794,
    "size": 0
  },
  "GPIO_setAnalogMode": {
    "address": 558584,
    "size": 0
  },
  "GPIO_setDirectionMode": {
    "address": 561653,
    "size": 0
  },
  "GPIO_setPadConfig": {
    "address": 558781,
    "size": 0
  },
  "GPIO_setPinConfig": {
    "address": 560014,
    "size": 0
  },
  "GPIO_setQualificationMode": {
    "address": 561619,
    "size": 0
  },
  "GPIO_setQualificationPeriod": {
    "address": 562213,
    "size": 0
  },
  "HAL_MTR1_init": {
    "address": 560203,
    "size": 0
  },
  "HAL_MTR_setGateDriver": {
    "address": 563083,
    "size": 0
  },
  "HAL_MTR_setParams": {
    "address": 560432,
    "size": 0
  },
  "HAL_clearDataRAM": {
    "address": 563560,
    "size": 0
  },
  "HAL_disableEncoderSPI": {
    "address": 561932,
    "size": 0
  },
  "HAL_enableCtrlInts": {
    "address": 563185,
    "size": 0
  },
  "HAL_enableDRV": {
    "address": 559915,
    "size": 0
  },
  "HAL_enableDebugInt": {
    "address": 563793,
    "size": 0
  },
  "HAL_enableGlobalInts": {
    "address": 563743,
    "size": 0
  },
  "HAL_init": {
    "address": 559602,
    "size": 0
  },
  "HAL_setMtrCMPSSDACValue": {
    "address": 562983,
    "size": 0
  },
  "HAL_setParams": {
    "address": 561749,
    "size": 0
  },
  "HAL_setTriggerPrams": {
    "address": 561685,
    "size": 0
  },
  "HAL_setupADCs": {
    "address": 554568,
    "size": 0
  },
  "HAL_setupCMPSSs": {
    "address": 553124,
    "size": 0
  },
  "HAL_setupCPUUsageTimer": {
    "address": 562240,
    "size": 0
  },
  "HAL_setupGPIOs": {
    "address": 544213,
    "size": 0
  },
  "HAL_setupI2CA": {
    "address": 556746,
    "size": 0
  },
  "HAL_setupMtrFaults": {
    "address": 553384,
    "size": 0
  },
  "HAL_setupPWMs": {
    "address": 550789,
    "size": 0
  },
  "HAL_setupQEP": {
    "address": 557536,
    "size": 0
  },
  "HAL_setupTimeBaseTimer": {
    "address": 560995,
    "size": 0
  },
  "I2C_clearInterruptStatus": {
    "address": 563001,
    "size": 0
  },
  "I2C_enableInterrupt": {
    "address": 562541,
    "size": 0
  },
  "I2C_initController": {
    "address": 559154,
    "size": 0
  },
  "INVERSE_init": {
    "address": 563747,
    "size": 0
  },
  "INVERSE_setParams": {
    "address": 563361,
    "size": 0
  },
  "IPARK_init": {
    "address": 563751,
    "size": 0
  },
  "Interrupt_defaultHandler": {
    "address": 563235,
    "size": 0
  },
  "Interrupt_disable": {
    "address": 558228,
    "size": 0
  },
  "Interrupt_enable": {
    "address": 559441,
    "size": 0
  },
  "Interrupt_illegalOperationHandler": {
    "address": 563314,
    "size": 0
  },
  "Interrupt_initModule": {
    "address": 558653,
    "size": 0
  },
  "Interrupt_initVectorTable": {
    "address": 562848,
    "size": 0
  },
  "Interrupt_nmiHandler": {
    "address": 563324,
    "size": 0
  },
  "MemCfg_setLSRAMControllerSel": {
    "address": 561439,
    "size": 0
  },
  "Obk_Cla1BackgroundTask": {
    "address": 36904,
    "size": 0
  },
  "Obk_Cla1Task7": {
    "address": 36678,
    "size": 0
  },
  "Obk_Cla1_FstLoop": {
    "address": 36442,
    "size": 0
  },
  "Obk_Cla1_Halls": {
    "address": 36772,
    "size": 0
  },
  "Obk_ClaTask1Cntr": {
    "address": 41230,
    "size": 644
  },
  "Obk_ClaTask1CntrHigh": {
    "address": 41228,
    "size": 644
  },
  "Obk_ClaTask1CntrLow": {
    "address": 41226,
    "size": 644
  },
  "Obk_ClaTask2HallCntr": {
    "address": 41234,
    "size": 644
  },
  "Obk_ClaTask7Cntr": {
    "address": 41222,
    "size": 644
  },
  "Obk_ClaTaskBgnCntr": {
    "address": 41224,
    "size": 644
  },
  "PARK_init": {
    "address": 563755,
    "size": 0
  },
  "PI_init": {
    "address": 563759,
    "size": 0
  },
  "SCI_clearInterruptStatus": {
    "address": 562158,
    "size": 0
  },
  "SCI_disableInterrupt": {
    "address": 562293,
    "size": 0
  },
  "SCI_enableInterrupt": {
    "address": 562319,
    "size": 0
  },
  "SCI_setConfig": {
    "address": 561549,
    "size": 0
  },
  "SPI_clearInterruptStatus": {
    "address": 561872,
    "size": 0
  },
  "SPI_enableInterrupt": {
    "address": 562469,
    "size": 0
  },
  "SPI_setBaudRate": {
    "address": 563293,
    "size": 0
  },
  "SPI_setConfig": {
    "address": 561780,
    "size": 0
  },
  "SVGENCURRENT_init": {
    "address": 563763,
    "size": 0
  },
  "SVGENCURRENT_setup": {
    "address": 562742,
    "size": 0
  },
  "SVGEN_init": {
    "address": 563767,
    "size": 0
  },
  "SysCtl_delay": {
    "address": 56141,
    "size": 0
  },
  "SysCtl_isPLLValid": {
    "address": 554124,
    "size": 0
  },
  "SysCtl_selectOscSource": {
    "address": 560387,
    "size": 0
  },
  "SysCtl_selectXTAL": {
    "address": 558969,
    "size": 0
  },
  "SysCtl_selectXTALSingleEnded": {
    "address": 561902,
    "size": 0
  },
  "SysCtl_setClock": {
    "address": 552041,
    "size": 0
  },
  "TRAJ_init": {
    "address": 563771,
    "size": 0
  },
  "USER_setMotor1Params": {
    "address": 548895,
    "size": 0
  },
  "USER_setParams_priv": {
    "address": 556511,
    "size": 0
  },
  "XBAR_setEPWMMuxConfig": {
    "address": 560740,
    "size": 0
  },
  "XBAR_setOutputMuxConfig": {
    "address": 561476,
    "size": 0
  },
  "_args_main": {
    "address": 563259,
    "size": 0
  },
  "_c_int00": {
    "address": 562564,
    "size": 0
  },
  "_lock": {
    "address": 62444,
    "size": 975
  },
  "_nop": {
    "address": 563378,
    "size": 0
  },
  "_register_lock": {
    "address": 563374,
    "size": 0
  },
  "_register_unlock": {
    "address": 563370,
    "size": 0
  },
  "_system_post_cinit": {
    "address": 545095,
    "size": 0
  },
  "_system_pre_init": {
    "address": 563796,
    "size": 0
  },
  "_unlock": {
    "address": 62446,
    "size": 975
  },
  "abort": {
    "address": 561244,
    "size": 0
  },
  "angleGen_M1": {
    "address": 62502,
    "size": 976
  },
  "apply_rotation": {
    "address": 557780,
    "size": 0
  },
  "blinking_states": {
    "address": 62420,
    "size": 975
  },
  "bootloadDataBuffer": {
    "address": 61810,
    "size": 965
  },
  "bootloadFinish": {
    "address": 55063,
    "size": 0
  },
  "btn_down_state": {
    "address": 61436,
    "size": 959
  },
  "btn_on_off_state": {
    "address": 61432,
    "size": 959
  },
  "btn_up_state": {
    "address": 61434,
    "size": 959
  },
  "cal_flash_erased": {
    "address": 561584,
    "size": 0
  },
  "calcMotorOverCurrentThreshold": {
    "address": 561037,
    "size": 0
  },
  "calculateRMSData": {
    "address": 555964,
    "size": 0
  },
  "calibrate_adc_offset": {
    "address": 54055,
    "size": 0
  },
  "calibrate_angle_offset": {
    "address": 55300,
    "size": 0
  },
  "calibrate_loadcell_gain": {
    "address": 55412,
    "size": 0
  },
  "calibrate_motor_dir": {
    "address": 55182,
    "size": 0
  },
  "capture_raw_state_data": {
    "address": 552316,
    "size": 0
  },
  "checkCmpssOverCurrentFault": {
    "address": 558302,
    "size": 0
  },
  "check_calibration_valid": {
    "address": 55712,
    "size": 0
  },
  "claFastData": {
    "address": 40960,
    "size": 640
  },
  "clarke_I_M1": {
    "address": 62488,
    "size": 976
  },
  "clarke_I_M1_CLA": {
    "address": 41238,
    "size": 644
  },
  "clarke_V_M1": {
    "address": 62482,
    "size": 976
  },
  "clarke_V_M1_CLA": {
    "address": 41244,
    "size": 644
  },
  "code_start": {
    "address": 524288,
    "size": 0
  },
  "collectRMSData": {
    "address": 557619,
    "size": 0
  },
  "compare_float32": {
    "address": 562869,
    "size": 0
  },
  "controlVars": {
    "address": 61464,
    "size": 960
  },
  "data_counter": {
    "address": 62440,
    "size": 975
  },
  "debug_bypass": {
    "address": 62114,
    "size": 970
  },
  "debug_bypass_process": {
    "address": 563247,
    "size": 0
  },
  "ema_filter": {
    "address": 563198,
    "size": 0
  },
  "encIsr": {
    "address": 53789,
    "size": 0
  },
  "enc_M1": {
    "address": 62656,
    "size": 979
  },
  "enc_M1_CLA": {
    "address": 41262,
    "size": 644
  },
  "encoder_init": {
    "address": 559495,
    "size": 0
  },
  "encoder_set_min_max_rad": {
    "address": 563641,
    "size": 0
  },
  "encoder_update": {
    "address": 557163,
    "size": 0
  },
  "est": {
    "address": 58868,
    "size": 919
  },
  "exit": {
    "address": 561246,
    "size": 0
  },
  "g_active_buffer_index": {
    "address": 62452,
    "size": 975
  },
  "g_active_buffer_ptr": {
    "address": 61502,
    "size": 960
  },
  "g_data_ready_for_processing": {
    "address": 61500,
    "size": 960
  },
  "g_processed_state_data": {
    "address": 61632,
    "size": 963
  },
  "g_raw_state_data": {
    "address": 61568,
    "size": 962
  },
  "g_state_buffers": {
    "address": 61938,
    "size": 967
  },
  "globalEncoderHandle": {
    "address": 62434,
    "size": 975
  },
  "hal": {
    "address": 1026,
    "size": 16
  },
  "halHandle": {
    "address": 1024,
    "size": 16
  },
  "halMtr_M1": {
    "address": 62616,
    "size": 978
  },
  "halMtr_M1_CLA": {
    "address": 41318,
    "size": 645
  },
  "imu_ctrl_registers": {
    "address": 61440,
    "size": 960
  },
  "imu_init": {
    "address": 560476,
    "size": 0
  },
  "imu_raw_data": {
    "address": 61454,
    "size": 960
  },
  "initMotor1CtrlParameters": {
    "address": 547558,
    "size": 0
  },
  "initMotor1Handles": {
    "address": 560110,
    "size": 0
  },
  "initRs485": {
    "address": 555146,
    "size": 0
  },
  "initSciCom": {
    "address": 553884,
    "size": 0
  },
  "initSpi": {
    "address": 559272,
    "size": 0
  },
  "initSpi_imu": {
    "address": 559031,
    "size": 0
  },
  "initializeBootloader": {
    "address": 55869,
    "size": 0
  },
  "ipark_V_M1": {
    "address": 62466,
    "size": 976
  },
  "ipark_V_M1_CLA": {
    "address": 41250,
    "size": 644
  },
  "led_data": {
    "address": 63296,
    "size": 989
  },
  "led_states": {
    "address": 563800,
    "size": 8809
  },
  "loadEnd_SFRA_F32_Data": {
    "address": 49152,
    "size": 0
  },
  "loadEnd_ctrlfuncs": {
    "address": 49152,
    "size": 0
  },
  "loadEnd_datalog_data": {
    "address": 49152,
    "size": 0
  },
  "loadEnd_dmaBuf_data": {
    "address": 49152,
    "size": 0
  },
  "loadEnd_est_data": {
    "address": 60316,
    "size": 0
  },
  "loadEnd_foc_data": {
    "address": 63296,
    "size": 0
  },
  "loadEnd_foc_data_cla": {
    "address": 41358,
    "size": 0
  },
  "loadEnd_hal_data": {
    "address": 1066,
    "size": 0
  },
  "loadEnd_motor_data": {
    "address": 49152,
    "size": 0
  },
  "loadEnd_sys_data": {
    "address": 63388,
    "size": 0
  },
  "loadEnd_user_data": {
    "address": 62402,
    "size": 0
  },
  "loadEnd_vibc_data": {
    "address": 49152,
    "size": 0
  },
  "loadEnd_ws2812_data": {
    "address": 63340,
    "size": 0
  },
  "loadStart_SFRA_F32_Data": {
    "address": 49152,
    "size": 0
  },
  "loadStart_ctrlfuncs": {
    "address": 49152,
    "size": 0
  },
  "loadStart_datalog_data": {
    "address": 49152,
    "size": 0
  },
  "loadStart_dmaBuf_data": {
    "address": 49152,
    "size": 0
  },
  "loadStart_est_data": {
    "address": 58868,
    "size": 0
  },
  "loadStart_foc_data": {
    "address": 62464,
    "size": 0
  },
  "loadStart_foc_data_cla": {
    "address": 41238,
    "size": 0
  },
  "loadStart_hal_data": {
    "address": 1024,
    "size": 0
  },
  "loadStart_motor_data": {
    "address": 49152,
    "size": 0
  },
  "loadStart_sys_data": {
    "address": 63360,
    "size": 0
  },
  "loadStart_user_data": {
    "address": 61464,
    "size": 0
  },
  "loadStart_vibc_data": {
    "address": 49152,
    "size": 0
  },
  "loadStart_ws2812_data": {
    "address": 63296,
    "size": 0
  },
  "load_calibration_data": {
    "address": 55522,
    "size": 0
  },
  "lsm6dsl_acceleration_raw_get": {
    "address": 560295,
    "size": 0
  },
  "lsm6dsl_angular_rate_raw_get": {
    "address": 560341,
    "size": 0
  },
  "lsm6dsl_gy_data_rate_set": {
    "address": 560520,
    "size": 0
  },
  "lsm6dsl_gy_full_scale_set": {
    "address": 560564,
    "size": 0
  },
  "lsm6dsl_reset_set": {
    "address": 560608,
    "size": 0
  },
  "lsm6dsl_status_reg_get": {
    "address": 563018,
    "size": 0
  },
  "lsm6dsl_xl_data_rate_set": {
    "address": 560652,
    "size": 0
  },
  "lsm6dsl_xl_full_scale_set": {
    "address": 560696,
    "size": 0
  },
  "main": {
    "address": 563646,
    "size": 0
  },
  "main_init": {
    "address": 553634,
    "size": 0
  },
  "main_loop": {
    "address": 551143,
    "size": 0
  },
  "median_filter": {
    "address": 559761,
    "size": 0
  },
  "memcpy": {
    "address": 561961,
    "size": 0
  },
  "memset": {
    "address": 563567,
    "size": 0
  },
  "motor1CtrlISR": {
    "address": 49152,
    "size": 0
  },
  "motorHandle_M1": {
    "address": 62464,
    "size": 976
  },
  "motorInitAdc": {
    "address": 559655,
    "size": 0
  },
  "motorSetVars_M1": {
    "address": 62720,
    "size": 980
  },
  "motorVars_M1": {
    "address": 62848,
    "size": 982
  },
  "msg_buf": {
    "address": 61504,
    "size": 961
  },
  "mu_register_status_data": {
    "address": 561811,
    "size": 0
  },
  "mu_sdad_transmission": {
    "address": 560826,
    "size": 0
  },
  "mu_spi_transfer": {
    "address": 558374,
    "size": 0
  },
  "park_I_M1": {
    "address": 62470,
    "size": 976
  },
  "park_I_M1_CLA": {
    "address": 41254,
    "size": 644
  },
  "park_V_M1": {
    "address": 62474,
    "size": 976
  },
  "park_V_M1_CLA": {
    "address": 41258,
    "size": 644
  },
  "pi_Id_M1": {
    "address": 62528,
    "size": 977
  },
  "pi_Iq_M1": {
    "address": 62544,
    "size": 977
  },
  "pi_spd_M1": {
    "address": 62560,
    "size": 977
  },
  "prevEncState": {
    "address": 41220,
    "size": 644
  },
  "processCommand": {
    "address": 546800,
    "size": 0
  },
  "processObakeCommand": {
    "address": 551476,
    "size": 0
  },
  "process_state_data": {
    "address": 543328,
    "size": 0
  },
  "qsort": {
    "address": 555317,
    "size": 0
  },
  "readDataFromFlash": {
    "address": 561513,
    "size": 0
  },
  "readImuSequence": {
    "address": 560062,
    "size": 0
  },
  "resetMotorControl": {
    "address": 556377,
    "size": 0
  },
  "resp_buf": {
    "address": 61720,
    "size": 964
  },
  "restartMotorControl": {
    "address": 556859,
    "size": 0
  },
  "rotationCount": {
    "address": 62432,
    "size": 975
  },
  "rotationMatrix": {
    "address": 62402,
    "size": 975
  },
  "rs485Obj": {
    "address": 60352,
    "size": 943
  },
  "rs485Transmit": {
    "address": 559708,
    "size": 0
  },
  "rs485_watchdog_counter": {
    "address": 61438,
    "size": 959
  },
  "runEnd_ctrlfuncs": {
    "address": 49152,
    "size": 0
  },
  "runMotor1Control": {
    "address": 545960,
    "size": 0
  },
  "runMotor1OffsetsCalculation": {
    "address": 545096,
    "size": 0
  },
  "runMotorMonitor": {
    "address": 549944,
    "size": 0
  },
  "runStart_ctrlfuncs": {
    "address": 49152,
    "size": 0
  },
  "sciRxIsr": {
    "address": 54280,
    "size": 0
  },
  "sciTimerIsr": {
    "address": 54638,
    "size": 0
  },
  "sciTxIsr": {
    "address": 54798,
    "size": 0
  },
  "sciUpdateFreq": {
    "address": 555646,
    "size": 0
  },
  "sensorDataTransmission": {
    "address": 61447,
    "size": 960
  },
  "set_led_state": {
    "address": 562587,
    "size": 0
  },
  "setupClarke_I": {
    "address": 562420,
    "size": 0
  },
  "setupClarke_V": {
    "address": 562889,
    "size": 0
  },
  "setupControllers": {
    "address": 551763,
    "size": 0
  },
  "speedcalc_M1": {
    "address": 62592,
    "size": 978
  },
  "spiIsr": {
    "address": 557258,
    "size": 0
  },
  "spiIsr_imu": {
    "address": 557351,
    "size": 0
  },
  "spiObj": {
    "address": 61334,
    "size": 958
  },
  "spiObj_imu": {
    "address": 61376,
    "size": 959
  },
  "startSpiTransfer": {
    "address": 556962,
    "size": 0
  },
  "startSpiTransfer_imu": {
    "address": 558844,
    "size": 0
  },
  "stopMotorControl": {
    "address": 561717,
    "size": 0
  },
  "svgen_M1": {
    "address": 62478,
    "size": 976
  },
  "svgencurrent_M1": {
    "address": 62494,
    "size": 976
  },
  "svgencurrent_M1_CLA": {
    "address": 41346,
    "size": 646
  },
  "systemVars": {
    "address": 63360,
    "size": 990
  },
  "toggle_blink_state": {
    "address": 559330,
    "size": 0
  },
  "traj_spd_M1": {
    "address": 62510,
    "size": 976
  },
  "updateGlobalVariables": {
    "address": 555483,
    "size": 0
  },
  "update_circular_buffer": {
    "address": 561079,
    "size": 0
  },
  "userParams_M1": {
    "address": 62144,
    "size": 971
  },
  "velocityElec_Hz": {
    "address": 61460,
    "size": 960
  },
  "writeDataToFlash": {
    "address": 56008,
    "size": 0
  },
  "ws2812_data": {
    "address": 63312,
    "size": 989
  },
  "ws2812_init": {
    "address": 557065,
    "size": 0
  },
  "ws2812_isr": {
    "address": 55939,
    "size": 0
  },
  "ws2812_set_color": {
    "address": 563158,
    "size": 0
  },
  "ws2812_update": {
    "address": 550378,
    "size": 0
  }
};

function readSymbol(symbolName) {
    if (symbols[symbolName]) {
        var sym = symbols[symbolName];
        try {
            // Read from specific address
            var value = debugSession.memory.readData(0, sym.address, 4);
            print(symbolName + " @ 0x" + sym.address.toString(16) + " = " + value);
            return value;
        } catch (e) {
            print("Error reading " + symbolName + ": " + e.message);
        }
    } else {
        print("Symbol not found: " + symbolName);
    }
}

function searchAndRead(pattern) {
    var regex = new RegExp(pattern, 'i');
    for (var name in symbols) {
        if (regex.test(name)) {
            readSymbol(name);
        }
    }
}

// Example usage:
print("Available symbols: " + Object.keys(symbols).length);
print("\nReading motor-related variables:");
searchAndRead("motor");
