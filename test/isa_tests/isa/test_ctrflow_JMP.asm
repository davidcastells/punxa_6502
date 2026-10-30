; Original NMOS 6502 JMP: $4C absolute, $6C indirect; preserve registers/P/SP.
; Indirect destination = M[p] | M[(p & $FF00) | ((p+1) & $FF)] << 8.
; In particular ($xxFF) reads its high byte from $xx00, not $(xx+1)00.
; ATmega JMP/IJMP patterns: distinct entries, skipped paths, stack neutrality.
; Fixed expectations and linked target labels. No JMP assertion/reporting helper:
; comparisons use BEQ; previously verified JSR reports to fail/end, without RTS.
; PHP captures P before the target and at the first destination instruction.
; No PLA/PLP. I=0 follows simulator initialization, not physical reset testing.
.setcpu "6502"
.include "test_protocol.inc"
.export start, end, saved_a, saved_x, saved_y, saved_sp, pre_p, post_p
.export path_marker, check_stage, done_cases, guard_0, guard_1, bad_entry
.segment "CODE"

saved_a = $2010
saved_x = $2011
saved_y = $2012
saved_sp = $2014
check_stage = $2015
path_marker = $2016
guard_0 = $2020
guard_1 = $2021
done_cases = $2040 ; seven separate completion bytes, never an INC counter
pre_p = $01FF
post_p = $01FE

.macro CHECK_MEM location, expected
    .local ok
    lda location
    cmp #expected
    beq ok
    jsr fail ; no JMP is used to check JMP
ok:
.endmacro

.macro INIT_CASE
    lda #0
    sta path_marker
    sta check_stage
    lda #$AA
    sta pre_p
    sta post_p
    lda #$22
    sta $01FD
    sta $0101 ; $0100 is deliberately a pointer decoy in cases 6/7
    lda #$A5
    sta guard_0
    lda #$5A
    sta guard_1
    ldx #$FF
    txs
.endmacro

.macro SEED value_a, value_x, value_y, carry, overflow, decimal
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
    ldx #value_x
    ldy #value_y
    lda #value_a
    php ; fixed pre-target status, SP=$FE at JMP
.endmacro

.macro ARRIVE marker
    php ; FIRST destination instruction; capture before any flag-changing helper
    sta saved_a
    stx saved_x
    sty saved_y
    lda #marker
    sta path_marker
.endmacro

.macro TRAP marker, stage
    ARRIVE marker
    lda #stage
    sta check_stage
    jsr fail
.endmacro

.macro CHECK_STATE number, marker, status, value_a, value_x, value_y
    lda #1
    sta check_stage
    CHECK_MEM test_case, number ; a different legitimate entry cannot pass
    CHECK_MEM path_marker, marker
    lda #2
    sta check_stage
    CHECK_MEM pre_p, status
    CHECK_MEM post_p, status ; all six live flags, B/bit5 stack copy and I=0
    lda #3
    sta check_stage
    CHECK_MEM saved_a, value_a
    CHECK_MEM saved_x, value_x
    CHECK_MEM saved_y, value_y
    lda #4
    sta check_stage
    tsx
    stx saved_sp
    CHECK_MEM saved_sp, $FD ; only the two checker PHPs decrement SP
    lda #5
    sta check_stage
    CHECK_MEM $01FD, $22
    CHECK_MEM $0101, $22
    CHECK_MEM guard_0, $A5
    CHECK_MEM guard_1, $5A
.endmacro

.macro MARK_DONE number, marker
    lda #marker
    sta done_cases+number-1
    lda #0
    sta check_stage
.endmacro

start:
    lda #0
    sta final_result
    .repeat 7, index
        sta done_cases+index
    .endrepeat

; CASE 1: Absolute forward, skipping an executable fall-through trap.
.export case_01, probe_01, fallthrough_01, entry_01, captured_01, passed_01
case_01:
    TEST_CASE 1
    INIT_CASE
    SEED $55, $AA, $3C, 0, 0, 0
