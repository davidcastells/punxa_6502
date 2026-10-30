; Original NMOS 6502 ROR: result=(old_C<<7)|(operand>>1), new_C=operand&1.
; Set N/Z from the 8-bit result; preserve V/D/I and unrelated registers/SP.
; ATmega ROR supplies zero/LSB/carry-in/shift patterns, not AVR flag semantics.
; Fixed expectations, never computed with ROR itself. All five standard forms.
; Pre/post PHP bytes independently check setup Carry and resulting flags.
; Direct stack reads avoid PLA/PLP; live accumulator comparison detects wide A.
; I=0 is the simulator convention; no physical reset, I=1 or timing claim.
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
    CHECK_MEM saved_sp, $FD ; two checker PHPs; ROR itself preserves SP=$FE
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

; CASE 1: 6A Accumulator, $00/C=0 -> $00; N/Z/C=0/1/0, clear seeded N.
.export ror_probe_01, ror_after_01, ror_captured_01, ror_passed_01
    TEST_CASE 1
    INIT_CASE
    SETUP_ACC $00, $80, $3C, 0, 0, 0
ror_probe_01:
    ror a
ror_after_01:
    CAPTURE_STATE
ror_captured_01:
    CHECK_ACC $00, $B0, $32, $80, $3C
ror_passed_01:

; CASE 2: 6A Accumulator, $00/C=1 -> $80; N/Z/C=1/0/0, preserve V/D=1.
.export ror_probe_02, ror_after_02, ror_captured_02, ror_passed_02
    TEST_CASE 2
    INIT_CASE
    SETUP_ACC $00, $00, $AA, 1, 1, 1
ror_probe_02:
    ror a
ror_after_02:
    CAPTURE_STATE
ror_captured_02:
    CHECK_ACC $80, $7B, $F8, $00, $AA
ror_passed_02:

; CASE 3: 6A Accumulator, $01/C=0 -> $00; N/Z/C=0/1/1, bit0 becomes Carry.
.export ror_probe_03, ror_after_03, ror_captured_03, ror_passed_03
    TEST_CASE 3
    INIT_CASE
    SETUP_ACC $01, $80, $55, 0, 1, 0
ror_probe_03:
    ror a
ror_after_03:
    CAPTURE_STATE
ror_captured_03:
    CHECK_ACC $00, $F0, $73, $80, $55
ror_passed_03:

; CASE 4: 6A Accumulator, $02/C=0 -> $01; N/Z/C=0/0/0, clear seeded Z.
.export ror_probe_04, ror_after_04, ror_captured_04, ror_passed_04
    TEST_CASE 4
    INIT_CASE
    SETUP_ACC $02, $00, $FF, 0, 0, 1
ror_probe_04:
    ror a
ror_after_04:
    CAPTURE_STATE
ror_captured_04:
    CHECK_ACC $01, $3A, $38, $00, $FF
ror_passed_04:

; CASE 5: 6A Accumulator, $80/C=0 -> $40; N/Z/C=0/0/0, logical shift.
.export ror_probe_05, ror_after_05, ror_captured_05, ror_passed_05
    TEST_CASE 5
    INIT_CASE
    SETUP_ACC $80, $80, $00, 0, 1, 0
ror_probe_05:
    ror a
ror_after_05:
    CAPTURE_STATE
ror_captured_05:
    CHECK_ACC $40, $F0, $70, $80, $00
ror_passed_05:

; CASE 6: 6A Accumulator, $81/C=1 -> $C0; N/Z/C=1/0/1.
.export ror_probe_06, ror_after_06, ror_captured_06, ror_passed_06
    TEST_CASE 6
    INIT_CASE
    SETUP_ACC $81, $00, $81, 1, 0, 1
ror_probe_06:
    ror a
ror_after_06:
    CAPTURE_STATE
ror_captured_06:
    CHECK_ACC $C0, $3B, $B9, $00, $81
ror_passed_06:

; CASE 7: 6A Accumulator, $FF/C=0 -> $7F; N/Z/C=0/0/1, clear seeded N.
.export ror_probe_07, ror_after_07, ror_captured_07, ror_passed_07
    TEST_CASE 7
    INIT_CASE
    SETUP_ACC $FF, $80, $7F, 0, 0, 0
ror_probe_07:
    ror a
ror_after_07:
    CAPTURE_STATE
ror_captured_07:
    CHECK_ACC $7F, $B0, $31, $80, $7F
ror_passed_07:

; CASE 8: 6A Accumulator, $FF/C=1 -> $FF; N/Z/C=1/0/1, all-one boundary.
.export ror_probe_08, ror_after_08, ror_captured_08, ror_passed_08
    TEST_CASE 8
    INIT_CASE
    SETUP_ACC $FF, $00, $5A, 1, 1, 1
ror_probe_08:
    ror a
ror_after_08:
    CAPTURE_STATE
ror_captured_08:
    CHECK_ACC $FF, $7B, $F9, $00, $5A
ror_passed_08:

; CASE 9: 66 Zero Page $0040, $02/C=0 -> $01; N/Z/C=0/0/0, A stays $55.
.export ror_probe_09, ror_after_09, ror_captured_09, ror_passed_09
    TEST_CASE 9
    INIT_CASE
    INIT_MEMORY $0040, $02, $0042, $0140
    SETUP_MEMORY $80, $00, 0, 1, 1
ror_probe_09:
    ror $40
ror_after_09:
    CAPTURE_STATE
ror_captured_09:
    CHECK_MEMORY $0040, $01, $7A, $78, $80, $00, $0042, $0140
ror_passed_09:

; CASE 10: 76 Zero Page,X $FF+$02 wraps to $0001, $01/C=1 -> $80.
; N/Z/C=1/0/1; unindexed $00FF and unwrapped $0101 are distinct sentinels.
.export ror_probe_10, ror_after_10, ror_captured_10, ror_passed_10
    TEST_CASE 10
    INIT_CASE
    INIT_MEMORY $0001, $01, $00FF, $0101
    SETUP_MEMORY $02, $00, 1, 0, 0
ror_probe_10:
    ror $FF,x
ror_after_10:
    CAPTURE_STATE
ror_captured_10:
    CHECK_MEMORY $0001, $80, $33, $B1, $02, $00, $00FF, $0101
ror_passed_10:

; CASE 11: 6E Absolute $1000, $80/C=1 -> $C0; N/Z/C=1/0/0, A stays $55.
.export ror_probe_11, ror_after_11, ror_captured_11, ror_passed_11
    TEST_CASE 11
    INIT_CASE
    INIT_MEMORY $1000, $80, $1002, $0000
    SETUP_MEMORY $02, $00, 1, 1, 0
ror_probe_11:
    ror $1000
ror_after_11:
    CAPTURE_STATE
ror_captured_11:
    CHECK_MEMORY $1000, $C0, $73, $F0, $02, $00, $1002, $0000
ror_passed_11:

; CASE 12: 7E Absolute,X $12FF+$01 crosses to $1300, $01/C=0 -> $00.
; N/Z/C=0/1/1; $1200 detects lost page carry, $12FF is also a lower guard.
.export ror_probe_12, ror_after_12, ror_captured_12, ror_passed_12
    TEST_CASE 12
    INIT_CASE
    INIT_MEMORY $1300, $01, $1200, $1302
    SETUP_MEMORY $01, $80, 0, 0, 1
ror_probe_12:
    ror $12FF,x
ror_after_12:
    CAPTURE_STATE
ror_captured_12:
    CHECK_MEMORY $1300, $00, $B8, $3B, $01, $80, $1200, $1302
ror_passed_12:

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
