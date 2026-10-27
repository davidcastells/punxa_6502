; NMOS 6502 TSX, implied addressing. SP -> X; N/Z updated, SP/A/Y/C/V/D/I preserved.
; ATmega IN/MOV: fixed readback, destination/source and state preservation.
; Setup TXS is followed by a real PHA: target SP is NOT a TXS/TSX round trip.
; Direct stack marker/PHP-byte checks and read-only SP observations support it.
; No TSX is used in the checking code. PHP snapshots precede comparisons.
; Fixed expectations; no CPU-derived expected values. See Batch 5 report.
; I=0 is this simulator's startup convention, NOT physical reset behavior.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, check_stage, check_phase
.segment "CODE"
check_stage = $2015
check_phase = $2016

.macro CHECK_MEM location, expected, stage
    .local ok
    lda #stage
    sta check_stage
    lda location
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

; Establish V using binary ADC before selecting D; loads then seed N/Z.
.macro SEED_CVD carry, overflow, decimal
    cld
    clc
    lda #0
    adc #0
    .if overflow
        lda #$7F
        adc #1
    .endif
    .if carry
        sec
    .else
        clc
    .endif
    .if decimal
        sed
    .endif
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage
    sta check_phase

; CASE 1: SP $00 -> X; opposing initial N/Z
    TEST_CASE 1
    lda #$AA
    sta $0100
    lda #$22
    sta $01FF
    ldx #$01
    txs
    lda #$55
    pha
    SEED_CVD 1, 1, 1
    lda #$55
    ldy #$33
    ldx #$FF
.export tsx_probe_01_1
tsx_probe_01_1:
    tsx
.export tsx_after_01_1
tsx_after_01_1:
    sta $2020
    stx $2021
    sty $2022
    php
.export tsx_captured_01_1
tsx_captured_01_1:
    lda #1
    sta check_phase
    CHECK_MEM $0100, $7B, 1 ; full status byte, I=0
    CHECK_MEM $2021, $00, 2 ; TSX case 1 phase 1 expected X
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2022, $33, 4 ; Y preserved
.export tsx_checked_01_1
tsx_checked_01_1:
    CHECK_MEM $0101, $55, 5 ; setup PHA wrote independent known stack address
    CHECK_MEM $01FF, $22, 5 ; below final PHP slot untouched
    lda #0
    sta check_stage
    sta check_phase
.export tsx_passed_01
tsx_passed_01:

; CASE 2: SP $01 -> X; opposing initial N/Z
    TEST_CASE 2
    lda #$AA
    sta $0101
    lda #$22
    sta $0100
    ldx #$02
    txs
    lda #$55
    pha
    SEED_CVD 0, 0, 0
    lda #$55
    ldy #$33
    ldx #$00
.export tsx_probe_02_1
tsx_probe_02_1:
    tsx
.export tsx_after_02_1
tsx_after_02_1:
    sta $2020
    stx $2021
    sty $2022
    php
.export tsx_captured_02_1
tsx_captured_02_1:
    lda #1
    sta check_phase
    CHECK_MEM $0101, $30, 1 ; full status byte, I=0
    CHECK_MEM $2021, $01, 2 ; TSX case 2 phase 1 expected X
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2022, $33, 4 ; Y preserved
.export tsx_checked_02_1
tsx_checked_02_1:
    CHECK_MEM $0102, $55, 5 ; setup PHA wrote independent known stack address
    CHECK_MEM $0100, $22, 5 ; below final PHP slot untouched
    lda #0
    sta check_stage
    sta check_phase
.export tsx_passed_02
tsx_passed_02:

; CASE 3: SP $7F -> X; opposing initial N/Z
    TEST_CASE 3
    lda #$AA
    sta $017F
    lda #$22
    sta $017E
    ldx #$80
    txs
    lda #$55
    pha
    SEED_CVD 1, 0, 0
    lda #$55
    ldy #$33
    ldx #$80
.export tsx_probe_03_1
tsx_probe_03_1:
    tsx
.export tsx_after_03_1
tsx_after_03_1:
    sta $2020
    stx $2021
    sty $2022
    php
.export tsx_captured_03_1
tsx_captured_03_1:
    lda #1
    sta check_phase
    CHECK_MEM $017F, $31, 1 ; full status byte, I=0
    CHECK_MEM $2021, $7F, 2 ; TSX case 3 phase 1 expected X
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2022, $33, 4 ; Y preserved
.export tsx_checked_03_1
tsx_checked_03_1:
    CHECK_MEM $0180, $55, 5 ; setup PHA wrote independent known stack address
    CHECK_MEM $017E, $22, 5 ; below final PHP slot untouched
    lda #0
    sta check_stage
    sta check_phase
.export tsx_passed_03
tsx_passed_03:

; CASE 4: SP $80 -> X; opposing initial N/Z
    TEST_CASE 4
    lda #$AA
    sta $0180
    lda #$22
    sta $017F
    ldx #$81
    txs
    lda #$55
    pha
    SEED_CVD 0, 1, 0
    lda #$55
    ldy #$33
    ldx #$00
.export tsx_probe_04_1
tsx_probe_04_1:
    tsx
.export tsx_after_04_1
tsx_after_04_1:
    sta $2020
    stx $2021
    sty $2022
    php
