; NMOS 6502 PLP ($28, implied): SP = SP+1, then P = mem[$0100+SP].
; N V D I Z C come from bits 7 6 3 2 1 0 of the pulled byte. Bit 5 and B (bit 4)
; are not stored flags: PLP ignores them, and PHP always pushes them as 1.
; So the PHP byte after PLP must be (pulled | $30), whatever bits 4/5 were.
; The pulled byte is placed with STA and SP set with TXS (no PHA/PLA dependency).
; Every case seeds the OPPOSITE of the pulled C/V/D/I (and N/Z where one LDA can)
; so a flag PLP fails to restore is detected. Cases 5-10 pull one flag at a time
; to catch bit-mapping errors. Case 13 wraps SP $FF -> $00 (pulls $0100).
; Case 14 checks memory and SP without a following PHP, which would overwrite
; the pulled slot. A, X, Y, SP and guard bytes are checked in every case.
; No interrupts are modelled, so pulling I=1 has no side effect here.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_sp, check_stage
.export guard_0, guard_1
.segment "CODE"
saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_sp = $2014
check_stage = $2015
guard_0 = $2020
guard_1 = $2021

.macro CHECK_A expected
    .local ok
    cmp #expected
    beq ok
    jmp fail
ok:
.endmacro

.macro CHECK_MEM location, expected
    lda location
    CHECK_A expected
.endmacro

.macro INIT_GUARDS
    lda #$C6
    sta $01FE ; slot below the pulled byte
    sta $01FD
    lda #$22
    sta $0100
    lda #$A5
    sta guard_0
    lda #$5A
    sta guard_1
.endmacro

; ADC establishes V in binary mode before the optional SED; LDY/LDX/LDA follow.
.macro SEED carry, overflow, decimal, interrupt
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
    .if interrupt
        sei
    .else
        cli
    .endif
.endmacro

; Pulled byte at $01FF with SP=$FE, so PLP reads $01FF and leaves SP=$FF.
.macro SETUP_PLP pulled, carry, overflow, decimal, interrupt, value_a
    INIT_GUARDS
    lda #pulled
    sta $01FF
    ldx #$FE
    txs
    SEED carry, overflow, decimal, interrupt
    ldx #$A5
    ldy #$5A
    lda #value_a ; last load seeds N/Z
.endmacro

; Must directly follow PLP: PHP writes the restored P to $01FF (SP $FF -> $FE).
.macro CAPTURE_STATE
    php
    sta saved_a
    stx saved_x
    sty saved_y
.endmacro

.macro CHECK_PLP expected_p, value_a
    lda #1
    sta check_stage
    CHECK_MEM $01FF, expected_p ; full restored status byte, bits 4/5 = 1
    lda #2
    sta check_stage
    CHECK_MEM saved_a, value_a
    CHECK_MEM saved_x, $A5
    CHECK_MEM saved_y, $5A
    tsx
    stx saved_sp
    CHECK_MEM saved_sp, $FE ; PLP: $FE -> $FF, then the checker PHP: -> $FE
    lda #3
    sta check_stage
    CHECK_MEM $01FE, $C6
    CHECK_MEM $01FD, $C6
    CHECK_MEM $0100, $22
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
    cli
    cld
    lda #0
    sta check_stage
.endmacro

.macro PLP_CASE pulled, carry, overflow, decimal, interrupt, value_a, expected_p
    SETUP_PLP pulled, carry, overflow, decimal, interrupt, value_a
    plp
    CAPTURE_STATE
    CHECK_PLP expected_p, value_a
.endmacro

start:
    lda #0
    sta final_result
    sta check_stage

; CASE 1: pull $00 over all-set C/V/D/I and N=1 -> every flag cleared, P=$30.
.export plp_passed_01
    TEST_CASE 1
    PLP_CASE $00, 1, 1, 1, 1, $80, $30
plp_passed_01:

; CASE 2: pull $FF over all-clear flags -> every flag set, N and Z together.
.export plp_passed_02
    TEST_CASE 2
    PLP_CASE $FF, 0, 0, 0, 0, $01, $FF
plp_passed_02:

; CASE 3: pull $CF (B=0, bit5=0, all flags 1) -> PHP still pushes $FF.
.export plp_passed_03
    TEST_CASE 3
    PLP_CASE $CF, 0, 0, 0, 0, $01, $FF
plp_passed_03:

; CASE 4: pull $30 (only B and bit 5) over all-set flags -> no flag set, P=$30.
.export plp_passed_04
    TEST_CASE 4
    PLP_CASE $30, 1, 1, 1, 1, $80, $30
plp_passed_04:

; CASES 5-10: one flag pulled at a time; all others seeded to 1 and must clear.
.export plp_passed_05, plp_passed_06, plp_passed_07, plp_passed_08
.export plp_passed_09, plp_passed_10
    TEST_CASE 5 ; C only
    PLP_CASE $01, 0, 1, 1, 1, $80, $31
