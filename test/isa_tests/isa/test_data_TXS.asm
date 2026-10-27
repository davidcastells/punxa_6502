; NMOS 6502 TXS, implied addressing. X -> SP; all status flags and A/X/Y preserved.
; ATmega OUT/PUSH: literal destination readback, source/flags, stack guards.
; No TSX in this file. PHP/PHA must write two fixed stack-page addresses.
; The first target initializes SP before any stack use; no assumed initial SP.
; Full status bytes are read before comparisons; read-only SP is independent.
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

; CASE 1: X $00 -> SP; flags oppose source N/Z
    TEST_CASE 1
    lda #$AA
    sta $0100
    lda #$AA
    sta $01FF
    lda #$22
    sta $0101
    lda #$22
    sta $01FE
    SEED_CVD 1, 1, 1
    lda #$55
    ldx #$00
    ldy #$80
.export txs_probe_01_1
txs_probe_01_1:
    txs
.export txs_after_01_1
txs_after_01_1:
    sta $2020
    stx $2021
    sty $2022
    php
    pha
.export txs_captured_01_1
txs_captured_01_1:
    lda #1
    sta check_phase
    CHECK_MEM $0100, $F9, 1 ; TXS case 1 phase 1 full unchanged status
    CHECK_MEM $01FF, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $00, 4 ; source X preserved
    CHECK_MEM $2022, $80, 4 ; Y preserved
    CHECK_MEM $0101, $22, 5 ; upper stack guard
    CHECK_MEM $01FE, $22, 5 ; lower stack guard
.export txs_checked_01_1
txs_checked_01_1:
    lda #0
    sta check_stage
    sta check_phase
.export txs_passed_01
txs_passed_01:

; CASE 2: X $01 -> SP; flags oppose source N/Z
    TEST_CASE 2
    lda #$AA
    sta $0101
    lda #$AA
    sta $0100
    lda #$22
    sta $0102
    lda #$22
    sta $01FF
    SEED_CVD 0, 0, 0
    lda #$55
    ldx #$01
    ldy #$00
.export txs_probe_02_1
txs_probe_02_1:
    txs
.export txs_after_02_1
txs_after_02_1:
    sta $2020
    stx $2021
    sty $2022
    php
    pha
.export txs_captured_02_1
txs_captured_02_1:
    lda #1
    sta check_phase
    CHECK_MEM $0101, $32, 1 ; TXS case 2 phase 1 full unchanged status
    CHECK_MEM $0100, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $01, 4 ; source X preserved
    CHECK_MEM $2022, $00, 4 ; Y preserved
    CHECK_MEM $0102, $22, 5 ; upper stack guard
    CHECK_MEM $01FF, $22, 5 ; lower stack guard
.export txs_checked_02_1
txs_checked_02_1:
    lda #0
    sta check_stage
    sta check_phase
.export txs_passed_02
txs_passed_02:

; CASE 3: X $7F -> SP; flags oppose source N/Z
    TEST_CASE 3
    lda #$AA
    sta $017F
    lda #$AA
    sta $017E
    lda #$22
    sta $0180
    lda #$22
    sta $017D
    SEED_CVD 1, 0, 0
    lda #$55
    ldx #$7F
    ldy #$80
.export txs_probe_03_1
txs_probe_03_1:
    txs
.export txs_after_03_1
txs_after_03_1:
    sta $2020
    stx $2021
    sty $2022
    php
    pha
.export txs_captured_03_1
txs_captured_03_1:
    lda #1
    sta check_phase
    CHECK_MEM $017F, $B1, 1 ; TXS case 3 phase 1 full unchanged status
    CHECK_MEM $017E, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $7F, 4 ; source X preserved
    CHECK_MEM $2022, $80, 4 ; Y preserved
    CHECK_MEM $0180, $22, 5 ; upper stack guard
    CHECK_MEM $017D, $22, 5 ; lower stack guard
.export txs_checked_03_1
txs_checked_03_1:
    lda #0
    sta check_stage
    sta check_phase
.export txs_passed_03
txs_passed_03:

; CASE 4: X $80 -> SP; flags oppose source N/Z
    TEST_CASE 4
    lda #$AA
    sta $0180
    lda #$AA
    sta $017F
    lda #$22
    sta $0181
    lda #$22
    sta $017E
    SEED_CVD 0, 1, 0
    lda #$55
    ldx #$80
    ldy #$00
.export txs_probe_04_1
txs_probe_04_1:
    txs
.export txs_after_04_1
txs_after_04_1:
    sta $2020
    stx $2021
    sty $2022
    php
    pha
.export txs_captured_04_1
txs_captured_04_1:
    lda #1
    sta check_phase
    CHECK_MEM $0180, $72, 1 ; TXS case 4 phase 1 full unchanged status
    CHECK_MEM $017F, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $80, 4 ; source X preserved
    CHECK_MEM $2022, $00, 4 ; Y preserved
    CHECK_MEM $0181, $22, 5 ; upper stack guard
    CHECK_MEM $017E, $22, 5 ; lower stack guard
.export txs_checked_04_1
txs_checked_04_1:
    lda #0
    sta check_stage
    sta check_phase
.export txs_passed_04
txs_passed_04:

; CASE 5: X $FF -> SP; flags oppose source N/Z
    TEST_CASE 5
    lda #$AA
    sta $01FF
    lda #$AA
    sta $01FE
    lda #$22
    sta $0100
    lda #$22
    sta $01FD
    SEED_CVD 0, 0, 1
    lda #$55
    ldx #$FF
    ldy #$00
