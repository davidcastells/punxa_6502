; NMOS 6502 INX: formal self-checking Phase A2 test.
; Expectations are fixed constants, never calculated with the target instruction.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p, saved_x
.segment "CODE"
saved_a = $2010
saved_p = $2011
saved_x = $2012

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
.macro CHECK_X value, status
    php
    stx saved_x
    pla
    sta saved_p
    CHECK_BYTE status
    lda saved_x
    CHECK_BYTE value
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: $00 -> $01
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $55, 1, 0, 1
    ldx #$00
probe_1:
    inx
    CHECK_X $01, $71
passed_1:

; CASE 2: $7E -> $7F
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $55, 1, 0, 1
    ldx #$7E
probe_2:
    inx
    CHECK_X $7F, $71
passed_2:

; CASE 3: $FE -> $FF
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $55, 1, 0, 1
    ldx #$FE
probe_3:
    inx
    CHECK_X $FF, $F1
passed_3:

; CASE 4: $FF -> $00
.export probe_4, passed_4
    TEST_CASE 4
    SEED_P $55, 1, 0, 1
    ldx #$FF
probe_4:
    inx
    CHECK_X $00, $73
passed_4:

; CASE 5: $01 -> $02 nonzero even result
.export probe_5, passed_5
    TEST_CASE 5
    SEED_P $55, 1, 0, 1
    ldx #$01
probe_5:
    inx
    CHECK_X $02, $71
passed_5:

; CASE 6: $7F -> $80
.export probe_6, passed_6
    TEST_CASE 6
    SEED_P $55, 1, 0, 1
    ldx #$7F
probe_6:
    inx
    CHECK_X $80, $F1
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
