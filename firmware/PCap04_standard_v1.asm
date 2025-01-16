;--------------------------------------------------------
;	File: PCap04_standard_vXX.asm
;   Description:
;	
;   This is the standard firmware that translates the TDC Start and TDC Stop values into 
;	CDC and RDC values.
;   Further depending on the configuration, the Capacitance and Resistance ratios are 
;   calculated. From 9 possible results, 8 results are given out in the Result register RES0....7.
;	Pre-requisite : The Resistance Ratios can be calculated for Internal or External sensor 
;					and Internal or External Reference. However, for this firmware, following 
;					should be ensured. 
;					PT0 - External Sensor or External Reference
;					PT1 - External Sensor ONLY
;					Internal or External Reference ought to be selected in the R_PORT_EN_IREF
;					bit of Configuration Register 23.
;	Outputs:
;		RES0 .... 5 : Capacitance Ratios for Capacitance Ports PC0.....5
;		RES6		: Resistance Ratio for External Sensor at Port PT1, w.r.t. Internal or External reference
;		RES7		: Resistance Ratio for Internal sensor, w.r.t. Internal or External reference
;		PULSE0 & PULSE1 :	Pulse Outputs
;
;              
;	Date  : 08.04.2016
;	Author: VK/OH
;--------------------------------------------------------

#device PCap04v1

CONST FPP_CRATIO				27					; FPP of the Capacitance Ratios result
CONST FPP_RRATIO				25					; FPP of the Resistance Ratios result
CONST C_REF_PORT_NUMBER			0					; Port number of the reference Capacitance port (0....6 for Grounded ; 0...2 for Floating)

;--------------------- Addresses in the NVRAM -----------------------------
CONST NV_PULSE0_CAL				800					; Address of calibration values for pulse0 output of capacitance measurement
CONST NV_PULSE1_CAL				NV_PULSE0_CAL + 12  ; Address of calibration values for pulse1 output of capacitance measurement

;------------------Persistent RAM ----------------------------
CONST RAM_CDC_MV_RSHIFT			30					; RAM that stores a copy of the NVRAM address containing the no. of right shifts on the CDC values
CONST RAM_EXTERNAL_FLAGS		31					; RAM that stores a copy of the CFG_ADD_EXTERNAL_FLAGS

;------------------Temporary memory ----------------------------
CONST C0_Ratio_RAM				0					; C0_Ratio from CDC
CONST C1_Ratio_RAM				1					; C1_Ratio from CDC
CONST C2_Ratio_RAM				2					; C2_Ratio from CDC
CONST C3_Ratio_RAM				3					; C3_Ratio from CDC
CONST C4_Ratio_RAM				4					; C4_Ratio from CDC
CONST C5_Ratio_RAM				5					; C5_Ratio from CDC

CONST R0_Ratio_RAM				6					; R0_Ratio from RDC
CONST R1_Ratio_RAM				7					; R1_Ratio from RDC
CONST R2_Ratio_RAM				8					; R2_Ratio from RDC
CONST R3_Ratio_RAM				9					; R3_Ratio from RDC

CONST PULSE0_current_result		10					; Value to be given out on Pulse0
CONST PULSE1_current_result		11					; Value to be given out on Pulse1

CONST AkkuC						20					; Temporary accumulator




#include <pcap_standard.h>

;------------------Arguments memory for ROM routines----------------------------
; For PULSE0
CONST PULSE0_Capacitance_1     	Arg_0 ; 74     		; Capacitance value at Calibration point 1
CONST PULSE0_Capacitance_2	    Arg_1 ; 75     		; Capacitance value at Calibration point 2
CONST PULSE0_out_1	    		Arg_2 ; 76     		; Pulse0 out value at Calibration point 1
CONST PULSE0_out_2	    		Arg_3 ; 77     		; Pulse0 out value at Calibration point 2
CONST PULSE0_out_max    		Arg_4 ; 78     		; Upper limit of Pulse0 out value 
CONST PULSE0_out_min     		Arg_5 ; 79     		; Lower limit of Pulse0 out value     
 
