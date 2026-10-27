; NMOS TAY: A -> Y, updates N/Z, preserves A/X/SP/C/V/D/I.
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
.macro SETUP value, old_y, seed_x, carry, overflow, decimal
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
    ldy #old_y ; no TAY setup or reciprocal TYA checker
    lda #value
    ldx #seed_x ; seed N/Z independently without changing A/Y
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

; CASE 1: Zero replaces $FF; opposing initial N; C/V/D stay set.
.export tay_probe_01, tay_after_01, tay_captured_01, tay_checked_01, tay_passed_01
    TEST_CASE 1
    SETUP $00, $FF, $80, 1, 1, 1
tay_probe_01:
    tay
tay_after_01:
    CAPTURE saved_a
tay_captured_01:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $00, $80, $00, $7B, 1
tay_checked_01:
    CHECK_SP $FE
tay_passed_01:

; CASE 2: $01 clears old Z, preserving C/V/D=0.
.export tay_probe_02, tay_after_02, tay_captured_02, tay_checked_02, tay_passed_02
    TEST_CASE 2
    SETUP $01, $80, $00, 0, 0, 0
tay_probe_02:
    tay
tay_after_02:
    CAPTURE saved_a
tay_captured_02:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $01, $00, $01, $30, 1
tay_checked_02:
    CHECK_SP $FE
tay_passed_02:

; CASE 3: Largest positive $7F clears old N; C preserved.
.export tay_probe_03, tay_after_03, tay_captured_03, tay_checked_03, tay_passed_03
    TEST_CASE 3
    SETUP $7F, $00, $80, 1, 0, 0
tay_probe_03:
    tay
tay_after_03:
    CAPTURE saved_a
tay_captured_03:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $7F, $80, $7F, $31, 1
tay_checked_03:
    CHECK_SP $FE
tay_passed_03:

; CASE 4: $80 sets N and clears old Z; V preserved.
.export tay_probe_04, tay_after_04, tay_captured_04, tay_checked_04, tay_passed_04
    TEST_CASE 4
    SETUP $80, $7F, $00, 0, 1, 0
tay_probe_04:
    tay
tay_after_04:
    CAPTURE saved_a
tay_captured_04:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $80, $00, $80, $F0, 1
tay_checked_04:
    CHECK_SP $FE
tay_passed_04:

; CASE 5: $FF sets N, clears Z and preserves C/D with V clear.
.export tay_probe_05, tay_after_05, tay_captured_05, tay_checked_05, tay_passed_05
    TEST_CASE 5
    SETUP $FF, $00, $00, 1, 0, 1
tay_probe_05:
    tay
tay_after_05:
    CAPTURE saved_a
tay_captured_05:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $FF, $00, $FF, $B9, 1
tay_checked_05:
    CHECK_SP $FE
tay_passed_05:

; CASE 6: Typical $55 clears old N; V/D stay set.
.export tay_probe_06, tay_after_06, tay_captured_06, tay_checked_06, tay_passed_06
    TEST_CASE 6
    SETUP $55, $AA, $80, 0, 1, 1
tay_probe_06:
    tay
tay_after_06:
    CAPTURE saved_a
tay_captured_06:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT saved_a, $01FF, $55, $80, $55, $78, 1
tay_checked_06:
    CHECK_SP $FE
tay_passed_06:

; CASE 7: Consecutive transfers 00->80->01, no full setup between targets.
; Capture all intermediate registers/P before any comparisons; C/V/D stay1.
; Only the deliberate PHP snapshots change SP: target entries FF/FE/FD.
.export tay_probe_07_1, tay_after_07_1, tay_captured_07_1, tay_checked_07_1
.export tay_probe_07_2, tay_after_07_2, tay_captured_07_2, tay_checked_07_2
.export tay_probe_07_3, tay_after_07_3, tay_captured_07_3, tay_checked_07_3, tay_passed_07
    TEST_CASE 7
    SETUP $00, $55, $AA, 1, 1, 1
tay_probe_07_1:
    tay
tay_after_07_1:
    CAPTURE $2020
tay_captured_07_1:
    lda #$80
tay_probe_07_2:
    tay
tay_after_07_2:
    CAPTURE $2024
tay_captured_07_2:
    lda #$01
tay_probe_07_3:
    tay
tay_after_07_3:
    CAPTURE $2028
tay_captured_07_3:
    tsx
    stx saved_sp
    CHECK_SNAPSHOT $2020, $01FF, $00, $AA, $00, $7B, 1
tay_checked_07_1:
    CHECK_SNAPSHOT $2024, $01FE, $80, $AA, $80, $F9, 2
tay_checked_07_2:
    CHECK_SNAPSHOT $2028, $01FD, $01, $AA, $01, $79, 3
tay_checked_07_3:
    CHECK_SP $FC
tay_passed_07:

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
