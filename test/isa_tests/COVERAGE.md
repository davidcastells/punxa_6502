# ISA Coverage Matrix - after expansion Batch 5

Updated 2026-10-26 from the completed review, Phase A/B3 and Batch 1-5 evidence.
Implementation labels/modes are carried forward; no full CPU review was repeated.
Scope: SingleCycle6502 and documented original NMOS instructions.

B3 note: the shared LDA Immediate subset brought the count to18 files but
still17 target mnemonics. $A9 was already covered, so B3 added no SingleCycle
target mnemonic/opcode pair. That subset
checks A/Z on5 cases and actually passes on both models (481/974 clocks);
this is not full LDA correctness or a new full-suite run.
See [MultiCycle matrix](MULTICYCLE_COMPATIBILITY.md) and
[B3 evidence](results/phase_b3_2026-10-22_03/REPORT.md).

## Counting and interpretation

- Opcode/Decode baseline:56 mnemonics /151 opcode-mode pairs.
- Actual Execute paths, including partial/defective behavior:39 /116.
- Formal targets: **32/39=82.05%**, in33 files (Batch 4:29/39=74.36%).
- Observed target pairs including isolated original cases: **101/116=87.07%**
  (Batch 4:98/116=84.48%). Batch 5 adds three observed target opcodes.
- Sequential --all reaches **97/116=83.62%**. Four ASL memory forms were
  actually executed only in isolated original case blocks after file failure.
- No formal target coverage remains for7 Execute mnemonics /15 pairs.
- Coverage includes meaningful failing checks; it is not CPU correctness.

Fully implemented means the reviewed RAM functional logic is present, not
independently verified unless Test Result says so. Partially implemented
has known semantic/shared-address limitations. Physical timing, MMIO and
reset/interrupt correctness are not implied; stack requires explicit SP setup.
Not verified means no independent target test, even if used as a helper.

G8 = #, zp, zp,X, abs, abs,X, abs,Y, (zp,X), (zp),Y.
G7 = G8 without #. M4 = zp, zp,X, abs, abs,X.
A=Accumulator; imp=Implied; rel=Relative.

## Execute-path matrix

