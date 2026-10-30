; NMOS 6502 SED ($F8, implied): set D only; preserve N/V/I/Z/C and A/X/Y/SP.
; ATmega CLC/SEC patterns: clear/set preconditions, idempotence, other-state checks.
; Fixed full PHP bytes; no decimal arithmetic oracle and no SED setup helper.
; D=1 cases retain D from the preceding checked target, then assert preconditions.
; PHP captures P immediately before/after each target; all comparisons come later.
; No PLA/PLP. Target SP is $FE, or $FD for the repeated operation in case 6.
; I=0 is this simulator's convention, not physical reset or I=1 validation.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_sp, check_stage
.export repeat_a, repeat_x, repeat_y, pre_p, post_p, repeat_p, guard_0, guard_1
.segment "CODE"

saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_sp = $2014
check_stage = $2015
repeat_a = $2030
repeat_x = $2031
repeat_y = $2032
pre_p = $01FF
post_p = $01FE
repeat_p = $01FD
guard_0 = $2020
guard_1 = $2021

.macro CHECK_MEM location, expected
    .local ok
    lda location
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

.macro INIT_STACK_GUARDS
    lda #$AA
    sta pre_p
    sta post_p
    sta repeat_p
    lda #$22
    sta $01FC
    sta $0100
    lda #$A5
    sta guard_0
    lda #$5A
    sta guard_1
    ldx #$FF
    txs
.endmacro

.macro SEED_REGS value_a, value_x, value_y, carry
    .if carry
        sec
    .else
        clc
    .endif
    ldx #value_x
    ldy #value_y
    lda #value_a ; final N/Z; none of these instructions changes V/D
.endmacro

; Caller first uses CLD. Binary ADC establishes V only as a setup helper;
; no ADC/SBC executes with D=1. Fixed pre/post PHP bytes are the SED oracle.
.macro SEED_BINARY value_a, value_x, value_y, carry, overflow
    clc
    lda #0
    adc #0
    .if overflow
        lda #$7F
        adc #1
    .endif
    SEED_REGS value_a, value_x, value_y, carry
.endmacro

; PHP and these stores preserve flags between target and captured snapshots.
.macro CAPTURE_REGS base
    sta base
    stx base+1
    sty base+2
.endmacro

.macro CHECK_REGS base, value_a, value_x, value_y
    CHECK_MEM base, value_a
    CHECK_MEM base+1, value_x
    CHECK_MEM base+2, value_y
.endmacro

.macro CHECK_CASE expected_pre, expected_post, value_a, value_x, value_y, repeated
    lda #1
    sta check_stage
    CHECK_MEM pre_p, expected_pre ; independently fixed setup, including D
    lda #2
    sta check_stage
    CHECK_MEM post_p, expected_post ; D set; all other status bits preserved
    lda #3
    sta check_stage
    CHECK_REGS saved_a, value_a, value_x, value_y
    .if repeated
        lda #4
        sta check_stage
        CHECK_MEM repeat_p, expected_post
        CHECK_REGS repeat_a, value_a, value_x, value_y
    .endif
    lda #5
    sta check_stage
    tsx
    stx saved_sp
    .if repeated
        CHECK_MEM saved_sp, $FC ; three checker PHPs, no target SP change
    .else
        CHECK_MEM saved_sp, $FD ; two checker PHPs, no target SP change
    .endif
    lda #6
    sta check_stage
    CHECK_MEM $01FC, $22
    CHECK_MEM $0100, $22
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
    .if repeated = 0
        CHECK_MEM repeat_p, $AA ; no third stack write in single-target cases
    .endif
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: D=0 -> 1; N/Z/C/V=0. CLD setup must produce pre-P=$30.
.export sed_seed_01, sed_probe_01_1, sed_after_01_1, sed_captured_01, sed_passed_01
    TEST_CASE 1
    INIT_STACK_GUARDS
    cld
