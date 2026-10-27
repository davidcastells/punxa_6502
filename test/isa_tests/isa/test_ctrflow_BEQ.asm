; NMOS 6502 BEQ: formal self-checking Phase A test.
; Fixed expectations follow the SY6500/MCS6500 Programming Manual.
; I remains zero; PHP's B/unused bits are checked as its stack representation.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p
.segment "CODE"
saved_a = $2010
saved_p = $2011

.macro CHECK_BYTE expected
    .local ok, bad
    cmp #expected
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
; ADC establishes V; CMP establishes C, avoiding target CLC/SEC in setup.
; All arithmetic is binary. Last LDA supplies the requested N/Z.
.macro SEED_P value, carry, decimal, overflow
    cld
    lda #0
    adc #0 ; C becomes zero regardless of incoming carry
    .if overflow
        lda #$7F
        adc #1
    .endif
    lda #$80
    .if carry
        cmp #0
    .else
        cmp #$FF
    .endif
    .if decimal
        sed
    .else
        cld
    .endif
    lda #value
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Forward taken Z=1
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $00, 0, 0, 0
probe_1:
    beq taken_1
    jmp fail
taken_1:
    CHECK_STATE $00, $32
passed_1:

; CASE 2: Forward not taken Z=0
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $80, 1, 1, 1
probe_2:
    beq bad_2
    jmp check_2
bad_2:
    jmp fail
check_2:
    CHECK_STATE $80, $F9
passed_2:

; CASE 3: Backward taken Z=1
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $00, 1, 0, 1
    jmp probe_3
taken_3:
    jmp check_3
probe_3:
    beq taken_3
    jmp fail
check_3:
    CHECK_STATE $00, $73
passed_3:

; CASE 4: Backward not taken Z=0
.export probe_4, passed_4
    TEST_CASE 4
    SEED_P $01, 0, 0, 0
    jmp probe_4
bad_4:
    jmp fail
probe_4:
    beq bad_4
    CHECK_STATE $01, $30
passed_4:

; CASE 5: Forward page crossing
.export probe_5, passed_5
    TEST_CASE 5
    SEED_P $00, 1, 0, 1
    jmp probe_5
    .align $100, $00
    .res $FA, $00
probe_5:
    beq taken_5
    jmp fail
    .byte 0
taken_5:
    .assert (>taken_5) <> (>(probe_5+2)), lderror, "forward page crossing required"
    CHECK_STATE $00, $73
passed_5:

; CASE 6: Backward page crossing
.export probe_6, passed_6
    TEST_CASE 6
    SEED_P $00, 0, 1, 0
    jmp probe_6
    .align $100, $00
    .res $F8, $00
taken_6:
    jmp check_6
    .res 5, $00
probe_6:
    beq taken_6
    jmp fail
check_6:
    .assert (>taken_6) <> (>(probe_6+2)), lderror, "backward page crossing required"
    CHECK_STATE $00, $3A
passed_6:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
