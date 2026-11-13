; NMOS 6502 EOR: A = A ^ M; N/Z from the result; C/V/D/I preserved.
; Eight modes; fixed XOR results (never computed with EOR) and full status byte.
; Structure follows test_logic_ORA.asm; ATmega EOR supplies pattern ideas only.
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
    ldy #index_y ; seeds the incoming N/Z; also supplies the Y index
.endmacro
.macro CHECK_EOR value, flags, index_x, index_y
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
    CHECK_A value
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
; EOR only reads memory: the operand byte must be unchanged afterwards.
.macro CHECK_OPERAND address, value
    lda #4
    sta check_stage
    lda address
    CHECK_A value
    lda #0
    sta check_stage
.endmacro
start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Immediate complementary $55^$AA=$FF; sets N, preserves C/V/D=1.
.export eor_probe_01, eor_after_01, eor_passed_01
    TEST_CASE 1
    SETUP $55, $A6, $00, 1, 1, 1
eor_probe_01:
    eor #$AA
eor_after_01:
    CHECK_EOR $FF, $F9, $A6, $00
eor_passed_01:

; CASE 2: Immediate self-cancel $FF^$FF=$00; clears seeded N, sets Z.
.export eor_probe_02, eor_after_02, eor_passed_02
    TEST_CASE 2
    SETUP $FF, $A6, $80, 0, 0, 0
eor_probe_02:
    eor #$FF
eor_after_02:
    CHECK_EOR $00, $32, $A6, $80
eor_passed_02:

; CASE 3: Immediate identity $5A^$00=$5A; clears seeded Z, preserves C.
.export eor_probe_03, eor_after_03, eor_passed_03
    TEST_CASE 3
    SETUP $5A, $A6, $00, 1, 0, 0
eor_probe_03:
    eor #$00
eor_after_03:
    CHECK_EOR $5A, $31, $A6, $00
eor_passed_03:

; CASE 4: Immediate invert $33^$FF=$CC (differs from OR=$FF and AND=$33).
.export eor_probe_04, eor_after_04, eor_passed_04
    TEST_CASE 4
    SETUP $33, $A6, $00, 0, 1, 0
eor_probe_04:
    eor #$FF
eor_after_04:
    CHECK_EOR $CC, $F0, $A6, $00
eor_passed_04:

; CASE 5: Immediate shared bits cancel $0F^$8F=$80; preserves C/D.
.export eor_probe_05, eor_after_05, eor_passed_05
    TEST_CASE 5
    SETUP $0F, $A6, $00, 1, 0, 1
eor_probe_05:
    eor #$8F
eor_after_05:
    CHECK_EOR $80, $B9, $A6, $00
eor_passed_05:

; CASE 6: Zero Page $40=$59; $A6^$59=$FF; operand not written back.
.export eor_probe_06, eor_after_06, eor_passed_06
    TEST_CASE 6
    lda #$59
    sta $40
    SETUP $A6, $A6, $00, 0, 1, 1
eor_probe_06:
    eor $40
eor_after_06:
    CHECK_EOR $FF, $F8, $A6, $00
    CHECK_OPERAND $40, $59
eor_passed_06:

; CASE 7: zp,X $FF+2 wraps to $01=$C3, not $0101=$11; $C3^$C3=$00.
.export eor_probe_07, eor_after_07, eor_passed_07
    TEST_CASE 7
    lda #$C3
    sta $01
    lda #$11
    sta $0101
    SETUP $C3, $02, $80, 0, 0, 0
eor_probe_07:
    eor $FF,x
eor_after_07:
    CHECK_EOR $00, $32, $02, $80
eor_passed_07:

; CASE 8: Absolute $1000=$0F; $3C^$0F=$33; preserves C/V/D.
.export eor_probe_08, eor_after_08, eor_passed_08
    TEST_CASE 8
    lda #$0F
    sta $1000
    SETUP $3C, $A6, $80, 1, 1, 1
eor_probe_08:
    eor $1000
eor_after_08:
    CHECK_EOR $33, $79, $A6, $80
    CHECK_OPERAND $1000, $0F
eor_passed_08:

; CASE 9: abs,X $12FF+1 -> $1300=$55, not $1200=$11.
.export eor_probe_09, eor_after_09, eor_passed_09
    TEST_CASE 9
    lda #$55
    sta $1300
    lda #$11
    sta $1200
    SETUP $00, $01, $80, 0, 0, 0
eor_probe_09:
    eor $12FF,x
eor_after_09:
    CHECK_EOR $55, $30, $01, $80
eor_passed_09:

; CASE 10: abs,Y $13FF+2 -> $1401=$AA, not $1301=$11; $55^$AA=$FF.
.export eor_probe_10, eor_after_10, eor_passed_10
    TEST_CASE 10
    lda #$AA
    sta $1401
    lda #$11
    sta $1301
    SETUP $55, $A6, $02, 1, 0, 0
eor_probe_10:
    eor $13FF,y
eor_after_10:
    CHECK_EOR $FF, $B1, $A6, $02
eor_passed_10:

; CASE 11: (zp,X) $60+4 -> pointer $64/$65 -> $1500=$F0; $0F^$F0=$FF.
.export eor_probe_11, eor_after_11, eor_passed_11
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
eor_probe_11:
    eor ($60,x)
eor_after_11:
    CHECK_EOR $FF, $F0, $04, $00
eor_passed_11:

; CASE 12: (zp),Y pointer $16FF+1 crosses page to $1700=$80; $C0^$80=$40.
.export eor_probe_12, eor_after_12, eor_passed_12
    TEST_CASE 12
    lda #$FF
    sta $70
    lda #$16
    sta $71
    lda #$80
    sta $1700
    lda #$11
    sta $1600
    SETUP $C0, $A6, $01, 1, 0, 1
eor_probe_12:
    eor ($70),y
eor_after_12:
    CHECK_EOR $40, $39, $A6, $01
eor_passed_12:

; CASE 13: (zp,X) $FF+1 wraps pointer to $00/$01, not $0100/$0101.
.export eor_probe_13, eor_after_13, eor_passed_13
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
eor_probe_13:
    eor ($FF,x)
eor_after_13:
    CHECK_EOR $81, $B0, $01, $00
eor_passed_13:

; CASE 14: (zp,X) pointer at $FF reads its high byte at $00, not $0100.
.export eor_probe_14, eor_after_14, eor_passed_14
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
eor_probe_14:
    eor ($FE,x)
eor_after_14:
    CHECK_EOR $42, $39, $01, $80
eor_passed_14:

; CASE 15: (zp),Y pointer high at $FF wraps to $00 before adding Y=1.
; $84^$80=$04: bit7 cancels, so N=0 although A and M are both negative.
.export eor_probe_15, eor_after_15, eor_passed_15
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
    SETUP $84, $A6, $01, 0, 1, 0
eor_probe_15:
    eor ($FF),y
eor_after_15:
    CHECK_EOR $04, $70, $A6, $01
eor_passed_15:

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
    .assert * <= $0FFF, lderror, "program must not overlap memory data guards"