| Category | Instruction | CPU Implementation | CPU Addressing Modes | ISA Test | Tested Modes / Properties | Test Result | Remaining Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Data | LDA | Partially implemented | G8 | [Yes: test_data_LDA.asm](isa/test_data_LDA.asm) | G8; N/Z; C/V/D preservation samples | 29 PASS /3 FAIL (earlier isolated baseline); full FAIL30 | I preservation; mode-specific state combinations; known indirect wrapping |
| Data | LDX | Fully implemented | #, zp, zp,Y, abs, abs,Y | [Yes: test_data_LDX.asm](isa/test_data_LDX.asm) | five modes; X/N/Z | 15 PASS | C/V/D/I and other-register preservation; more address boundaries |
| Data | LDY | Fully implemented | #, zp, zp,X, abs, abs,X | [Yes: test_data_LDY.asm](isa/test_data_LDY.asm) | five modes; 00/55/7F/80/FF; Y/N/Z, A/X/SP/C/V/D preservation, I=0; zp,X wrap and abs,X page crossing | 12 PASS; full PASS12,5750 clocks | I=1 preservation; full16-bit indexed wrap; exhaustive inputs/state combinations |
| Data | STA | Partially implemented | G7 | [Yes: test_data_STA.asm](isa/test_data_STA.asm) | G7; address/data/guards, A/flags; I/V initially0 | 10 PASS | V=1/I=1 preservation; indirect boundaries; 16-bit wrap |
| Data | STX | Fully implemented | zp, zp,Y, abs | [Yes: test_data_STX.asm](isa/test_data_STX.asm) | three modes; data/address/guards, zp,Y wrap, FFFF, X/A/Y/SP and flags | 8 PASS; full PASS8,5341 clocks | I=1 preservation; further values/status combinations |
| Data | STY | Fully implemented | zp, zp,X, abs | [Yes: test_data_STY.asm](isa/test_data_STY.asm) | three modes; data/address/neighbor guards, Y/A/X/SP and flags; zp,X wrap and FFFF | 8 PASS; full PASS8,5341 clocks | I=1 preservation; further values/state combinations |
| Transfer | TAX | Fully implemented | imp | [Yes: test_data_TAX.asm](isa/test_data_TAX.asm) | A to X; 00/01/7F/80/FF/55; opposing N/Z; A/Y/SP preserved; C/V/D varied, I=0 | 6 PASS; full PASS6,2898 clocks | I=1 preservation; exhaustive input/state combinations |
| Transfer | TAY | Fully implemented | imp | [Yes: test_data_TAY.asm](isa/test_data_TAY.asm) | A->Y;00/01/7F/80/FF/55; opposing N/Z, A/X/SP/C/V/D preservation, I=0; three-transfer sequence with every intermediate snapshot checked | 7 scenarios PASS,9 targets; full PASS7,3749 clocks | I=1; further values/orderings, exhaustive state combinations |
| Transfer | TXA | Fully implemented | imp | [Yes: test_data_TXA.asm](isa/test_data_TXA.asm) | X->A;00/01/7F/80/FF/55; opposing N/Z, X/Y/SP/C/V/D preservation, I=0;00->80->01 sequence | 7 scenarios PASS,9 targets; full PASS7,3749 clocks | I=1; further values/orderings, exhaustive state combinations |
| Transfer | TYA | Fully implemented | imp | [Yes: test_data_TYA.asm](isa/test_data_TYA.asm) | Y->A;00/01/7F/80/FF/55; opposing N/Z, Y/X/SP/C/V/D preservation, I=0;00->80->01 sequence | 7 scenarios PASS,9 targets; full PASS7,3749 clocks | I=1; further values/orderings, exhaustive state combinations |
| Transfer | TSX | Fully implemented | imp | [Yes: test_data_TSX.asm](isa/test_data_TSX.asm) | SP->X at00/01/7F/80/FF/55; opposing N/Z; SP/A/Y/C/V/D preserved, I=0;00->FF->FE sequence; fixed stack evidence and independent SP observations | 7 scenarios PASS,9 targets; full PASS7,4682 clocks | I=1; further values/sequences; physical reset/interrupt effects |
| Transfer | TXS | Fully implemented | imp | [Yes: test_data_TXS.asm](isa/test_data_TXS.asm) | X->SP at00/01/7F/80/FF/55; A/X/Y and all flags at I=0 preserved;00->80->55 sequence; fixed PHP/PHA addresses/guards, no TSX oracle; independent SP observations | 7 scenarios PASS,9 targets; full PASS7,5648 clocks | I=1; further input/status combinations |
| Arithmetic | ADC | Partially implemented | G8 | [Yes: test_arith_ADC.asm](isa/test_arith_ADC.asm) | G8 binary; A/C/Z/N/V, D=0 | 15 PASS | Decimal; I preservation; further operands and indirect boundaries |
| Arithmetic | SBC | Partially implemented | G8 | [Yes: test_arith_SBC.asm](isa/test_arith_SBC.asm) | G8, D=0; A/C/Z/N/V; borrow-in/out, overflow both directions; zp,X wrap and page crossing; X/Y/SP preservation | 15 PASS; full PASS15,6681 clocks | Decimal deferred; indirect wrapping, full 16-bit wrap, exhaustive operands; I=1 |
| Compare | CMP | Partially implemented | G8 | [Yes: test_arith_CMP.asm](isa/test_arith_CMP.asm) | G8; C/Z/N, A unchanged, V/D preserved; independent ADC oracle | 10 PASS / 0 FAIL | Indirect boundaries; I preservation; more operand/status combinations |
| Compare | CPY | Fully implemented | #, zp, abs | [Yes: test_arith_CPY.asm](isa/test_arith_CPY.asm) | three modes; equality/less/greater in each; unsigned C, wrapped N, Z; incoming C ignored; Y/A/X/SP/V/D preserved, I=0; operand unchanged | 12 PASS; full PASS12,6015 clocks | I=1 preservation; exhaustive operand/status combinations |
| Inc/Dec | INC | Partially implemented | M4 | [Yes: test_arith_INC.asm](isa/test_arith_INC.asm) | M4; memory/guards, N/Z, A/other flags | 4 PASS / 1 FAIL; full FAIL5 | Known FF to00 flags failure; more per-mode boundaries |
| Inc/Dec | DEC | Partially implemented | M4 | No | - | Not verified | 00 toFF, N normalization and flags |
| Inc/Dec | INX | Partially implemented | imp | [Yes: test_arith_INX.asm](isa/test_arith_INX.asm) | imp; X/N/Z and C/V/D preservation; I=0 | 4 PASS / 2 FAIL; full FAIL5 | Known nonzero-even Z failures; exhaustive inputs/status combinations |
| Inc/Dec | INY | Partially implemented | imp | No | - | Not verified | Z calculation and 8-bit Y wrap |
| Inc/Dec | DEX | Fully implemented | imp | [Yes: test_arith_DEX.asm](isa/test_arith_DEX.asm) | ordinary/even results, 00->FF,01->00,80->7F,81->80; X/N/Z, A/Y/SP/C/V/D preservation, I=0; memory guards/no target writes | 8 PASS; full PASS8,4489 clocks | I=1; exhaustive inputs/state combinations |
| Inc/Dec | DEY | Fully implemented | imp | No | - | Not verified | Zero, negative, wrap, N/Z |
| Logic | AND | Partially implemented | G8 | [Yes: test_logic_AND.asm](isa/test_logic_AND.asm) | G8; A/N/Z and C/V/D preservation | 10 PASS / 0 FAIL | Indirect boundaries; I preservation; further patterns/status combinations |
| Logic | ORA | Partially implemented | G8 | [Yes: test_logic_ORA.asm](isa/test_logic_ORA.asm) | G8; complementary/zero/all-one/partial patterns; A/N/Z, X/Y/SP/C/V/D preservation, I=0; zp/indexed/indirect boundaries | 12 PASS /3 FAIL; full FAIL13,6030 clocks; 14/15 isolated FAIL | Known shared indirect pointer wrapping; later assertions after failed check; full16-bit wrap; I=1; exhaustive patterns |
| Shift | ASL | Partially implemented | A + M4 (broken memory write-back) | [Yes: test_bitmap_ASL.asm](isa/test_bitmap_ASL.asm) | A + M4*; values/C/N/Z, memory write-back | 3 PASS / 6 FAIL; full FAIL4 | Known A width/write-back defects; later memory flag assertions not reached |
| Shift | ROR | Partially implemented | A + M4 (broken memory write-back) | No | - | Not verified | Carry-in/out, N/Z and memory forms |
| Branch | BCC | Partially implemented | rel | [Yes: test_ctrflow_BCC.asm](isa/test_ctrflow_BCC.asm) | C=0 taken/C=1 fallthrough; signed directions, taken page crossing and not-taken encoded crossing; +127/-128; path marker/exact PC and A/X/Y/SP/flags | 8 PASS; full PASS8,4176 clocks | Full16-bit PC wrap; I=1; offset0 and other flag/state combinations |
| Branch | BEQ | Partially implemented | rel | [Yes: test_ctrflow_BEQ.asm](isa/test_ctrflow_BEQ.asm) | rel; conditions/directions/pages and A/flags | 6 PASS / 0 FAIL | Full PC wrap, I=1 preservation, displacement endpoints |
| Branch | BNE | Partially implemented | rel | [Yes: test_ctrflow_BNE.asm](isa/test_ctrflow_BNE.asm) | rel; conditions, signed offsets/pages, limits, flags | 8 PASS | Full PC wrap and I=1 preservation |
| Control flow | JMP | Partially implemented | abs; (abs) defective | No (helper) | - | Not verified | Absolute, full indirect pointer and NMOS page-end behavior |
| Control flow | JSR | Fully implemented | abs | [Yes: test_ctrflow_JSR.asm](isa/test_ctrflow_JSR.asm) | abs; entry/frame/SP/flags, nesting, no RTS oracle | 3 PASS / 0 FAIL | Further nesting, frame and memory boundaries |
| Control flow | RTS | Partially implemented | imp | [Yes: test_ctrflow_RTS.asm](isa/test_ctrflow_RTS.asm) | imp; manual frames/PC/SP/flags, page carry and nesting | 4 PASS / 0 FAIL | Full FFFF+1 PC wrap; further frame boundaries |
| Stack | PHA | Fully implemented | imp | [Yes: test_data_PHA.asm](isa/test_data_PHA.asm) | imp; byte/address/SP/flags and wrap | 4 PASS / 0 FAIL | Further stack values/guards; I=1 preservation |
| Stack | PHP | Fully implemented | imp | [Yes: test_data_PHP.asm](isa/test_data_PHP.asm) | Full raw30/32/B0/31/70/38/7B/F9 status bytes, B/bit5=1 and I=0; stack address/decrement/wrap/guards, registers, live C/Z; independent observations verify all live flags; three-push sequence | 9 scenarios PASS,11 targets; full PASS9,7289 clocks | I=1/arbitrary status patterns unavailable; live N/V/D/I preservation additionally needs observer, not assembly-only proof; reset/interrupt behavior |
| Stack | PLA | Partially implemented | imp | [Yes: test_data_PLA.asm](isa/test_data_PLA.asm) | imp; byte/address/SP then N/Z; wrap | 0 PASS / 5 FAIL; full FAIL1 | Known missing N/Z updates; further inputs/status combinations |
| Flags | CLC | Fully implemented | imp | [Yes: test_mcu_CLC.asm](isa/test_mcu_CLC.asm) | imp; carry clear/idempotence, A/other flags | 3 PASS / 0 FAIL | I=1 preservation and further flag combinations |
| Flags | SEC | Fully implemented | imp | [Yes: test_mcu_SEC.asm](isa/test_mcu_SEC.asm) | imp; carry set/idempotence, A/other flags | 3 PASS / 0 FAIL | I=1 preservation and further flag combinations |
| Flags | CLD | Fully implemented | imp | No (helper) | - | Not verified | Independent D clear and other-state preservation |
| Flags | SED | Fully implemented | imp | No (helper) | - | Not verified | Independent D set and other-state preservation |

