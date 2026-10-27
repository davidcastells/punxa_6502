; NMOS 6502 TAX: A -> X; sets N/Z, preserves A/Y/SP/C/V/D/I.
; ATmega MOV supplies the transfer/source-preservation pattern, not flag rules.
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

; Seed C/V/D through implemented helpers. The final LDY deliberately gives
; opposing N/Z without changing A. I remains the simulator's initial zero.
.macro SETUP value, old_x, seed_y, carry, overflow, decimal
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
    ldx #old_x
    lda #value
    ldy #seed_y
.endmacro

.macro CHECK_TAX value, seed_y, flags
    ; Preserve the target state before any load, transfer or comparison.
    sta saved_a
    stx saved_x
    sty saved_y
    php
    tsx
    stx saved_sp
    ; Read the PHP byte directly: no reliance on PLA's known missing N/Z.
    lda $01FF
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags
    lda #2
    sta check_stage
    lda saved_x
    CHECK_A value
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A value
    lda #4
    sta check_stage
    lda saved_y
    CHECK_A seed_y
    lda #5
    sta check_stage
    lda saved_sp
    CHECK_A $FE ; SP was $FF; only the checker PHP has pushed one byte.
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: zero replaces $FF; clears N, sets Z; preserves C/V/D=1.
.export tax_probe_01, tax_after_01, tax_passed_01
    TEST_CASE 1
    SETUP $00, $FF, $80, 1, 1, 1
tax_probe_01:
    tax
tax_after_01:
    CHECK_TAX $00, $80, $7B
tax_passed_01:

; CASE 2: $01 replaces $80; clears preexisting Z; C/V/D remain zero.
.export tax_probe_02, tax_after_02, tax_passed_02
    TEST_CASE 2
    SETUP $01, $80, $00, 0, 0, 0
tax_probe_02:
    tax
tax_after_02:
    CHECK_TAX $01, $00, $30
tax_passed_02:

; CASE 3: largest positive byte $7F clears N; C remains set.
.export tax_probe_03, tax_after_03, tax_passed_03
    TEST_CASE 3
    SETUP $7F, $00, $80, 1, 0, 0
tax_probe_03:
    tax
tax_after_03:
    CHECK_TAX $7F, $80, $31
tax_passed_03:

; CASE 4: $80 sets N and clears Z; V remains set.
.export tax_probe_04, tax_after_04, tax_passed_04
    TEST_CASE 4
    SETUP $80, $7F, $00, 0, 1, 0
tax_probe_04:
    tax
tax_after_04:
    CHECK_TAX $80, $00, $F0
tax_passed_04:

; CASE 5: $FF sets N, clears Z and preserves C/D with V clear.
.export tax_probe_05, tax_after_05, tax_passed_05
    TEST_CASE 5
    SETUP $FF, $00, $00, 1, 0, 1
tax_probe_05:
    tax
tax_after_05:
    CHECK_TAX $FF, $00, $B9
tax_passed_05:

; CASE 6: typical alternating bits $55 clear N; V/D remain set.
.export tax_probe_06, tax_after_06, tax_passed_06
    TEST_CASE 6
    SETUP $55, $AA, $80, 0, 1, 1
tax_probe_06:
    tax
tax_after_06:
    CHECK_TAX $55, $80, $78
tax_passed_06:

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