plp_passed_05:
    TEST_CASE 6 ; Z only
    PLP_CASE $02, 1, 1, 1, 1, $80, $32
plp_passed_06:
    TEST_CASE 7 ; I only
    PLP_CASE $04, 1, 1, 1, 0, $80, $34
plp_passed_07:
    TEST_CASE 8 ; D only
    PLP_CASE $08, 1, 1, 0, 1, $80, $38
plp_passed_08:
    TEST_CASE 9 ; V only
    PLP_CASE $40, 1, 0, 1, 1, $80, $70
plp_passed_09:
    TEST_CASE 10 ; N only (seeded N=0, Z=1)
    PLP_CASE $80, 1, 1, 1, 1, $00, $B0
plp_passed_10:

; CASE 11: alternating $A5 (N,bit5,I,C; B=0) over the complementary state.
.export plp_passed_11
    TEST_CASE 11
    PLP_CASE $A5, 0, 1, 1, 0, $00, $B5
plp_passed_11:

; CASE 12: alternating $5A (V,B,D,Z; bit5=0) over the complementary state.
.export plp_passed_12
    TEST_CASE 12
    PLP_CASE $5A, 1, 0, 0, 1, $80, $7A
plp_passed_12:

; CASE 13: SP wraps $FF -> $00, so PLP pulls $0100 ($C3), not $0200 or $01FF.
; The checker PHP then writes $0100 and SP returns to $FF.
.export plp_probe_13, plp_passed_13
    TEST_CASE 13
    INIT_GUARDS
    lda #$C3
    sta $0100
    lda #$5D
    sta $01FF ; decoy: the slot that is NOT pulled
    ldx #$FF
    txs
    SEED 0, 0, 1, 1
    ldx #$A5
    ldy #$5A
    lda #$01
plp_probe_13:
    plp
    CAPTURE_STATE
    lda #1
    sta check_stage
    CHECK_MEM $0100, $F3 ; $C3 | $30
    lda #2
    sta check_stage
    CHECK_MEM saved_a, $01
    CHECK_MEM saved_x, $A5
    CHECK_MEM saved_y, $5A
    tsx
    stx saved_sp
    CHECK_MEM saved_sp, $FF
    lda #3
    sta check_stage
    CHECK_MEM $01FF, $5D
    CHECK_MEM $01FE, $C6
    cli
    cld
    lda #0
    sta check_stage
plp_passed_13:

; CASE 14: no PHP after PLP. PLP must not write the stack: the pulled byte,
; the slot below and the other guards are unchanged; SP is exactly $FF.
; STA/STX/STY right after PLP keep A/X/Y without touching the stack.
.export plp_probe_14, plp_passed_14
    TEST_CASE 14
    SETUP_PLP $96, 0, 1, 0, 1, $3C
plp_probe_14:
    plp
    sta saved_a
    stx saved_x
    sty saved_y
    tsx
    stx saved_sp
    lda #1
    sta check_stage
    CHECK_MEM saved_sp, $FF
    CHECK_MEM $01FF, $96 ; pulled byte not written back
    CHECK_MEM $01FE, $C6
    CHECK_MEM $01FD, $C6
    CHECK_MEM $0100, $22
    lda #2
    sta check_stage
    CHECK_MEM saved_a, $3C
    CHECK_MEM saved_x, $A5
    CHECK_MEM saved_y, $5A
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
    cli
    cld
    lda #0
    sta check_stage
plp_passed_14:

; CASE 15: SP wraps $FF -> $00, checked DIRECTLY right after PLP (case 13 only
; sees SP after the checker PHP). No PHP: STA/STX/STY keep A/X/Y without touching
; the stack, then TSX reads the post-PLP SP. PLP pulls $0100 ($69); the pulled
; byte must not be written back and the decoy at $01FF must be untouched.
.export plp_probe_15, plp_passed_15
    TEST_CASE 15
    INIT_GUARDS
    lda #$69
    sta $0100 ; the byte PLP must pull after the wrap
    lda #$5D
    sta $01FF ; decoy: the slot that is NOT pulled
    ldx #$FF
    txs
    SEED 1, 0, 0, 0
    ldx #$A5
    ldy #$5A
    lda #$E7
plp_probe_15:
    plp
    sta saved_a
    stx saved_x
    sty saved_y
    tsx
    stx saved_sp
    lda #1
    sta check_stage
    CHECK_MEM saved_sp, $00 ; actual SP immediately after PLP
    CHECK_MEM $0100, $69 ; pulled byte not written back
    CHECK_MEM $01FF, $5D ; decoy untouched
    CHECK_MEM $01FE, $C6
    CHECK_MEM $01FD, $C6
    lda #2
    sta check_stage
    CHECK_MEM saved_a, $E7
    CHECK_MEM saved_x, $A5
    CHECK_MEM saved_y, $5A
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
    cli
    cld
    lda #0
    sta check_stage
plp_passed_15:

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
    .assert * <= $0FFF, lderror, "program must not overlap memory data guards"