* All four ASL memory cases independently FAIL. First assertion checks write-back;
later A/flags assertions are not reached. Actual wrong A/flags are retained
as independent target-retirement observations.

## Defined/decoded standard instructions without dedicated Execute

| Category | Instruction | CPU Implementation | CPU Addressing Modes | ISA Test | Tested Modes | Test Result | Remaining Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Compare | CPX | Not implemented | None; Decode: #, zp, abs | No | - | Not verified | Execute and formal checks |
| Logic | EOR | Not implemented | None; Decode: G8 | No | - | Not verified | Execute and formal checks |
| Logic | BIT | Not implemented | None; Decode: zp, abs | No | - | Not verified | Execute and formal checks |
| Shift | LSR | Not implemented | None; Decode: A + M4 | No | - | Not verified | Execute and formal checks |
| Shift | ROL | Not implemented | None; Decode: A + M4 | No | - | Not verified | Execute and formal checks |
| Branch | BCS | Not implemented | None; Decode: rel | No | - | Not verified | Execute and formal checks |
| Branch | BMI | Not implemented | None; Decode: rel | No | - | Not verified | Execute and formal checks |
| Branch | BPL | Not implemented | None; Decode: rel | No | - | Not verified | Execute and formal checks |
| Branch | BVC | Not implemented | None; Decode: rel | No | - | Not verified | Execute and formal checks |
| Branch | BVS | Not implemented | None; Decode: rel | No | - | Not verified | Execute and formal checks |
| Flags | CLI | Not implemented | None; Decode: imp | No | - | Not verified | Execute and formal checks |
| Flags | SEI | Not implemented | None; Decode: imp | No | - | Not verified | Execute and formal checks |
| Flags | CLV | Not implemented | None; Decode: imp | No | - | Not verified | Execute and formal checks |
| Stack | PLP | Not implemented | None; Decode: imp | No | - | Not verified | Execute and formal checks |
| Interrupt | BRK | Not implemented | None; Decode: imp | No | - | Not verified | Execute and formal checks |
| Interrupt | RTI | Not implemented | None; Decode: imp | No | - | Not verified | Execute and formal checks |
| Misc | NOP | Not implemented | None; Decode: imp | No | - | Not verified | Execute and formal checks |

