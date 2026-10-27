; NMOS 6502 LDX: five standard addressing modes, 15 numbered scenarios.
; Expected behavior: SY6500/MCS6500 Programming Manual, section 7.0.
; Each scenario changes X and checks N/Z before any comparison can clobber them.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, actual_x, saved_p, check_stage
.segment "CODE"

actual_x    = $2010
saved_p     = $2011
check_stage = $2012 ; 0=not checking/done, 1=flags, 2=X value

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

; STX absolute does not change flags. Capture P before PLA/AND/CMP or LDA
; can change live N/Z. Do not use TXA or CPX before the status snapshot.
; The original P byte and X value remain available for failure diagnosis.
.macro CHECK_LDX expected, flags
    stx actual_x
    php
    pla
    sta saved_p

    lda #1
    sta check_stage
    lda saved_p
    and #$82
    CHECK_A flags

    lda #2
    sta check_stage
    lda actual_x
    CHECK_A expected

    lda #0
    sta check_stage
.endmacro

start:
    ; Bootstrap the stack through LDA/TAX/TXS, not an LDX under test.
    lda #$FF
    tax
    txs
    cld
    lda #0
    sta final_result
    sta check_stage

; CASE 1: Immediate typical $55; clears Z
.export ldx_probe_01, ldx_after_01
    TEST_CASE 1
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$AA
    tax
    lda #$00
ldx_probe_01:
    ldx #$55
ldx_after_01:
    CHECK_LDX $55, $00

; CASE 2: Immediate $00; clears N and sets Z
.export ldx_probe_02, ldx_after_02
    TEST_CASE 2
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$FF
    tax
    lda #$80
ldx_probe_02:
    ldx #$00
ldx_after_02:
    CHECK_LDX $00, $02

; CASE 3: Immediate $7F; clears N
.export ldx_probe_03, ldx_after_03
    TEST_CASE 3
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$80
    tax
    lda #$80
ldx_probe_03:
    ldx #$7F
ldx_after_03:
    CHECK_LDX $7F, $00

; CASE 4: Immediate $80; sets N and clears Z
.export ldx_probe_04, ldx_after_04
    TEST_CASE 4
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$7F
    tax
    lda #$00
ldx_probe_04:
    ldx #$80
ldx_after_04:
    CHECK_LDX $80, $80

; CASE 5: Immediate $FF; sets N and clears Z
.export ldx_probe_05, ldx_after_05
    TEST_CASE 5
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$00
    tax
    lda #$00
ldx_probe_05:
    ldx #$FF
ldx_after_05:
    CHECK_LDX $FF, $80

; CASE 6: Zero Page $40 holds $A6
.export ldx_probe_06, ldx_after_06
    TEST_CASE 6
    lda #$A6
    sta $40
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$59
    tax
    lda #$00
ldx_probe_06:
    ldx $40
ldx_after_06:
    CHECK_LDX $A6, $80

; CASE 7: Zero Page zero clears N and sets Z
.export ldx_probe_07, ldx_after_07
    TEST_CASE 7
    lda #0
    sta $41
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$FF
    tax
    lda #$80
ldx_probe_07:
    ldx $41
ldx_after_07:
    CHECK_LDX $00, $02

; CASE 8: Zero Page,Y selects $42 with Y=2
.export ldx_probe_08, ldx_after_08
    TEST_CASE 8
    lda #$11
    sta $40
    lda #$3C
    sta $42
    ldy #2
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$C3
    tax
    lda #$80
ldx_probe_08:
    ldx $40,y
ldx_after_08:
    CHECK_LDX $3C, $00

; CASE 9: Zero Page,Y wraps $FF+2 to $01
.export ldx_probe_09, ldx_after_09
    TEST_CASE 9
    lda #$80
    sta $01
    lda #$11
    sta $0101
    ldy #2
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$7F
    tax
    lda #$00
ldx_probe_09:
    ldx $FF,y
ldx_after_09:
    CHECK_LDX $80, $80

; CASE 10: Absolute typical $55 at $1000
.export ldx_probe_10, ldx_after_10
    TEST_CASE 10
    lda #$55
    sta $1000
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$AA
    tax
    lda #$00
ldx_probe_10:
    ldx $1000
ldx_after_10:
    CHECK_LDX $55, $00

; CASE 11: Absolute zero clears N and sets Z
.export ldx_probe_11, ldx_after_11
    TEST_CASE 11
    lda #0
    sta $1001
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$FF
    tax
    lda #$80
ldx_probe_11:
    ldx $1001
ldx_after_11:
    CHECK_LDX $00, $02

; CASE 12: Absolute $FF sets N and clears Z
.export ldx_probe_12, ldx_after_12
    TEST_CASE 12
    lda #$FF
    sta $1002
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$00
    tax
    lda #$00
ldx_probe_12:
    ldx $1002
ldx_after_12:
    CHECK_LDX $FF, $80

; CASE 13: Absolute,Y selects $1102 with Y=2
.export ldx_probe_13, ldx_after_13
    TEST_CASE 13
    lda #$11
    sta $1100
    lda #$7F
    sta $1102
    ldy #2
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$80
    tax
    lda #$80
ldx_probe_13:
    ldx $1100,y
ldx_after_13:
    CHECK_LDX $7F, $00

; CASE 14: Absolute,Y crosses $12FF+1 to $1300
.export ldx_probe_14, ldx_after_14
    TEST_CASE 14
    lda #$11
    sta $1200
    lda #$80
    sta $1300
    ldy #1
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$7F
    tax
    lda #$00
ldx_probe_14:
    ldx $12FF,y
ldx_after_14:
    CHECK_LDX $80, $80

; CASE 15: Absolute,Y crosses $12FF+2 to zero at $1301
.export ldx_probe_15, ldx_after_15
    TEST_CASE 15
    lda #$11
    sta $1201
    lda #0
    sta $1301
    ldy #2
    ; Start X at a different value; seed N/Z opposite to the expected result.
    lda #$FF
    tax
    lda #$80
ldx_probe_15:
    ldx $12FF,y
ldx_after_15:
    CHECK_LDX $00, $02

success:
    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
