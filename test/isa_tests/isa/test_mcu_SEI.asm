; NMOS 6502 SEI: sets the Interrupt Disable flag I; all other flags/state kept.
; Structure follows test_mcu_CLC.asm. PHP stack bytes are checked in full
; (B/bit5 = 1). I=0 at program start is the simulator reset convention.
; A pre-target PHP snapshot proves the initial I/C/V/D/N/Z of each case.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p, saved_pre
.segment "CODE"
saved_a = $2010
saved_p = $2011
saved_pre = $2012

.macro CHECK_BYTE expected
    .local ok, bad
    cmp #expected
    bne bad
    jmp ok
bad:
    jmp fail
ok:
.endmacro
; Snapshot P before the target. PHP/STA/PLA keep C/V/D/I; the final LDA
; reloads the seed value, restoring exactly the N/Z that SEED_P produced.
.macro CAPTURE_PRE
    php
    sta saved_a
    pla
    sta saved_pre
    lda saved_a
.endmacro
; Capture P before any comparison/load or PLA can change live N/Z.
.macro CHECK_STATE value, pre_status, status
    php
    sta saved_a
    pla
    sta saved_p
    lda saved_pre
    CHECK_BYTE pre_status
    lda saved_p
    CHECK_BYTE status
    lda saved_a
    CHECK_BYTE value
.endmacro
; ADC establishes V; CMP establishes C. Neither touches I.
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

; CASE 1: Set I from 0; Z and C stay set.
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $00, 1, 0, 0
    CAPTURE_PRE
probe_1:
    sei
    CHECK_STATE $00, $33, $37
passed_1:

; CASE 2: Idempotent: I is already 1 from case 1; ordinary nonzero value.
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $55, 0, 0, 0
    CAPTURE_PRE
probe_2:
    sei
    CHECK_STATE $55, $34, $34
passed_2:

; CASE 3: I already 1; preserve N, V, D and C set.
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $80, 1, 1, 1
    CAPTURE_PRE
probe_3:
    sei
    CHECK_STATE $80, $FD, $FD
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