probe_01:
    jmp entry_01
fallthrough_01:
    TRAP $F1, 7
entry_01:
    ARRIVE $11
captured_01:
    CHECK_STATE 1, $11, $30, $55, $AA, $3C
    MARK_DONE 1, $11
passed_01:
    .assert entry_01 > probe_01+3, lderror, "case 1 must skip executable code"

; CASE 2: Absolute forward across a page; target address supplied by the linker.
.export case_02, probe_02, fallthrough_02, entry_02, captured_02, passed_02
case_02:
    TEST_CASE 2
    INIT_CASE
    SEED $00, $80, $7F, 1, 1, 1
probe_02:
    jmp entry_02
fallthrough_02:
    TRAP $F2, 7
    .align $100, $00
entry_02:
    ARRIVE $22
captured_02:
    CHECK_STATE 2, $22, $7B, $00, $80, $7F
    MARK_DONE 2, $22
passed_02:
    .assert (>probe_02) <> (>entry_02), lderror, "case 2 must cross a page"

; CASE 3: Absolute backward. Independently tested BNE enters the target probe.
.export case_03, probe_03, fallthrough_03, entry_03, captured_03, passed_03
case_03:
    TEST_CASE 3
    INIT_CASE
    SEED $80, $00, $FF, 1, 1, 0 ; Z=0 for setup branch
    bne probe_03
    TRAP $E3, 7 ; failed setup branch must not masquerade as a successful JMP
entry_03:
    ARRIVE $33
    bne captured_03 ; marker $33 establishes Z=0; P was already captured
probe_03:
    jmp entry_03
fallthrough_03:
    TRAP $F3, 7
captured_03:
    CHECK_STATE 3, $33, $F1, $80, $00, $FF
    MARK_DONE 3, $33
passed_03:
    .assert entry_03 < probe_03, lderror, "case 3 must jump backward"

; CASE 4: Normal 16-bit indirect destination via pointer at $0040/$0041.
.export case_04, probe_04, fallthrough_04, entry_04, captured_04, passed_04
case_04:
    TEST_CASE 4
    INIT_CASE
    lda #<entry_04
    sta $0040
    lda #>entry_04
    sta $0041
    lda #$11
    sta $003F
    lda #$22
    sta $0042
    SEED $7F, $55, $AA, 1, 1, 0
probe_04:
    jmp ($0040)
fallthrough_04:
    TRAP $F4, 7
entry_04:
    ARRIVE $44
captured_04:
    CHECK_STATE 4, $44, $71, $7F, $55, $AA
    lda #6
    sta check_stage
    CHECK_MEM $0040, <entry_04
    CHECK_MEM $0041, >entry_04
    CHECK_MEM $003F, $11
    CHECK_MEM $0042, $22
    MARK_DONE 4, $44
passed_04:

; CASE 5: Nonzero pointer high byte. $1240 is real; $0040 is a decoy.
.export case_05, probe_05, fallthrough_05, entry_05, captured_05, passed_05
case_05:
    TEST_CASE 5
    INIT_CASE
    lda #<entry_05
    sta $1240
    lda #>entry_05
    sta $1241
    lda #<bad_entry
    sta $0040
    lda #>bad_entry
    sta $0041
    lda #$11
    sta $123F
    lda #$22
    sta $1242
    SEED $FF, $A5, $5A, 0, 0, 1
probe_05:
    jmp ($1240)
fallthrough_05:
    TRAP $F5, 7
entry_05:
    ARRIVE $55
captured_05:
    CHECK_STATE 5, $55, $B8, $FF, $A5, $5A
    lda #6
    sta check_stage
    CHECK_MEM $1240, <entry_05
    CHECK_MEM $1241, >entry_05
    CHECK_MEM $0040, <bad_entry
    CHECK_MEM $0041, >bad_entry
    CHECK_MEM $123F, $11
    CHECK_MEM $1242, $22
    MARK_DONE 5, $55
passed_05:

; CASE 6: NMOS ($00FF) reads high byte at $0000. $0100 is an executable decoy.
; This isolates page wrapping without a nonzero pointer high byte.
.export case_06, probe_06, fallthrough_06, entry_06, captured_06, passed_06
case_06:
    TEST_CASE 6
    INIT_CASE
    lda #<entry_06
    sta $00FF
    lda #>entry_06
    sta $0000
    lda #>bad_entry
    sta $0100
    lda #$11
    sta $00FE
    lda #$22
    sta $0001
    SEED $80, $02, $81, 1, 1, 1
probe_06:
    ; ca65 rejects page-ending indirect syntax; emit the documented 6C FF 00.
    .byte $6C
    .word $00FF
fallthrough_06:
    TRAP $F6, 7
    .align $100, $00
entry_06:
    ARRIVE $66
captured_06:
    CHECK_STATE 6, $66, $F9, $80, $02, $81
    lda #6
    sta check_stage
    CHECK_MEM $00FF, <entry_06
    CHECK_MEM $0000, >entry_06
    CHECK_MEM $0100, >bad_entry
    CHECK_MEM $00FE, $11
    CHECK_MEM $0001, $22
    MARK_DONE 6, $66
passed_06:

; CASE 7: NMOS ($12FF) uses $12FF/$1200, not $1300 or truncated zero page.
; Distinct executable alternatives: linear -> entry_02, truncated/wrapped ->
; entry_06, truncated/linear -> bad_entry. All share the same low address byte.
.export case_07, probe_07, fallthrough_07, entry_07, captured_07, passed_07
case_07:
    TEST_CASE 7
    INIT_CASE
    lda #<entry_07
    sta $12FF
    sta $00FF
    lda #>entry_07
    sta $1200
    lda #>entry_02
    sta $1300
    lda #>entry_06
    sta $0000
    lda #>bad_entry
    sta $0100
    lda #$11
    sta $12FE
    lda #$22
    sta $1201
    SEED $00, $7F, $80, 0, 0, 0
probe_07:
    ; Keep the NMOS boundary expectation: explicit 6C FF 12, no assembler bypass.
    .byte $6C
    .word $12FF
fallthrough_07:
    TRAP $F7, 7
    .align $100, $00
entry_07:
    ARRIVE $77
captured_07:
    CHECK_STATE 7, $77, $32, $00, $7F, $80
    lda #6
    sta check_stage
    CHECK_MEM $12FF, <entry_07
    CHECK_MEM $1200, >entry_07
    CHECK_MEM $1300, >entry_02
    CHECK_MEM $00FF, <entry_07
    CHECK_MEM $0000, >entry_06
    CHECK_MEM $0100, >bad_entry
    CHECK_MEM $12FE, $11
    CHECK_MEM $1201, $22
    MARK_DONE 7, $77
passed_07:

success:
    lda #9
    sta check_stage
    CHECK_MEM done_cases, $11
    CHECK_MEM done_cases+1, $22
    CHECK_MEM done_cases+2, $33
    CHECK_MEM done_cases+3, $44
    CHECK_MEM done_cases+4, $55
    CHECK_MEM done_cases+5, $66
    CHECK_MEM done_cases+6, $77
    lda #1
    sta final_result
    jsr end ; reporting helper is JSR, never target JMP
fail:
    lda #255
    sta final_result
    jsr end
end:
    beq end
    bne end

    .align $100, $00
bad_entry:
    TRAP $E1, 8
    .assert (<entry_02) = (<entry_06), lderror, "decoy low bytes must match"
    .assert (<entry_06) = (<entry_07), lderror, "decoy low bytes must match"
    .assert (<entry_07) = (<bad_entry), lderror, "decoy low bytes must match"
    .assert (>entry_02) <> (>entry_06), lderror, "decoy pages must differ"
    .assert (>entry_06) <> (>entry_07), lderror, "decoy pages must differ"
    .assert (>entry_07) <> (>bad_entry), lderror, "decoy pages must differ"
