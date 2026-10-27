; NMOS 6502 LDA functional ISA test.
; Cases 1-8 retain the values/addressing checks of the original test.
; All eight addressing modes, N/Z transitions, flag preservation and boundaries.
; Reference: SY6500/MCS6500 Programming Manual, sections 2.1.1 and 6.1-6.5.
; No cycle-accurate bus timing is asserted.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end
.segment "CODE"

actual = $2010 ; test-local scratch, separate from protocol and source data

; Preserve a local short branch; an absolute jump reaches fail in large tests.
.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

; Snapshot flags BEFORE CMP or LDA changes them.
; STA/PHP preserve status. PLA's own flag effects happen after PHP's snapshot.
; Requires functioning STA, PHP, PLA, AND, CMP, BEQ and JMP helpers.
.macro CHECK_LDA expected, flags, mask
    sta actual
    php
    pla
    and #mask
    CHECK_A flags
    lda actual
    CHECK_A expected
.endmacro

start:
    ldx #$FF
    txs
    cld
    lda #0
    sta final_result

; CASE 1: Immediate normal value (original case 1)
    TEST_CASE 1
    lda #0
    lda #$55
    CHECK_LDA $55, $0, $82

; CASE 2: Immediate zero clears N and sets Z (original case 2)
    TEST_CASE 2
    lda #$80
    lda #$00
    CHECK_LDA $00, $2, $82

; CASE 3: Immediate maximum sets N and clears Z (original case 3)
    TEST_CASE 3
    lda #0
    lda #$FF
    CHECK_LDA $ff, $80, $82

; CASE 4: Zero page (original case 4)
    TEST_CASE 4
    lda #$A6
    sta $40
    lda #0
    lda $40
    CHECK_LDA $a6, $80, $82

; CASE 5: Absolute (original case 5)
    TEST_CASE 5
    lda #$3C
    sta $1000
    lda #$80
    lda $1000
    CHECK_LDA $3c, $0, $82

; CASE 6: Zero page,X (original case 6)
    TEST_CASE 6
    lda #$72
    sta $41
    ldx #1
    lda #0
    lda $40,x
    CHECK_LDA $72, $0, $82

; CASE 7: Absolute,X (original case 7)
    TEST_CASE 7
    lda #$83
    sta $1001
    ldx #1
    lda #0
    lda $1000,x
    CHECK_LDA $83, $80, $82

; CASE 8: Absolute,Y (original case 8)
    TEST_CASE 8
    lda #$94
    sta $1102
    ldy #2
    lda #0
    lda $1100,y
    CHECK_LDA $94, $80, $82

; CASE 9: Indexed indirect (zero page,X)
    TEST_CASE 9
    lda #$00
    sta $44
    lda #$12
    sta $45
    lda #$56
    sta $1200
    ldx #4
    lda #0
    lda ($40,x)
    CHECK_LDA $56, $0, $82

; CASE 10: Indirect indexed (zero page),Y; zero result
    TEST_CASE 10
    lda #$00
    sta $40
    sta $1202
    lda #$12
    sta $41
    ldy #2
    lda #$80
    lda ($40),y
    CHECK_LDA $00, $2, $82

; CASE 11: Immediate positive sign boundary
    TEST_CASE 11
    lda #$80
    lda #$7F
    CHECK_LDA $7f, $0, $82

; CASE 12: Immediate negative sign boundary
    TEST_CASE 12
    lda #0
    lda #$80
    CHECK_LDA $80, $80, $82

; CASE 13: Zero page zero clears N and sets Z
    TEST_CASE 13
    lda #0
    sta $40
    lda #$80
    lda $40
    CHECK_LDA $00, $2, $82

; CASE 14: Absolute negative clears Z
    TEST_CASE 14
    lda #$FF
    sta $1000
    lda #0
    lda $1000
    CHECK_LDA $ff, $80, $82

; CASE 15: Zero page,X wraps $FF + 2 to $01
    TEST_CASE 15
    lda #$34
    sta $01
    lda #$90
    sta $0101
    ldx #2
    lda #0
    lda $FF,x
    CHECK_LDA $34, $0, $82

; CASE 16: Absolute,X crosses a page boundary
    TEST_CASE 16
    lda #$65
    sta $1300
    ldx #1
    lda #0
    lda $12FF,x
    CHECK_LDA $65, $0, $82

