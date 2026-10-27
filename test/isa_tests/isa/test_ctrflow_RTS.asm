; NMOS 6502 RTS: Phase A3, stack/call semantics with explicit SP setup.
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

; CASE 1: Manual return frame, independent of JSR
.export probe_1, passed_1, landing_1
    TEST_CASE 1
    lda #<(landing_1-1)
    sta $01FE
    lda #>(landing_1-1)
    sta $01FF
    ldx #$FD
    txs
    SEED_P $55, 1, 0, 1
probe_1:
    rts
    jmp fail
landing_1:
    CHECK_STACK $55, $FF, $71
passed_1:

; CASE 2: SP=$FF wraps while popping two bytes
.export probe_2, passed_2, landing_2
    TEST_CASE 2
    lda #<(landing_2-1)
    sta $0100
    lda #>(landing_2-1)
    sta $0101
    ldx #$FF
    txs
    SEED_P $80, 0, 1, 1
probe_2:
    rts
    jmp fail
landing_2:
    CHECK_STACK $80, $01, $F8
passed_2:

; CASE 3: Return-address low byte $FF carries into next page
.export probe_3, passed_3, landing_3
    TEST_CASE 3
    lda #<(landing_3-1)
    sta $01FE
    lda #>(landing_3-1)
    sta $01FF
    ldx #$FD
    txs
    SEED_P $00, 1, 0, 0
probe_3:
    rts
    jmp fail
    .align $100, $00
landing_3:
    .assert <landing_3 = 0, lderror, "return must cross page from low FF"
    CHECK_STACK $00, $FF, $33
passed_3:

; CASE 4: Nested JSR/RTS integration returns through both frames
.export probe_4, passed_4, landing_4
    TEST_CASE 4
    ldx #$FF
    txs
    SEED_P $80, 1, 0, 1
    jsr outer_4
landing_4:
    jmp verify_4
outer_4:
    jsr inner_4
inner_return_4:
    rts
    jmp fail
inner_4:
probe_4:
    rts
    jmp fail
verify_4:
    CHECK_STACK $80, $FF, $F1
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
