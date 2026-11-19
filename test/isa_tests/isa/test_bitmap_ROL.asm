; Original NMOS 6502 ROL: result=((operand<<1)|old_C)&$FF, new_C=operand>>7.
; Set N/Z from the 8-bit result; preserve V/D/I and unrelated registers/SP.
; Fixed expectations, never computed with ROL itself. All five standard forms.
; Structure follows test_bitmap_ROR.asm (cases 1-12): pre/post PHP bytes
; independently check the setup and the full resulting status byte.
; Cases 13-16 are stack-guard cases for the four memory forms. A PHP capture
; writes to the free stack slot $0100+SP and would hide a write made there by
; ROL itself, so these cases do NOT use PHP after the target: they first store
; A (no flag or stack effect), then check the free slot, the slot below it, SP,
; A and the result. Their flags, X/Y and guard bytes are covered by cases 9-12.
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
    CHECK_MEM saved_sp, $FD ; two checker PHPs; ROL itself preserves SP=$FE
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

; Stack-guard setup: SP=$FF at the target, no PHP. $01FF is the free slot
; ($0100+SP); $01FE is the slot below it (a decrement-then-write push).
.macro SETUP_STACK index_x, seed_y, carry, overflow, decimal
    lda #$C6
    sta $01FF
    sta $01FE
    SEED_CVD carry, overflow, decimal
    ldx #index_x
    lda #$55
    ldy #seed_y
.endmacro

; Must directly follow the target. STA changes neither flags nor stack.
; Only what cases 9-12 cannot observe is checked here (code size limit):
; X/Y, neighbours, sentinels and flags of the same forms are checked there.
.macro CHECK_STACK target, value
    sta saved_a
    lda #6
    sta check_stage
    CHECK_MEM $01FF, $C6 ; free slot $0100+SP not written by ROL
    CHECK_MEM $01FE, $C6 ; nor the slot below it
    tsx
    stx saved_sp
    CHECK_MEM saved_sp, $FF ; SP unchanged by ROL
    lda #7
    sta check_stage
    CHECK_MEM saved_a, $55 ; A restored
    CHECK_MEM target, value ; result still written to the right address
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result

; CASE 1: 2A Accumulator, $00/C=0 -> $00; N/Z/C=0/1/0, clear seeded N.
.export rol_probe_01, rol_after_01, rol_captured_01, rol_passed_01
    TEST_CASE 1
    INIT_CASE
    SETUP_ACC $00, $80, $3C, 0, 0, 0
rol_probe_01:
    rol a
rol_after_01:
    CAPTURE_STATE
rol_captured_01:
    CHECK_ACC $00, $B0, $32, $80, $3C
rol_passed_01:

; CASE 2: 2A Accumulator, $00/C=1 -> $01; carry enters bit 0; preserve V/D=1.
.export rol_probe_02, rol_after_02, rol_captured_02, rol_passed_02
    TEST_CASE 2
    INIT_CASE
    SETUP_ACC $00, $00, $AA, 1, 1, 1
rol_probe_02:
    rol a
rol_after_02:
    CAPTURE_STATE
rol_captured_02:
    CHECK_ACC $01, $7B, $78, $00, $AA
rol_passed_02:

; CASE 3: 2A Accumulator, $80/C=0 -> $00; N/Z/C=0/1/1, bit7 becomes Carry.
.export rol_probe_03, rol_after_03, rol_captured_03, rol_passed_03
    TEST_CASE 3
    INIT_CASE
    SETUP_ACC $80, $80, $55, 0, 1, 0
rol_probe_03:
    rol a
rol_after_03:
    CAPTURE_STATE
rol_captured_03:
    CHECK_ACC $00, $F0, $73, $80, $55
rol_passed_03:

; CASE 4: 2A Accumulator, $40/C=0 -> $80; N/Z/C=1/0/0, clear seeded Z; D=1.
.export rol_probe_04, rol_after_04, rol_captured_04, rol_passed_04
    TEST_CASE 4
    INIT_CASE
    SETUP_ACC $40, $00, $FF, 0, 0, 1
rol_probe_04:
    rol a
rol_after_04:
    CAPTURE_STATE
rol_captured_04:
    CHECK_ACC $80, $3A, $B8, $00, $FF
rol_passed_04:

; CASE 5: 2A Accumulator, $55/C=1 -> $AB; N/Z/C=1/0/0, alternating bits.
.export rol_probe_05, rol_after_05, rol_captured_05, rol_passed_05
    TEST_CASE 5
    INIT_CASE
    SETUP_ACC $55, $00, $80, 1, 1, 0
rol_probe_05:
    rol a
rol_after_05:
    CAPTURE_STATE
rol_captured_05:
    CHECK_ACC $AB, $73, $F0, $00, $80
rol_passed_05:

; CASE 6: 2A Accumulator, $81/C=1 -> $03; N/Z/C=0/0/1, carry in and out; D=1.
.export rol_probe_06, rol_after_06, rol_captured_06, rol_passed_06
    TEST_CASE 6
    INIT_CASE
    SETUP_ACC $81, $00, $81, 1, 0, 1
rol_probe_06:
    rol a
rol_after_06:
    CAPTURE_STATE
rol_captured_06:
    CHECK_ACC $03, $3B, $39, $00, $81
rol_passed_06:

; CASE 7: 2A Accumulator, $FF/C=0 -> $FE; N/Z/C=1/0/1, clear seeded Z.
.export rol_probe_07, rol_after_07, rol_captured_07, rol_passed_07
    TEST_CASE 7
    INIT_CASE
    SETUP_ACC $FF, $00, $7F, 0, 0, 0
rol_probe_07:
    rol a
rol_after_07:
    CAPTURE_STATE
rol_captured_07:
    CHECK_ACC $FE, $32, $B1, $00, $7F
rol_passed_07:

; CASE 8: 2A Accumulator, $FF/C=1 -> $FF; N/Z/C=1/0/1, all-one boundary; V/D=1.
.export rol_probe_08, rol_after_08, rol_captured_08, rol_passed_08
    TEST_CASE 8
    INIT_CASE
    SETUP_ACC $FF, $00, $5A, 1, 1, 1
rol_probe_08:
    rol a
rol_after_08:
    CAPTURE_STATE
rol_captured_08:
    CHECK_ACC $FF, $7B, $F9, $00, $5A
rol_passed_08:

; CASE 9: 26 Zero Page $0040, $01/C=0 -> $02; N/Z/C=0/0/0, A stays $55; V/D=1.
.export rol_probe_09, rol_after_09, rol_captured_09, rol_passed_09
    TEST_CASE 9
    INIT_CASE
    INIT_MEMORY $0040, $01, $0042, $0140
    SETUP_MEMORY $80, $00, 0, 1, 1
rol_probe_09:
    rol $40
rol_after_09:
    CAPTURE_STATE
rol_captured_09:
    CHECK_MEMORY $0040, $02, $7A, $78, $80, $00, $0042, $0140
rol_passed_09:

; CASE 10: 36 Zero Page,X $FF+$02 wraps to $0001, $80/C=1 -> $01.
; N/Z/C=0/0/1; unindexed $00FF and unwrapped $0101 are distinct sentinels.
.export rol_probe_10, rol_after_10, rol_captured_10, rol_passed_10
    TEST_CASE 10
    INIT_CASE
    INIT_MEMORY $0001, $80, $00FF, $0101
    SETUP_MEMORY $02, $80, 1, 0, 0
rol_probe_10:
    rol $FF,x
rol_after_10:
    CAPTURE_STATE
rol_captured_10:
    CHECK_MEMORY $0001, $01, $B1, $31, $02, $80, $00FF, $0101
rol_passed_10:

; CASE 11: 2E Absolute $1000, $C0/C=1 -> $81; N/Z/C=1/0/1, A stays $55.
.export rol_probe_11, rol_after_11, rol_captured_11, rol_passed_11
    TEST_CASE 11
    INIT_CASE
    INIT_MEMORY $1000, $C0, $1002, $0000
    SETUP_MEMORY $02, $00, 1, 1, 0
rol_probe_11:
    rol $1000
rol_after_11:
    CAPTURE_STATE
rol_captured_11:
    CHECK_MEMORY $1000, $81, $73, $F1, $02, $00, $1002, $0000
rol_passed_11:

; CASE 12: 3E Absolute,X $12FF+$01 crosses to $1300, $80/C=0 -> $00.
; N/Z/C=0/1/1; $1200 detects lost page carry, $12FF is also a lower guard; D=1.
.export rol_probe_12, rol_after_12, rol_captured_12, rol_passed_12
    TEST_CASE 12
    INIT_CASE
    INIT_MEMORY $1300, $80, $1200, $1302
    SETUP_MEMORY $01, $80, 0, 0, 1
rol_probe_12:
    rol $12FF,x
rol_after_12:
    CAPTURE_STATE
rol_captured_12:
    CHECK_MEMORY $1300, $00, $B8, $3B, $01, $80, $1200, $1302
rol_passed_12:

; CASE 13: stack guard, 26 Zero Page $0040, $81/C=1 -> $03.
.export rol_probe_13, rol_passed_13
    TEST_CASE 13
    INIT_CASE
    INIT_MEMORY $0040, $81, $0042, $0140
    SETUP_STACK $80, $00, 1, 0, 0
rol_probe_13:
    rol $40
    CHECK_STACK $0040, $03
rol_passed_13:

; CASE 14: stack guard, 36 Zero Page,X $FF+$02 -> $0001, $40/C=0 -> $80.
.export rol_probe_14, rol_passed_14
    TEST_CASE 14
    INIT_CASE
    INIT_MEMORY $0001, $40, $00FF, $0101
    SETUP_STACK $02, $80, 0, 1, 0
rol_probe_14:
    rol $FF,x
    CHECK_STACK $0001, $80
rol_passed_14:

; CASE 15: stack guard, 2E Absolute $1000, $81/C=0 -> $02.
.export rol_probe_15, rol_passed_15
    TEST_CASE 15
    INIT_CASE
    INIT_MEMORY $1000, $81, $1002, $0000
    SETUP_STACK $02, $00, 0, 0, 1
rol_probe_15:
    rol $1000
    CHECK_STACK $1000, $02
rol_passed_15:

; CASE 16: stack guard, 3E Absolute,X $12FF+$01 -> $1300, $FF/C=1 -> $FF.
.export rol_probe_16, rol_passed_16
    TEST_CASE 16
    INIT_CASE
    INIT_MEMORY $1300, $FF, $1200, $1302
    SETUP_STACK $01, $80, 1, 1, 1
rol_probe_16:
    rol $12FF,x
    CHECK_STACK $1300, $FF
rol_passed_16:

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
