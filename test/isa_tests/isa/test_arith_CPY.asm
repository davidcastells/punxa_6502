; NMOS 6502 CPY: Y-M updates C/Z/N, with no register or operand write-back.
; C=(Y>=M), Z=(Y==M), N=bit7((Y-M)&$FF); V/D/I remain unchanged.
; ATmega CP/CPI supply comparison/preservation patterns, not carry/V semantics.
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
    cmp #expected ; only literal-byte equality; never CPY as its own oracle
    beq ok
    jmp fail
ok:
.endmacro

.macro SETUP value_y, value_a, carry, overflow, decimal
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
    ldy #value_y ; independently verified LDY helper
    ldx #$AA
    lda #value_a ; seed opposing Z or N without altering Y/C/V/D
.endmacro

.macro CHECK_CPY value_y, value_a, flags
    sta saved_a
    php ; capture comparison status before any checking helper changes it
    tya
    sta saved_y
    txa
    sta saved_x
    tsx
    txa
    sta saved_sp
    lda $01FF ; no reliance on PLA's missing N/Z or a CPY/transfer round trip
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags ; full saved status, fixed NMOS expectations
    lda #2
    sta check_stage
    lda saved_y
    CHECK_A value_y
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A value_a
    lda saved_x
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
.export cpy_probe_01, cpy_after_01, cpy_passed_01
    TEST_CASE 1
    SETUP $00, $55, 0, 1, 1
cpy_probe_01:
    cpy #$00
cpy_after_01:
    CHECK_CPY $00, $55, $7B
cpy_passed_01:

; CASE 2: Same equal operands with initial C=1: CPY ignores incoming C.
.export cpy_probe_02, cpy_after_02, cpy_passed_02
    TEST_CASE 2
    SETUP $00, $55, 1, 0, 0
cpy_probe_02:
    cpy #$00
cpy_after_02:
    CHECK_CPY $00, $55, $33
cpy_passed_02:

; CASE 3: Immediate $10<$20: clears C/Z, sets N from $F0.
.export cpy_probe_03, cpy_after_03, cpy_passed_03
    TEST_CASE 3
    SETUP $10, $00, 1, 0, 0
cpy_probe_03:
    cpy #$20
cpy_after_03:
    CHECK_CPY $10, $00, $B0
cpy_passed_03:

; CASE 4: Immediate $20>$10: sets C, clears Z; V stays set.
.export cpy_probe_04, cpy_after_04, cpy_passed_04
    TEST_CASE 4
    SETUP $20, $00, 0, 1, 0
cpy_probe_04:
    cpy #$10
cpy_after_04:
    CHECK_CPY $20, $00, $71
cpy_passed_04:

; CASE 5: Immediate $00<$FF, yet wrapped difference=$01 so N=0, C=0.
.export cpy_probe_05, cpy_after_05, cpy_passed_05
    TEST_CASE 5
    SETUP $00, $80, 1, 0, 1
cpy_probe_05:
    cpy #$FF
cpy_after_05:
    CHECK_CPY $00, $80, $38
cpy_passed_05:

; CASE 6: Immediate $FF>$00, yet difference=$FF so N=1, C=1.
.export cpy_probe_06, cpy_after_06, cpy_passed_06
    TEST_CASE 6
    SETUP $FF, $00, 0, 1, 1
cpy_probe_06:
    cpy #$00
cpy_after_06:
    CHECK_CPY $FF, $00, $F9
cpy_passed_06:

; CASE 7: Zero Page $FF==$FF sets C/Z, preserving D.
.export cpy_probe_07, cpy_after_07, cpy_passed_07
    TEST_CASE 7
    lda #$FF
    sta $40
    SETUP $FF, $55, 0, 0, 1
cpy_probe_07:
    cpy $40
cpy_after_07:
    CHECK_CPY $FF, $55, $3B
    CHECK_OPERAND $40, $FF
cpy_passed_07:

; CASE 8: Zero Page $7F<$80: C=0/N=1; V/D stay set.
.export cpy_probe_08, cpy_after_08, cpy_passed_08
    TEST_CASE 8
    lda #$80
    sta $41
    SETUP $7F, $00, 1, 1, 1
cpy_probe_08:
    cpy $41
cpy_after_08:
    CHECK_CPY $7F, $00, $F8
    CHECK_OPERAND $41, $80
cpy_passed_08:

; CASE 9: Zero Page $80>$7F: C=1/N=0; no signed-overflow update to V.
.export cpy_probe_09, cpy_after_09, cpy_passed_09
    TEST_CASE 9
    lda #$7F
    sta $42
    SETUP $80, $80, 0, 0, 0
cpy_probe_09:
    cpy $42
cpy_after_09:
    CHECK_CPY $80, $80, $31
    CHECK_OPERAND $42, $7F
cpy_passed_09:

; CASE 10: Absolute $80==$80; sets C/Z, preserving V/D.
.export cpy_probe_10, cpy_after_10, cpy_passed_10
    TEST_CASE 10
    lda #$80
    sta $1000
    SETUP $80, $55, 0, 1, 1
cpy_probe_10:
    cpy $1000
cpy_after_10:
    CHECK_CPY $80, $55, $7B
    CHECK_OPERAND $1000, $80
cpy_passed_10:

; CASE 11: Absolute last address $FFFF holds $FF; $7F<$FF gives N=1/C=0.
.export cpy_probe_11, cpy_after_11, cpy_passed_11
    TEST_CASE 11
    lda #$FF
    sta $FFFF
    SETUP $7F, $00, 1, 0, 0
cpy_probe_11:
    cpy $FFFF
cpy_after_11:
    CHECK_CPY $7F, $00, $B0
    CHECK_OPERAND $FFFF, $FF
cpy_passed_11:

; CASE 12: Absolute $FF>$7F gives N=1/C=1, with V unchanged at 1.
.export cpy_probe_12, cpy_after_12, cpy_passed_12
    TEST_CASE 12
    lda #$7F
    sta $1001
    SETUP $FF, $00, 0, 1, 0
cpy_probe_12:
    cpy $1001
cpy_after_12:
    CHECK_CPY $FF, $00, $F1
    CHECK_OPERAND $1001, $7F
cpy_passed_12:

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
