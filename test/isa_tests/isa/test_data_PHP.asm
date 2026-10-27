; NMOS 6502 PHP, implied addressing. push full status copy, then SP=(SP-1)&$FF.
; ATmega PUSH: direct stack-byte checks, SP change, guards and sequences.
; NMOS copy bits B=1 and bit5=1 are compared explicitly, never masked.
; No PLP/PLA or second PHP is used as a status-value checking oracle.
; Checked TSX reads SP; PHA additionally proves the following stack address.
; C/Z are branched on immediately; independent observer checks all live flags.
; Live N/V/D/I preservation additionally requires the read-only observation:
; BMI/BVS/SEI/PLP lack Execute paths; I=1 and arbitrary P are not covered.
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

; Check live C/Z before any flag-changing helper. Only failure writes markers.
.macro CHECK_LIVE_CZ carry, zero, phase
    .local carry_ok, ok, bad
    .if carry
        bcc bad
    .else
        bcc carry_ok
        jmp bad
    .endif
carry_ok:
    .if zero
        beq ok
    .else
        bne ok
    .endif
bad:
    lda #6
    sta check_stage
    lda #phase
    sta check_phase
    jmp fail
ok:
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage
    sta check_phase

; CASE 1: ordinary N/Z=0; all writable seed flags clear
    TEST_CASE 1
    lda #$AA
    sta $01FF
    lda #$AA
    sta $01FE
    lda #$22
    sta $01FD
    lda #$22
    sta $0100
    ldx #$FF
    txs
    SEED_CVD 0, 0, 0
    ldx #$AA
    ldy #$55
    lda #$55
.export php_probe_01_1
php_probe_01_1:
    php
.export php_after_01_1
php_after_01_1:
    CHECK_LIVE_CZ 0, 0, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_01_1
php_captured_01_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $01FF, $30, 1 ; PHP case 1 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_01_1
php_checked_01_1:
    CHECK_MEM $2050, $FE, 2 ; TSX independent SP decrement check
    CHECK_MEM $01FE, $55, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0100, $22, 5 ; upper stack guard
    CHECK_MEM $01FD, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_01
php_passed_01:

; CASE 2: Z=1
    TEST_CASE 2
    lda #$AA
    sta $0180
    lda #$AA
    sta $017F
    lda #$22
    sta $017E
    lda #$22
    sta $0181
    ldx #$80
    txs
    SEED_CVD 0, 0, 0
    ldx #$AA
    ldy #$55
    lda #$00
.export php_probe_02_1
php_probe_02_1:
    php
.export php_after_02_1
php_after_02_1:
    CHECK_LIVE_CZ 0, 1, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_02_1
php_captured_02_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $0180, $32, 1 ; PHP case 2 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $00, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_02_1
php_checked_02_1:
    CHECK_MEM $2050, $7F, 2 ; TSX independent SP decrement check
    CHECK_MEM $017F, $00, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0181, $22, 5 ; upper stack guard
    CHECK_MEM $017E, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_02
php_passed_02:

; CASE 3: N=1; SP $01 -> $00
    TEST_CASE 3
    lda #$AA
    sta $0101
    lda #$AA
    sta $0100
    lda #$22
    sta $01FF
    lda #$22
    sta $0102
    ldx #$01
    txs
    SEED_CVD 0, 0, 0
    ldx #$AA
    ldy #$55
    lda #$80
.export php_probe_03_1
php_probe_03_1:
    php
.export php_after_03_1
php_after_03_1:
    CHECK_LIVE_CZ 0, 0, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_03_1
php_captured_03_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $0101, $B0, 1 ; PHP case 3 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $80, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_03_1
php_checked_03_1:
    CHECK_MEM $2050, $00, 2 ; TSX independent SP decrement check
    CHECK_MEM $0100, $80, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0102, $22, 5 ; upper stack guard
    CHECK_MEM $01FF, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_03
php_passed_03:

; CASE 4: C=1; SP $00 -> $FF, fixed page-$01 address
    TEST_CASE 4
    lda #$AA
    sta $0100
    lda #$AA
    sta $01FF
    lda #$22
    sta $01FE
    lda #$22
    sta $0101
    ldx #$00
    txs
    SEED_CVD 1, 0, 0
    ldx #$AA
    ldy #$55
    lda #$55
.export php_probe_04_1
php_probe_04_1:
    php
.export php_after_04_1
php_after_04_1:
    CHECK_LIVE_CZ 1, 0, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_04_1
php_captured_04_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $0100, $31, 1 ; PHP case 4 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_04_1
php_checked_04_1:
    CHECK_MEM $2050, $FF, 2 ; TSX independent SP decrement check
    CHECK_MEM $01FF, $55, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0101, $22, 5 ; upper stack guard
    CHECK_MEM $01FE, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_04
php_passed_04:

; CASE 5: V=1
    TEST_CASE 5
    lda #$AA
    sta $017F
    lda #$AA
    sta $017E
    lda #$22
    sta $017D
    lda #$22
    sta $0180
    ldx #$7F
    txs
    SEED_CVD 0, 1, 0
    ldx #$AA
    ldy #$55
    lda #$55
.export php_probe_05_1
php_probe_05_1:
    php
.export php_after_05_1
php_after_05_1:
    CHECK_LIVE_CZ 0, 0, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_05_1
php_captured_05_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $017F, $70, 1 ; PHP case 5 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_05_1
php_checked_05_1:
    CHECK_MEM $2050, $7E, 2 ; TSX independent SP decrement check
    CHECK_MEM $017E, $55, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0180, $22, 5 ; upper stack guard
    CHECK_MEM $017D, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_05
