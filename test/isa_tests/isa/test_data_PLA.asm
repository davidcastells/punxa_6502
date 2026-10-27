; NMOS 6502 PLA: Phase A3, stack/call semantics with explicit SP setup.
; The checker never uses PLA, and captures flags before TSX changes N/Z.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p, saved_sp
.segment "CODE"
saved_a = $2010
saved_p = $2011
saved_sp = $2012

.macro CHECK_BYTE expected
    .local ok, bad
    cmp #expected
    bne bad
    jmp ok
bad:
    jmp fail
ok:
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

; PHP contributes one additional push. Read that known stack slot directly.
; Check value and SP before status, so a PLA flag defect cannot hide data checks.
.macro CHECK_STACK value, sp, status
    sta saved_a
    php
    tsx
    stx saved_sp
    lda $0100+sp
    sta saved_p
    lda saved_a
    CHECK_BYTE value
    lda saved_sp
    CHECK_BYTE ((sp-1) & $FF)
    lda saved_p
    CHECK_BYTE status
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Pop ordinary positive byte; clear stale N
.export probe_1, passed_1
    TEST_CASE 1
    lda #$55
    sta $01FF ; direct setup, no PHA dependency
    ldx #$FE
    txs
    SEED_P $80, 1, 0, 1
probe_1:
    pla
    CHECK_STACK $55, $FF, $71
passed_1:

; CASE 2: Pop zero; set Z and clear N
.export probe_2, passed_2
    TEST_CASE 2
    lda #$00
    sta $0180 ; direct setup, no PHA dependency
    ldx #$7F
    txs
    SEED_P $80, 1, 0, 1
probe_2:
    pla
    CHECK_STACK $00, $80, $73
passed_2:

; CASE 3: Pop $80; set N and clear Z
.export probe_3, passed_3
    TEST_CASE 3
    lda #$80
    sta $0101 ; direct setup, no PHA dependency
    ldx #$00
    txs
    SEED_P $00, 1, 0, 1
probe_3:
    pla
    CHECK_STACK $80, $01, $F1
passed_3:

; CASE 4: Pop $FF; preserve C/V/D
.export probe_4, passed_4
    TEST_CASE 4
    lda #$FF
    sta $01FF ; direct setup, no PHA dependency
    ldx #$FE
    txs
    SEED_P $00, 1, 1, 1
probe_4:
    pla
    CHECK_STACK $FF, $FF, $F9
passed_4:

; CASE 5: SP=$FF wraps to $00 and reads $0100
.export probe_5, passed_5
    TEST_CASE 5
    lda #$7F
    sta $0100 ; direct setup, no PHA dependency
    ldx #$FF
    txs
    SEED_P $00, 1, 0, 1
probe_5:
    pla
    CHECK_STACK $7F, $00, $71
passed_5:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
