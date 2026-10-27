; NMOS 6502 BCC: C=0 takes signed relative branch, preserving all flags/state.
; ATmega BRCC supplies condition/path patterns; offsets here are 6502 byte offsets.
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
.macro CHECK_BCC value, flags
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

; CASE 1: Forward taken with C=0; distinct good and bad path stores.
.export bcc_probe_01, bcc_good_01, bcc_bad_01, bcc_passed_01
    TEST_CASE 1
    SETUP $55, 0, 0, 0
bcc_probe_01:
    bcc bcc_good_01
bcc_bad_01:
    sty path_marker
    jmp check_01
bcc_good_01:
    stx path_marker
check_01:
    CHECK_BCC $55, $30
bcc_passed_01:

; CASE 2: Forward not taken C=1, even though the encoded target crosses a page.
.export bcc_probe_02, bcc_good_02, bcc_bad_02, bcc_passed_02
    TEST_CASE 2
    SETUP $80, 1, 1, 1
    jmp bcc_probe_02
    .align $100, $00
    .res $FA, $00
bcc_probe_02:
    bcc bcc_bad_02
bcc_good_02:
    stx path_marker
    jmp check_02
bcc_bad_02:
    sty path_marker
check_02:
    .assert (>bcc_bad_02) <> (>(bcc_probe_02+2)), lderror, "case2 encoded target must cross page"
    CHECK_BCC $80, $F9
bcc_passed_02:

; CASE 3: Backward taken C=0, with Z/V/D set.
.export bcc_probe_03, bcc_good_03, bcc_bad_03, bcc_passed_03
    TEST_CASE 3
    SETUP $00, 0, 1, 1
    jmp bcc_probe_03
bcc_good_03:
    stx path_marker
    jmp check_03
bcc_probe_03:
    bcc bcc_good_03
bcc_bad_03:
    sty path_marker
check_03:
    CHECK_BCC $00, $7A
bcc_passed_03:

; CASE 4: Backward not taken C=1; fallthrough is the only good path.
.export bcc_probe_04, bcc_good_04, bcc_bad_04, bcc_passed_04
    TEST_CASE 4
    SETUP $55, 1, 0, 0
    jmp bcc_probe_04
bcc_bad_04:
    sty path_marker
    jmp check_04
bcc_probe_04:
    bcc bcc_bad_04
bcc_good_04:
    stx path_marker
check_04:
    CHECK_BCC $55, $31
bcc_passed_04:

; CASE 5: Forward taken across a page with C=0; V remains set.
.export bcc_probe_05, bcc_good_05, bcc_bad_05, bcc_passed_05
    TEST_CASE 5
    SETUP $01, 0, 1, 0
    jmp bcc_probe_05
    .align $100, $00
    .res $FA, $00
bcc_probe_05:
    bcc bcc_good_05
bcc_bad_05:
    sty path_marker
    jmp check_05
bcc_good_05:
    .assert (>bcc_good_05) <> (>(bcc_probe_05+2)), lderror, "case5 must cross forward"
    stx path_marker
check_05:
    CHECK_BCC $01, $70
bcc_passed_05:

; CASE 6: Backward taken across a page with C=0; N/D remain set.
.export bcc_probe_06, bcc_good_06, bcc_bad_06, bcc_passed_06
    TEST_CASE 6
    SETUP $80, 0, 0, 1
    jmp bcc_probe_06
    .align $100, $00
    .res $F8, $00
bcc_good_06:
    stx path_marker
    jmp check_06
    .res 2, $00
bcc_probe_06:
    bcc bcc_good_06
bcc_bad_06:
    sty path_marker
check_06:
    .assert (>bcc_good_06) <> (>(bcc_probe_06+2)), lderror, "case6 must cross backward"
    CHECK_BCC $80, $B8
bcc_passed_06:

; CASE 7: Maximum positive displacement +127 bytes from PC after operand.
.export bcc_probe_07, bcc_good_07, bcc_bad_07, bcc_passed_07
    TEST_CASE 7
    SETUP $00, 0, 0, 0
bcc_probe_07:
    bcc bcc_good_07
bcc_bad_07:
    sty path_marker
    jmp check_07
    .res 121, $00
bcc_good_07:
    .assert bcc_good_07-(bcc_probe_07+2) = 127, lderror, "case7 must be +127"
    stx path_marker
check_07:
    CHECK_BCC $00, $32
bcc_passed_07:

; CASE 8: Minimum negative displacement -128 bytes; preserve N/V.
.export bcc_probe_08, bcc_good_08, bcc_bad_08, bcc_passed_08
    TEST_CASE 8
    SETUP $80, 0, 1, 0
    jmp bcc_probe_08
bcc_good_08:
    stx path_marker
    jmp check_08
    .res 120, $00
bcc_probe_08:
    bcc bcc_good_08
bcc_bad_08:
    sty path_marker
check_08:
    .assert bcc_good_08-(bcc_probe_08+2) = -128, lderror, "case8 must be -128"
    CHECK_BCC $80, $F0
bcc_passed_08:

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