; For PULSE1 
CONST PULSE1_Capacitance_1     	Arg_0 ; 74     		; Capacitance value at Calibration point 1
CONST PULSE1_Capacitance_2	    Arg_1 ; 75     		; Capacitance value at Calibration point 2
CONST PULSE1_out_1	    		Arg_2 ; 76     		; PULSE1 out value at Calibration point 1
CONST PULSE1_out_2	    		Arg_3 ; 77     		; PULSE1 out value at Calibration point 2
CONST PULSE1_out_max    		Arg_4 ; 78     		; Upper limit of PULSE1 out value 
CONST PULSE1_out_min     		Arg_5 ; 79     		; Lower limit of PULSE1 out value         


; ----------------------- header files ----------------------

 ;#define __compile_lib__

; ---------------------- library elements ----------------

;#define __WORKAROUND_ROM_V01__

; ---------------------- Debugging ----------------------

 ; #define	__DEBUG__

; -------------------------------------------------------



#ifdef __compile_lib__
	org	1024
	
		#include "..\rom\tdc.lib"
		#include "..\rom\standard.lib"
		#include "..\rom\math.lib"
		#include "..\rom\dma.lib"
		#include "..\rom\rdc.lib"
		#include "..\rom\cdc.lib"
		#include "..\rom\memory.lib"
		#include "..\rom\pulse.lib"
		#include "..\rom\NVblock_copy.lib"
#else
		#include <PCap04_ROM_addresses_standard.h>
#endif



org 0

#include <std_dispatch.asm>
		
;----------------------------------------------------------

MK_main:

; Checking for CDC_TRIG_BG_N to trigger band gap before CDC
	
;	jcd		CDC_TRIG_BG_N, MK_skip_BG_TRIG
;          bitS TRIG_BG
		  
;MK_skip_BG_TRIG:	

;------------ Main Ratio determinations--------------------
	jsb		MK_cdc_process				

	jcd 	TENDFLAG_N, MK_skip_rdc
		jsb		MK_rdc_process
	MK_skip_rdc:

	jsb		MK_Pulse_Interface
	
; Testing ROM Version read
	; jsb		_ROM_Version__
	; rad		RES5
	; move	r, a
	jsb 	MK_EOP		
		
	
		

		
		
		
MK_cdc_process:
;---------------------------Capacitance Ratio Determination-----------------------------------------
; Input		: Stack - 1 : Number of fractional digits in the result (cdc_fpp)
;           : Stack - 0 : Reference Port Number(0....6 for Grounded ; 0...2 for Floating)
;			: A Accu 	: factor for Mi - Only the fractional part in format ufd8 (__sub_cdc_gain_corr__)
;						  The integer part is assumed to be 1.
;			: FLAG_CDC_INV bit in FLAGREG to be set/cleared
;			  0 : inverse capacitance ratios
;			  1	: capacitance ratios
; Output	: The addresses __sub_cdc_C0_Ratio_temp .... __sub_cdc_C5_Ratio_temp are updated with 
;			  relevant Capacitance Ratios (Or Inverse)
;---------------------------------------------------------------------------------------------------


	
;--------------------------------------------------------------------------------------
	push	8								; Initializing AkkuC = -8 = -(No. of CDC Measurement value registers)
	rad		rad_stack_6b
	move	a, r
	not		a
	inc		a
	rad		AkkuC							
	move	r, a
	
    load	a, M0
    push	DPTR0							; Initialising DPTR0 with the start address of the measurement value
    move	r, a
	
