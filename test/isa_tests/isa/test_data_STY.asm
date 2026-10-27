; NMOS 6502 STY: zp, zp,X and absolute; source Y and flags are unchanged.
; ATmega STS/STD: read-back, source/flags preservation and address guards.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_p, saved_sp, check_stage
.segment "CODE"

saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_p = $2013
saved_sp = $2014
check_stage = $2015

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

.macro SETUP target, left, right, wrong, value, index_x, carry, overflow, decimal
    ldx #$FF
    txs
    ; Initialize using STA, never the STY target.
    lda #(value ^ $FF)
    sta target
    lda #$22
    sta left
    sta right
    lda #$11
    sta wrong
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
    ldy #value ; LDY is verified before adding this formal file
    lda #$55
    ; N/Z are deliberately unrelated to the stored byte, X also indexes zp,X.
    ldx #index_x
.endmacro

.macro CHECK_STY target, left, right, wrong, value, index_x, flags
    sta saved_a
    php ; capture unchanged target status before register-transfer helpers
    tya ; do not verify STY by storing Y with another STY
    sta saved_y
    txa
    sta saved_x
    tsx
    txa
    sta saved_sp
    lda $01FF ; direct status snapshot; no PLA or CPY dependency
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags
    lda #2
    sta check_stage
    lda saved_y
    CHECK_A value
    lda #3
    sta check_stage
    lda target
    CHECK_A value
    lda left
    CHECK_A $22
    lda right
    CHECK_A $22
    lda wrong
    CHECK_A $11
    lda #4
    sta check_stage
    lda saved_a
    CHECK_A $55
    lda saved_x
    CHECK_A index_x
    lda saved_sp
    CHECK_A $FE ; only the checker PHP changed initial SP=$FF
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Zero Page typical $55; N stays set although Y is positive.
.export sty_probe_01, sty_after_01, sty_passed_01
    TEST_CASE 1
    SETUP $0040, $003F, $0041, $0042, $55, $80, 0, 0, 0
sty_probe_01:
    sty $40
sty_after_01:
    CHECK_STY $0040, $003F, $0041, $0042, $55, $80, $B0
sty_passed_01:

; CASE 2: Zero Page zero must not set Z from the stored byte.
.export sty_probe_02, sty_after_02, sty_passed_02
    TEST_CASE 2
    SETUP $0041, $0040, $0042, $0043, $00, $80, 1, 0, 0
sty_probe_02:
    sty $41
sty_after_02:
    CHECK_STY $0041, $0040, $0042, $0043, $00, $80, $B1
sty_passed_02:

; CASE 3: Zero Page $FF; N stays clear and Z/V/D stay set.
.export sty_probe_03, sty_after_03, sty_passed_03
    TEST_CASE 3
    SETUP $0042, $0041, $0043, $0044, $FF, $00, 0, 1, 1
sty_probe_03:
    sty $42
sty_after_03:
    CHECK_STY $0042, $0041, $0043, $0044, $FF, $00, $7A
sty_passed_03:

; CASE 4: Zero Page,X $40+2 selects $42, leaving unindexed $40 intact.
.export sty_probe_04, sty_after_04, sty_passed_04
    TEST_CASE 4
    SETUP $0042, $0041, $0043, $0040, $7F, $02, 1, 0, 0
sty_probe_04:
    sty $40,x
sty_after_04:
    CHECK_STY $0042, $0041, $0043, $0040, $7F, $02, $31
sty_passed_04:

; CASE 5: Zero Page,X $FF+2 wraps to $01, not $0101.
.export sty_probe_05, sty_after_05, sty_passed_05
    TEST_CASE 5
    SETUP $0001, $0000, $0002, $0101, $80, $02, 0, 1, 0
sty_probe_05:
    sty $FF,x
sty_after_05:
    CHECK_STY $0001, $0000, $0002, $0101, $80, $02, $70
sty_passed_05:

; CASE 6: Absolute $1000; $A6 with Z/C/V/D set and N clear.
.export sty_probe_06, sty_after_06, sty_passed_06
    TEST_CASE 6
    SETUP $1000, $0FFF, $1001, $1002, $A6, $00, 1, 1, 1
sty_probe_06:
    sty $1000
sty_after_06:
    CHECK_STY $1000, $0FFF, $1001, $1002, $A6, $00, $7B
sty_passed_06:

; CASE 7: Last address $FFFF, guarding $FFFE/$0000 and wrong-page $00FF.
.export sty_probe_07, sty_after_07, sty_passed_07
    TEST_CASE 7
    SETUP $FFFF, $FFFE, $0000, $00FF, $FF, $80, 0, 0, 0
sty_probe_07:
    sty $FFFF
sty_after_07:
    CHECK_STY $FFFF, $FFFE, $0000, $00FF, $FF, $80, $B0
sty_passed_07:

; CASE 8: Absolute zero at page start $1200, guarding both page sides.
.export sty_probe_08, sty_after_08, sty_passed_08
    TEST_CASE 8
    SETUP $1200, $11FF, $1201, $1100, $00, $80, 1, 0, 1
sty_probe_08:
    sty $1200
sty_after_08:
    CHECK_STY $1200, $11FF, $1201, $1100, $00, $80, $B9
sty_passed_08:

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
