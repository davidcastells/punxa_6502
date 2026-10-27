; Original NMOS 6502 STA: seven addressing modes, ten core scenarios.
; Reference: SY6500/MCS6500 Programming Manual, section 2.1.2.
; PHP precedes all checking. N/Z are deliberately unrelated to stored A.
; I and V are checked at their reset value (0); C/D/N/Z vary across cases.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_p
.segment "CODE"

saved_a = $2010
saved_p = $2011

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

.macro CHECK_STA target, value, flags, guard
    php
    sta saved_a
    pla
    sta saved_p
    and #$CF ; N V D I Z C; exclude PHP's B/unused representation
    CHECK_A flags
    lda saved_a
    CHECK_A value
    lda target
    CHECK_A value
    lda guard
    CHECK_A $11
    lda target-1
    CHECK_A $22
    lda target+1
    CHECK_A $22
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Zero Page: store $55 at $40
.export probe_1, passed_1
    TEST_CASE 1
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$AA
    stx $0040
    ldx #$22
    stx $003F
    stx $0041
    ldx #$11
    stx $0042
    clc
    cld
    lda #$55
    ldy #$80
probe_1:
    sta $40
    CHECK_STA $0040, $55, $80, $0042
passed_1:

; CASE 2: Absolute: store zero at $1000
.export probe_2, passed_2
    TEST_CASE 2
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$FF
    stx $1000
    ldx #$22
    stx $0FFF
    stx $1001
    ldx #$11
    stx $1002
    sec
    cld
    lda #$00
    ldy #$80
probe_2:
    sta $1000
    CHECK_STA $1000, $00, $81, $1002
passed_2:

; CASE 3: Absolute: store $FF with D set
.export probe_3, passed_3
    TEST_CASE 3
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$00
    stx $1001
    ldx #$22
    stx $1000
    stx $1002
    ldx #$11
    stx $1003
    clc
    sed
    lda #$FF
    ldy #1
probe_3:
    sta $1001
    CHECK_STA $1001, $FF, $08, $1003
passed_3:

; CASE 4: Zero Page,X: $40+2 selects $42
.export probe_4, passed_4
    TEST_CASE 4
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$80
    stx $0042
    ldx #$22
    stx $0041
    stx $0043
    ldx #$11
    stx $0040
    ldx #2
    sec
    cld
    lda #$7F
    ldy #0
probe_4:
    sta $40,x
    CHECK_STA $0042, $7F, $03, $0040
passed_4:

; CASE 5: Zero Page,X: $FF+2 wraps to $01
.export probe_5, passed_5
    TEST_CASE 5
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$7F
    stx $0001
    ldx #$22
    stx $0000
    stx $0002
    ldx #$11
    stx $0101
    ldx #2
    clc
    cld
    lda #$80
    ldy #0
probe_5:
    sta $FF,x
    CHECK_STA $0001, $80, $02, $0101
passed_5:

; CASE 6: Absolute,X: $12FF+1 crosses to $1300
.export probe_6, passed_6
    TEST_CASE 6
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$59
    stx $1300
    ldx #$22
    stx $12FF
    stx $1301
    ldx #$11
    stx $1200
    ldx #1
    sec
    cld
    lda #$A6
    ldy #0
probe_6:
    sta $12FF,x
    CHECK_STA $1300, $A6, $03, $1200
passed_6:

; CASE 7: Absolute,Y: $13FF+2 crosses to $1401
.export probe_7, passed_7
    TEST_CASE 7
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$C3
    stx $1401
    ldx #$22
    stx $1400
    stx $1402
    ldx #$11
    stx $1301
    ldy #2
    clc
    sed
    lda #$3C
    ldx #$80
probe_7:
    sta $13FF,y
    CHECK_STA $1401, $3C, $88, $1301
passed_7:

; CASE 8: Indexed indirect: ($60,X), X=4, pointer $64 -> $1500
.export probe_8, passed_8
    TEST_CASE 8
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$AA
    stx $1500
    ldx #$22
    stx $14FF
    stx $1501
    ldx #$11
    stx $1600
    ldx #0
    stx $64
    stx $60
    ldx #$15
    stx $65
    ldx #$16
    stx $61
    ldx #4
    sec
    cld
    lda #$55
    ldy #0
probe_8:
    sta ($60,x)
    CHECK_STA $1500, $55, $03, $1600
passed_8:

; CASE 9: Indirect indexed: ($70),Y, $1600+3 -> $1603
.export probe_9, passed_9
    TEST_CASE 9
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$7F
    stx $1603
    ldx #$22
    stx $1602
    stx $1604
    ldx #$11
    stx $1600
    ldx #0
    stx $70
    ldx #$16
    stx $71
    ldy #3
    clc
    cld
    lda #$80
    ldx #0
probe_9:
    sta ($70),y
    CHECK_STA $1603, $80, $02, $1600
passed_9:

; CASE 10: Indirect indexed: $16FF+1 crosses to $1700
.export probe_10, passed_10
    TEST_CASE 10
    ; STX initializes destination/guards independently of the STA under test.
    ldx #$FF
    stx $1700
    ldx #$22
    stx $16FF
    stx $1701
    ldx #$11
    stx $1600
    ldx #$FF
    stx $70
    ldx #$16
    stx $71
    ldy #1
    sec
    cld
    lda #$00
    ldx #$80
probe_10:
    sta ($70),y
    CHECK_STA $1700, $00, $81, $1600
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