MK_format_MV_loop:

	rad 	_at_DPTR0						; Setting the RAM address of the measurement value 
	move	a, r							; Reading the measurement value
											; Detecting overflow in Measurement for each raw value (MV = 0xFFFFFFFF set by tdc.lib)
	inc r									; if r = 0xffffffff (-1) result of increment will be zero
	jEQ	MK_mw_overflow							

	rad		RAM_CDC_MV_RSHIFT				; Reading the number of right shifts configured
	move	b, r
	jEQ		MK_No_change_in_MV

		shiftR	a								; Shifting measurement value to right
		shiftR  a
		shiftR  a
		load	b, 0x1FFFFFFF					; mask raw value, because shiftR is sign dependant
		and		a, b

	MK_No_change_in_MV:

	rad		_at_DPTR0
	move	r, a							; Moving the shifted and masked value back to the MW register
	push	DPTR0
	inc		r								; Incrementing to point to the next MW

	rad		AkkuC
	inc		r
	move	b, r
	jNE		MK_format_MV_loop


;--------------------------------------------------------------------------------------
; Ratio or Inverse calculation

	; load2exp	a, FLAG_CDC_INV			; Setting FLAG_CDC_INV (Bit 5) of FLAGREG
	; rad 	FLAGREG
	; or 		r, a
	
	load2exp	a, FLAG_CDC_INV
	not		a							; Clearing FLAG_CDC_INV (Bit 5) of FLAGREG
	push 	FLAGREG
	and 	r, a

	load 	a, CFG_ADD_C_GAIN_CORR
	push	mem_add
	move	r, a
	jsb		_ROM_memory_rd_a_u08b__		; A-Accu = __sub_cdc_gain_corr__ (only fractional part with fpp 8, Integer part = 1)

	push	FPP_CRATIO					; Stack - 1 ---> Number of fpp in the result
	push 	C_REF_PORT_NUMBER			; Stack - 0 ---> Reference Port Number

	jsb		_ROM_cdc__					; Calling ROM routine for Ratio calculation

;------------------------------------------------------------------
; Checking if Asynchronous read by the serial interface is enabled (EN_ASYNC_RD in External Flag register)
; EN_ASYNC_RD=1  & INTERRUPT_IN_N=0 -----> Update the result registers
; EN_ASYNC_RD=1  & INTERRUPT_IN_N=1 -----> Do NOT Update the result registers
; EN_ASYNC_RD=0 -----> Always update the result registers

	rad		RAM_EXTERNAL_FLAGS					; RAM copy of External Flag register
	move 	a, r
	
	load	b, CFG_BM_EN_ASYNC_RD				; Loading bit mask for EN_ASYNC_RD
	and		b, a	
	jEQ		MK_Copy_Results						; Always update the result registers
	
	; INTERRUPT_IN_N = 0 when INT pin is 0, and 1 when INT pin is 1. 
	
	jcd		INTERRUPT_IN_N, MK_Copy_Results		; Update the result registers when INTERRUPT = 1 (processed)
	jcd 	TRUE, MK_cdc_reinitialize			; When previous interrupt is still unprocessed (0), only initialise cdc registers
		
												
;------------------------------------------------------------------

MK_Copy_Results:


; Copying the temporary bank of 6 addresses to the Result registers RES0 ..... RES5


#ifdef __DEBUG__
	load 	b, 2		; copy only the first 2 values (RES0 and RES1)
#else	
    ; --------------- mw2res ----------
    load	b, 6
#endif    



    load	a, __sub_cdc_C0_Ratio_temp
    push	DPTR1
    move	r, a
    load	a, RES0
    push	DPTR0
    move	r, a
    jsb		_ROM_dma__
	
; Copying the Cratio results to the persistent bank in RAM (For pulse output later)
    load	b, 6
    load	a, __sub_cdc_C0_Ratio_temp
    push	DPTR1
    move	r, a
    load	a, C0_Ratio_RAM
    push	DPTR0
    move	r, a
    jsb		_ROM_dma__
    jcd 	TRUE, MK_cdc_reinitialize

		MK_mw_overflow:
		rad		RES0
		move	r, a
		push	RES1
		move	r, a
		push	RES2
		move	r, a
		push	RES3
		move	r, a
		push	RES4
		move	r, a
		push	RES5
		move	r, a
		push	RES6
		move	r, a
		push	RES7
		move	r, a
		; if no  cdc_reinitialize is performed after "overflow" is detected, a power on reset is necessary.
	