php_passed_05:

; CASE 6: D=1 after binary setup; no decimal arithmetic
    TEST_CASE 6
    lda #$AA
    sta $0155
    lda #$AA
    sta $0154
    lda #$22
    sta $0153
    lda #$22
    sta $0156
    ldx #$55
    txs
    SEED_CVD 0, 0, 1
    ldx #$AA
    ldy #$55
    lda #$55
.export php_probe_06_1
php_probe_06_1:
    php
.export php_after_06_1
php_after_06_1:
    CHECK_LIVE_CZ 0, 0, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_06_1
php_captured_06_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $0155, $38, 1 ; PHP case 6 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $55, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_06_1
php_checked_06_1:
    CHECK_MEM $2050, $54, 2 ; TSX independent SP decrement check
    CHECK_MEM $0154, $55, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0156, $22, 5 ; upper stack guard
    CHECK_MEM $0153, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_06
php_passed_06:

; CASE 7: C/V/D/Z=1
    TEST_CASE 7
    lda #$AA
    sta $01FF
    lda #$AA
    sta $01FE
    lda #$22
    sta $01FD
    lda #$22
    sta $0100
    ldx #$FF
    txs
    SEED_CVD 1, 1, 1
    ldx #$AA
    ldy #$55
    lda #$00
.export php_probe_07_1
php_probe_07_1:
    php
.export php_after_07_1
php_after_07_1:
    CHECK_LIVE_CZ 1, 1, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_07_1
php_captured_07_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $01FF, $7B, 1 ; PHP case 7 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $00, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_07_1
php_checked_07_1:
    CHECK_MEM $2050, $FE, 2 ; TSX independent SP decrement check
    CHECK_MEM $01FE, $00, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0100, $22, 5 ; upper stack guard
    CHECK_MEM $01FD, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_07
php_passed_07:

; CASE 8: C/V/D/N=1; wrap
    TEST_CASE 8
    lda #$AA
    sta $0100
    lda #$AA
    sta $01FF
    lda #$22
    sta $01FE
    lda #$22
    sta $0101
    ldx #$00
    txs
    SEED_CVD 1, 1, 1
    ldx #$AA
    ldy #$55
    lda #$80
.export php_probe_08_1
php_probe_08_1:
    php
.export php_after_08_1
php_after_08_1:
    CHECK_LIVE_CZ 1, 0, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_08_1
php_captured_08_1:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $0100, $F9, 1 ; PHP case 8 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $80, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_08_1
php_checked_08_1:
    CHECK_MEM $2050, $FF, 2 ; TSX independent SP decrement check
    CHECK_MEM $01FF, $80, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0101, $22, 5 ; upper stack guard
    CHECK_MEM $01FE, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_08
php_passed_08:

; CASE 9: three pushes across $0101/$0100/$01FF
    TEST_CASE 9
    lda #$AA
    sta $0101
    lda #$AA
    sta $0100
    lda #$AA
    sta $01FF
    lda #$AA
    sta $01FE
    lda #$22
    sta $01FD
    lda #$22
    sta $0102
    ldx #$01
    txs
    SEED_CVD 1, 1, 1
    ldx #$AA
    ldy #$55
    lda #$80
.export php_probe_09_1
php_probe_09_1:
    php
.export php_after_09_1
php_after_09_1:
    CHECK_LIVE_CZ 1, 0, 1
    sta $2020
    stx $2021
    sty $2022
.export php_captured_09_1
php_captured_09_1:
.export php_probe_09_2
php_probe_09_2:
    php
.export php_after_09_2
php_after_09_2:
    CHECK_LIVE_CZ 1, 0, 2
    sta $2030
    stx $2031
    sty $2032
.export php_captured_09_2
php_captured_09_2:
.export php_probe_09_3
php_probe_09_3:
    php
.export php_after_09_3
php_after_09_3:
    CHECK_LIVE_CZ 1, 0, 3
    sta $2040
    stx $2041
    sty $2042
.export php_captured_09_3
php_captured_09_3:
    tsx
    stx $2050
    pha
    lda #1
    sta check_phase
    CHECK_MEM $0101, $F9, 1 ; PHP case 9 phase 1 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2020, $80, 3 ; A preserved
    CHECK_MEM $2021, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2022, $55, 4 ; Y preserved
.export php_checked_09_1
php_checked_09_1:
    lda #2
    sta check_phase
    CHECK_MEM $0100, $F9, 1 ; PHP case 9 phase 2 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2030, $80, 3 ; A preserved
    CHECK_MEM $2031, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2032, $55, 4 ; Y preserved
.export php_checked_09_2
php_checked_09_2:
    lda #3
    sta check_phase
    CHECK_MEM $01FF, $F9, 1 ; PHP case 9 phase 3 exact NMOS byte; B/bit5/I checked
    CHECK_MEM $2040, $80, 3 ; A preserved
    CHECK_MEM $2041, $AA, 4 ; X preserved before TSX checker
    CHECK_MEM $2042, $55, 4 ; Y preserved
.export php_checked_09_3
php_checked_09_3:
    CHECK_MEM $2050, $FE, 2 ; TSX independent SP decrement check
    CHECK_MEM $01FE, $80, 5 ; following PHA writes the next fixed stack address
    CHECK_MEM $0102, $22, 5 ; upper stack guard
    CHECK_MEM $01FD, $22, 5 ; lower stack guard
    lda #0
    sta check_stage
    sta check_phase
.export php_passed_09
php_passed_09:

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
