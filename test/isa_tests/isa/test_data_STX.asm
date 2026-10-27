; NMOS 6502 STX: zp, zp,Y and absolute; store X without changing flags.
; ATmega STS/STD: read-back, source preservation and address discrimination.
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

.macro SETUP target, left, right, wrong, value, index, carry, overflow, decimal
    ldx #$FF
    txs
    ; STA, never STX, initializes destination and guard bytes.
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
    ldx #value
    lda #$55
    ; LDY supplies N/Z unrelated to the stored byte; also supplies zp,Y index.
    ldy #index
.endmacro

.macro CHECK_STX target, left, right, wrong, value, index, flags
    sta saved_a
    php ; capture flags BEFORE TXA/TYA/TSX change N/Z
    txa ; do not verify STX by storing X with another STX
    sta saved_x
    tya
    sta saved_y
    tsx
    txa
    sta saved_sp
    lda $01FF ; direct PHP snapshot; no PLA dependency
    sta saved_p
    lda #1
    sta check_stage
    lda saved_p
    CHECK_A flags
    lda #2
    sta check_stage
    lda saved_x
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
    lda saved_y
    CHECK_A index
    lda saved_sp
    CHECK_A $FE ; only the checker PHP changed initial SP=$FF
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Zero Page typical $55; N stays set although X is positive.
.export stx_probe_01, stx_after_01, stx_passed_01
    TEST_CASE 1
    SETUP $0040, $003F, $0041, $0042, $55, $80, 0, 0, 0
stx_probe_01:
    stx $40
stx_after_01:
    CHECK_STX $0040, $003F, $0041, $0042, $55, $80, $B0
stx_passed_01:

; CASE 2: Zero Page zero; STX must not set Z from the stored zero.
.export stx_probe_02, stx_after_02, stx_passed_02
    TEST_CASE 2
    SETUP $0041, $0040, $0042, $0043, $00, $80, 1, 0, 0
stx_probe_02:
    stx $41
stx_after_02:
    CHECK_STX $0041, $0040, $0042, $0043, $00, $80, $B1
stx_passed_02:

; CASE 3: Zero Page $FF; N stays clear and Z/V/D stay set.
.export stx_probe_03, stx_after_03, stx_passed_03
    TEST_CASE 3
    SETUP $0042, $0041, $0043, $0044, $FF, $00, 0, 1, 1
stx_probe_03:
    stx $42
stx_after_03:
    CHECK_STX $0042, $0041, $0043, $0044, $FF, $00, $7A
stx_passed_03:

; CASE 4: Zero Page,Y $40+2 selects $42, leaving unindexed $40 intact.
.export stx_probe_04, stx_after_04, stx_passed_04
    TEST_CASE 4
    SETUP $0042, $0041, $0043, $0040, $7F, $02, 1, 0, 0
stx_probe_04:
    stx $40,y
stx_after_04:
    CHECK_STX $0042, $0041, $0043, $0040, $7F, $02, $31
stx_passed_04:

; CASE 5: Zero Page,Y $FF+2 wraps to $01, not $0101.
.export stx_probe_05, stx_after_05, stx_passed_05
    TEST_CASE 5
    SETUP $0001, $0000, $0002, $0101, $80, $02, 0, 1, 0
stx_probe_05:
    stx $FF,y
stx_after_05:
    CHECK_STX $0001, $0000, $0002, $0101, $80, $02, $70
stx_passed_05:

; CASE 6: Absolute $1000; $A6 data with Z/C/V/D set, N clear.
.export stx_probe_06, stx_after_06, stx_passed_06
    TEST_CASE 6
    SETUP $1000, $0FFF, $1001, $1002, $A6, $00, 1, 1, 1
stx_probe_06:
    stx $1000
stx_after_06:
    CHECK_STX $1000, $0FFF, $1001, $1002, $A6, $00, $7B
stx_passed_06:

; CASE 7: Last byte $FFFF, guards $FFFE/$0000 and wrong-page $00FF.
.export stx_probe_07, stx_after_07, stx_passed_07
    TEST_CASE 7
    SETUP $FFFF, $FFFE, $0000, $00FF, $FF, $80, 0, 0, 0
stx_probe_07:
    stx $FFFF
stx_after_07:
    CHECK_STX $FFFF, $FFFE, $0000, $00FF, $FF, $80, $B0
stx_passed_07:

; CASE 8: Absolute zero at page start $1200, guarding both page sides.
.export stx_probe_08, stx_after_08, stx_passed_08
    TEST_CASE 8
    SETUP $1200, $11FF, $1201, $1100, $00, $80, 1, 0, 1
stx_probe_08:
    stx $1200
stx_after_08:
    CHECK_STX $1200, $11FF, $1201, $1100, $00, $80, $B9
stx_passed_08:

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