.export tsx_captured_04_1
tsx_captured_04_1:
    lda #1
    sta check_phase
    CHECK_MEM $0180, $F0, 1 ; full status byte, I=0
    CHECK_MEM $2021, $80, 2 ; TSX case 4 phase 1 expected X
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2022, $33, 4 ; Y preserved
.export tsx_checked_04_1
tsx_checked_04_1:
    CHECK_MEM $0181, $55, 5 ; setup PHA wrote independent known stack address
    CHECK_MEM $017F, $22, 5 ; below final PHP slot untouched
    lda #0
    sta check_stage
    sta check_phase
.export tsx_passed_04
tsx_passed_04:

; CASE 5: SP $FF -> X; opposing initial N/Z
    TEST_CASE 5
    lda #$AA
    sta $01FF
    lda #$22
    sta $01FE
    ldx #$00
    txs
    lda #$55
    pha
    SEED_CVD 0, 0, 1
    lda #$55
    ldy #$33
    ldx #$00
.export tsx_probe_05_1
tsx_probe_05_1:
    tsx
.export tsx_after_05_1
tsx_after_05_1:
    sta $2020
    stx $2021
    sty $2022
    php
.export tsx_captured_05_1
tsx_captured_05_1:
    lda #1
    sta check_phase
    CHECK_MEM $01FF, $B8, 1 ; full status byte, I=0
    CHECK_MEM $2021, $FF, 2 ; TSX case 5 phase 1 expected X
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2022, $33, 4 ; Y preserved
.export tsx_checked_05_1
tsx_checked_05_1:
    CHECK_MEM $0100, $55, 5 ; setup PHA wrote independent known stack address
    CHECK_MEM $01FE, $22, 5 ; below final PHP slot untouched
    lda #0
    sta check_stage
    sta check_phase
.export tsx_passed_05
tsx_passed_05:

; CASE 6: SP $55 -> X; opposing initial N/Z
    TEST_CASE 6
    lda #$AA
    sta $0155
    lda #$22
    sta $0154
    ldx #$56
    txs
    lda #$55
    pha
    SEED_CVD 1, 1, 1
    lda #$55
    ldy #$33
    ldx #$80
.export tsx_probe_06_1
tsx_probe_06_1:
    tsx
.export tsx_after_06_1
tsx_after_06_1:
    sta $2020
    stx $2021
    sty $2022
    php
.export tsx_captured_06_1
tsx_captured_06_1:
    lda #1
    sta check_phase
    CHECK_MEM $0155, $79, 1 ; full status byte, I=0
    CHECK_MEM $2021, $55, 2 ; TSX case 6 phase 1 expected X
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2022, $33, 4 ; Y preserved
.export tsx_checked_06_1
tsx_checked_06_1:
    CHECK_MEM $0156, $55, 5 ; setup PHA wrote independent known stack address
    CHECK_MEM $0154, $22, 5 ; below final PHP slot untouched
    lda #0
    sta check_stage
    sta check_phase
.export tsx_passed_06
tsx_passed_06:

; CASE 7: Consecutive SP $00 -> $FF -> $FE; checker pushes change SP
    TEST_CASE 7
    lda #$AA
    sta $0100
    lda #$AA
    sta $01FF
    lda #$AA
    sta $01FE
    lda #$22
    sta $01FD
    ldx #$01
    txs
    lda #$55
    pha
    SEED_CVD 1, 1, 1
    lda #$55
    ldy #$33
    ldx #$FF
.export tsx_probe_07_1
tsx_probe_07_1:
    tsx
.export tsx_after_07_1
tsx_after_07_1:
    sta $2020
    stx $2021
    sty $2022
    php
.export tsx_captured_07_1
tsx_captured_07_1:
    ldx #$00
.export tsx_probe_07_2
tsx_probe_07_2:
    tsx
.export tsx_after_07_2
tsx_after_07_2:
    sta $2030
    stx $2031
    sty $2032
    php
.export tsx_captured_07_2
tsx_captured_07_2:
    ldx #$00
.export tsx_probe_07_3
tsx_probe_07_3:
    tsx
.export tsx_after_07_3
tsx_after_07_3:
    sta $2040
    stx $2041
    sty $2042
    php
.export tsx_captured_07_3
tsx_captured_07_3:
    lda #1
    sta check_phase
    CHECK_MEM $0100, $7B, 1 ; full status byte, I=0
    CHECK_MEM $2021, $00, 2 ; TSX case 7 phase 1 expected X
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2022, $33, 4 ; Y preserved
.export tsx_checked_07_1
tsx_checked_07_1:
    lda #2
    sta check_phase
    CHECK_MEM $01FF, $F9, 1 ; full status byte, I=0
    CHECK_MEM $2031, $FF, 2 ; TSX case 7 phase 2 expected X
    CHECK_MEM $2030, $55, 3 ; A preserved
    CHECK_MEM $2032, $33, 4 ; Y preserved
.export tsx_checked_07_2
tsx_checked_07_2:
    lda #3
    sta check_phase
    CHECK_MEM $01FE, $F9, 1 ; full status byte, I=0
    CHECK_MEM $2041, $FE, 2 ; TSX case 7 phase 3 expected X
    CHECK_MEM $2040, $55, 3 ; A preserved
    CHECK_MEM $2042, $33, 4 ; Y preserved
.export tsx_checked_07_3
tsx_checked_07_3:
    CHECK_MEM $0101, $55, 5 ; setup PHA wrote independent known stack address
    CHECK_MEM $01FD, $22, 5 ; below final PHP slot untouched
    lda #0
    sta check_stage
    sta check_phase
.export tsx_passed_07
tsx_passed_07:

success:
    lda #1
    sta final_result
    jmp end
fail:
    lda #255
    sta final_result
    jmp end
end:
    jmp end