These17 account for35 opcode/mode pairs. NOP falls through UNHANDLED; that
accidental empty behavior is not a dedicated implementation. Other decode-only
instructions can also retire, so absence of exceptions does not prove support.

## Remaining gaps and evidence

Untested Execute targets: DEC, INY, DEY; ROR; JMP; CLD, SED.
Auxiliary usage is not formal target coverage.

Further gaps: Decimal arithmetic; I=1 setup/preservation (SEI/PLP/RTI missing);
shared indirect boundaries; full PC wrapping; exhaustive patterns;
MMIO/timing/reset/IRQ/NMI; MultiCycle. ADC Decimal carry and SBC NMOS Decimal
flags remain separate concerns without new executed cases.

Baseline sources: [instruction_decode.py](../../punxa_6502/instruction_decode.py)
and [singlecycle_processor.py](../../punxa_6502/algorithmic/singlecycle_processor.py).
Known locations: indirect189-209; ASL271-276; INC329-334; INX335-339;
PLA487-489; indirect JMP179-188; RTS491-505. The comment questioning NMOS LDY
$B4 is incorrect; the mapped zp,X form is included. No decoder/CPU fix was made.

[Phase A report](results/phase_a_2026-10-22_01/REPORT.md) and summary.json
retain actual file/case totals, target opcodes, CPU issues and Phase B readiness.
Historical LDA independent32-case results remain in results/lda_2026-10-20_02;
this phase reran full LDA only.

