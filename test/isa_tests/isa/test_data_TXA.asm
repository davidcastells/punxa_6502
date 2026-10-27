; NMOS TXA: X -> A, updates N/Z, preserves X/Y/SP/C/V/D/I.
; ATmega MOV supplies value/source-preservation and sequence patterns only.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_p, saved_sp, check_stage, check_phase
.segment "CODE"
saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_p = $2013
saved_sp = $2014
check_stage = $2015
check_phase = $2016

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro
.macro SETUP source_x, old_a, seed_y, carry, overflow, decimal
    ldx #$FF
    txs
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
    ldx #source_x ; source setup never uses TXA
    lda #old_a
    ldy #seed_y ; opposing N/Z without changing source X or destination A
.endmacro
.macro CAPTURE base
    sta base
    stx base+1
    sty base+2
    php ; stores above preserve the target flags; no comparisons yet
.endmacro
.macro CHECK_SNAPSHOT base, stack_address, value_a, value_x, value_y, flags, phase
    lda #phase
    sta check_phase
    lda #1
    sta check_stage
    lda stack_address ; direct PHP snapshot, no PLA or reverse-transfer oracle
    sta base+3
    CHECK_A flags
    lda #2
    sta check_stage
    lda base
    CHECK_A value_a
    lda base+1
    CHECK_A value_x
    lda base+2
    CHECK_A value_y
.endmacro
.macro CHECK_SP expected
    lda #3
    sta check_stage
    lda saved_sp
    CHECK_A expected
    lda #0
    sta check_stage
    sta check_phase
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage
    sta check_phase

; CASE 1: Zero replaces FF; clears N, sets Z, preserves C/V/D=1.
.export txa_probe_01, txa_after_01, txa_captured_01, txa_checked_01, txa_passed_01
    TEST_CASE 1
    SETUP $00, $FF, $80, 1, 1, 1
txa_probe_01:
    txa
txa_after_01:
    CAPTURE saved_a
txa_captured_01:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $00, $00, $80, $7B, 1
txa_checked_01:
    CHECK_SP $FE
txa_passed_01:

; CASE 2: 01 clears old Z; preserves C/V/D=0.
.export txa_probe_02, txa_after_02, txa_captured_02, txa_checked_02, txa_passed_02
    TEST_CASE 2
    SETUP $01, $80, $00, 0, 0, 0
txa_probe_02:
    txa
txa_after_02:
    CAPTURE saved_a
txa_captured_02:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $01, $01, $00, $30, 1
txa_checked_02:
    CHECK_SP $FE
txa_passed_02:

; CASE 3: 7F clears old N, preserving C.
.export txa_probe_03, txa_after_03, txa_captured_03, txa_checked_03, txa_passed_03
    TEST_CASE 3
    SETUP $7F, $00, $80, 1, 0, 0
txa_probe_03:
    txa
txa_after_03:
    CAPTURE saved_a
txa_captured_03:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $7F, $7F, $80, $31, 1
txa_checked_03:
    CHECK_SP $FE
txa_passed_03:

; CASE 4: 80 sets N, clears Z, preserving V.
.export txa_probe_04, txa_after_04, txa_captured_04, txa_checked_04, txa_passed_04
    TEST_CASE 4
    SETUP $80, $7F, $00, 0, 1, 0
txa_probe_04:
    txa
txa_after_04:
    CAPTURE saved_a
txa_captured_04:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $80, $80, $00, $F0, 1
txa_checked_04:
    CHECK_SP $FE
txa_passed_04:

; CASE 5: FF sets N, clears Z, preserving C/D.
.export txa_probe_05, txa_after_05, txa_captured_05, txa_checked_05, txa_passed_05
    TEST_CASE 5
    SETUP $FF, $00, $00, 1, 0, 1
txa_probe_05:
    txa
txa_after_05:
    CAPTURE saved_a
txa_captured_05:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $FF, $FF, $00, $B9, 1
txa_checked_05:
    CHECK_SP $FE
txa_passed_05:

; CASE 6: Typical55 clears N, preserving V/D.
.export txa_probe_06, txa_after_06, txa_captured_06, txa_checked_06, txa_passed_06
    TEST_CASE 6
    SETUP $55, $AA, $80, 0, 1, 1
txa_probe_06:
    txa
txa_after_06:
    CAPTURE saved_a
txa_captured_06:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $55, $55, $80, $78, 1
txa_checked_06:
    CHECK_SP $FE
txa_passed_06:

; CASE 7: Consecutive X->A transfers 00->80->01, source X always preserved.
; Capture every intermediate state before comparisons. C/V/D stay1;
; only PHP snapshots change SP, so target entries are FF/FE/FD.
.export txa_probe_07_1, txa_after_07_1, txa_captured_07_1, txa_checked_07_1
.export txa_probe_07_2, txa_after_07_2, txa_captured_07_2, txa_checked_07_2
.export txa_probe_07_3, txa_after_07_3, txa_captured_07_3, txa_checked_07_3, txa_passed_07
    TEST_CASE 7
    SETUP $00, $55, $55, 1, 1, 1
txa_probe_07_1:
    txa
txa_after_07_1:
    CAPTURE $2020
txa_captured_07_1:
    ldx #$80
txa_probe_07_2:
    txa
txa_after_07_2:
    CAPTURE $2024
txa_captured_07_2:
    ldx #$01
txa_probe_07_3:
    txa
txa_after_07_3:
    CAPTURE $2028
txa_captured_07_3:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT $2020, $01FF, $00, $00, $55, $7B, 1
txa_checked_07_1:
    CHECK_SNAPSHOT $2024, $01FE, $80, $80, $55, $F9, 2
txa_checked_07_2:
    CHECK_SNAPSHOT $2028, $01FD, $01, $01, $55, $79, 3
txa_checked_07_3:
    CHECK_SP $FC
txa_passed_07:

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
