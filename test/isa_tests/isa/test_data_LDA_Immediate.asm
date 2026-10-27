; Shared NMOS 6502 formal subset: LDA immediate accumulator and Z behavior.
; Fixed expectations: LDA loads its operand and Z is 1 exactly for zero.
; N, preserved flags and other modes remain covered by the original LDA file,
; not by this subset. No reset-I/D assumption, stack, CLD or PHP dependency.
; Helpers: CMP immediate (A unchanged; equality sets Z), BEQ/BNE relative,
; JMP absolute, STA absolute for protocol. Checks use equal AND unequal inputs.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end
.segment "CODE"

.macro CHECK_Z zero
    .local correct
    .if zero
        beq correct
    .else
        bne correct
    .endif
    jmp fail
correct:
.endmacro

.macro CHECK_A expected
    .local equal, unequal
    cmp #expected
    beq equal
    jmp fail
equal:
    ; Check that the comparator/branch helper can distinguish inequality too.
    cmp #(expected ^ $FF)
    bne unequal
    jmp fail
unequal:
.endmacro

start:
    lda #0
    sta final_result

    ; Guard the oracle's not-taken paths as well as the taken paths below.
    lda #$55
    cmp #$55
    bne helper_bad
    cmp #$AA
    beq helper_bad
    jmp helpers_ok
helper_bad:
    jmp fail
helpers_ok:

; Each target replaces a different A and the opposite initial Z.
    TEST_CASE 1
    lda #$80
.export probe_1, after_1, passed_1
probe_1:
    lda #$00
after_1:
    CHECK_Z 1
    CHECK_A $00
passed_1:

    TEST_CASE 2
    lda #$00
.export probe_2, after_2, passed_2
probe_2:
    lda #$3C
after_2:
    CHECK_Z 0
    CHECK_A $3C
passed_2:

    TEST_CASE 3
    lda #$00
.export probe_3, after_3, passed_3
probe_3:
    lda #$80
after_3:
    CHECK_Z 0
    CHECK_A $80
passed_3:

    TEST_CASE 4
    lda #$00
.export probe_4, after_4, passed_4
probe_4:
    lda #$FF
after_4:
    CHECK_Z 0
    CHECK_A $FF
passed_4:

    TEST_CASE 5
    lda #$00
.export probe_5, after_5, passed_5
probe_5:
    lda #$A5
after_5:
    CHECK_Z 0
    CHECK_A $A5
passed_5:

    lda #1
    sta final_result
end:
    jmp end

fail:
    lda #255
    sta final_result
    jmp end
