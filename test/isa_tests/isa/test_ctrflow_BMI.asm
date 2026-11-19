; NMOS 6502 BMI: N=1 takes signed relative branch, preserving all flags/state.
; Structure follows test_ctrflow_BCC.asm; offsets are 6502 byte offsets.
; N comes from bit 7 of the final LDA in SETUP. C, V, D and Z are varied
; independently so a branch on the wrong flag (or an unimplemented BMI that
; simply falls through) is detected. Case 2 uses $7F so only bit 7 decides.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_p, saved_sp, check_stage, path_marker
.segment "CODE"
saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_p = $2013
saved_sp = $2014
check_stage = $2015
path_marker = $2020

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro
.macro SETUP value, carry, overflow, decimal
    ldx #$FF
    txs
    lda #$11
    sta path_marker ; neither correct ($AA) nor wrong ($55) path marker
    cld
    clc
    lda #0
    adc #0
    .if overflow
        lda #$7F
        adc #1
    .endif
    .if carry
        sec
    .else
        clc
    .endif
    .if decimal
        sed
    .endif
    ldx #$AA
    ldy #$55
    lda #value
.endmacro
.macro CHECK_BRANCH value, flags
    ; Path stores use STX/STY: flags and unrelated registers stay unchanged.
    sta saved_a
    php
    stx saved_x
    sty saved_y
    tsx
    stx saved_sp
    lda $01FF
    sta saved_p
    lda #1
    sta check_stage
    lda path_marker
    CHECK_A $AA ; reaching end alone is not a valid branch assertion
    lda #2
    sta check_stage
    lda saved_p
    CHECK_A flags
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A value
    lda saved_x
    CHECK_A $AA
    lda saved_y
    CHECK_A $55
    lda saved_sp
    CHECK_A $FE
    lda #0
    sta check_stage
.endmacro
start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Forward taken with N=1; C/V/D clear.
.export bmi_probe_01, bmi_good_01, bmi_bad_01, bmi_passed_01
    TEST_CASE 1
    SETUP $80, 0, 0, 0
bmi_probe_01:
    bmi bmi_good_01
bmi_bad_01:
    sty path_marker
    jmp check_01
bmi_good_01:
    stx path_marker
check_01:
    CHECK_BRANCH $80, $B0
bmi_passed_01:

; CASE 2: Forward not taken N=0 (A=$7F, bit 6 set) with C/V/D set (a
; BCS/BVS-like test would branch); the encoded target crosses a page.
.export bmi_probe_02, bmi_good_02, bmi_bad_02, bmi_passed_02
    TEST_CASE 2
    SETUP $7F, 1, 1, 1
    jmp bmi_probe_02
    .align $100, $00
    .res $FA, $00
bmi_probe_02:
    bmi bmi_bad_02
bmi_good_02:
    stx path_marker
    jmp check_02
bmi_bad_02:
    sty path_marker
check_02:
    .assert (>bmi_bad_02) <> (>(bmi_probe_02+2)), lderror, "case2 encoded target must cross page"
    CHECK_BRANCH $7F, $79
bmi_passed_02:

; CASE 3: Backward taken N=1, with C/V/D set.
.export bmi_probe_03, bmi_good_03, bmi_bad_03, bmi_passed_03
    TEST_CASE 3
    SETUP $80, 1, 1, 1
    jmp bmi_probe_03
bmi_good_03:
    stx path_marker
    jmp check_03
bmi_probe_03:
    bmi bmi_good_03
bmi_bad_03:
    sty path_marker
check_03:
    CHECK_BRANCH $80, $F9
bmi_passed_03:

; CASE 4: Backward not taken N=0 with Z=1 and C=1 (BEQ/BCS-like tests would
; branch); fallthrough is the only good path.
.export bmi_probe_04, bmi_good_04, bmi_bad_04, bmi_passed_04
    TEST_CASE 4
    SETUP $00, 1, 0, 0
    jmp bmi_probe_04
bmi_bad_04:
    sty path_marker
    jmp check_04
bmi_probe_04:
    bmi bmi_bad_04
bmi_good_04:
    stx path_marker
check_04:
    CHECK_BRANCH $00, $33
bmi_passed_04:

; CASE 5: Forward taken across a page with N=1; V remains set.
.export bmi_probe_05, bmi_good_05, bmi_bad_05, bmi_passed_05
    TEST_CASE 5
    SETUP $FF, 0, 1, 0
    jmp bmi_probe_05
    .align $100, $00
    .res $FA, $00
bmi_probe_05:
    bmi bmi_good_05
bmi_bad_05:
    sty path_marker
    jmp check_05
bmi_good_05:
    .assert (>bmi_good_05) <> (>(bmi_probe_05+2)), lderror, "case5 must cross forward"
    stx path_marker
check_05:
    CHECK_BRANCH $FF, $F0
bmi_passed_05:

; CASE 6: Backward taken across a page with N=1; D remains set.
.export bmi_probe_06, bmi_good_06, bmi_bad_06, bmi_passed_06
    TEST_CASE 6
    SETUP $C0, 0, 0, 1
    jmp bmi_probe_06
    .align $100, $00
    .res $F8, $00
bmi_good_06:
    stx path_marker
    jmp check_06
    .res 2, $00
bmi_probe_06:
    bmi bmi_good_06
bmi_bad_06:
    sty path_marker
check_06:
    .assert (>bmi_good_06) <> (>(bmi_probe_06+2)), lderror, "case6 must cross backward"
    CHECK_BRANCH $C0, $B8
bmi_passed_06:

; CASE 7: Maximum positive displacement +127 bytes from PC after operand.
.export bmi_probe_07, bmi_good_07, bmi_bad_07, bmi_passed_07
    TEST_CASE 7
    SETUP $81, 0, 0, 0
bmi_probe_07:
    bmi bmi_good_07
bmi_bad_07:
    sty path_marker
    jmp check_07
    .res 121, $00
bmi_good_07:
    .assert bmi_good_07-(bmi_probe_07+2) = 127, lderror, "case7 must be +127"
    stx path_marker
check_07:
    CHECK_BRANCH $81, $B0
bmi_passed_07:

; CASE 8: Minimum negative displacement -128 bytes; preserve V/C.
.export bmi_probe_08, bmi_good_08, bmi_bad_08, bmi_passed_08
    TEST_CASE 8
    SETUP $FE, 1, 1, 0
    jmp bmi_probe_08
bmi_good_08:
    stx path_marker
    jmp check_08
    .res 120, $00
bmi_probe_08:
    bmi bmi_good_08
bmi_bad_08:
    sty path_marker
check_08:
    .assert bmi_good_08-(bmi_probe_08+2) = -128, lderror, "case8 must be -128"
    CHECK_BRANCH $FE, $F1
bmi_passed_08:

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
