; NMOS 6502 DEY ($88, implied): Y=(Y-1)&$FF; update N/Z only.
; ATmega DEC supplies ordinary/zero/sign/wrap scenario patterns, not flag rules.
; Fixed expectations; never use DEY itself to calculate an expected value.
; Helpers follow formal DEX/LDY tests. PHP precedes every flag-changing check.
; Live CPY equality supplements STY: an 8-bit store can hide an over-wide Y.
; C/V/D are varied; I stays at the simulator's initial zero (not reset testing).
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

.macro SETUP old_y, seed_x, carry, overflow, decimal
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
    ldy #old_y
    lda #$55
    ldx #seed_x ; seed opposing N/Z without changing A/Y/C/V/D
.endmacro

.macro CAPTURE_STATE
    sta saved_a
    stx saved_x
    sty saved_y
    php ; stores above preserve flags; snapshot before TSX/loads/CPY/CMP
    tsx
    stx saved_sp
    lda $01FF ; direct status-byte read, no PLA dependency
    sta saved_p
.endmacro

.macro CHECK_DEY value, flags, seed_x
    .local y_ok
    lda #1
    sta check_stage
    cpy #value ; compare live Y as well as its saved eight-bit representation
    beq y_ok
    jmp fail
y_ok:
    lda saved_y
    CHECK_A value
    lda #2
    sta check_stage
    lda saved_p
    CHECK_A flags ; full byte: N/V/1/B/D/I/Z/C, with I=0
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A $55
    lda saved_x
    CHECK_A seed_x
    lda saved_sp
    CHECK_A $FE ; target preserves SP=$FF; checker PHP alone decrements it
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

; CASE 1: $02->$01 clears seeded Z; preserves C/V=1 and D=0.
.export dey_probe_01, dey_after_01, dey_captured_01, dey_passed_01
    TEST_CASE 1
    SETUP $02, $00, 1, 1, 0
dey_probe_01:
    dey
dey_after_01:
    CAPTURE_STATE
dey_captured_01:
    CHECK_DEY $01, $71, $00
dey_passed_01:

; CASE 2: $01->$00 clears seeded N and sets Z; preserves C=1 and V/D=0.
.export dey_probe_02, dey_after_02, dey_captured_02, dey_passed_02
    TEST_CASE 2
    SETUP $01, $80, 1, 0, 0
dey_probe_02:
    dey
dey_after_02:
    CAPTURE_STATE
dey_captured_02:
    CHECK_DEY $00, $33, $80
dey_passed_02:

; CASE 3: $00->$FF wraps to eight bits, sets N and clears Z; preserves V/D=1.
.export dey_probe_03, dey_after_03, dey_captured_03, dey_passed_03
    TEST_CASE 3
    SETUP $00, $00, 0, 1, 1
dey_probe_03:
    dey
dey_after_03:
    CAPTURE_STATE
dey_captured_03:
    CHECK_DEY $FF, $F8, $00
dey_passed_03:

; CASE 4: $80->$7F clears N, keeps Z clear; preserves C/V/D=1.
.export dey_probe_04, dey_after_04, dey_captured_04, dey_passed_04
    TEST_CASE 4
    SETUP $80, $80, 1, 1, 1
dey_probe_04:
    dey
dey_after_04:
    CAPTURE_STATE
dey_captured_04:
    CHECK_DEY $7F, $79, $80
dey_passed_04:

; CASE 5: $81->$80 sets N and clears Z; C/V/D remain clear.
.export dey_probe_05, dey_after_05, dey_captured_05, dey_passed_05
    TEST_CASE 5
    SETUP $81, $00, 0, 0, 0
dey_probe_05:
    dey
dey_after_05:
    CAPTURE_STATE
dey_captured_05:
    CHECK_DEY $80, $B0, $00
dey_passed_05:

; CASE 6: $FF->$FE is negative and nonzero even; keep Z clear, preserve C/D=1.
.export dey_probe_06, dey_after_06, dey_captured_06, dey_passed_06
    TEST_CASE 6
    SETUP $FF, $00, 1, 0, 1
dey_probe_06:
    dey
dey_after_06:
    CAPTURE_STATE
dey_captured_06:
    CHECK_DEY $FE, $B9, $00
dey_passed_06:

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