; CASE 17: Absolute,Y crosses a page boundary
    TEST_CASE 17
    lda #$76
    sta $1301
    ldy #2
    lda #0
    lda $12FF,y
    CHECK_LDA $76, $0, $82

; CASE 18: Indirect indexed,Y crosses a page boundary
    TEST_CASE 18
    lda #$FF
    sta $40
    lda #$12
    sta $41
    lda #$87
    sta $1301
    ldy #2
    lda #0
    lda ($40),y
    CHECK_LDA $87, $80, $82

; CASE 19: Indirect indexed,Y with index zero
    TEST_CASE 19
    lda #$00
    sta $40
    lda #$14
    sta $41
    lda #$98
    sta $1400
    ldy #0
    lda #0
    lda ($40),y
    CHECK_LDA $98, $80, $82

; CASE 20: Indexed indirect,X with index zero
    TEST_CASE 20
    lda #$00
    sta $40
    lda #$14
    sta $41
    lda #$A9
    sta $1400
    ldx #0
    lda #0
    lda ($40,x)
    CHECK_LDA $a9, $80, $82

; CASE 21: LDA preserves clear carry
    TEST_CASE 21
    clc
    lda #$80
    lda #$55
    CHECK_LDA $55, $0, $83

; CASE 22: LDA preserves set carry
    TEST_CASE 22
    sec
    lda #$80
    lda #0
    CHECK_LDA $00, $3, $83

; CASE 23: LDA preserves set overflow
    TEST_CASE 23
    clc
    lda #$7F
    adc #1
    lda #0
    lda #$55
    CHECK_LDA $55, $40, $c3

; CASE 24: LDA preserves clear overflow
    TEST_CASE 24
    clc
    lda #0
    adc #0
    lda #$80
    CHECK_LDA $80, $80, $c3

; CASE 25: LDA preserves decimal flag
    TEST_CASE 25
    sed
    lda #0
    lda #$55
    CHECK_LDA $55, $8, $8a
    cld

; CASE 26: Absolute load from top of 64 KiB memory
    TEST_CASE 26
    lda #$5A
    sta $FFFF
    lda #0
    lda $FFFF
    CHECK_LDA $5a, $0, $82

; CASE 27: Absolute,X wraps 16-bit effective address
    TEST_CASE 27
    lda #$AB
    sta $01
    ldx #2
    lda #0
    lda $FFFF,x
    CHECK_LDA $ab, $80, $82

; CASE 28: Absolute,Y wraps 16-bit effective address
    TEST_CASE 28
    lda #$BC
    sta $01
    ldy #2
    lda #0
    lda $FFFF,y
    CHECK_LDA $bc, $80, $82

; CASE 29: Indirect indexed,Y wraps 16-bit effective address
    TEST_CASE 29
    lda #$FE
    sta $40
    lda #$FF
    sta $41
    lda #$CD
    sta $01
    ldy #3
    lda #0
    lda ($40),y
    CHECK_LDA $cd, $80, $82

; CASE 30: Indexed indirect,X pointer index wraps within zero page
    TEST_CASE 30
    lda #$00
    sta $00
    sta $0100
    lda #$14
    sta $01
    lda #$15
    sta $0101
    lda #$9A
    sta $1400
    lda #$11
    sta $1500
    ldx #1
    lda #0
    lda ($FF,x)
    CHECK_LDA $9a, $80, $82

; CASE 31: Indexed indirect,X pointer high byte wraps $FF to $00
    TEST_CASE 31
    lda #$00
    sta $FF
    lda #$14
    sta $00
    lda #$15
    sta $0100
    lda #$AB
    sta $1400
    lda #$11
    sta $1500
    ldx #0
    lda #0
    lda ($FF,x)
    CHECK_LDA $ab, $80, $82

; CASE 32: Indirect indexed,Y pointer high byte wraps $FF to $00
    TEST_CASE 32
    lda #$00
    sta $FF
    lda #$14
    sta $00
    lda #$15
    sta $0100
    lda #$BC
    sta $1401
    lda #$11
    sta $1501
    ldy #1
    lda #0
    lda ($FF),y
    CHECK_LDA $bc, $80, $82

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
