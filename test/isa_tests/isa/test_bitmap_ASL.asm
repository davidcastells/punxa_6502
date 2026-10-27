; NMOS 6502 ASL: formal self-checking Phase A2 test.
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
.macro CHECK_ACC value, status
    php
    sta saved_a
    ; Compare live A before PLA: saving A would truncate an invalid wide value.
    CHECK_BYTE value
    pla
    sta saved_p
    CHECK_BYTE status
.endmacro
.macro CHECK_MEMORY target, value, status, guard
    php
    sta saved_a
    pla
    sta saved_p
    lda target
    CHECK_BYTE value
    lda saved_a
    CHECK_BYTE $55 ; accumulator is unaffected by memory INC/ASL
    lda guard
    CHECK_BYTE $11
    lda target-1
    CHECK_BYTE $22
    lda target+1
    CHECK_BYTE $22
    lda saved_p
    CHECK_BYTE status
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Accumulator $00 -> $00
.export probe_1, passed_1
    TEST_CASE 1
    SEED_P $00, 1, 0, 1
probe_1:
    asl a
    CHECK_ACC $00, $72
passed_1:

; CASE 2: Accumulator $01 -> $02
.export probe_2, passed_2
    TEST_CASE 2
    SEED_P $01, 1, 0, 1
probe_2:
    asl a
    CHECK_ACC $02, $70
passed_2:

; CASE 3: Accumulator $40 -> $80
.export probe_3, passed_3
    TEST_CASE 3
    SEED_P $40, 1, 0, 1
probe_3:
    asl a
    CHECK_ACC $80, $F0
passed_3:

; CASE 4: Accumulator $80 -> $00
.export probe_4, passed_4
    TEST_CASE 4
    SEED_P $80, 1, 0, 1
probe_4:
    asl a
    CHECK_ACC $00, $73
passed_4:

; CASE 5: Accumulator $FF -> $FE
.export probe_5, passed_5
    TEST_CASE 5
    SEED_P $FF, 1, 0, 1
probe_5:
    asl a
    CHECK_ACC $FE, $F1
passed_5:

; CASE 6: Zero Page write-back
.export probe_6, passed_6
    TEST_CASE 6
    ldx #$21
    stx $0040
    ldx #$22
    stx $003F
    stx $0041
    ldx #$11
    stx $0042
    SEED_P $55, 1, 0, 1
probe_6:
    asl $40
    CHECK_MEMORY $0040, $42, $70, $0042
passed_6:

; CASE 7: Zero Page,X wrap and carry-out
.export probe_7, passed_7
    TEST_CASE 7
    ldx #$80
    stx $0001
    ldx #$22
    stx $0000
    stx $0002
    ldx #$11
    stx $0101
    ldx #2
    SEED_P $55, 1, 0, 1
probe_7:
    asl $FF,x
    CHECK_MEMORY $0001, $00, $73, $0101
passed_7:

; CASE 8: Absolute negative result
.export probe_8, passed_8
    TEST_CASE 8
    ldx #$40
    stx $1000
    ldx #$22
    stx $0FFF
    stx $1001
    ldx #$11
    stx $1002
    SEED_P $55, 1, 0, 1
probe_8:
    asl $1000
    CHECK_MEMORY $1000, $80, $F0, $1002
passed_8:

; CASE 9: Absolute,X page carry and high input
.export probe_9, passed_9
    TEST_CASE 9
    ldx #$FF
    stx $1300
    ldx #$22
    stx $12FF
    stx $1301
    ldx #$11
    stx $1200
    ldx #1
    SEED_P $55, 1, 0, 1
probe_9:
    asl $12FF,x
    CHECK_MEMORY $1300, $FE, $F1, $1200
passed_9:

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
