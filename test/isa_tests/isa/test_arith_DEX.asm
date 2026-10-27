; NMOS 6502 DEX: X=(X-1)&$FF; sets N/Z, preserves A/Y/SP/C/V/D/I.
; ATmega DEC supplies ordinary/zero/sign/wrap scenarios; DEX does not update V.
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
guard_0 = $2020
guard_1 = $2021

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro
.macro SETUP old_x, seed_y, carry, overflow, decimal
    ldx #$FF
    txs
    lda #$A5
    sta guard_0
    lda #$5A
    sta guard_1
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
    lda #$55
    ldy #seed_y ; opposing initial N/Z, without changing X/A/C/V/D
.endmacro
.macro CHECK_DEX value, flags, seed_y
    sta saved_a
    php ; status first; STX/STY preserve it too
    stx saved_x
    sty saved_y
    tsx
    stx saved_sp
    lda $01FF ; no PLA dependency
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags
    lda #2
    sta check_stage
    lda saved_x
    CHECK_A value ; literal expectation, no DEX-based loop/oracle
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A $55
    lda saved_y
    CHECK_A seed_y
    lda saved_sp
    CHECK_A $FE
    lda #4
    sta check_stage
    lda guard_0
    CHECK_A $A5
    lda guard_1
    CHECK_A $5A
    lda #0
    sta check_stage
.endmacro
start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Ordinary $02->$01, clears Z; preserves C/V.
.export dex_probe_01, dex_after_01, dex_passed_01
    TEST_CASE 1
    SETUP $02, $00, 1, 1, 0
dex_probe_01:
    dex
dex_after_01:
    CHECK_DEX $01, $71, $00
dex_passed_01:

; CASE 2: $03->$02, nonzero even result must have Z=0 (INX defect control).
.export dex_probe_02, dex_after_02, dex_passed_02
    TEST_CASE 2
    SETUP $03, $00, 0, 0, 1
dex_probe_02:
    dex
dex_after_02:
    CHECK_DEX $02, $38, $00
dex_passed_02:

; CASE 3: $01->$00 sets Z, clears seeded N and preserves C.
.export dex_probe_03, dex_after_03, dex_passed_03
    TEST_CASE 3
    SETUP $01, $80, 1, 0, 0
dex_probe_03:
    dex
dex_after_03:
    CHECK_DEX $00, $33, $80
dex_passed_03:

; CASE 4: $00->$FF wraps to eight bits, sets N and clears Z; preserves V/D.
.export dex_probe_04, dex_after_04, dex_passed_04
    TEST_CASE 4
    SETUP $00, $00, 0, 1, 1
dex_probe_04:
    dex
dex_after_04:
    CHECK_DEX $FF, $F8, $00
dex_passed_04:

; CASE 5: $80->$7F crosses signed boundary; V stays at its seeded one.
.export dex_probe_05, dex_after_05, dex_passed_05
    TEST_CASE 5
    SETUP $80, $80, 1, 1, 1
dex_probe_05:
    dex
dex_after_05:
    CHECK_DEX $7F, $79, $80
dex_passed_05:

; CASE 6: $81->$80 sets N, clears Z; V stays clear.
.export dex_probe_06, dex_after_06, dex_passed_06
    TEST_CASE 6
    SETUP $81, $00, 0, 0, 0
dex_probe_06:
    dex
dex_after_06:
    CHECK_DEX $80, $B0, $00
dex_passed_06:

; CASE 7: $FF->$FE, negative nonzero even result keeps Z clear.
.export dex_probe_07, dex_after_07, dex_passed_07
    TEST_CASE 7
    SETUP $FF, $00, 1, 0, 1
dex_probe_07:
    dex
dex_after_07:
    CHECK_DEX $FE, $B9, $00
dex_passed_07:

; CASE 8: $7F->$7E clears N, leaves Z clear and preserves V.
.export dex_probe_08, dex_after_08, dex_passed_08
    TEST_CASE 8
    SETUP $7F, $80, 0, 1, 0
dex_probe_08:
    dex
dex_after_08:
    CHECK_DEX $7E, $70, $80
dex_passed_08:

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
