; Original NMOS 6502 BNE: branch exactly when Z=0; signed displacement
; is added to the PC after the two-byte instruction. Branches preserve flags.
; Reference: SY6500/MCS6500 Programming Manual, sections 4.1.1 and 4.1.2.6.
; This test uses BEQ/JMP for assertions, never BNE as its own checker.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p
.segment "CODE"

saved_a = $2010
saved_p = $2011

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

; ADC binary semantics were verified before introducing this BNE test.
; Set V through ADC instead of unsupported CLV/BIT/PLP helpers.
.macro SEED_BRANCH value, carry, decimal, overflow
    cld
    clc
    .if overflow
        lda #$7F
        adc #1
    .else
        lda #0
        adc #0
    .endif
    .if carry
        sec
    .else
        clc
    .endif
    .if decimal
        sed
    .else
        cld
    .endif
    lda #value
.endmacro

.macro CHECK_BRANCH value, flags
    php ; preserve status before any comparison/load
    sta saved_a
    pla
    sta saved_p
    and #$CF ; check all six real status flags; I remains 0
    CHECK_A flags
    lda saved_a
    CHECK_A value
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Forward taken, Z=0
.export probe_1, passed_1, taken_1
    TEST_CASE 1
    SEED_BRANCH $01, 0, 0, 0
probe_1:
    bne taken_1
    jmp fail
taken_1:
    CHECK_BRANCH $01, $00
passed_1:

; CASE 2: Forward not taken, Z=1
.export probe_2, passed_2, fallthrough_2
    TEST_CASE 2
    SEED_BRANCH $00, 1, 1, 1
probe_2:
    bne bad_2
fallthrough_2:
    jmp check_2
bad_2:
    jmp fail
check_2:
    CHECK_BRANCH $00, $4B
passed_2:

; CASE 3: Backward taken, Z=0
.export probe_3, passed_3, taken_3
    TEST_CASE 3
    SEED_BRANCH $80, 1, 0, 1
    jmp probe_3
taken_3:
    jmp check_3
probe_3:
    bne taken_3
    jmp fail
check_3:
    CHECK_BRANCH $80, $C1
passed_3:

; CASE 4: Backward not taken, Z=1
.export probe_4, passed_4, fallthrough_4
    TEST_CASE 4
    SEED_BRANCH $00, 0, 0, 0
    jmp probe_4
bad_4:
    jmp fail
probe_4:
    bne bad_4
fallthrough_4:
    CHECK_BRANCH $00, $02
passed_4:

; CASE 5: Forward taken across page boundary
.export probe_5, passed_5, taken_5
    TEST_CASE 5
    SEED_BRANCH $01, 1, 0, 1
    jmp probe_5
    .align $100, $00
    .res $FA, $00
probe_5:
    bne taken_5
    jmp fail
    .byte $00
taken_5:
    .assert (>taken_5) <> (>(probe_5+2)), lderror, "case 5 must cross forward"
    CHECK_BRANCH $01, $41
passed_5:

; CASE 6: Backward taken across page boundary
.export probe_6, passed_6, taken_6
    TEST_CASE 6
    SEED_BRANCH $80, 0, 1, 0
    jmp probe_6
    .align $100, $00
    .res $F8, $00
taken_6:
    jmp check_6
    .res 5, $00
probe_6:
    bne taken_6
    jmp fail
check_6:
    .assert (>taken_6) <> (>(probe_6+2)), lderror, "case 6 must cross backward"
    CHECK_BRANCH $80, $88
passed_6:

; CASE 7: Maximum positive displacement +127
.export probe_7, passed_7, taken_7
    TEST_CASE 7
    SEED_BRANCH $01, 0, 0, 0
probe_7:
    bne taken_7
    jmp fail
    .res 124, $00
taken_7:
    .assert taken_7-(probe_7+2) = 127, lderror, "case 7 must be +127"
    CHECK_BRANCH $01, $00
passed_7:

; CASE 8: Minimum negative displacement -128
.export probe_8, passed_8, taken_8
    TEST_CASE 8
    SEED_BRANCH $80, 1, 0, 1
    jmp probe_8
taken_8:
    jmp check_8
    .res 123, $00
probe_8:
    bne taken_8
    jmp fail
check_8:
    .assert taken_8-(probe_8+2) = -128, lderror, "case 8 must be -128"
    CHECK_BRANCH $80, $C1
passed_8:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
