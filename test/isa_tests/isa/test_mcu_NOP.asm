; NMOS 6502 NOP ($EA, implied): no operation; PC advances by one byte.
; Preserves N/V/D/I/Z/C, A/X/Y/SP and memory. Structure follows test_mcu_CLD.asm.
; PHP snapshots immediately before/after NOP; compare BOTH bytes afterwards so
; a failed setup cannot masquerade as a preserved status.
; PHP changes SP: entry to each first NOP is $FE, a repeated capture is $FD.
; Cases 5 and 6 check the next instruction runs at exactly NOP+1, including
; when NOP is the last byte of a page (PC high byte must increment).
; I=0 at startup is the simulator convention; case 3 sets I with SEI.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_sp, check_stage
.export repeat_a, repeat_x, repeat_y, pre_p, post_p, repeat_p, guard_0, guard_1
.segment "CODE"

saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_sp = $2014
check_stage = $2015
repeat_a = $2030
repeat_x = $2031
repeat_y = $2032
pre_p = $01FF
post_p = $01FE
repeat_p = $01FD
guard_0 = $2020
guard_1 = $2021

.macro CHECK_MEM location, expected
    .local ok
    lda location
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

.macro INIT_STACK_GUARDS
    lda #$AA
    sta pre_p
    sta post_p
    sta repeat_p
    lda #$22
    sta $01FC
    sta $0100
    lda #$A5
    sta guard_0
    lda #$5A
    sta guard_1
    ldx #$FF
    txs
.endmacro

; Establish V in binary mode BEFORE optional SED.
; Last LDA supplies N/Z; loads and CLC/SEC do not change V or D.
.macro SEED value_a, value_x, value_y, carry, overflow, decimal
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
    ldx #value_x
    ldy #value_y
    lda #value_a
.endmacro

; Used after the post-target PHP. These stores preserve all live flags.
.macro CAPTURE_REGS base
    sta base
    stx base+1
    sty base+2
.endmacro

.macro CHECK_REGS base, value_a, value_x, value_y
    CHECK_MEM base, value_a
    CHECK_MEM base+1, value_x
    CHECK_MEM base+2, value_y
.endmacro

; Guard bytes outside the checker's own stack slots must be untouched.
.macro CHECK_GUARDS
    CHECK_MEM $01FC, $22
    CHECK_MEM $0100, $22
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
.endmacro

.macro CHECK_CASE expected_pre, expected_post, value_a, value_x, value_y, repeated
    lda #1
    sta check_stage
    CHECK_MEM pre_p, expected_pre ; full independently fixed setup status
    lda #2
    sta check_stage
    CHECK_MEM post_p, expected_post ; every status bit preserved by NOP
    lda #3
    sta check_stage
    CHECK_REGS saved_a, value_a, value_x, value_y
    .if repeated
        lda #4
        sta check_stage
        CHECK_MEM repeat_p, expected_post
        CHECK_REGS repeat_a, value_a, value_x, value_y
    .endif
    lda #5
    sta check_stage
    tsx
    stx saved_sp
    .if repeated
        CHECK_MEM saved_sp, $FC ; three checker PHPs, no target SP change
    .else
        CHECK_MEM saved_sp, $FD ; two checker PHPs, no target SP change
    .endif
    lda #6
    sta check_stage
    CHECK_GUARDS
    .if repeated = 0
        CHECK_MEM repeat_p, $AA ; no third stack write in single-target cases
    .endif
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Single NOP with N/V/D/Z/C clear (P=$30).
.export nop_seed_01, nop_probe_01, nop_after_01, nop_captured_01, nop_passed_01
    TEST_CASE 1
    INIT_STACK_GUARDS
nop_seed_01:
    SEED $55, $AA, $3C, 0, 0, 0
    php
nop_probe_01:
    nop
nop_after_01:
    php
    CAPTURE_REGS saved_a
nop_captured_01:
    CHECK_CASE $30, $30, $55, $AA, $3C, 0
nop_passed_01:

; CASE 2: Single NOP with N/V/D/C set (P=$F9).
.export nop_seed_02, nop_probe_02, nop_after_02, nop_captured_02, nop_passed_02
    TEST_CASE 2
    INIT_STACK_GUARDS
nop_seed_02:
    SEED $80, $00, $FF, 1, 1, 1
    php
nop_probe_02:
    nop
nop_after_02:
    php
    CAPTURE_REGS saved_a
nop_captured_02:
    CHECK_CASE $F9, $F9, $80, $00, $FF, 0
nop_passed_02:

; CASE 3: Single NOP with I/Z/C set (P=$37). CLI afterwards restores I=0.
.export nop_seed_03, nop_probe_03, nop_after_03, nop_captured_03, nop_passed_03
    TEST_CASE 3
    INIT_STACK_GUARDS
nop_seed_03:
    SEED $00, $80, $7F, 1, 0, 0
    sei
    php
nop_probe_03:
    nop
nop_after_03:
    php
    CAPTURE_REGS saved_a
    cli
nop_captured_03:
    CHECK_CASE $37, $37, $00, $80, $7F, 0
nop_passed_03:

; CASE 4: Consecutive NOPs. One NOP, capture, then three more NOPs, capture.
; Both captures must equal the seeded state (V/D/C set, P=$79).
.export nop_seed_04, nop_probe_04_1, nop_after_04_1
.export nop_probe_04_2, nop_after_04_2, nop_captured_04, nop_passed_04
    TEST_CASE 4
    INIT_STACK_GUARDS
nop_seed_04:
    SEED $7F, $A5, $5A, 1, 1, 1
    php
nop_probe_04_1:
    nop
nop_after_04_1:
    php
    CAPTURE_REGS saved_a
nop_probe_04_2:
    nop
    nop
    nop
nop_after_04_2:
    php
    CAPTURE_REGS repeat_a
nop_captured_04:
    CHECK_CASE $79, $79, $7F, $A5, $5A, 1
nop_passed_04:

; CASE 5: Execution continues at exactly NOP+1. NOP is followed by three
; one-byte instructions; every one must run. If NOP consumed one extra byte
; X=$11/Y=$21, two extra bytes X=$11/Y=$20; no PC advance never terminates.
.export nop_probe_05, nop_after_05, nop_passed_05
    TEST_CASE 5
    INIT_STACK_GUARDS
    ldx #$10
    ldy #$20
nop_probe_05:
    nop
nop_after_05:
    inx
    iny
    inx
    stx saved_x
    sty saved_y
    lda #1
    sta check_stage
    CHECK_MEM saved_x, $12
    CHECK_MEM saved_y, $21
    lda #2
    sta check_stage
    CHECK_GUARDS
    CHECK_MEM post_p, $AA ; no stack write by NOP
    lda #0
    sta check_stage
nop_passed_05:

; CASE 6: NOP is the last byte of a page; the next instruction is at the
; start of the following page (V set, P=$70).
.export nop_seed_06, nop_probe_06, nop_after_06, nop_captured_06, nop_passed_06
    TEST_CASE 6
    INIT_STACK_GUARDS
nop_seed_06:
    SEED $01, $3C, $C3, 0, 1, 0
    php
    jmp nop_probe_06
    .align $100, $00
    .res $FF, $00
nop_probe_06:
    nop
nop_after_06:
    .assert (>nop_after_06) <> (>nop_probe_06), lderror, "case6 NOP must be the last byte of a page"
    php
    CAPTURE_REGS saved_a
nop_captured_06:
    CHECK_CASE $70, $70, $01, $3C, $C3, 0
nop_passed_06:

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
