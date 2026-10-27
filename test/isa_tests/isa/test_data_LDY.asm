; NMOS 6502 LDY: five modes, fixed Y/N/Z and unaffected-state expectations.
; ATmega LDI/LDS supply value/address patterns; 6502 LDY updates N/Z.
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

.macro SETUP old_y, index_x, carry, overflow, decimal
    ldx #$FF
    txs
    lda #old_y
    tay ; set old Y without using the LDY target
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
    lda #$55
    ; Final LDX supplies initial N/Z and the index, without changing A/Y.
    ldx #index_x
.endmacro

.macro CHECK_LDY value, flags, index_x
    sta saved_a
    php ; capture target flags BEFORE TYA/TXA/TSX change N/Z
    tya ; no STY or CPY dependency in the Y assertion
    sta saved_y
    txa
    sta saved_x
    tsx
    txa
    sta saved_sp
    lda $01FF ; direct PHP snapshot, no PLA dependency
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags
    lda #2
    sta check_stage
    lda saved_y
    CHECK_A value
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A $55
    lda saved_x
    CHECK_A index_x
    lda saved_sp
    CHECK_A $FE ; initial SP=$FF, only the checker PHP has pushed
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Immediate typical $55 clears Z; preserves C/V/D=1.
.export ldy_probe_01, ldy_after_01, ldy_passed_01
    TEST_CASE 1
    SETUP $AA, $00, 1, 1, 1
ldy_probe_01:
    ldy #$55
ldy_after_01:
    CHECK_LDY $55, $79, $00
ldy_passed_01:

; CASE 2: Immediate zero replaces $FF; clears N and sets Z.
.export ldy_probe_02, ldy_after_02, ldy_passed_02
    TEST_CASE 2
    SETUP $FF, $80, 0, 0, 0
ldy_probe_02:
    ldy #$00
ldy_after_02:
    CHECK_LDY $00, $32, $80
ldy_passed_02:

; CASE 3: Immediate $7F clears N, preserving C.
.export ldy_probe_03, ldy_after_03, ldy_passed_03
    TEST_CASE 3
    SETUP $00, $80, 1, 0, 0
ldy_probe_03:
    ldy #$7F
ldy_after_03:
    CHECK_LDY $7F, $31, $80
ldy_passed_03:

; CASE 4: Immediate $80 sets N and clears Z, preserving V.
.export ldy_probe_04, ldy_after_04, ldy_passed_04
    TEST_CASE 4
    SETUP $7F, $00, 0, 1, 0
ldy_probe_04:
    ldy #$80
ldy_after_04:
    CHECK_LDY $80, $F0, $00
ldy_passed_04:

; CASE 5: Immediate $FF sets N and clears Z, preserving C/D.
.export ldy_probe_05, ldy_after_05, ldy_passed_05
    TEST_CASE 5
    SETUP $00, $00, 1, 0, 1
ldy_probe_05:
    ldy #$FF
ldy_after_05:
    CHECK_LDY $FF, $B9, $00
ldy_passed_05:

; CASE 6: Zero Page typical $A6; preserves V/D and clears old Z.
.export ldy_probe_06, ldy_after_06, ldy_passed_06
    TEST_CASE 6
    lda #$A6
    sta $40
    SETUP $59, $00, 0, 1, 1
ldy_probe_06:
    ldy $40
ldy_after_06:
    CHECK_LDY $A6, $F8, $00
ldy_passed_06:

; CASE 7: Zero Page last byte $FF holds zero; clears old N.
.export ldy_probe_07, ldy_after_07, ldy_passed_07
    TEST_CASE 7
    lda #$00
    sta $FF
    SETUP $FF, $80, 1, 1, 0
ldy_probe_07:
    ldy $FF
ldy_after_07:
    CHECK_LDY $00, $73, $80
ldy_passed_07:

; CASE 8: Zero Page,X $40+2 selects $42=$3C, not $40=$11.
.export ldy_probe_08, ldy_after_08, ldy_passed_08
    TEST_CASE 8
    lda #$3C
    sta $42
    lda #$11
    sta $40
    SETUP $C3, $02, 1, 0, 0
ldy_probe_08:
    ldy $40,x
ldy_after_08:
    CHECK_LDY $3C, $31, $02
ldy_passed_08:

; CASE 9: Zero Page,X $FF+2 wraps to $01, not $0101.
.export ldy_probe_09, ldy_after_09, ldy_passed_09
    TEST_CASE 9
    lda #$80
    sta $01
    lda #$11
    sta $0101
    SETUP $7F, $02, 0, 1, 0
ldy_probe_09:
    ldy $FF,x ; $B4 is a documented NMOS opcode despite decoder comments
ldy_after_09:
    CHECK_LDY $80, $F0, $02
ldy_passed_09:

; CASE 10: Absolute $1000 holds $FF; preserves C/D.
.export ldy_probe_10, ldy_after_10, ldy_passed_10
    TEST_CASE 10
    lda #$FF
    sta $1000
    SETUP $00, $00, 1, 0, 1
ldy_probe_10:
    ldy $1000
ldy_after_10:
    CHECK_LDY $FF, $B9, $00
ldy_passed_10:

; CASE 11: Absolute,X crosses $12FF+1 to zero at $1300, not $1200.
.export ldy_probe_11, ldy_after_11, ldy_passed_11
    TEST_CASE 11
    lda #$00
    sta $1300
    lda #$11
    sta $1200
    SETUP $FF, $01, 0, 1, 0
ldy_probe_11:
    ldy $12FF,x
ldy_after_11:
    CHECK_LDY $00, $72, $01
ldy_passed_11:

; CASE 12: Absolute,X crosses $13FF+2 to $1401=$80, not $1301.
.export ldy_probe_12, ldy_after_12, ldy_passed_12
    TEST_CASE 12
    lda #$80
    sta $1401
    lda #$11
    sta $1301
    SETUP $7F, $02, 1, 0, 0
ldy_probe_12:
    ldy $13FF,x
ldy_after_12:
    CHECK_LDY $80, $B1, $02
ldy_passed_12:

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
