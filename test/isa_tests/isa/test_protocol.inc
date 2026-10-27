; Shared ISA protocol, corresponding to ATmega's exported result symbols.
; These are CPU byte addresses; both fields are exactly one byte.
; Address ownership stays here, not in the Python runner. No BSS is allocated.
.ifndef TEST_PROTOCOL_INCLUDED
TEST_PROTOCOL_INCLUDED = 1

test_case    = $2003
final_result = $2004
.export test_case, final_result

; Record the scenario BEFORE setup or the instruction under test.
.macro TEST_CASE number
    .assert number >= 1 .and number <= 255, error, "case must fit in one byte"
    lda #number
    sta test_case
.endmacro

.endif
