; NMOS 6502 AND: formal self-checking Phase A test.
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

; CASE 1: Immediate complementary patterns -> zero
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $55, 0, 0, 0
    ldx #$80
probe_1:
    and #$AA
    CHECK_STATE $00, $32
passed_1:

; CASE 2: Immediate negative pattern
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $F0, 1, 0, 1
    ldx #0
probe_2:
    and #$CC
    CHECK_STATE $C0, $F1
passed_2:

; CASE 3: Immediate clears N and clears stale Z
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $FF, 0, 1, 1
    ldx #0
probe_3:
    and #$0F
    CHECK_STATE $0F, $78
passed_3:

; CASE 4: Zero Page
.export probe_4, passed_4
    TEST_CASE 4
    ldx #$0F
    stx $40
    SEED_P $3C, 1, 0, 0
    ldx #$80
probe_4:
    and $40
    CHECK_STATE $0C, $31
passed_4:

; CASE 5: Zero Page,X wrap
.export probe_5, passed_5
    TEST_CASE 5
    ldx #$80
    stx $01
    ldx #$11
    stx $0101
    ldx #2
    SEED_P $FF, 0, 0, 0
    ldy #0
probe_5:
    and $FF,x
    CHECK_STATE $80, $B0
passed_5:

; CASE 6: Absolute zero
.export probe_6, passed_6
    TEST_CASE 6
    ldx #$0F
    stx $1000
    SEED_P $F0, 1, 0, 1
    ldx #$80
probe_6:
    and $1000
    CHECK_STATE $00, $73
passed_6:

; CASE 7: Absolute,X page carry
.export probe_7, passed_7
    TEST_CASE 7
    ldx #$FF
    stx $1300
    ldx #$11
    stx $1200
    ldx #1
    SEED_P $AA, 0, 0, 0
    ldy #0
probe_7:
    and $12FF,x
    CHECK_STATE $AA, $B0
passed_7:

; CASE 8: Absolute,Y page carry
.export probe_8, passed_8
    TEST_CASE 8
    ldx #$55
    stx $1401
    ldx #$11
    stx $1301
    ldy #2
    SEED_P $7F, 1, 0, 0
    ldx #$80
probe_8:
    and $13FF,y
    CHECK_STATE $55, $31
passed_8:

; CASE 9: Indexed indirect
.export probe_9, passed_9
    TEST_CASE 9
    ldx #$80
    stx $1500
    ldx #0
    stx $64
    ldx #$15
    stx $65
    ldx #4
    SEED_P $81, 0, 0, 1
    ldy #0
probe_9:
    and ($60,x)
    CHECK_STATE $80, $F0
passed_9:

; CASE 10: Indirect indexed page carry; D preserved
.export probe_10, passed_10
    TEST_CASE 10
    ldx #$AA
    stx $1700
    ldx #$FF
    stx $70
    ldx #$16
    stx $71
    ldy #1
    SEED_P $55, 1, 1, 0
    ldx #$80
probe_10:
    and ($70),y
    CHECK_STATE $00, $3B
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
