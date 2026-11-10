; NMOS 6502 CLV: clears the Overflow flag V; all other flags/state kept.
; Structure follows test_mcu_CLC.asm. PHP stack bytes are checked in full.
; V=1 is produced by ADC signed overflow ($7F+1). A pre-target PHP snapshot
; proves the actual V (and other flags) before CLV runs.
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
; ADC establishes V; CMP establishes C (CMP does not touch V).
.macro SEED_P value, carry, decimal, overflow
    cld
    lda #0
    adc #0 ; C and V become zero regardless of incoming state
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

; CASE 1: Clear V=1; Z and C stay set.
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $00, 1, 0, 1
    CAPTURE_PRE
probe_1:
    clv
    CHECK_STATE $00, $73, $33
passed_1:

; CASE 2: Idempotent with V=0; ordinary nonzero value.
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $55, 0, 0, 0
    CAPTURE_PRE
probe_2:
    clv
    CHECK_STATE $55, $30, $30
passed_2:

; CASE 3: Clear V=1; preserve N, D and C set.
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $80, 1, 1, 1
    CAPTURE_PRE
probe_3:
    clv
    CHECK_STATE $80, $F9, $B9
passed_3:

; CASE 4: Clear V=1 while I=1 (set by SEI helper); I must be preserved.
.export probe_4, passed_4
    TEST_CASE 4
    sei
    SEED_P $55, 0, 0, 1
    CAPTURE_PRE
probe_4:
    clv
    CHECK_STATE $55, $74, $34
passed_4:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