; Re-initializing the CDC registers to 0 for the next measurement cycle
MK_cdc_reinitialize:	
    push	 1
    push	 M0
    jsb 	_ROM_cdc_initialize__
	jcd		TRUE, MK_cdc_process_end

;------------------------------------------------------------------
	
	
;------------------------------------------------------------------
MK_cdc_process_end:	
	jrt
	
;---------------------------Resistance Ratio Determination-----------------------------------------
 
MK_rdc_process:
	; Checking in the Configuration Register if External or Internal Reference is configured
; rad TM1
; move b, r
; rad RES6
; move r, b
; rad TM0
; move b, r
; rad RES7
; move r, b
	
	load	a, CFG_ADD_R_PORT_EN_IREF		; Reading the Configuration register
	push	mem_add
	move	r, a
	load 	a, CFG_BM_R_PORT_EN_IREF			; Setting the bit pertaining to R_PORT_EN_IREF of Config.Reg. in A-Akku
	 
	jsb		_ROM_memory_rd_b_u08b__			; B contains content of CFG_ADD_R_PORT_EN_IREF register 

	; If R_PORT_EN_IREF = 0, then External Reference ---> REF_PORT_NUMBER = 1
	; If R_PORT_EN_IREF = 1, then Internal Reference ---> REF_PORT_NUMBER = 0
	
	and		a, b
    jEQ 	MK_ext_ref_init		; A-Akku is 0, then Reference Port Number is 1
	 move	a, b				; If Internal Reference, then REF_PORT_NUMBER = 0
	 sub	a, b				; Clearing A-Akku
	 jcd	TRUE, MK_skip_ext_ref_init
MK_ext_ref_init:	 
	 load2exp	a, 0			; Initializing A-Akku = REF_PORT_NUMBER =  1	 
	 
	 
MK_skip_ext_ref_init:
	; A Akku contains the Reference Port Number

	push	FPP_RRATIO				; Number of fpp in the result
	
									; A-Akku		: Reference Port Number (0 or 1)
									; Stack - 0 	: Value of fpp of result = __rdc_fpp__ 
	jsb		_ROM_rdc__
	;jsb		_ROM_rdc_inverse__
		

;------------------------------------------------------------------
; Checking if Asynchronous read by the serial interface is enabled (EN_ASYNC_RD in External Flag register)
; EN_ASYNC_RD=1  & INTERRUPT_IN_N=0 -----> Update the result registers
; EN_ASYNC_RD=1  & INTERRUPT_IN_N=1 -----> Do NOT Update the result registers
; EN_ASYNC_RD=0 -----> Always update the result registers

	rad		RAM_EXTERNAL_FLAGS					; RAM copy of External Flag register
	move 	a, r
	
	load	b, CFG_BM_EN_ASYNC_RD				; Loading bit mask for EN_ASYNC_RD
	and		a, b	
	jEQ		MK_Copy_RDC_Results					; Always update the result registers
	
	jcd		INTERRUPT_IN_N, MK_Copy_RDC_Results ; Update the result registers when INTERRUPT = 1 (processed)
	jcd 	TRUE, MK_rdc_reinitialize			; When previous interrupt is still unprocessed (0), only initialise cdc registers	jcd TRUE, MK_rdc_reinitialize												
												
;------------------------------------------------------------------
; ---- if RDC finished, write RDC-Values to RES6 & 7 (NOTE : Overall only 8 Result registers)

	   ; rad	__sub_rdc_R0_Ratio_temp
       ; move	a, r
       ; rad	RES6
       ; move	r, a

       ; rad 	__sub_rdc_R1_Ratio_temp
       ; move	a, r
       ; rad 	RES7
       ; move	r, a
