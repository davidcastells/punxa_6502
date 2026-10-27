; NMOS 6502 ORA: eight modes; fixed OR results, N/Z and state preservation.
; ATmega OR/ORI provide pattern/boundary ideas, not AVR flag semantics.
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
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro
.macro SETUP value, index_x, index_y, carry, overflow, decimal
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
    ldx #index_x
    lda #value
    ldy #index_y ; independent initial N/Z; also supplies indirect/absolute index
.endmacro
.macro CHECK_ORA value, flags, index_x, index_y
    sta saved_a
    php ; snapshot before comparison/load/transfer helpers
    stx saved_x
    sty saved_y
    tsx
    stx saved_sp
    lda $01FF ; direct PHP snapshot; no PLA dependency
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags
    lda #2
    sta check_stage
    lda saved_a
    CHECK_A value ; literal expected byte, never calculated with ORA
    lda #3
    sta check_stage
    lda saved_x
    CHECK_A index_x
    lda saved_y
    CHECK_A index_y
    lda saved_sp
    CHECK_A $FE
    lda #0
    sta check_stage
.endmacro
start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Immediate complementary $55|$AA=$FF, preserves C/V/D=1.
.export ora_probe_01, ora_after_01, ora_passed_01
    TEST_CASE 1
    SETUP $55, $A6, $00, 1, 1, 1
ora_probe_01:
    ora #$AA
ora_after_01:
    CHECK_ORA $FF, $F9, $A6, $00
ora_passed_01:

; CASE 2: Immediate zero|zero; clears old N and sets Z.
.export ora_probe_02, ora_after_02, ora_passed_02
    TEST_CASE 2
    SETUP $00, $A6, $80, 0, 0, 0
ora_probe_02:
    ora #$00
ora_after_02:
    CHECK_ORA $00, $32, $A6, $80
ora_passed_02:

; CASE 3: Immediate identity $55|$00=$55; clears stale Z.
.export ora_probe_03, ora_after_03, ora_passed_03
    TEST_CASE 3
    SETUP $55, $A6, $00, 1, 0, 0
ora_probe_03:
    ora #$00
ora_after_03:
    CHECK_ORA $55, $31, $A6, $00
ora_passed_03:

; CASE 4: Immediate all-one operand $33|$FF=$FF, preserves V.
.export ora_probe_04, ora_after_04, ora_passed_04
    TEST_CASE 4
    SETUP $33, $A6, $00, 0, 1, 0
ora_probe_04:
    ora #$FF
ora_after_04:
    CHECK_ORA $FF, $F0, $A6, $00
ora_passed_04:

; CASE 5: Immediate partial bit setting $A0|$0A=$AA, preserves C/D.
.export ora_probe_05, ora_after_05, ora_passed_05
    TEST_CASE 5
    SETUP $A0, $A6, $00, 1, 0, 1
ora_probe_05:
    ora #$0A
ora_after_05:
    CHECK_ORA $AA, $B9, $A6, $00
ora_passed_05:

; CASE 6: Zero Page $40=$59; $A6|$59=$FF.
.export ora_probe_06, ora_after_06, ora_passed_06
    TEST_CASE 6
    lda #$59
    sta $40
    SETUP $A6, $A6, $00, 0, 1, 1
ora_probe_06:
    ora $40
ora_after_06:
    CHECK_ORA $FF, $F8, $A6, $00
ora_passed_06:

; CASE 7: zp,X $FF+2 wraps to $01=$80, not $0101=$11.
.export ora_probe_07, ora_after_07, ora_passed_07
    TEST_CASE 7
    lda #$80
    sta $01
    lda #$11
    sta $0101
    SETUP $01, $02, $00, 0, 0, 0
ora_probe_07:
    ora $FF,x
ora_after_07:
    CHECK_ORA $81, $B0, $02, $00
ora_passed_07:

; CASE 8: Absolute $1000=$0F; $30|$0F=$3F, preserves C/V/D.
.export ora_probe_08, ora_after_08, ora_passed_08
    TEST_CASE 8
    lda #$0F
    sta $1000
    SETUP $30, $A6, $80, 1, 1, 1
