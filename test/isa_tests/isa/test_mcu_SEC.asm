; NMOS 6502 SEC: formal self-checking Phase A test.
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

; CASE 1: Set clear carry; Z stays set
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $00, 0, 0, 0
probe_1:
    sec
    CHECK_STATE $00, $33
passed_1:

; CASE 2: Idempotent carry operation; ordinary nonzero
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $55, 1, 0, 0
probe_2:
    sec
    CHECK_STATE $55, $31
passed_2:

; CASE 3: Preserve N, V and D set
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $80, 0, 1, 1
probe_3:
    sec
    CHECK_STATE $80, $F9
passed_3:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
