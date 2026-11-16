; NMOS 6502 CPX: X-M updates C/Z/N, with no register or operand write-back.
; C=(X>=M), Z=(X==M), N=bit7((X-M)&$FF); V/D/I remain unchanged.
; Structure mirrors test_arith_CPY.asm with the roles of X and Y swapped.
; Required modes: Immediate ($E0), Zero Page ($E4); Absolute ($EC) also sampled.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_p, saved_sp, check_stage
.segment "CODE"

saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_p = $2013
saved_sp = $2014
check_stage = $2015

.macro CHECK_A expected
    .local ok
    cmp #expected ; only literal-byte equality; never CPX as its own oracle
    beq ok
    jmp fail
ok:
.endmacro

.macro SETUP value_x, value_a, carry, overflow, decimal
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
    ldx #value_x ; independently verified LDX helper
    ldy #$AA
    lda #value_a ; seed opposing Z or N without altering X/C/V/D
.endmacro

.macro CHECK_CPX value_x, value_a, flags
    sta saved_a
    php ; capture comparison status before any checking helper changes it
    txa
    sta saved_x
    tya
    sta saved_y
    tsx
    txa
    sta saved_sp
    lda $01FF ; direct PHP snapshot; no PLA dependency
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags ; full saved status, fixed NMOS expectations
    lda #2
    sta check_stage
    lda saved_x
    CHECK_A value_x ; CPX must not modify X
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A value_a
    lda saved_y
    CHECK_A $AA
    lda saved_sp
    CHECK_A $FE ; initial SP=$FF; checker PHP accounts for the one-byte push
    lda #0
    sta check_stage
.endmacro

.macro CHECK_OPERAND address, value
    lda #4
    sta check_stage
    lda address
    CHECK_A value ; memory operand must not be written back
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Immediate $00==$00 with initial C=0; sets C/Z, preserves V/D.
.export cpx_probe_01, cpx_after_01, cpx_passed_01
    TEST_CASE 1
    SETUP $00, $55, 0, 1, 1
cpx_probe_01:
    cpx #$00
cpx_after_01:
    CHECK_CPX $00, $55, $7B
cpx_passed_01:

; CASE 2: Same equal operands with initial C=1: CPX ignores incoming C.
.export cpx_probe_02, cpx_after_02, cpx_passed_02
    TEST_CASE 2
    SETUP $00, $55, 1, 0, 0
cpx_probe_02:
    cpx #$00
cpx_after_02:
    CHECK_CPX $00, $55, $33
cpx_passed_02:

; CASE 3: Immediate $10<$20: clears C/Z, sets N from $F0.
.export cpx_probe_03, cpx_after_03, cpx_passed_03
    TEST_CASE 3
    SETUP $10, $00, 1, 0, 0
cpx_probe_03:
    cpx #$20
cpx_after_03:
    CHECK_CPX $10, $00, $B0
cpx_passed_03:

; CASE 4: Immediate $20>$10: sets C, clears Z; V stays set.
.export cpx_probe_04, cpx_after_04, cpx_passed_04
    TEST_CASE 4
    SETUP $20, $00, 0, 1, 0
cpx_probe_04:
    cpx #$10
cpx_after_04:
    CHECK_CPX $20, $00, $71
cpx_passed_04:

; CASE 5: Immediate $00<$FF, yet wrapped difference=$01 so N=0, C=0.
.export cpx_probe_05, cpx_after_05, cpx_passed_05
    TEST_CASE 5
    SETUP $00, $80, 1, 0, 1
cpx_probe_05:
    cpx #$FF
cpx_after_05:
    CHECK_CPX $00, $80, $38
cpx_passed_05:

; CASE 6: Immediate $FF>$00, yet difference=$FF so N=1, C=1.
.export cpx_probe_06, cpx_after_06, cpx_passed_06
    TEST_CASE 6
    SETUP $FF, $00, 0, 1, 1
cpx_probe_06:
    cpx #$00
cpx_after_06:
    CHECK_CPX $FF, $00, $F9
cpx_passed_06:

; CASE 7: Zero Page $FF==$FF sets C/Z, preserving D.
.export cpx_probe_07, cpx_after_07, cpx_passed_07
    TEST_CASE 7
    lda #$FF
    sta $40
    SETUP $FF, $55, 0, 0, 1
cpx_probe_07:
    cpx $40
cpx_after_07:
    CHECK_CPX $FF, $55, $3B
    CHECK_OPERAND $40, $FF
cpx_passed_07:

; CASE 8: Zero Page $7F<$80: C=0/N=1; V/D stay set.
.export cpx_probe_08, cpx_after_08, cpx_passed_08
    TEST_CASE 8
    lda #$80
    sta $41
    SETUP $7F, $00, 1, 1, 1
cpx_probe_08:
    cpx $41
cpx_after_08:
    CHECK_CPX $7F, $00, $F8
    CHECK_OPERAND $41, $80
cpx_passed_08:

; CASE 9: Zero Page $80>$7F: C=1/N=0; no signed-overflow update to V.
.export cpx_probe_09, cpx_after_09, cpx_passed_09
    TEST_CASE 9
    lda #$7F
    sta $42
    SETUP $80, $80, 0, 0, 0
cpx_probe_09:
    cpx $42
cpx_after_09:
    CHECK_CPX $80, $80, $31
    CHECK_OPERAND $42, $7F
cpx_passed_09:

; CASE 10: Zero Page last byte $FF holds $01; $02>$01: C=1, Z/N=0, V kept.
; $0100 (one past zero page) holds $02 and would give Z=1 if read instead.
.export cpx_probe_10, cpx_after_10, cpx_passed_10
    TEST_CASE 10
    lda #$01
    sta $FF
    lda #$02
    sta $0100
    SETUP $02, $00, 0, 1, 0
cpx_probe_10:
    cpx $FF
cpx_after_10:
    CHECK_CPX $02, $00, $71
    CHECK_OPERAND $FF, $01
cpx_passed_10:

; CASE 11: Absolute $80==$80; sets C/Z, preserving V/D.
.export cpx_probe_11, cpx_after_11, cpx_passed_11
    TEST_CASE 11
    lda #$80
    sta $1000
    SETUP $80, $55, 0, 1, 1
cpx_probe_11:
    cpx $1000
cpx_after_11:
    CHECK_CPX $80, $55, $7B
    CHECK_OPERAND $1000, $80
cpx_passed_11:

; CASE 12: Absolute $FF>$7F gives N=1/C=1, with V unchanged at 1.
.export cpx_probe_12, cpx_after_12, cpx_passed_12
    TEST_CASE 12
    lda #$7F
    sta $1001
    SETUP $FF, $00, 0, 1, 0
cpx_probe_12:
    cpx $1001
cpx_after_12:
    CHECK_CPX $FF, $00, $F1
    CHECK_OPERAND $1001, $7F
cpx_passed_12:

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
