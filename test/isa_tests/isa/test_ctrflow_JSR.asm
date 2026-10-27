; NMOS 6502 JSR: Phase A3, stack/call semantics with explicit SP setup.
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

; CASE 1: Independent entry and return-address frame
.export probe_1, passed_1, return_1, entry_1
    TEST_CASE 1
    ldx #$FF
    txs
    SEED_P $55, 1, 0, 1
probe_1:
    jsr entry_1
return_1:
    jmp fail ; JSR is checked independently, never via RTS
entry_1:
    CHECK_STACK $55, $FD, $71
    lda $01FF
    CHECK_BYTE >(return_1-1)
    lda $01FE
    CHECK_BYTE <(return_1-1)
    jmp passed_1
passed_1:

; CASE 2: Two-byte push wraps SP=$00
.export probe_2, passed_2, return_2, entry_2
    TEST_CASE 2
    ldx #$00
    txs
    SEED_P $80, 0, 1, 1
probe_2:
    jsr entry_2
return_2:
    jmp fail ; JSR is checked independently, never via RTS
entry_2:
    CHECK_STACK $80, $FE, $F8
    lda $0100
    CHECK_BYTE >(return_2-1)
    lda $01FF
    CHECK_BYTE <(return_2-1)
    jmp passed_2
passed_2:

; CASE 3: Nested entry checks two frames without RTS
.export probe_3, passed_3, return_3, entry_3
    TEST_CASE 3
    ldx #$FF
    txs
    SEED_P $55, 1, 0, 1
probe_3:
    jsr entry_3
return_3:
    jmp fail ; JSR is checked independently, never via RTS
entry_3:
    jsr inner_3
inner_return_3:
    jmp fail
inner_3:
    CHECK_STACK $55, $FB, $71
    lda $01FF
    CHECK_BYTE >(return_3-1)
    lda $01FE
    CHECK_BYTE <(return_3-1)
    lda $01FD
    CHECK_BYTE >(inner_return_3-1)
    lda $01FC
    CHECK_BYTE <(inner_return_3-1)
    jmp passed_3
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
