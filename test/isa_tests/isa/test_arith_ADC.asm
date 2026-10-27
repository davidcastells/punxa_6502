; Original NMOS 6502 ADC: binary arithmetic, all eight addressing modes.
; Reference: SY6500/MCS6500 Programming Manual, section 2.2.1.
; Decimal arithmetic is intentionally deferred. Every case explicitly clears D.
; Expected A/C/Z/N/V are constants derived from 8-bit binary addition.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p
.segment "CODE"

saved_a = $2010
saved_p = $2011

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

.macro CHECK_ADC value, flags
    php ; capture C/Z/N/V before the first comparison or load
    sta saved_a
    pla
    sta saved_p
    and #$CB ; N V D Z C; D must remain clear
    CHECK_A flags
    lda saved_a
    CHECK_A value
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Immediate: $12+$34, C=0
.export probe_1, passed_1
    TEST_CASE 1
    cld
    clc
    lda #$12
probe_1:
    adc #$34
    CHECK_ADC $46, $00
passed_1:

; CASE 2: Immediate: zero result
.export probe_2, passed_2
    TEST_CASE 2
    cld
    clc
    lda #$00
probe_2:
    adc #0
    CHECK_ADC $00, $02
passed_2:

; CASE 3: Immediate: carry-in alone
.export probe_3, passed_3
    TEST_CASE 3
    cld
    sec
    lda #$00
probe_3:
    adc #0
    CHECK_ADC $01, $00
passed_3:

; CASE 4: Immediate: $FF+$01 gives carry and zero
.export probe_4, passed_4
    TEST_CASE 4
    cld
    clc
    lda #$FF
probe_4:
    adc #1
    CHECK_ADC $00, $03
passed_4:

; CASE 5: Immediate: $FF+$00+C gives carry and zero
.export probe_5, passed_5
    TEST_CASE 5
    cld
    sec
    lda #$FF
probe_5:
    adc #0
    CHECK_ADC $00, $03
passed_5:

; CASE 6: Immediate: positive signed overflow ($7F+$01)
.export probe_6, passed_6
    TEST_CASE 6
    cld
    clc
    lda #$7F
probe_6:
    adc #1
    CHECK_ADC $80, $C0
passed_6:

; CASE 7: Immediate: negative signed overflow ($80+$80)
.export probe_7, passed_7
    TEST_CASE 7
    cld
    clc
    lda #$80
probe_7:
    adc #$80
    CHECK_ADC $00, $43
passed_7:

; CASE 8: Immediate: mixed signs clear previous V ($80+$7F)
.export probe_8, passed_8
    TEST_CASE 8
    cld
    clc
    lda #$80
probe_8:
    adc #$7F
    CHECK_ADC $FF, $80
passed_8:

; CASE 9: Zero Page: $FE+$01
.export probe_9, passed_9
    TEST_CASE 9
    ldx #1
    stx $40
    cld
    clc
    lda #$FE
probe_9:
    adc $40
    CHECK_ADC $FF, $80
passed_9:

; CASE 10: Zero Page,X: $FF+2 wraps to $01; carry-in
.export probe_10, passed_10
    TEST_CASE 10
    ldx #1
    stx $01
    ldx #$11
    stx $0101
    ldx #2
    cld
    sec
    lda #$7E
probe_10:
    adc $FF,x
    CHECK_ADC $80, $C0
passed_10:

; CASE 11: Absolute: $10+$01 clears previous V
.export probe_11, passed_11
    TEST_CASE 11
    ldx #1
    stx $1000
    cld
    clc
    lda #$10
probe_11:
    adc $1000
    CHECK_ADC $11, $00
passed_11:

; CASE 12: Absolute,X: $12FF+1 crosses page; carry-in/out
.export probe_12, passed_12
    TEST_CASE 12
    ldx #1
    stx $1300
    ldx #$11
    stx $1200
    ldx #1
    cld
    sec
    lda #$FE
probe_12:
    adc $12FF,x
    CHECK_ADC $00, $03
passed_12:

; CASE 13: Absolute,Y: $13FF+2 crosses page; overflow
.export probe_13, passed_13
    TEST_CASE 13
    ldx #$7F
    stx $1401
    ldx #$11
    stx $1301
    ldy #2
    cld
    clc
    lda #$01
probe_13:
    adc $13FF,y
    CHECK_ADC $80, $C0
passed_13:

; CASE 14: Indexed indirect: ($60,X), pointer $64 -> $1500
.export probe_14, passed_14
    TEST_CASE 14
    ldx #$80
    stx $1500
    ldx #0
    stx $64
    stx $60
    ldx #$15
    stx $65
    ldx #$16
    stx $61
    ldx #$11
    stx $1600
    ldx #4
    cld
    clc
    lda #$80
probe_14:
    adc ($60,x)
    CHECK_ADC $00, $43
passed_14:

; CASE 15: Indirect indexed: $16FF+1 crosses page; overflow
.export probe_15, passed_15
    TEST_CASE 15
    ldx #1
    stx $1700
    ldx #$11
    stx $1600
    ldx #$FF
    stx $70
    ldx #$16
    stx $71
    ldy #1
    cld
    clc
    lda #$7F
probe_15:
    adc ($70),y
    CHECK_ADC $80, $C0
passed_15:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
