; NMOS 6502 CMP: formal self-checking Phase A test.
; Fixed expectations follow the SY6500/MCS6500 Programming Manual.
; I remains zero; PHP's B/unused bits are checked as its stack representation.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p
.segment "CODE"
saved_a = $2010
saved_p = $2011

; CMP is not used as its own oracle: binary ADC computes byte-expected.
; Existing formal ADC and BNE supply independent equality checking.
.macro CHECK_BYTE expected
    .local ok, bad
    cld
    clc
    adc #((-expected) & $FF)
    bne bad
    jmp ok
bad:
    jmp fail
ok:
.endmacro
; Capture P before any comparison/load or PLA can change live N/Z.
.macro CHECK_STATE value, status
    php
    sta saved_a
    pla
    sta saved_p
    CHECK_BYTE status
    lda saved_a
    CHECK_BYTE value
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Immediate equal
.export probe_1, passed_1
    TEST_CASE 1
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$42
probe_1:
    cmp #$42
    CHECK_STATE $42, $33
passed_1:

; CASE 2: Immediate unsigned greater, negative difference
.export probe_2, passed_2
    TEST_CASE 2
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$FF
probe_2:
    cmp #1
    CHECK_STATE $FF, $B1
passed_2:

; CASE 3: Immediate less, borrow
.export probe_3, passed_3
    TEST_CASE 3
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$00
    sec ; verify CMP clears a preexisting carry on less-than
probe_3:
    cmp #1
    CHECK_STATE $00, $B0
passed_3:

; CASE 4: Zero Page: $00 < $FF, positive wrapped difference
.export probe_4, passed_4
    TEST_CASE 4
    ldx #$FF
    stx $40
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$00
probe_4:
    cmp $40
    CHECK_STATE $00, $30
passed_4:

; CASE 5: Zero Page,X: $FF+2 wraps to $01
.export probe_5, passed_5
    TEST_CASE 5
    ldx #$80
    stx $01
    ldx #$11
    stx $0101
    ldx #2
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$7F
probe_5:
    cmp $FF,x
    CHECK_STATE $7F, $B0
passed_5:

; CASE 6: Absolute greater
.export probe_6, passed_6
    TEST_CASE 6
    ldx #$55
    stx $1000
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$56
probe_6:
    cmp $1000
    CHECK_STATE $56, $31
passed_6:

; CASE 7: Absolute,X page carry
.export probe_7, passed_7
    TEST_CASE 7
    ldx #1
    stx $1300
    ldx #$11
    stx $1200
    ldx #1
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$80
probe_7:
    cmp $12FF,x
    CHECK_STATE $80, $31
passed_7:

; CASE 8: Absolute,Y page carry
.export probe_8, passed_8
    TEST_CASE 8
    ldx #$7F
    stx $1401
    ldx #$11
    stx $1301
    ldy #2
    cld
    clc
    lda #0
    adc #0
    cld
    lda #$80
probe_8:
    cmp $13FF,y
    CHECK_STATE $80, $31
passed_8:

; CASE 9: Indexed indirect equal; V stays set
.export probe_9, passed_9
    TEST_CASE 9
    ldx #$80
    stx $1500
    ldx #0
    stx $64
    ldx #$15
    stx $65
    ldx #4
    cld
    clc
    lda #$7F
    adc #1
    cld
    lda #$80
probe_9:
    cmp ($60,x)
    CHECK_STATE $80, $73
passed_9:

; CASE 10: Indirect indexed page carry; D stays set
.export probe_10, passed_10
    TEST_CASE 10
    ldx #0
    stx $1700
    ldx #$FF
    stx $70
    ldx #$16
    stx $71
    ldy #1
    cld
    clc
    lda #0
    adc #0
    sed
    lda #$FF
probe_10:
    cmp ($70),y
    CHECK_STATE $FF, $B9
passed_10:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