ora_probe_08:
    ora $1000
ora_after_08:
    CHECK_ORA $3F, $79, $A6, $80
ora_passed_08:

; CASE 9: abs,X $12FF+1 -> $1300=$55, not $1200=$11.
.export ora_probe_09, ora_after_09, ora_passed_09
    TEST_CASE 9
    lda #$55
    sta $1300
    lda #$11
    sta $1200
    SETUP $00, $01, $80, 0, 0, 0
ora_probe_09:
    ora $12FF,x
ora_after_09:
    CHECK_ORA $55, $30, $01, $80
ora_passed_09:

; CASE 10: abs,Y $13FF+2 -> $1401=$AA; $55|$AA=$FF.
.export ora_probe_10, ora_after_10, ora_passed_10
    TEST_CASE 10
    lda #$AA
    sta $1401
    lda #$11
    sta $1301
    SETUP $55, $A6, $02, 1, 0, 0
ora_probe_10:
    ora $13FF,y
ora_after_10:
    CHECK_ORA $FF, $B1, $A6, $02
ora_passed_10:

; CASE 11: (zp,X) $60+4 -> pointer $64/$65 -> $1500=$F0.
.export ora_probe_11, ora_after_11, ora_passed_11
    TEST_CASE 11
    lda #$00
    sta $64
    sta $60
    lda #$15
    sta $65
    lda #$16
    sta $61
    lda #$F0
    sta $1500
    lda #$11
    sta $1600
    SETUP $0F, $04, $00, 0, 1, 0
ora_probe_11:
    ora ($60,x)
ora_after_11:
    CHECK_ORA $FF, $F0, $04, $00
ora_passed_11:

; CASE 12: (zp),Y pointer $16FF+1 crosses page to $1700=$80.
.export ora_probe_12, ora_after_12, ora_passed_12
    TEST_CASE 12
    lda #$FF
    sta $70
    lda #$16
    sta $71
    lda #$80
    sta $1700
    lda #$11
    sta $1600
    SETUP $40, $A6, $01, 1, 0, 1
ora_probe_12:
    ora ($70),y
ora_after_12:
    CHECK_ORA $C0, $B9, $A6, $01
ora_passed_12:

; CASE 13: (zp,X) $FF+1 wraps pointer to $00/$01, not $0100/$0101.
.export ora_probe_13, ora_after_13, ora_passed_13
    TEST_CASE 13
    lda #$00
    sta $00
    sta $0100
    lda #$18
    sta $01
    lda #$19
    sta $0101
    lda #$80
    sta $1800
    lda #$11
    sta $1900
    SETUP $01, $01, $00, 0, 0, 0
ora_probe_13:
    ora ($FF,x)
ora_after_13:
    CHECK_ORA $81, $B0, $01, $00
ora_passed_13:

; CASE 14: (zp,X) pointer at $FF reads its high byte at $00, not $0100.
.export ora_probe_14, ora_after_14, ora_passed_14
    TEST_CASE 14
    lda #$00
    sta $FF
    lda #$18
    sta $00
    lda #$19
    sta $0100
    lda #$40
    sta $1800
    lda #$11
    sta $1900
    SETUP $02, $01, $80, 1, 0, 1
ora_probe_14:
    ora ($FE,x)
ora_after_14:
    CHECK_ORA $42, $39, $01, $80
ora_passed_14:

; CASE 15: (zp),Y pointer high at $FF wraps to $00 before adding Y=1.
.export ora_probe_15, ora_after_15, ora_passed_15
    TEST_CASE 15
    lda #$00
    sta $FF
    lda #$18
    sta $00
    lda #$19
    sta $0100
    lda #$80
    sta $1801
    lda #$11
    sta $1901
    SETUP $04, $A6, $01, 0, 1, 0
ora_probe_15:
    ora ($FF),y
ora_after_15:
    CHECK_ORA $84, $F0, $A6, $01
ora_passed_15:

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