Historical Phase A file results: **12 PASS /5 FAIL /0 TIMEOUT /0 ERROR**, exit1.
Phase A's new68 cases: **54 PASS /14 FAIL**, including isolated original blocks.
Phase A sequential new files:54 PASS /4 FAIL /10 NOT_REACHED.
No file PASS rate is used as an opcode coverage percentage.

## Batch 1 observed increment

TAX $AA; STX $86/$96/$8E; SBC $E9/$E5/$F5/$ED/$FD/$F9/$E1/$F1
all retired at their exported target probes with fixed expectations and completed
self-checks. All29 new cases PASS; no CPU difference was reproduced by them.
The full21-file SingleCycle run is16 PASS /5 FAIL /0 TIMEOUT /0 ERROR, exit1.
All original17 file outcomes/cases/clocks/PCs match Phase A; the B3 subset also
passes. LDA31/32 and later unreached old cases were not re-executed this batch.
The count74 combines historical62 with these disjoint12 target pairs.

The unchanged shared MultiCycle LDA Immediate file was rerun: PASS5,974 clocks,
55 retired. New files are NOT_RUN on MultiCycle: all require missing CLD/PHP;
STX also requires missing zp,Y and SBC has no dispatched Execute path.
These static blockers are not dynamically executed FAIL/ERROR outcomes.

[Batch 1 evidence](results/expansion_batch1_2026-10-23_01/REPORT.md) includes
per-case states, bus addresses/data, three negative controls and exact CLI records.

## Batch 2 observed increment

LDY $A0/$A4/$B4/$AC/$BC; STY $84/$94/$8C; CPY $C0/$C4/$CC all actually
retired at their target probes and completed the fixed self-checks. All32 new
cases PASS. Full24-file SingleCycle --all:19 PASS /5 FAIL /0 TIMEOUT /0 ERROR,
exit1. All21 prior outcomes/cases/clocks/PCs match Batch 1; no new CPU semantic
difference was reproduced. Old cases after a file's first failure were not rerun.
Coverage85 combines retained historical74 with these disjoint11 target pairs.

LDY does not use STY/CPY to assert Y. TAY/TYA/TSX/PHP have a focused diagnostic
preflight; read-only target observations also confirm saved checker bytes.
STY and CPY use the already-verified LDY. CPY assertions use literal-byte CMP
equality, not CPY itself. Helper/diagnostic executions add no formal target count.

New files are NOT_RUN on MultiCycle. All require missing CLD/PHP/SEC/SED;
LDY lacks zp/zp,X/abs/abs,X, STY lacks zp/zp,X, and CPY lacks zp/abs dispatch.
Static presence of LDY#, STY abs and CPY# is not semantic validation or evidence
that an unchanged complete file is executable. No MultiCycle simulation was run
in Batch 2. [Batch 2 evidence](results/expansion_batch2_2026-10-26_01/REPORT.md)
retains per-case outcomes, traces, observed opcodes, negative controls and blockers.

## Batch 3 observed increment

ORA $09/$05/$15/$0D/$1D/$19/$01/$11; BCC $90; DEX $CA all actually retired
as formal targets. Full ORA reaches cases1-13 (12 PASS /1 FAIL;14/15 NOT_REACHED).
Original cases13/14/15 then independently FAIL, retaining assertions and expected
values: aggregate ORA12 PASS /3 FAIL. BCC8 PASS and DEX8 PASS. These31 new
cases yield28 PASS /3 FAIL, with no ERROR/TIMEOUT. Full27-file --all is21 PASS /
6 FAIL, exit1; all24 prior outcomes/cases/clocks/PCs match Batch 2.

ORA13 reads pointer0100/0101 and operand1900 instead of pointer0000/0001 and
operand1800; ORA14/15 read pointer00FF/0100 instead of00FF/0000, loading1900/
1901 instead of1800/1801. This newly confirms ORA's exposure to the previously
known shared addressing defects, not a new OR boolean-operation defect.
Case14 checks flags successfully then fails on A;13/15 fail first on flags.
Independent observations do not imply later assembly assertions executed.

BCC checks every retirement PC and distinct path stores, including both page
directions and signed limits. Its wrong-destination control fails on the path
marker. DEX samples nonzero even results with Z=0, unlike the known INX defect;
target bus monitoring shows no writes and memory guards remain intact.
Coverage95 combines historical85 and ten new pairs, all reached by full files.

