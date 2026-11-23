; NMOS 6502 ASL: formal self-checking Phase A2 test.
; Expectations are fixed constants, never calculated with the target instruction.
; Cases 1-9: functional tests of all five forms (PHP-based flag checks).
; Cases 10-15: stack side-effect regression of the memory forms 0E/1E, without
; any PHP before the memory checks, plus bus monitoring (see bus_monitor.py).
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p, saved_x, check_stage
.segment "CODE"
saved_a = $2010
saved_p = $2011
saved_x = $2012
check_stage = $2015

.macro CHECK_BYTE expected
    .local ok, bad
    cmp #expected
    bne bad
    jmp ok
bad:
    jmp fail
ok:
.endmacro
; ADC establishes V; CMP establishes C, avoiding target CLC/SEC in setup.
; All arithmetic is binary. Last LDA supplies the requested N/Z.
.macro SEED_P value, carry, decimal, overflow
    cld
    lda #0
    adc #0 ; C becomes zero regardless of incoming carry
    .if overflow
        lda #$7F
        adc #1
    .endif
    lda #$80
    .if carry
        cmp #0
    .else
        cmp #$FF
    .endif
    .if decimal
        sed
    .else
        cld
    .endif
    lda #value
.endmacro
.macro CHECK_ACC value, status
    php
    sta saved_a
    ; Compare live A before PLA: saving A would truncate an invalid wide value.
    CHECK_BYTE value
    pla
    sta saved_p
    CHECK_BYTE status
.endmacro
.macro CHECK_MEMORY target, value, status, guard
    php
    sta saved_a
    pla
    sta saved_p
    lda target
    CHECK_BYTE value
    lda saved_a
    CHECK_BYTE $55 ; accumulator is unaffected by memory INC/ASL
    lda guard
    CHECK_BYTE $11
    lda target-1
    CHECK_BYTE $22
    lda target+1
    CHECK_BYTE $22
    lda saved_p
    CHECK_BYTE status
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; ===========================================================================
; Functional tests, all forms (cases 1-9)
; ===========================================================================

; CASE 1: Accumulator $00 -> $00
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $00, 1, 0, 1
probe_1:
    asl a
    CHECK_ACC $00, $72
passed_1:

; CASE 2: Accumulator $01 -> $02
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $01, 1, 0, 1
probe_2:
    asl a
    CHECK_ACC $02, $70
passed_2:

; CASE 3: Accumulator $40 -> $80
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $40, 1, 0, 1
probe_3:
    asl a
    CHECK_ACC $80, $F0
passed_3:

; CASE 4: Accumulator $80 -> $00
.export probe_4, passed_4
    TEST_CASE 4
    SEED_P $80, 1, 0, 1
probe_4:
    asl a
    CHECK_ACC $00, $73
passed_4:

; CASE 5: Accumulator $FF -> $FE
.export probe_5, passed_5
    TEST_CASE 5
    SEED_P $FF, 1, 0, 1
probe_5:
    asl a
    CHECK_ACC $FE, $F1
passed_5:

; CASE 6: Zero Page write-back
.export probe_6, passed_6
    TEST_CASE 6
    ldx #$21
    stx $0040
    ldx #$22
    stx $003F
    stx $0041
    ldx #$11
    stx $0042
    SEED_P $55, 1, 0, 1
probe_6:
    asl $40
    CHECK_MEMORY $0040, $42, $70, $0042
passed_6:

; CASE 7: Zero Page,X wrap and carry-out
.export probe_7, passed_7
    TEST_CASE 7
    ldx #$80
    stx $0001
    ldx #$22
    stx $0000
    stx $0002
    ldx #$11
    stx $0101
    ldx #2
    SEED_P $55, 1, 0, 1
probe_7:
    asl $FF,x
    CHECK_MEMORY $0001, $00, $73, $0101
passed_7:

; CASE 8: Absolute negative result
.export probe_8, passed_8
    TEST_CASE 8
    ldx #$40
    stx $1000
    ldx #$22
    stx $0FFF
    stx $1001
    ldx #$11
    stx $1002
    SEED_P $55, 1, 0, 1
probe_8:
    asl $1000
    CHECK_MEMORY $1000, $80, $F0, $1002
passed_8:

; CASE 9: Absolute,X page carry and high input
.export probe_9, passed_9
    TEST_CASE 9
    ldx #$FF
    stx $1300
    ldx #$22
    stx $12FF
    stx $1301
    ldx #$11
    stx $1200
    ldx #1
    SEED_P $55, 1, 0, 1
probe_9:
    asl $12FF,x
    CHECK_MEMORY $1300, $FE, $F1, $1200
passed_9:

; ===========================================================================
; Stack side-effect regression, memory forms 0E/1E (cases 10-15)
; ASL ABS/ABSX must change nothing but its operand: A, X, Y and SP are kept.
; SP is set to $FE in every case, so a stray stack write would land on $01FE.
; Operands: ordinary memory, the stack page away from SP, and exactly $0100+SP.
; Unlike cases 1-9, no PHP runs between the target and the checks (a PHP
; would overwrite $01FE and hide a stray write).
; Each asl_stk_probe_N is also bus-monitored (see bus_monitor.py): the only
; write allowed is to asl_stk_probe_N_ea, and only after the operand is read.
; Guard set-up and the guard check are shared routines (after `end`) so that
; the file fits in CODE $0200-$0FFF; they are only called with SP=$80, so the
; JSR return address lands on $0180/$017F, away from every guard and operand.
; ===========================================================================

; Guards (shared routine), then the operand.
.macro STK_INIT_MEMORY target, old
    ldx #$80
    txs ; JSR return address goes to $0180/$017F
    jsr stk_init_guards
    lda #old
    sta target
.endmacro

; Explicit SP=$FE and D=0; A=$55 must survive; Y seeds N/Z opposite to the result.
.macro STK_SETUP index_x, carry, seed_y
    cld
    .if carry
        sec
    .else
        clc
    .endif
    ldx #$FE
    txs
    ldx #index_x
    lda #$55
    ldy #seed_y
.endmacro

; Straight after the target, with no stack access: flags (branches only), live
; A/X/Y/SP, then the operand. After the operand has passed, its guard value is
; restored, so stk_check_guards checks every other guard exactly as if that
; one were skipped. Only then is SP moved to $80 for the JSR.
.macro STK_CHECK_RESULT target, value, carry, negative, zero, index_x, seed_y, guard
    .local n_ok, bad, done
    .if carry
        bcc bad
    .else
        bcs bad
    .endif
    .if negative
        bmi n_ok ; no BPL: SingleCycle6502 does not implement it
        jmp fail
n_ok:
    .else
        bmi bad
    .endif
    .if zero
        bne bad
    .else
        beq bad
    .endif
    cmp #$55 ; live A: memory forms keep the accumulator
    bne bad
    lda #2
    sta check_stage
    cpx #index_x
    bne bad
    cpy #seed_y
    bne bad
    tsx
    cpx #$FE
    bne bad
    lda #3
    sta check_stage
    lda target
    cmp #value
    bne bad
    lda #guard
    sta target
    ldx #$80
    txs ; JSR return address goes to $0180/$017F
    jsr stk_check_guards
    jmp done
bad:
    jmp fail
done:
.endmacro

.macro STK_GUARD location, expected
    lda location
    cmp #expected
    bne stk_guard_bad
.endmacro

; CASE 10 (stack 1): 0E Absolute, ordinary memory $1010, $81/C=1 -> $02; N/Z/C=0/0/1.
.export asl_stk_probe_1, asl_stk_probe_1_ea, asl_stk_passed_1
asl_stk_probe_1_ea = $1010
    TEST_CASE 10
    STK_INIT_MEMORY $1010, $81
    STK_SETUP $5A, 1, $80
asl_stk_probe_1:
    asl $1010
    STK_CHECK_RESULT $1010, $02, 1, 0, 0, $5A, $80, $22
asl_stk_passed_1:

; CASE 11 (stack 2): 1E Absolute,X, ordinary memory $12FF+$01 = $1300, $40 -> $80;
; N/Z/C=1/0/0.
.export asl_stk_probe_2, asl_stk_probe_2_ea, asl_stk_passed_2
asl_stk_probe_2_ea = $1300
    TEST_CASE 11
    STK_INIT_MEMORY $1300, $40
    STK_SETUP $01, 1, $00
asl_stk_probe_2:
    asl $12FF,x
    STK_CHECK_RESULT $1300, $80, 0, 1, 0, $01, $00, $22
