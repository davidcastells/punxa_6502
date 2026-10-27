# LDA Cases 30-32: NMOS review and minimum reproductions

## Architectural rule

Reference: the original
[SY6500/MCS6500 Programming Manual](https://syncopate.us/books/Synertek6502ProgrammingManual.html),
sections 6.4/6.5, examples 6.10/6.11 and appendix E.8/E.9.
Both pointer bytes are fetched in page zero. Indexing and incrementing that
pointer do not carry into the stack page.

With byte memory M and an 8-bit operand zp:

- (zp,X): p=(zp+X)&$FF; EA=M[p] | (M[(p+1)&$FF]<<8).
- (zp),Y: p=zp; EA=((M[p] | (M[(p+1)&$FF]<<8))+Y)&$FFFF.

All three expected data bytes have bit 7 set and are nonzero: N=1, Z=0.
These are functional rules, not assertions about dummy reads or chip timing.

## Production assembly audit

The [original assembly](isa/test_data_LDA.asm) is unchanged.

- Case 30 (line 302): operand $FF and X=1 select pointer $0000/$0001.
- Case 31 (line 320): operand $FF and X=0 select $00FF/$0000.
- Case 32 (line 337): operand $FF selects $00FF/$0000 before Y=1 is added.

Every scenario sets its pointer, index, expected target byte, and a different
byte at the incorrect target. It is independent of prior scenarios.
TEST_CASE runs before scenario setup, so its A/N/Z effects do not interfere.

Code ($0200-$0FFF), source data ($1400/$1401 and $1500/$1501), protocol
($2003/$2004), and saved accumulator ($2010) do not overlap.
The sentinel at $0100/$0101 is in the stack page, but balanced PHP/PLA uses
$01FF with the initialized SP=$FF, and does not clobber those bytes.

CHECK_LDA first stores A with STA and snapshots status with PHP.
PLA/AND/CMP/later LDA operate after that snapshot. Thus the N/Z check does
not accidentally inspect flags modified by the comparison itself.
The current wrong load $11 gives N=0,Z=0 and first fails the N assertion;
the actual loaded byte remains at $2010.

The expected values and addresses are correct; no production test change
is needed for these three cases.

## Minimum setup and observed reads

All numbers are hexadecimal. The opcode is A1 FF for Cases 30/31 and B1 FF
for Case 32. Only the listed memory and index values are needed to reproduce
the failing load; test reporting adds supporting instructions.

| Case | Instruction/index | Memory setup | Expected pointer reads | Actual pointer reads | Expected data | Actual data |
| --- | --- | --- | --- | --- | --- | --- |
| 30 | LDA ($FF,X), X=1 | M[0000]=00, M[0001]=14; M[0100]=00, M[0101]=15; M[1400]=9A, M[1500]=11 | 0000/0001 | 0100/0101 | [1400]=9A | [1500]=11 |
| 31 | LDA ($FF,X), X=0 | M[00FF]=00, M[0000]=14; M[0100]=15; M[1400]=AB, M[1500]=11 | 00FF/0000 | 00FF/0100 | [1400]=AB | [1500]=11 |
| 32 | LDA ($FF),Y, Y=1 | M[00FF]=00, M[0000]=14; M[0100]=15; M[1401]=BC, M[1501]=11 | 00FF/0000 | 00FF/0100 | [1401]=BC | [1501]=11 |

Smaller local reproducers use the original setup and LDA but compare the saved
byte directly, without PHP/PLA/AND or CHECK_LDA. A simulator-clock observer
records the bus address/read wires and A/N/Z when the LDA retires.
It calls the original clock; it does not change CPU registers, memory or CPU
methods. An independent address calculation from the initialized memory checks
the expected literal against the NMOS formula. These observations are retained
in results/lda_2026-10-20_02/followup_summary.json.

## CPU locations, left unchanged

File:
[algorithmic/singlecycle_processor.py](../../punxa_6502/algorithmic/singlecycle_processor.py).

| Case | Location | Implementation issue |
| --- | --- | --- |
| 30 | Line 193, then 194-195 | add += self.X leaves $0100; the two bytes come from $0100/$0101 |
| 31 | Line 195 | memoryRead(add+1) reads $0100 instead of wrapping to $0000 |
| 32 | Line 205, then 208-209 | Same high-byte problem; Y is added to the already wrong pointer |

There are three failing scenarios and two related omissions: pointer-index
wrapping, and pointer-high-byte wrapping in both indirect paths.
No CPU fix is included.

## Cycle-budget evidence

The real sequential test currently fails at Case 30 in 4713 clocks; that
early exit does not show whether the old 5000 limit fits all 32 cases.

A timing-only copy changes the failure jump within CHECK_A from fail to its
local continuation. Instructions retain their lengths. All scenario bodies and
CPU behavior remain unchanged; failed assertions no longer stop that copy.
Its reported success is excluded from functional pass counts.

Measured: the 5000 cap times out in Case 31; a 20000 cap allows all scenario
numbers 1-32 to be visited and completes at 5281 clocks.
The new default 10000 leaves 4719 clocks of measured headroom, while retaining
a finite limit and the --max-cycles override. This is not a prediction of
future suite sizes or physical 6502 timing.

The functional result remains 29 PASS / 3 FAIL. Timing completion does not
turn the known CPU failures into passes.