MK_Copy_RDC_Results:	   
       rad 	__sub_rdc_R2_Ratio_temp				; External Sensor w.r.t. Reference(Ext OR Int)
       move	a, r
       rad 	RES6
       move	r, a
	   rad	R0_Ratio_RAM						; Saving a copy in the RAM for pulse output selection later
	   move	r, a
	   
       rad 	__sub_rdc_R3_Ratio_temp				; Internal Sensor w.r.t. Reference(Ext OR Int)
       move	a, r
       rad 	RES7
       move	r, a
	   rad	R1_Ratio_RAM						; Saving a copy in the RAM for pulse output selection later
	   move	r, a
       
MK_rdc_reinitialize:
; Reinitializing the RDC registers to 0 for the next measurement cycle

        push	1
        push	TM0
        jsb 	_ROM_rdc_initialize__		

		load2exp a, RST_RDC					; Added so that TENDFLAG_N is cleared at the end of a RDC calculation
		push 	FLAGREG
		or		r, a
		
MK_rdc_process_end:
        jrt

;----------------------------------------------------------


MK_Pulse_Interface:

; Preparing to select the Capacitance or Resistance Ratios needed for the Pulse Interface
; C0_Ratio_RAM + Pulse_Select  = Address of Ratio for Pulse Interface
	
	load	a, CFG_ADD_Pulse_Select			; Reading the Pulse_Select from NVRAM
	push	mem_add
	move	r, a
	jsb		_ROM_memory_rd_a_u08b__		; A = Address containing Pulse_Select
	
	load2exp b, 7       				; load dividend for modulo division
	rad 	AkkuC
	move 	r, b
	sub 	b, r           				; To clear B-Akku
	jsb 	div_04         				; Modulo division
										; B = Pulse_Remainder<7..4>, A = Pulse_Remainder<3..0> *2^4
	shiftR 	a      				
	shiftR 	a				
	shiftR 	a				
	shiftR 	a				
	rad 	DPTR0        				; DPTR0 = Pulse_Remainder<3..0>
	move 	r, a        
	
	load 	a, C0_Ratio_RAM
	add 	b, a
	rad 	DPTR1 						; DPTR1 = &C0_Ratio_RAM + Pulse_Remainder<7..4>
	move 	r, b
	rad 	DPTR0						; DPTR0 = &C0_Ratio_RAM + Pulse_Remainder<3..0>
	add 	r, a

	rad		_at_DPTR0
	move	a, r
	rad		PULSE0_current_result
	move	r, a						; Value to be given out on Pulse0 Output
	rad		_at_DPTR1
	move	a, r
	rad		PULSE1_current_result
	move	r, a						; Value to be given out on Pulse1 Output



; For using the Pulse Interface ROM routine, the argument memory has to be initialised with the following:
;					Inputs :
;					A-Akku	: Value of result_n
;					DPTR0	: Start address of the RAM containing the constant values in 6 consecutive 
;						    addresses in the following order: 
;							result_1		(Same fpp as result_2 and result_n)
;							result_2 		(Same fpp as result_1 and result_n)
;							pulse_out_1 	(Integer)
;							pulse_out_2		(Integer)
;							pulse_out_max	(Integer)
;							pulse_out_min	(Integer)

;-------------------- PULSE0 Output-----------------------
; Copying 32-bit values : PULSE0_Capacitance_1 and PULSE0_Capacitance_2 to argument memory

		load	a, PULSE0_Capacitance_1			; DPTR0 <----- starting argument memory address (RAM)
		push 	DPTR0
		move 	r, a

		load2exp a, 1							; Count = 2
		load	b, 	NV_PULSE0_CAL				; Starting address of Pulse Interface Calibration values in NVRAM
		jsb		_ROM_NVblock_copy_32b_			; Subroutine to copy values from NVRAM -> RAM
												; Returns current NVRAM address in B-Akku
												
