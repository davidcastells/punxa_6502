; NMOS 6502 BIT: N = M7, V = M6, Z = ((A & M) == 0); A, C, D, I and memory unchanged.
; Zero page ($24) and absolute ($2C). Fixed expectations; full status byte via PHP.
; Structure follows test_logic_EOR.asm.
; Every case seeds the OPPOSITE of the expected N, V and Z (V via ADC, N/Z via the
; final LDY in SETUP), so a BIT that leaves a flag untouched is detected.
; A is never equal to M or to A & M, so a BIT that writes A is detected.
; Operand values are chosen so that taking N/V from A, or from A & M, instead of
; from M gives a different status byte; Z cases have A and M both non-zero.
; Absolute cases put a different decoy byte at the matching zero-page address $40.
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
zp_operand = $40
abs_operand = $1240

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
    ldy #index_y ; seeds the incoming N/Z
.endmacro
.macro CHECK_BIT value, flags, index_x, index_y
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
    CHECK_A value ; A unchanged
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
; Write the operand and both neighbours (guards $11 / $22).
.macro PLACE address, value
    lda #$11
    sta address-1
    lda #$22
    sta address+1
    lda #value
    sta address
.endmacro
; BIT only reads memory: operand and neighbours must be unchanged.
.macro CHECK_MEMORY address, value
    lda #4
    sta check_stage
    lda address
    CHECK_A value
    lda address-1
    CHECK_A $11
    lda address+1
    CHECK_A $22
    lda #0
    sta check_stage
.endmacro
start:
    lda #0
    sta final_result
    sta check_stage

; ---------------------------------------------------------------- Zero page

; CASE 1: zp M=$C0 (N=1,V=1), A=$E0, A&M=$C0 -> Z=0. Seeded N=0,V=0,Z=1; C=1.
.export bit_probe_01, bit_after_01, bit_passed_01
    TEST_CASE 1
    PLACE zp_operand, $C0
    SETUP $E0, $A6, $00, 1, 0, 0
bit_probe_01:
    bit zp_operand
bit_after_01:
    CHECK_BIT $E0, $F1, $A6, $00
    CHECK_MEMORY zp_operand, $C0
bit_passed_01:

; CASE 2: zp M=$3F (N=0,V=0), A=$C0, A&M=$00 -> Z=1. A has bits 7/6 set, so
; N/V taken from A would be wrong. Seeded N=1,V=1,Z=0; D=1.
.export bit_probe_02, bit_after_02, bit_passed_02
    TEST_CASE 2
    PLACE zp_operand, $3F
    SETUP $C0, $A6, $80, 0, 1, 1
bit_probe_02:
    bit zp_operand
bit_after_02:
    CHECK_BIT $C0, $3A, $A6, $80
    CHECK_MEMORY zp_operand, $3F
bit_passed_02:

; CASE 3: zp M=$80 (N=1,V=0), A=$7F, A&M=$00 -> Z=1. N comes from M even though
; the AND result is zero. Seeded N=0,V=1,Z=0; C=1.
.export bit_probe_03, bit_after_03, bit_passed_03
    TEST_CASE 3
    PLACE zp_operand, $80
    SETUP $7F, $A6, $01, 1, 1, 0
bit_probe_03:
    bit zp_operand
bit_after_03:
    CHECK_BIT $7F, $B3, $A6, $01
    CHECK_MEMORY zp_operand, $80
bit_passed_03:

; CASE 4: zp M=$40 (N=0,V=1), A=$BF, A&M=$00 -> Z=1. V comes from M while A
; bit 6 is clear. I=1 (SEI) must be preserved. Seeded N=1,V=0,Z=0.
.export bit_probe_04, bit_after_04, bit_passed_04
    TEST_CASE 4
    PLACE zp_operand, $40
    SETUP $BF, $A6, $80, 0, 0, 0
    sei
bit_probe_04:
    bit zp_operand
bit_after_04:
    CHECK_BIT $BF, $76, $A6, $80
    cli
    CHECK_MEMORY zp_operand, $40
bit_passed_04:

; CASE 5: zp M=$01 (N=0,V=0), A=$FF, A&M=$01 -> Z=0. N/V from A or from M=$FF
; would be wrong. Seeded N=0,V=1,Z=1; C=1, D=1.
.export bit_probe_05, bit_after_05, bit_passed_05
    TEST_CASE 5
    PLACE zp_operand, $01
    SETUP $FF, $A6, $00, 1, 1, 1
bit_probe_05:
    bit zp_operand
bit_after_05:
    CHECK_BIT $FF, $39, $A6, $00
    CHECK_MEMORY zp_operand, $01
bit_passed_05:

; ----------------------------------------------------------------- Absolute
; zp_operand ($40) holds a decoy so reading $40 instead of $1240 is detected.

; CASE 6: abs M=$C1 (N=1,V=1), A=$03, A&M=$01 -> Z=0. Decoy $00.
; Seeded N=0,V=0,Z=1; D=1.
.export bit_probe_06, bit_after_06, bit_passed_06
    TEST_CASE 6
    PLACE zp_operand, $00
    PLACE abs_operand, $C1
    SETUP $03, $A6, $00, 0, 0, 1
bit_probe_06:
    bit abs_operand
bit_after_06:
    CHECK_BIT $03, $F8, $A6, $00
    CHECK_MEMORY abs_operand, $C1
    CHECK_MEMORY zp_operand, $00
bit_passed_06:

; CASE 7: abs M=$80 (N=1,V=0), A=$40, A&M=$00 -> Z=1. A bit 6 is set, so V
; from A would be wrong. Decoy $7F. Seeded N=0,V=1,Z=0; C=1, D=1.
.export bit_probe_07, bit_after_07, bit_passed_07
    TEST_CASE 7
    PLACE zp_operand, $7F
    PLACE abs_operand, $80
    SETUP $40, $A6, $01, 1, 1, 1
bit_probe_07:
    bit abs_operand
bit_after_07:
    CHECK_BIT $40, $BB, $A6, $01
    CHECK_MEMORY abs_operand, $80
    CHECK_MEMORY zp_operand, $7F
bit_passed_07:

; CASE 8: abs M=$7E (N=0,V=1), A=$81, A&M=$00 -> Z=1. I=1 preserved.
; Decoy $81. Seeded N=1,V=0,Z=0; C=1.
.export bit_probe_08, bit_after_08, bit_passed_08
    TEST_CASE 8
    PLACE zp_operand, $81
    PLACE abs_operand, $7E
    SETUP $81, $A6, $80, 1, 0, 0
    sei
bit_probe_08:
    bit abs_operand
bit_after_08:
    CHECK_BIT $81, $77, $A6, $80
    cli
    CHECK_MEMORY abs_operand, $7E
    CHECK_MEMORY zp_operand, $81
bit_passed_08:

; CASE 9: abs M=$E7 (N=1,V=1), A=$FF, A&M=$E7 -> Z=0. Decoy $00.
; Seeded N=0,V=0,Z=1; C=0, D=0.
.export bit_probe_09, bit_after_09, bit_passed_09
    TEST_CASE 9
    PLACE zp_operand, $00
    PLACE abs_operand, $E7
    SETUP $FF, $A6, $00, 0, 0, 0
bit_probe_09:
    bit abs_operand
bit_after_09:
    CHECK_BIT $FF, $F0, $A6, $00
    CHECK_MEMORY abs_operand, $E7
    CHECK_MEMORY zp_operand, $00
bit_passed_09:

; CASE 10: abs M=$00 (N=0,V=0), A=$FF -> Z=1. Decoy $FF.
; Seeded N=1,V=1,Z=0; C=1, D=1.
.export bit_probe_10, bit_after_10, bit_passed_10
    TEST_CASE 10
    PLACE zp_operand, $FF
    PLACE abs_operand, $00
    SETUP $FF, $A6, $80, 1, 1, 1
bit_probe_10:
    bit abs_operand
bit_after_10:
    CHECK_BIT $FF, $3B, $A6, $80
    CHECK_MEMORY abs_operand, $00
    CHECK_MEMORY zp_operand, $FF
bit_passed_10:

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
