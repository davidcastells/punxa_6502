; NMOS 6502 PHA: Phase A3, stack/call semantics with explicit SP setup.
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

; CASE 1: Ordinary push from SP=$FF
.export probe_1, passed_1
    TEST_CASE 1
    ldx #$AA
    stx $01FF
    ldx #$22
    stx $0100
    ldx #$FF
    txs
    SEED_P $55, 1, 0, 1
probe_1:
    pha
    CHECK_STACK $55, $FE, $71
    lda $01FF
    CHECK_BYTE $55
    lda $0100
    CHECK_BYTE $22
passed_1:

; CASE 2: Zero byte from SP=$80
.export probe_2, passed_2
    TEST_CASE 2
    ldx #$FF
    stx $0180
    ldx #$22
    stx $0181
    ldx #$80
    txs
    SEED_P $00, 0, 0, 0
probe_2:
    pha
    CHECK_STACK $00, $7F, $32
    lda $0180
    CHECK_BYTE $00
    lda $0181
    CHECK_BYTE $22
passed_2:

; CASE 3: Negative byte near stack bottom
.export probe_3, passed_3
    TEST_CASE 3
    ldx #$7F
    stx $0101
    ldx #$22
    stx $0102
    ldx #$01
    txs
    SEED_P $80, 1, 1, 1
probe_3:
    pha
    CHECK_STACK $80, $00, $F9
    lda $0101
    CHECK_BYTE $80
    lda $0102
    CHECK_BYTE $22
passed_3:

; CASE 4: SP=$00 writes $0100 then wraps to $FF
.export probe_4, passed_4
    TEST_CASE 4
    ldx #$00
    stx $0100
    ldx #$22
    stx $0101
    ldx #$00
    txs
    SEED_P $FF, 0, 0, 0
probe_4:
    pha
    CHECK_STACK $FF, $FF, $B0
    lda $0100
    CHECK_BYTE $FF
    lda $0101
    CHECK_BYTE $22
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
