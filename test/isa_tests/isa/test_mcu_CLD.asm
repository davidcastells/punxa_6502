; NMOS 6502 CLD ($D8, implied): clear D only; preserve N/V/I/Z/C and A/X/Y/SP.
; ATmega CLC/SEC patterns: set/clear preconditions, idempotence, other-state checks.
; Fixed expectations; SED is only a setup helper, not a formal target here.
; PHP snapshots immediately before/after CLD; compare BOTH bytes afterwards so
; a failed setup cannot masquerade as a successful clear. No PLA/PLP dependency.
; PHP changes SP: entry to each first CLD is $FE, repeated CLD is $FD.
; I=0/D=0 at startup is the simulator convention, not physical reset testing.
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

; D=0 comes from initial simulator state or the preceding checked CLD.
; Establish V in binary mode BEFORE optional SED. No CLD setup/oracle is used.
; Last LDA supplies N/Z; loads and CLC/SEC do not change V or D.
.macro SEED value_a, value_x, value_y, carry, overflow, decimal
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

.macro CHECK_CASE expected_pre, expected_post, value_a, value_x, value_y, repeated
    lda #1
    sta check_stage
    CHECK_MEM pre_p, expected_pre ; full independently fixed setup status
    lda #2
    sta check_stage
    CHECK_MEM post_p, expected_post ; D cleared; all other status bits preserved
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
    CHECK_MEM $01FC, $22
    CHECK_MEM $0100, $22
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
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

; CASE 1: D=1 -> 0; N/Z/C/V=0. SED's precondition must yield P=$38.
.export cld_seed_01, cld_probe_01_1, cld_after_01_1, cld_captured_01, cld_passed_01
    TEST_CASE 1
    INIT_STACK_GUARDS
cld_seed_01:
    SEED $55, $AA, $3C, 0, 0, 1
    php
cld_probe_01_1:
    cld
cld_after_01_1:
    php
    CAPTURE_REGS saved_a
cld_captured_01:
    CHECK_CASE $38, $30, $55, $AA, $3C, 0
cld_passed_01:

; CASE 2: D already 0; preserve Z=1/C=1 and clear N/V.
.export cld_seed_02, cld_probe_02_1, cld_after_02_1, cld_captured_02, cld_passed_02
    TEST_CASE 2
    INIT_STACK_GUARDS
cld_seed_02:
    SEED $00, $80, $7F, 1, 0, 0
    php
cld_probe_02_1:
    cld
cld_after_02_1:
    php
    CAPTURE_REGS saved_a
cld_captured_02:
    CHECK_CASE $33, $33, $00, $80, $7F, 0
cld_passed_02:

; CASE 3: D=1 -> 0; preserve N=1/V=1/C=1/Z=0.
.export cld_seed_03, cld_probe_03_1, cld_after_03_1, cld_captured_03, cld_passed_03
    TEST_CASE 3
    INIT_STACK_GUARDS
cld_seed_03:
    SEED $80, $00, $FF, 1, 1, 1
    php
cld_probe_03_1:
    cld
cld_after_03_1:
    php
    CAPTURE_REGS saved_a
cld_captured_03:
    CHECK_CASE $F9, $F1, $80, $00, $FF, 0
cld_passed_03:

; CASE 4: D=1 -> 0; preserve Z=1/V=1/C=0/N=0.
.export cld_seed_04, cld_probe_04_1, cld_after_04_1, cld_captured_04, cld_passed_04
    TEST_CASE 4
    INIT_STACK_GUARDS
cld_seed_04:
    SEED $00, $FF, $00, 0, 1, 1
    php
cld_probe_04_1:
    cld
cld_after_04_1:
    php
    CAPTURE_REGS saved_a
cld_captured_04:
    CHECK_CASE $7A, $72, $00, $FF, $00, 0
cld_passed_04:

; CASE 5: D already 0; preserve N=1/Z=0/C=0/V=0.
.export cld_seed_05, cld_probe_05_1, cld_after_05_1, cld_captured_05, cld_passed_05
    TEST_CASE 5
    INIT_STACK_GUARDS
cld_seed_05:
    SEED $FF, $55, $AA, 0, 0, 0
    php
cld_probe_05_1:
    cld
cld_after_05_1:
    php
    CAPTURE_REGS saved_a
cld_captured_05:
    CHECK_CASE $B0, $B0, $FF, $55, $AA, 0
cld_passed_05:

; CASE 6: Repeat CLD with only flag-neutral PHP/stores between targets.
; Capture each intermediate state: D=1 -> 0 -> 0; C/V=1, N/Z=0 preserved.
.export cld_seed_06, cld_probe_06_1, cld_after_06_1
.export cld_probe_06_2, cld_after_06_2, cld_captured_06, cld_passed_06
    TEST_CASE 6
    INIT_STACK_GUARDS
cld_seed_06:
    SEED $7F, $A5, $5A, 1, 1, 1
    php
cld_probe_06_1:
    cld
cld_after_06_1:
    php
    CAPTURE_REGS saved_a
cld_probe_06_2:
    cld
cld_after_06_2:
    php
    CAPTURE_REGS repeat_a
cld_captured_06:
    CHECK_CASE $79, $71, $7F, $A5, $5A, 1
cld_passed_06:

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
