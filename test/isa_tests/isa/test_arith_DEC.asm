; NMOS 6502 DEC: M=(M-1)&$FF; set N/Z, preserve A/X/Y/SP/C/V/D/I.
; Four forms: C6 zp, D6 zp,X, CE abs, DE abs,X. No accumulator form.
; ATmega DEC supplies value/zero/sign/wrap patterns; INC supplies memory guards.
; Fixed expectations; no DEC-generated expected values. PHP precedes comparisons.
; All helper writes are outside the target/guard/sentinel locations.
; I=0 is the simulator startup convention; reset/I=1 are not tested.
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

.macro INIT_MEMORY target, value, sentinel_0, sentinel_1
    lda #value
    sta target
    lda #$22
    sta target-1
    sta target+1
    lda #$11
    sta sentinel_0
    lda #$33
    sta sentinel_1
.endmacro

.macro SETUP index_x, seed_y, carry, overflow, decimal
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
    lda #$55
    ldy #seed_y ; seed N/Z without changing A/X or the target memory
.endmacro

.macro CAPTURE_STATE
    sta saved_a
    stx saved_x
    sty saved_y
    php ; stores preserve target flags; capture before TSX/loads/CMP
    tsx
    stx saved_sp
    lda $01FF ; read the status copy directly; no PLA dependency
    sta saved_p
.endmacro

.macro CHECK_DEC target, value, flags, index_x, seed_y, sentinel_0, sentinel_1
    lda #1
    sta check_stage
    lda target
    CHECK_A value ; expected eight-bit write-back at the intended address
    lda #2
    sta check_stage
    lda saved_p
    CHECK_A flags ; full fixed status byte, including C/V/D/I preservation
    lda #3
    sta check_stage
    lda saved_a
    CHECK_A $55
    lda saved_x
    CHECK_A index_x
    lda saved_y
    CHECK_A seed_y
    lda saved_sp
    CHECK_A $FE ; SP=$FF at target; checker PHP alone decrements it
    lda #4
    sta check_stage
    lda target-1
    CHECK_A $22
    lda target+1
    CHECK_A $22
    lda sentinel_0
    CHECK_A $11
    lda sentinel_1
    CHECK_A $33
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: C6 Zero Page, $0040: $02->$01; clear Z, preserve C/V.
.export dec_probe_01, dec_after_01, dec_captured_01, dec_passed_01
    TEST_CASE 1
    INIT_MEMORY $0040, $02, $0042, $0140
    SETUP $80, $00, 1, 1, 0
dec_probe_01:
    dec $40
dec_after_01:
    CAPTURE_STATE
dec_captured_01:
    CHECK_DEC $0040, $01, $71, $80, $00, $0042, $0140
dec_passed_01:

; CASE 2: C6 Zero Page, $0041: $01->$00; clear N, set Z, preserve C.
.export dec_probe_02, dec_after_02, dec_captured_02, dec_passed_02
    TEST_CASE 2
    INIT_MEMORY $0041, $01, $0043, $0141
    SETUP $02, $80, 1, 0, 0
dec_probe_02:
    dec $41
dec_after_02:
    CAPTURE_STATE
dec_captured_02:
    CHECK_DEC $0041, $00, $33, $02, $80, $0043, $0141
dec_passed_02:

; CASE 3: D6 Zero Page,X, $FF+$02 wraps to $0001; $00->$FF, N=1/Z=0.
; $00FF catches ignoring X; $0101 catches missing zero-page address wrap.
.export dec_probe_03, dec_after_03, dec_captured_03, dec_passed_03
    TEST_CASE 3
    INIT_MEMORY $0001, $00, $00FF, $0101
    SETUP $02, $00, 0, 1, 1
dec_probe_03:
    dec $FF,x
dec_after_03:
    CAPTURE_STATE
dec_captured_03:
    CHECK_DEC $0001, $FF, $F8, $02, $00, $00FF, $0101
dec_passed_03:

; CASE 4: CE Absolute, $1000: $80->$7F; clear N, preserve C/V/D.
.export dec_probe_04, dec_after_04, dec_captured_04, dec_passed_04
    TEST_CASE 4
    INIT_MEMORY $1000, $80, $1002, $0000
    SETUP $02, $80, 1, 1, 1
dec_probe_04:
    dec $1000
dec_after_04:
    CAPTURE_STATE
dec_captured_04:
    CHECK_DEC $1000, $7F, $79, $02, $80, $1002, $0000
dec_passed_04:

; CASE 5: DE Absolute,X, $12FF+$01 crosses to $1300; $81->$80, N=1/Z=0.
; $1200 catches a lost page carry; the lower guard also protects $12FF.
.export dec_probe_05, dec_after_05, dec_captured_05, dec_passed_05
    TEST_CASE 5
    INIT_MEMORY $1300, $81, $1200, $1302
    SETUP $01, $00, 0, 0, 0
dec_probe_05:
    dec $12FF,x
dec_after_05:
    CAPTURE_STATE
dec_captured_05:
    CHECK_DEC $1300, $80, $B0, $01, $00, $1200, $1302
dec_passed_05:

; CASE 6: CE Absolute, $1100: $FF->$FE; nonzero even result keeps Z clear.
.export dec_probe_06, dec_after_06, dec_captured_06, dec_passed_06
    TEST_CASE 6
    INIT_MEMORY $1100, $FF, $1102, $0000
    SETUP $80, $00, 1, 0, 1
dec_probe_06:
    dec $1100
dec_after_06:
    CAPTURE_STATE
dec_captured_06:
    CHECK_DEC $1100, $FE, $B9, $80, $00, $1102, $0000
dec_passed_06:

; CASE 7: D6 Zero Page,X, $40+$02 selects $0042; $01->$00, Z=1/N=0.
.export dec_probe_07, dec_after_07, dec_captured_07, dec_passed_07
    TEST_CASE 7
    INIT_MEMORY $0042, $01, $0040, $0142
    SETUP $02, $80, 0, 0, 1
dec_probe_07:
    dec $40,x
dec_after_07:
    CAPTURE_STATE
dec_captured_07:
    CHECK_DEC $0042, $00, $3A, $02, $80, $0040, $0142
dec_passed_07:

; CASE 8: DE Absolute,X, $13FF+$02 crosses to $1401; $00->$FF, N=1/Z=0.
; $1301 catches missing page carry; $13FF catches ignoring X.
.export dec_probe_08, dec_after_08, dec_captured_08, dec_passed_08
    TEST_CASE 8
    INIT_MEMORY $1401, $00, $1301, $13FF
    SETUP $02, $00, 1, 1, 0
dec_probe_08:
    dec $13FF,x
dec_after_08:
    CAPTURE_STATE
dec_captured_08:
    CHECK_DEC $1401, $FF, $F1, $02, $00, $1301, $13FF
dec_passed_08:

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