asl_stk_passed_2:

; CASE 12 (stack 3): 0E Absolute, stack page $01F0 (not $0100+SP), $C0 -> $80;
; N/Z/C=1/0/1.
.export asl_stk_probe_3, asl_stk_probe_3_ea, asl_stk_passed_3
asl_stk_probe_3_ea = $01F0
    TEST_CASE 12
    STK_INIT_MEMORY $01F0, $C0
    STK_SETUP $5A, 0, $00
asl_stk_probe_3:
    asl $01F0
    STK_CHECK_RESULT $01F0, $80, 1, 1, 0, $5A, $00, $E2
asl_stk_passed_3:

; CASE 13 (stack 4): 1E Absolute,X, stack page $01E8+$08 = $01F0, $80 -> $00;
; N/Z/C=0/1/1.
.export asl_stk_probe_4, asl_stk_probe_4_ea, asl_stk_passed_4
asl_stk_probe_4_ea = $01F0
    TEST_CASE 13
    STK_INIT_MEMORY $01F0, $80
    STK_SETUP $08, 0, $80
asl_stk_probe_4:
    asl $01E8,x
    STK_CHECK_RESULT $01F0, $00, 1, 0, 1, $08, $80, $E2
asl_stk_passed_4:

; CASE 14 (stack 5): 0E Absolute, operand exactly $0100+SP = $01FE, $81 -> $02;
; N/Z/C=0/0/1.
.export asl_stk_probe_5, asl_stk_probe_5_ea, asl_stk_passed_5
asl_stk_probe_5_ea = $01FE
    TEST_CASE 14
    STK_INIT_MEMORY $01FE, $81
    STK_SETUP $5A, 0, $80
asl_stk_probe_5:
    asl $01FE
    STK_CHECK_RESULT $01FE, $02, 1, 0, 0, $5A, $80, $EE
asl_stk_passed_5:

; CASE 15 (stack 6): 1E Absolute,X, operand exactly $0100+SP: $01F0+$0E = $01FE,
; $41 -> $82; N/Z/C=1/0/0.
.export asl_stk_probe_6, asl_stk_probe_6_ea, asl_stk_passed_6
asl_stk_probe_6_ea = $01FE
    TEST_CASE 15
    STK_INIT_MEMORY $01FE, $41
    STK_SETUP $0E, 1, $00
asl_stk_probe_6:
    asl $01F0,x
    STK_CHECK_RESULT $01FE, $82, 0, 1, 0, $0E, $00, $EE
asl_stk_passed_6:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end

; ---------------------------------------------------------------------------
; Shared routines of the stack side-effect cases, always called with SP=$80.
; ---------------------------------------------------------------------------

; Recognizable guards around SP, around the stack-page operand and around the
; ordinary operands ($1200 detects a lost ABSX page carry).
stk_init_guards:
    lda #1
    sta check_stage
    lda #$D8
    sta $01E8 ; unindexed base of the stack-page ABSX case
    lda #$E1
    sta $01EF
    lda #$E2
    sta $01F0
    lda #$E3
    sta $01F1
    lda #$ED
    sta $01FD
    lda #$EE
    sta $01FE
    lda #$EF
    sta $01FF
    lda #$22
    sta $100F
    sta $1010
    sta $1011
    sta $12FF
    sta $1300
    sta $1301
    lda #$11
    sta $1200
    rts

; Every guard; the operand location holds its restored guard value.
stk_check_guards:
    lda #4
    sta check_stage
    STK_GUARD $01FE, $EE ; $0100+SP: a stray push lands here
    STK_GUARD $01FD, $ED
    STK_GUARD $01FF, $EF
    STK_GUARD $01E8, $D8
    STK_GUARD $01EF, $E1
    STK_GUARD $01F0, $E2
    STK_GUARD $01F1, $E3
    STK_GUARD $100F, $22
    STK_GUARD $1010, $22
    STK_GUARD $1011, $22
    STK_GUARD $12FF, $22
    STK_GUARD $1300, $22
    STK_GUARD $1301, $22
    STK_GUARD $1200, $11
    lda #0
    sta check_stage
    rts
stk_guard_bad:
    jmp fail
    .assert * <= $0FFF, lderror, "program must not overlap memory data guards"