.export txs_probe_05_1
txs_probe_05_1:
    txs
.export txs_after_05_1
txs_after_05_1:
    sta $2020
    stx $2021
    sty $2022
    php
    pha
.export txs_captured_05_1
txs_captured_05_1:
    lda #1
    sta check_phase
    CHECK_MEM $01FF, $3A, 1 ; TXS case 5 phase 1 full unchanged status
    CHECK_MEM $01FE, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $FF, 4 ; source X preserved
    CHECK_MEM $2022, $00, 4 ; Y preserved
    CHECK_MEM $0100, $22, 5 ; upper stack guard
    CHECK_MEM $01FD, $22, 5 ; lower stack guard
.export txs_checked_05_1
txs_checked_05_1:
    lda #0
    sta check_stage
    sta check_phase
.export txs_passed_05
txs_passed_05:

; CASE 6: X $55 -> SP; flags oppose source N/Z
    TEST_CASE 6
    lda #$AA
    sta $0155
    lda #$AA
    sta $0154
    lda #$22
    sta $0156
    lda #$22
    sta $0153
    SEED_CVD 1, 1, 1
    lda #$55
    ldx #$55
    ldy #$80
.export txs_probe_06_1
txs_probe_06_1:
    txs
.export txs_after_06_1
txs_after_06_1:
    sta $2020
    stx $2021
    sty $2022
    php
    pha
.export txs_captured_06_1
txs_captured_06_1:
    lda #1
    sta check_phase
    CHECK_MEM $0155, $F9, 1 ; TXS case 6 phase 1 full unchanged status
    CHECK_MEM $0154, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $55, 4 ; source X preserved
    CHECK_MEM $2022, $80, 4 ; Y preserved
    CHECK_MEM $0156, $22, 5 ; upper stack guard
    CHECK_MEM $0153, $22, 5 ; lower stack guard
.export txs_checked_06_1
txs_checked_06_1:
    lda #0
    sta check_stage
    sta check_phase
.export txs_passed_06
txs_passed_06:

; CASE 7: Consecutive X $00 -> $80 -> $55; all intermediate SP/status checked
    TEST_CASE 7
    lda #$AA
    sta $0100
    lda #$AA
    sta $01FF
    lda #$22
    sta $0101
    lda #$22
    sta $01FE
    lda #$AA
    sta $0180
    lda #$AA
    sta $017F
    lda #$22
    sta $0181
    lda #$22
    sta $017E
    lda #$AA
    sta $0155
    lda #$AA
    sta $0154
    lda #$22
    sta $0156
    lda #$22
    sta $0153
    SEED_CVD 1, 1, 1
    lda #$55
    ldx #$00
    ldy #$80
.export txs_probe_07_1
txs_probe_07_1:
    txs
.export txs_after_07_1
txs_after_07_1:
    sta $2020
    stx $2021
    sty $2022
    php
    pha
.export txs_captured_07_1
txs_captured_07_1:
    ldx #$80
    ldy #$00
.export txs_probe_07_2
txs_probe_07_2:
    txs
.export txs_after_07_2
txs_after_07_2:
    sta $2030
    stx $2031
    sty $2032
    php
    pha
.export txs_captured_07_2
txs_captured_07_2:
    ldx #$55
    ldy #$80
.export txs_probe_07_3
txs_probe_07_3:
    txs
.export txs_after_07_3
txs_after_07_3:
    sta $2040
    stx $2041
    sty $2042
    php
    pha
.export txs_captured_07_3
txs_captured_07_3:
    lda #1
    sta check_phase
    CHECK_MEM $0100, $F9, 1 ; TXS case 7 phase 1 full unchanged status
    CHECK_MEM $01FF, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $00, 4 ; source X preserved
    CHECK_MEM $2022, $80, 4 ; Y preserved
    CHECK_MEM $0101, $22, 5 ; upper stack guard
    CHECK_MEM $01FE, $22, 5 ; lower stack guard
.export txs_checked_07_1
txs_checked_07_1:
    lda #2
    sta check_phase
    CHECK_MEM $0180, $7B, 1 ; TXS case 7 phase 2 full unchanged status
    CHECK_MEM $017F, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2030, $55, 3 ; A preserved
    CHECK_MEM $2031, $80, 4 ; source X preserved
    CHECK_MEM $2032, $00, 4 ; Y preserved
    CHECK_MEM $0181, $22, 5 ; upper stack guard
    CHECK_MEM $017E, $22, 5 ; lower stack guard
.export txs_checked_07_2
txs_checked_07_2:
    lda #3
    sta check_phase
    CHECK_MEM $0155, $F9, 1 ; TXS case 7 phase 3 full unchanged status
    CHECK_MEM $0154, $55, 2 ; PHA confirms second fixed stack address
    CHECK_MEM $2040, $55, 3 ; A preserved
    CHECK_MEM $2041, $55, 4 ; source X preserved
    CHECK_MEM $2042, $80, 4 ; Y preserved
    CHECK_MEM $0156, $22, 5 ; upper stack guard
    CHECK_MEM $0153, $22, 5 ; lower stack guard
.export txs_checked_07_3
txs_checked_07_3:
    lda #0
    sta check_stage
    sta check_phase
.export txs_passed_07
txs_passed_07:

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
