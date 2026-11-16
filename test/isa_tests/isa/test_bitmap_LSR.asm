; Original NMOS 6502 LSR: result=operand>>1 (bit7 becomes 0), new_C=operand&1.
; N is always cleared, Z from the 8-bit result; incoming C is NOT shifted in.
; Preserve V/D/I and unrelated registers/SP. Memory forms write back and keep A.
; Fixed expectations, never computed with LSR itself. All five standard forms.
; Pre/post PHP bytes independently check setup Carry and resulting flags.
; Structure follows test_bitmap_ROR.asm. I=0 is the simulator convention.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_sp, pre_p, post_p, check_stage
.export guard_0, guard_1
.segment "CODE"

saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_sp = $2014
check_stage = $2015
guard_0 = $2020
guard_1 = $2021
pre_p = $01FF
post_p = $01FE

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

.macro CHECK_MEM location, expected
    lda location
    CHECK_A expected
.endmacro

.macro INIT_CASE
    lda #1
    sta check_stage ; value assertion is first, without loading over live A
    lda #$AA
    sta pre_p
    sta post_p
    lda #$22
    sta $01FD
    sta $0100
    lda #$A5
    sta guard_0
    lda #$5A
    sta guard_1
    ldx #$FF
    txs
.endmacro

.macro INIT_MEMORY target, old, sentinel_0, sentinel_1
    lda #old
    sta target
    lda #$22
    sta target-1
    sta target+1
    lda #$11
    sta sentinel_0
    lda #$33
    sta sentinel_1
.endmacro

.macro SEED_CVD carry, overflow, decimal
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
.endmacro

.macro SETUP_ACC old, seed_x, seed_y, carry, overflow, decimal
    SEED_CVD carry, overflow, decimal
    ldy #seed_y
    lda #old
    ldx #seed_x ; opposing N/Z without changing the operand or Carry
    php ; SP=$FE at target; fixed pre-P checks the actual C/V/D/I/N/Z setup
.endmacro

.macro SETUP_MEMORY index_x, seed_y, carry, overflow, decimal
    SEED_CVD carry, overflow, decimal
    ldx #index_x
    lda #$55 ; must remain unchanged by every memory form
    ldy #seed_y ; seed opposing N/Z without changing A/X/C/V/D
    php
.endmacro

.macro CAPTURE_STATE
    php ; FIRST post-target instruction, before comparisons/loads/TSX
    sta saved_a
    stx saved_x
    sty saved_y
.endmacro

.macro CHECK_COMMON expected_pre, expected_post, value_a, value_x, value_y
    lda #2
    sta check_stage
    CHECK_MEM pre_p, expected_pre
    lda #3
    sta check_stage
    CHECK_MEM post_p, expected_post ; full N/V/1/B/D/I/Z/C byte, not masked
    lda #4
    sta check_stage
    CHECK_MEM saved_a, value_a
    CHECK_MEM saved_x, value_x
    CHECK_MEM saved_y, value_y
    tsx
    stx saved_sp
    CHECK_MEM saved_sp, $FD ; two checker PHPs; LSR itself preserves SP=$FE
    lda #5
    sta check_stage
    CHECK_MEM $01FD, $22
    CHECK_MEM $0100, $22
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
.endmacro

.macro CHECK_ACC value, expected_pre, expected_post, seed_x, seed_y
    CHECK_A value ; live A, before any load can truncate/hide an invalid result
    CHECK_COMMON expected_pre, expected_post, value, seed_x, seed_y
    lda #0
    sta check_stage
.endmacro

.macro CHECK_MEMORY target, value, expected_pre, expected_post, index_x, seed_y, sentinel_0, sentinel_1
    CHECK_MEM target, value ; actual byte written back, before other assertions
    CHECK_COMMON expected_pre, expected_post, $55, index_x, seed_y
    CHECK_MEM target-1, $22
    CHECK_MEM target+1, $22
    CHECK_MEM sentinel_0, $11
    CHECK_MEM sentinel_1, $33
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result

; CASE 1: 4A Accumulator, $00/C=0 -> $00; N/Z/C=0/1/0, clears seeded N.
.export lsr_probe_01, lsr_after_01, lsr_captured_01, lsr_passed_01
    TEST_CASE 1
    INIT_CASE
    SETUP_ACC $00, $80, $3C, 0, 0, 0
lsr_probe_01:
    lsr a
lsr_after_01:
    CAPTURE_STATE
lsr_captured_01:
    CHECK_ACC $00, $B0, $32, $80, $3C
lsr_passed_01:

; CASE 2: 4A Accumulator, $01/C=0 -> $00; N/Z/C=0/1/1, bit0 becomes Carry.
.export lsr_probe_02, lsr_after_02, lsr_captured_02, lsr_passed_02
    TEST_CASE 2
    INIT_CASE
    SETUP_ACC $01, $80, $55, 0, 1, 0
lsr_probe_02:
    lsr a
lsr_after_02:
    CAPTURE_STATE
lsr_captured_02:
    CHECK_ACC $00, $F0, $73, $80, $55
lsr_passed_02:

; CASE 3: 4A Accumulator, $80/C=1 -> $40 (not $C0): incoming C is not
; shifted in; C=0, clears seeded Z, preserves V/D=1.
.export lsr_probe_03, lsr_after_03, lsr_captured_03, lsr_passed_03
    TEST_CASE 3
    INIT_CASE
    SETUP_ACC $80, $00, $AA, 1, 1, 1
lsr_probe_03:
    lsr a
lsr_after_03:
    CAPTURE_STATE
lsr_captured_03:
    CHECK_ACC $40, $7B, $78, $00, $AA
lsr_passed_03:

; CASE 4: 4A Accumulator, $FF/C=1 -> $7F; N/Z/C=0/0/1, N cleared, D kept.
.export lsr_probe_04, lsr_after_04, lsr_captured_04, lsr_passed_04
    TEST_CASE 4
    INIT_CASE
    SETUP_ACC $FF, $80, $7F, 1, 0, 1
lsr_probe_04:
    lsr a
lsr_after_04:
    CAPTURE_STATE
lsr_captured_04:
    CHECK_ACC $7F, $B9, $39, $80, $7F
lsr_passed_04:

; CASE 5: 4A Accumulator, $AA/C=1 -> $55; N/Z/C=0/0/0, incoming C cleared.
.export lsr_probe_05, lsr_after_05, lsr_captured_05, lsr_passed_05
    TEST_CASE 5
    INIT_CASE
    SETUP_ACC $AA, $00, $81, 1, 0, 0
lsr_probe_05:
    lsr a
lsr_after_05:
    CAPTURE_STATE
lsr_captured_05:
    CHECK_ACC $55, $33, $30, $00, $81
lsr_passed_05:

; CASE 6: 4A Accumulator, $55/C=0 -> $2A; N/Z/C=0/0/1, V kept.
.export lsr_probe_06, lsr_after_06, lsr_captured_06, lsr_passed_06
    TEST_CASE 6
    INIT_CASE
    SETUP_ACC $55, $80, $5A, 0, 1, 0
lsr_probe_06:
    lsr a
lsr_after_06:
    CAPTURE_STATE
lsr_captured_06:
    CHECK_ACC $2A, $F0, $71, $80, $5A
lsr_passed_06:

; CASE 7: 46 Zero Page $0040, $02/C=1 -> $01; N/Z/C=0/0/0, A stays $55.
.export lsr_probe_07, lsr_after_07, lsr_captured_07, lsr_passed_07
    TEST_CASE 7
    INIT_CASE
    INIT_MEMORY $0040, $02, $0042, $0140
    SETUP_MEMORY $80, $00, 1, 1, 1
lsr_probe_07:
    lsr $40
lsr_after_07:
    CAPTURE_STATE
lsr_captured_07:
    CHECK_MEMORY $0040, $01, $7B, $78, $80, $00, $0042, $0140
lsr_passed_07:

; CASE 8: 46 Zero Page $0040, $01/C=0 -> $00; N/Z/C=0/1/1, clears seeded N.
.export lsr_probe_08, lsr_after_08, lsr_captured_08, lsr_passed_08
    TEST_CASE 8
    INIT_CASE
    INIT_MEMORY $0040, $01, $0042, $0140
    SETUP_MEMORY $80, $80, 0, 0, 0
lsr_probe_08:
    lsr $40
lsr_after_08:
    CAPTURE_STATE
lsr_captured_08:
    CHECK_MEMORY $0040, $00, $B0, $33, $80, $80, $0042, $0140
lsr_passed_08:

; CASE 9: 56 Zero Page,X $FF+$02 wraps to $0001, $81 -> $40; N/Z/C=0/0/1.
; Unindexed $00FF and unwrapped $0101 are distinct sentinels.
.export lsr_probe_09, lsr_after_09, lsr_captured_09, lsr_passed_09
    TEST_CASE 9
    INIT_CASE
    INIT_MEMORY $0001, $81, $00FF, $0101
    SETUP_MEMORY $02, $80, 0, 0, 0
lsr_probe_09:
    lsr $FF,x
lsr_after_09:
    CAPTURE_STATE
lsr_captured_09:
    CHECK_MEMORY $0001, $40, $B0, $31, $02, $80, $00FF, $0101
lsr_passed_09:

; CASE 10: 4E Absolute $1000, $80/C=1 -> $40; N/Z/C=0/0/0, V kept.
.export lsr_probe_10, lsr_after_10, lsr_captured_10, lsr_passed_10
    TEST_CASE 10
    INIT_CASE
    INIT_MEMORY $1000, $80, $1002, $0010
    SETUP_MEMORY $02, $00, 1, 1, 0
lsr_probe_10:
    lsr $1000
lsr_after_10:
    CAPTURE_STATE
lsr_captured_10:
    CHECK_MEMORY $1000, $40, $73, $70, $02, $00, $1002, $0010
lsr_passed_10:

; CASE 11: 5E Absolute,X $12FF+$01 crosses to $1300, $FF -> $7F; N/Z/C=0/0/1.
; $1200 detects a lost page carry; D is preserved.
.export lsr_probe_11, lsr_after_11, lsr_captured_11, lsr_passed_11
    TEST_CASE 11
    INIT_CASE
    INIT_MEMORY $1300, $FF, $1200, $1302
    SETUP_MEMORY $01, $80, 0, 0, 1
lsr_probe_11:
    lsr $12FF,x
lsr_after_11:
    CAPTURE_STATE
lsr_captured_11:
    CHECK_MEMORY $1300, $7F, $B8, $39, $01, $80, $1200, $1302
lsr_passed_11:

; CASE 12: 5E Absolute,X $1000+$05 -> $1005, $01 -> $00; N/Z/C=0/1/1.
; The unindexed base $1000 must stay untouched.
.export lsr_probe_12, lsr_after_12, lsr_captured_12, lsr_passed_12
    TEST_CASE 12
    INIT_CASE
    INIT_MEMORY $1005, $01, $1000, $1105
    SETUP_MEMORY $05, $80, 0, 0, 0
lsr_probe_12:
    lsr $1000,x
lsr_after_12:
    CAPTURE_STATE
lsr_captured_12:
    CHECK_MEMORY $1005, $00, $B0, $33, $05, $80, $1000, $1105
lsr_passed_12:

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
