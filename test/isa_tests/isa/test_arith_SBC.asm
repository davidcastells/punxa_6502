; NMOS 6502 SBC Binary only: A - M - (1-C); C=1 means no borrow.
; SY6500/MCS6500 Programming Manual, sections 2.2.2 and 2.2.3.
; ATmega SBC supplies boundary/borrow scenarios, not its carry convention.
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

.macro SETUP value, carry, index_x, index_y, overflow
    lda #2 ; stage 2 identifies a failure of the live accumulator check
    sta check_stage
    ldx #$FF
    txs
    cld ; every target runs with D=0, regardless of prior state
    clc
    lda #0
    adc #0 ; seed V=0 without a decode-only CLV/PLP helper
    .if overflow
        lda #$7F
        adc #1
    .endif
    .if carry
        sec
    .else
        clc
    .endif
    ldx #index_x
    ldy #index_y
    lda #value
.endmacro

.macro CHECK_SBC value, flags, index_x, index_y
    sta saved_a
    php ; capture C/Z/N/V before CMP; never use SBC as its own checker
    CHECK_A value ; compare live A before an 8-bit load could hide width errors
    stx saved_x
    sty saved_y
    tsx
    stx saved_sp
    lda $01FF ; direct PHP snapshot, no PLA dependency
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags ; full PHP byte: includes D=0 and initial I=0
    lda #3
    sta check_stage
    lda saved_x
    CHECK_A index_x
    lda saved_y
    CHECK_A index_y
    lda saved_sp
    CHECK_A $FE ; only the checker PHP changed initial SP=$FF
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Immediate $30-$10, C=1 -> $20, no borrow; clears seeded V.
.export sbc_probe_01, sbc_after_01, sbc_passed_01
    TEST_CASE 1
    SETUP $30, 1, $AA, $55, 1
sbc_probe_01:
    sbc #$10
sbc_after_01:
    CHECK_SBC $20, $31, $AA, $55
sbc_passed_01:

; CASE 2: Same operands with C=0 subtract one more -> $1F, no borrow.
.export sbc_probe_02, sbc_after_02, sbc_passed_02
    TEST_CASE 2
    SETUP $30, 0, $AA, $55, 1
sbc_probe_02:
    sbc #$10
sbc_after_02:
    CHECK_SBC $1F, $31, $AA, $55
sbc_passed_02:

; CASE 3: Equal operands $55-$55, C=1 -> zero, C=1/Z=1.
.export sbc_probe_03, sbc_after_03, sbc_passed_03
    TEST_CASE 3
    SETUP $55, 1, $AA, $55, 1
sbc_probe_03:
    sbc #$55
sbc_after_03:
    CHECK_SBC $00, $33, $AA, $55
sbc_passed_03:

; CASE 4: $00-$00 with C=0 -> $FF, borrow due solely to carry-in.
.export sbc_probe_04, sbc_after_04, sbc_passed_04
    TEST_CASE 4
    SETUP $00, 0, $AA, $55, 0
sbc_probe_04:
    sbc #$00
sbc_after_04:
    CHECK_SBC $FF, $B0, $AA, $55
sbc_passed_04:

; CASE 5: $00-$01 with C=1 -> $FF, clears C and Z, sets N.
.export sbc_probe_05, sbc_after_05, sbc_passed_05
    TEST_CASE 5
    SETUP $00, 1, $AA, $55, 0
sbc_probe_05:
    sbc #$01
sbc_after_05:
    CHECK_SBC $FF, $B0, $AA, $55
sbc_passed_05:

; CASE 6: -128 minus +1 -> $7F, signed overflow, no unsigned borrow.
.export sbc_probe_06, sbc_after_06, sbc_passed_06
    TEST_CASE 6
    SETUP $80, 1, $AA, $55, 0
sbc_probe_06:
    sbc #$01
sbc_after_06:
    CHECK_SBC $7F, $71, $AA, $55
sbc_passed_06:

; CASE 7: +127 minus -1 -> $80, signed overflow with unsigned borrow.
.export sbc_probe_07, sbc_after_07, sbc_passed_07
    TEST_CASE 7
    SETUP $7F, 1, $AA, $55, 0