; Copying 16-bit values : PULSE0_out_1,PULSE0_out_2, PULSE0_out_max and PULSE0_out_min to argument memory
		
		load2exp a, SIGNED_VALUE_NV			
		not		a
		push	FLAGREG							; Read unsigned values
		and		r, a							; Clearing the SIGNED_VALUE_NV bit
			
		load	a, PULSE0_out_1					; DPTR0 <----- starting argument memory address (RAM)
		push 	DPTR0	
		move 	r, a	
	
		load2exp a, 1							; Count = 2
												; B-Akku already contains current NVRAM address containing PULSE0_out_1 value
		jsb		_ROM_NVblock_copy_16b_			; Subroutine to copy values from NVRAM -> RAM

												; copy _out_1 to _out_min
		rad PULSE0_out_1
		move a, r
		rad PULSE0_out_min
		move r, a

		rad PULSE0_out_2						; copy _out_2 to _out_max
		move a, r
		rad PULSE0_out_max
		move r, a												

;-----------------------------------------------
	rad		PULSE0_current_result
	move	a, r

	
;-----------------------------------------------	
	push	1
	push	PULSE0_Capacitance_1				; Pushing the address PULSE0_Capacitance_1 into the stack
	rad 	rad_stack_12b			
	move 	b, r		
	push 	DPTR0								; DPTR0 contains starting address of the 
	move 	r, b								; constant values for Pulse output from Capacitance measurement
			
			
												; Input : DPTR0	: start address of the list in RAM
												;		 A-Akku	: Value of result_n
	jsb		_ROM_pulse_loaded_cal_vals			; Output in A-Akku is an integer

	push	PULSE0
	move	r, a								; Moving pulse output to the respective register
			
			
;-------------------- PULSE1 Output-----------------------
; Copying 32-bit values : PULSE1_Capacitance_1 and PULSE1_Capacitance_2 to argument memory

		load	a, PULSE1_Capacitance_1			; DPTR0 <----- starting argument memory address (RAM)
		push 	DPTR0
		move 	r, a

		load2exp a, 1							; Count = 2
		load	b, 	NV_PULSE1_CAL				; Starting address of Pulse Interface Calibration values in NVRAM
		jsb		_ROM_NVblock_copy_32b_			; Subroutine to copy values from NVRAM -> RAM
												; Returns current NVRAM address in B-Akku
												
; Copying 16-bit values : PULSE1_out_1,PULSE1_out_2, PULSE1_out_max and PULSE1_out_min to argument memory
		
		load2exp a, SIGNED_VALUE_NV			
		not		a
		push	FLAGREG							; Read unsigned values
		and		r, a							; Clearing the SIGNED_VALUE_NV bit
			
		load	a, PULSE1_out_1					; DPTR0 <----- starting argument memory address (RAM)
		push 	DPTR0	
		move 	r, a	
	
		load2exp a, 1							; Count = 4
												; B-Akku already contains current NVRAM address containing PULSE1_out_1 value
		jsb		_ROM_NVblock_copy_16b_			; Subroutine to copy values from NVRAM -> RAM

												; copy _out_1 to _out_min
		rad PULSE1_out_1
		move a, r
		rad PULSE1_out_min
		move r, a

		rad PULSE1_out_2						; copy _out_2 to _out_max
		move a, r
		rad PULSE1_out_max
		move r, a												
;-----------------------------------------------
	rad		PULSE1_current_result
	move	a, r
	push	1
	push	PULSE1_Capacitance_1				; Pushing the address PULSE1_Capacitance_1 into the stack
	rad 	rad_stack_12b			
	move 	b, r		
	push 	DPTR0								; DPTR0 contains starting address of the 
	move 	r, b								; constant values for Pulse output from Capacitance measurement
			
			
												; Input : DPTR0	: start address of the list in RAM
												;		 A-Akku	: Value of result_n
	jsb		_ROM_pulse_loaded_cal_vals			; Output in A-Akku is an integer			
	push	PULSE1
	move	r, a								; Moving pulse output to the respective register
			
jrt


; --- EOF ---