All three are NOT_RUN on MultiCycle: CLD/PHP/SEC/SED helpers lack dispatch.
ORA has only #/zp target paths; BCC lacks target dispatch; DEX has a path but
its complete file is blocked. No MultiCycle execution or weakened variants.
[Batch 3 evidence](results/expansion_batch3_2026-10-26_01/REPORT.md) retains
actual full/isolated/negative runs, pointer reads, branch paths and coverage basis.

## Batch 4 observed increment

TAY $A8, TXA $8A and TYA $98 each actually retired nine times: six single-value
cases plus three transfers in case7 (00->80->01). All seven scenarios per file
PASS:21 scenarios /27 checked target retirements. Each source/destination,
other register, SP and C/V/D/I=0 preservation check uses fixed expected snapshots.
The source registers are initialized through LDA/LDX/LDY; assertions use stores
and direct PHP bytes, with no reciprocal transfer as an oracle.

Case7 captures all three intermediate register/status sets before comparisons.
Only the checker PHP changes SP between targets: FF/FE/FD target entries and
FC after three snapshots. Each target itself preserves its entry SP. Read-only
observations verify all initial/retired states, saved bytes and no target writes.
Negative TAY/TYA middle-snapshot controls FAIL even with the final transfer
correct; the TXA wrong-Z control also FAILS. These diagnostics add no coverage.

Full30-file --all:24 PASS /6 FAIL /0 TIMEOUT /0 ERROR, exit1. All27 prior file
outcomes/cases/clocks/PCs match Batch 3. No new CPU difference was confirmed.
Coverage98 combines historical95 and three implied pairs; repeated executions
do not create extra pairs. Old isolated failures were not rerun this batch.

MultiCycle has all three target dispatch branches, but required CLD/PHP/SEC/SED
helpers still lack dispatch. All three unchanged files are NOT_RUN; no MultiCycle
simulation or weakened variants. [Batch 4 evidence](results/expansion_batch4_2026-10-26_01/REPORT.md)
retains individual cases/phases, captured-versus-checked controls and exact CLI logs.

## Batch 5 observed increment

TSX $BA, TXS $9A and PHP $08 actually retired9/9/11 times in7/7/9 numbered
scenarios; all23 scenarios PASS. Each file includes a three-operation sequence
and checks every intermediate snapshot. TSX checks00/01/7F/80/FF/55 plus
00->FF->FE, including N/Z changes. TXS checks the same values plus00->80->55,
preserving all six live flags at I=0 even when N/Z oppose the source byte.
PHP checks raw30/32/B0/31/70/38/7B/F9 bytes, SP FF/80/01/00/7F/55 and three
pushes at0101/0100/01FF. Guard checks stay inside the fixed stack page.

TSX has a real setup PHA after TXS, fixed X/status assertions and independent
read-only SP observations; TXS uses PHP/PHA writes at fixed addresses without
TSX. PHP checks literal RAM bytes and independently observed writes/state;
TSX checks SP only after target state capture, and a following PHA proves the
next stack address. PHP immediately checks live C/Z with branches. All live
flags are observed before/after each PHP: N/V/D/I preservation additionally
depends on this independent observer, not on a second PHP or assembly-only proof.
No PLA/PLP is used. Negative controls for wrong X, TXS N/Z and PHP bit5 each FAIL.

I=0 is the current simulator initialization convention; NMOS reset sets I=1.
SEI/PLP/RTI lack Execute paths, so I=1/arbitrary status combinations cannot be
reliably established here. Every status byte checks bit2=0 explicitly; B and
bit5 are each checked as1, not masked. No reset or interrupt claim is made.

Full33-file --all:27 PASS /6 FAIL /0 TIMEOUT /0 ERROR, exit1. All30 prior file
outcomes/cases/clocks/PCs match Batch 4, including six known failures. No new
CPU difference was reproduced.101 observed pairs combine98 retained historical
pairs and three new implied targets; sequential --all reaches97 pairs. Old
isolated ASL failures were not rerun, and diagnostic controls add no coverage.

All three unchanged files are NOT_RUN on MultiCycle. TSX/TXS have dispatch,
but required PHP/SEC/CLD/SED do not. PHP itself has no dispatch and additionally
requires missing BCC. Static dispatch presence does not prove full semantics;
no weakened file or MultiCycle simulation was used.
[Batch 5 evidence](results/expansion_batch5_2026-10-26_01/REPORT.md) retains
case results, raw target/stack observations, negative controls and CLI outputs.