sbc_probe_07:
    sbc #$FF
sbc_after_07:
    CHECK_SBC $80, $F0, $AA, $55
sbc_passed_07:

; CASE 8: $FF-$00, C=1 -> $FF, C stays set; clears seeded V.
.export sbc_probe_08, sbc_after_08, sbc_passed_08
    TEST_CASE 8
    SETUP $FF, 1, $AA, $55, 1
sbc_probe_08:
    sbc #$00
sbc_after_08:
    CHECK_SBC $FF, $B1, $AA, $55
sbc_passed_08:

; CASE 9: Zero Page $40=$01; $01-$01-1 -> $FF, borrow.
.export sbc_probe_09, sbc_after_09, sbc_passed_09
    TEST_CASE 9
    lda #$01
    sta $40
    SETUP $01, 0, $AA, $55, 0
sbc_probe_09:
    sbc $40
sbc_after_09:
    CHECK_SBC $FF, $B0, $AA, $55
sbc_passed_09:

; CASE 10: zp,X $FF+2 wraps to $01, not $0101; $80-$7F-1 -> $00/V=1.
.export sbc_probe_10, sbc_after_10, sbc_passed_10
    TEST_CASE 10
    lda #$7F
    sta $01
    lda #$11
    sta $0101
    SETUP $80, 0, $02, $55, 0
sbc_probe_10:
    sbc $FF,x
sbc_after_10:
    CHECK_SBC $00, $73, $02, $55
sbc_passed_10:

; CASE 11: Absolute $1000=$80; $80-$80 -> zero, clears seeded V.
.export sbc_probe_11, sbc_after_11, sbc_passed_11
    TEST_CASE 11
    lda #$80
    sta $1000
    SETUP $80, 1, $AA, $55, 1
sbc_probe_11:
    sbc $1000
sbc_after_11:
    CHECK_SBC $00, $33, $AA, $55
sbc_passed_11:

; CASE 12: Absolute,X $12FF+1 -> $1300, not $1200; borrow.
.export sbc_probe_12, sbc_after_12, sbc_passed_12
    TEST_CASE 12
    lda #$01
    sta $1300
    lda #$11
    sta $1200
    SETUP $00, 1, $01, $55, 0
sbc_probe_12:
    sbc $12FF,x
sbc_after_12:
    CHECK_SBC $FF, $B0, $01, $55
sbc_passed_12:

; CASE 13: Absolute,Y $13FF+2 -> $1401; -128-1-1 -> $7E/V=1.
.export sbc_probe_13, sbc_after_13, sbc_passed_13
    TEST_CASE 13
    lda #$01
    sta $1401
    lda #$11
    sta $1301
    SETUP $80, 0, $AA, $02, 0
sbc_probe_13:
    sbc $13FF,y
sbc_after_13:
    CHECK_SBC $7E, $71, $AA, $02
sbc_passed_13:

; CASE 14: (zp,X): ($60+4) -> $1500=$20, not unindexed pointer $1600.
.export sbc_probe_14, sbc_after_14, sbc_passed_14
    TEST_CASE 14
    lda #$00
    sta $64
    sta $60
    lda #$15
    sta $65
    lda #$16
    sta $61
    lda #$20
    sta $1500
    lda #$11
    sta $1600
    SETUP $50, 1, $04, $55, 0
sbc_probe_14:
    sbc ($60,x)
sbc_after_14:
    CHECK_SBC $30, $31, $04, $55
sbc_passed_14:

; CASE 15: (zp),Y: $16FF+2 -> $1701=$80, not $1601; +127-(-128).
.export sbc_probe_15, sbc_after_15, sbc_passed_15
    TEST_CASE 15
    lda #$FF
    sta $70
    lda #$16
    sta $71
    lda #$80
    sta $1701
    lda #$11
    sta $1601
    SETUP $7F, 1, $AA, $02, 0
sbc_probe_15:
    sbc ($70),y
sbc_after_15:
    CHECK_SBC $FF, $F0, $AA, $02
sbc_passed_15:

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