sed_seed_01:
    SEED_BINARY $55, $AA, $3C, 0, 0
    php
sed_probe_01_1:
    sed
sed_after_01_1:
    php
    CAPTURE_REGS saved_a
sed_captured_01:
    CHECK_CASE $30, $38, $55, $AA, $3C, 0
sed_passed_01:

; CASE 2: D already 1 from checked case 1; V remains 0. Preserve Z=1/C=1.
; No arithmetic or D-changing setup; pre-P=$3B independently verifies inheritance.
.export sed_seed_02, sed_probe_02_1, sed_after_02_1, sed_captured_02, sed_passed_02
    TEST_CASE 2
    INIT_STACK_GUARDS
sed_seed_02:
    SEED_REGS $00, $80, $7F, 1
    php
sed_probe_02_1:
    sed
sed_after_02_1:
    php
    CAPTURE_REGS saved_a
sed_captured_02:
    CHECK_CASE $3B, $3B, $00, $80, $7F, 0
sed_passed_02:

; CASE 3: D=0 -> 1; preserve N=1/V=1/C=1/Z=0.
.export sed_seed_03, sed_probe_03_1, sed_after_03_1, sed_captured_03, sed_passed_03
    TEST_CASE 3
    INIT_STACK_GUARDS
    cld
sed_seed_03:
    SEED_BINARY $80, $00, $FF, 1, 1
    php
sed_probe_03_1:
    sed
sed_after_03_1:
    php
    CAPTURE_REGS saved_a
sed_captured_03:
    CHECK_CASE $F1, $F9, $80, $00, $FF, 0
sed_passed_03:

; CASE 4: D/V already 1 from checked case 3; preserve Z=1/C=0/N=0.
; Pre-P=$7A checks D/V explicitly; no arithmetic or SED setup helper.
.export sed_seed_04, sed_probe_04_1, sed_after_04_1, sed_captured_04, sed_passed_04
    TEST_CASE 4
    INIT_STACK_GUARDS
sed_seed_04:
    SEED_REGS $00, $FF, $00, 0
    php
sed_probe_04_1:
    sed
sed_after_04_1:
    php
    CAPTURE_REGS saved_a
sed_captured_04:
    CHECK_CASE $7A, $7A, $00, $FF, $00, 0
sed_passed_04:

; CASE 5: D=0 -> 1; preserve N=1/Z=0/C=0/V=0.
.export sed_seed_05, sed_probe_05_1, sed_after_05_1, sed_captured_05, sed_passed_05
    TEST_CASE 5
    INIT_STACK_GUARDS
    cld
sed_seed_05:
    SEED_BINARY $FF, $55, $AA, 0, 0
    php
sed_probe_05_1:
    sed
sed_after_05_1:
    php
    CAPTURE_REGS saved_a
sed_captured_05:
    CHECK_CASE $B0, $B8, $FF, $55, $AA, 0
sed_passed_05:

; CASE 6: Repeat SED with only flag-neutral PHP/stores between targets.
; Capture every intermediate state: D=0 -> 1 -> 1; C/V=1, N/Z=0 preserved.
.export sed_seed_06, sed_probe_06_1, sed_after_06_1
.export sed_probe_06_2, sed_after_06_2, sed_captured_06, sed_passed_06
    TEST_CASE 6
    INIT_STACK_GUARDS
    cld
sed_seed_06:
    SEED_BINARY $7F, $A5, $5A, 1, 1
    php
sed_probe_06_1:
    sed
sed_after_06_1:
    php
    CAPTURE_REGS saved_a
sed_probe_06_2:
    sed
sed_after_06_2:
    php
    CAPTURE_REGS repeat_a
sed_captured_06:
    CHECK_CASE $71, $79, $7F, $A5, $5A, 1
sed_passed_06:

success:
    lda #1
    sta final_result
    jmp end
fail:
    lda #255
    sta final_result
    jmp end
end:
    jmp end
