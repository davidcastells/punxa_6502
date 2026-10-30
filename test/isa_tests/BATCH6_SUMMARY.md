# Batch 6: INY, DEY and DEC

Validated 2026-10-27 on `feature/6502-isa-batch6`. Three new formal assembly
files use the existing ATmega-style methodology: numbered self-checking scenarios,
fixed NMOS 6502 expectations, and `test_case` / `final_result` / common `end`.
CPU implementations, existing tests, runners, adapters and protocol are unchanged.

## Formal execution results

| New file | Target opcode / addressing mode | Complete-file result | Simulation clocks |
| --- | --- | --- | --- |
| [test_arith_INY.asm](isa/test_arith_INY.asm) | `$C8` implied | FAIL at case 2; case 1 PASS, cases 3-6 NOT_REACHED | 1007 |
| [test_arith_DEY.asm](isa/test_arith_DEY.asm) | `$88` implied | All 6 scenarios PASS sequentially | 3480 |
| [test_arith_DEC.asm](isa/test_arith_DEC.asm) | `$C6` zp, `$D6` zp,X, `$CE` abs, `$DE` abs,X | All 8 scenarios PASS sequentially | 5671 |

All files assembled and linked with ca65/ld65. INY exits 1; DEY and DEC exit 0.
The default 10000-clock limit and strict result protocol were retained.

## INY: two confirmed CPU behavior defects

Cases 3-6 were executed independently during focused validation, preserving their
setup and assertions. They were not reached by the complete-file regression.

| Case | Input -> expected Y | Expected N/Z | Observed Y; raw N/Z | Sequential | Isolated |
| --- | --- | --- | --- | --- | --- |
| 1 | `$00 -> $01` | 0/0 | `$01`; 0/0 | PASS | Not needed |
| 2 | `$01 -> $02` | 0/0 | `$02`; 0/1 | FAIL | Not needed |
| 3 | `$7E -> $7F` | 0/0 | `$7F`; 0/0 | NOT_REACHED | PASS |
| 4 | `$7F -> $80` | 1/0 | `$80`; 1/1 | NOT_REACHED | FAIL |
| 5 | `$FE -> $FF` | 1/0 | `$FF`; 1/0 | NOT_REACHED | PASS |
| 6 | `$FF -> $00` | 0/1 | `$100`; 2/1 | NOT_REACHED | FAIL |

Combined evidence: **3 PASS / 3 FAIL**. In
[SingleCycle INY](../../punxa_6502/algorithmic/singlecycle_processor.py#L340),
`Z=(Y&1)^1` tests parity instead of zero (cases 2/4), and `Y+=1` lacks an
8-bit mask (case 6). Captured status in case 2 is `$32`, expected `$30`.
In case 6, an 8-bit store hides the over-wide Y; live `CPY #$00` detects it.
Read-only observations confirm these differences before checking helpers execute.
Assertions after each first failure are not claimed to have run.

## DEY: six passing scenarios

Observed Y and N/Z match every fixed expectation below; all assertions completed.

| Case | Input -> expected and observed Y | Expected and observed N/Z |
| --- | --- | --- |
| 1 | `$02 -> $01` | 0/0 |
| 2 | `$01 -> $00` | 0/1 |
| 3 | `$00 -> $FF` | 1/0 |
| 4 | `$80 -> $7F` | 0/0 |
| 5 | `$81 -> $80` | 1/0 |
| 6 | `$FF -> $FE` | 1/0 |

No DEY defect was reproduced by these inputs, including 8-bit underflow.

## DEC: eight passing scenarios and a separate internal observation

Every expected memory byte and packed N/Z below matched actual execution.

| Case | Opcode / mode | Effective address | Input -> expected and observed byte | Expected and packed N/Z |
| --- | --- | --- | --- | --- |
| 1 | `$C6` zp | `$0040` | `$02 -> $01` | 0/0 |
| 2 | `$C6` zp | `$0041` | `$01 -> $00` | 0/1 |
| 3 | `$D6` zp,X | `$FF + $02 -> $0001` | `$00 -> $FF` | 1/0 |
| 4 | `$CE` abs | `$1000` | `$80 -> $7F` | 0/0 |
| 5 | `$DE` abs,X | `$12FF + $01 -> $1300` | `$81 -> $80` | 1/0 |
| 6 | `$CE` abs | `$1100` | `$FF -> $FE` | 1/0 |
| 7 | `$D6` zp,X | `$40 + $02 -> $0042` | `$01 -> $00` | 0/1 |
| 8 | `$DE` abs,X | `$13FF + $02 -> $1401` | `$00 -> $FF` | 1/0 |

**DEC remains a formal PASS.** Cases 3/8 independently expose raw `cpu.N=-1`
instead of canonical 1. [DEC execution](../../punxa_6502/algorithmic/singlecycle_processor.py#L313)
shifts the unmasked subtraction result; the memory bus and PHP stack copy retain
the correct eight-bit byte and N bit. Saved P is `$F8`/`$F1`, exactly expected.
This internal representation finding does not establish an architectural failure
in the covered cases; consequences for other consumers of N remain unverified.
No expected bit was masked and no FAIL was overridden.

## Assertions, helper evidence and negative controls

LDY establishes inputs; binary ADC/CLC/SEC establish C/V before CLD/SED selects D.
Final LDX (INY/DEY) or LDY (DEC) seeds opposing N/Z. Flag-neutral stores capture
registers, then PHP captures status before TSX, loads or comparisons alter it.
Direct `$01FF` reads avoid PLA. Fixed full status bytes check N/Z and C/V/D/I=0.
INY/DEY check both live Y via CPY and its saved byte; independent target-state
observations support the helper checks. DEC checks literal memory results,
neighbors and distinct address sentinels. All targets preserve A, SP and the
unaffected index registers; read-only observations also confirm target writes
(none for INY/DEY, intended address/data for DEC). Observers do not modify CPU/RAM.

Temporary copies outside formal discovery deliberately changed case 1 expectations:

| Test | Incorrect value expectation | Incorrect Z expectation |
| --- | --- | --- |
| INY | FAIL, stage 1, 368 clocks | FAIL, stage 2, 449 clocks |
| DEY | FAIL, stage 1, 363 clocks | FAIL, stage 2, 444 clocks |
| DEC | FAIL, stage 1, 437 clocks | FAIL, stage 2, 488 clocks |

All six controls returned status 255 with a correct target operation. They verify
assertion detection, add no coverage, and left the formal sources unchanged.

## Full SingleCycle regression and coverage

The completed `--all` run produced **36 files: 29 PASS / 7 FAIL / 0 TIMEOUT /
0 ERROR**, exit 1. All original 33 outcomes, failing/final cases, clocks and PCs
match Batch 5. Failures remain LDA case 30, INX case 5, INC case 5, ASL case 4,
PLA case 1, ORA case 13, plus new INY case 2.

- Targeted Execute-path mnemonics: **35/39 (89.74%)**.
- Observed target opcode/mode pairs: **107/116 (92.24%)**.
- Sequentially reached pairs: **103/116 (88.79%)**.

Batch 6 adds six distinct pairs, all reached sequentially. The four additional
observed pairs are historical isolated ASL memory executions, not new Batch 6
runs. Failing checks count as coverage, not correctness; helpers and controls
do not count. Two LDA files explain 36 files targeting 35 mnemonics. See
[COVERAGE.md](COVERAGE.md) for the inventory and historical baselines.

## Reproduction and limitations

With the [README setup](README.md#requirements-and-installation), run from the
repository root; use PATH or append `--cc65-bin "<path-to-cc65-bin>"`:

```sh
python test/isa_tests/tb_ISA_tests.py test_arith_INY
python test/isa_tests/tb_ISA_tests.py test_arith_DEY
python test/isa_tests/tb_ISA_tests.py test_arith_DEC
python test/isa_tests/tb_ISA_tests.py --all
```

Inputs and flag combinations are representative, not exhaustive. I=0 follows
simulator initialization, not physical NMOS reset; I=1, reset/interrupts, physical
timing/RMW dummy writes, MMIO and full 16-bit indexed wrap are unverified.
DEC underflow was observed only in zp,X and abs,X; packed flags do not prove
internal N normalization. Batch 6 did not run MultiCycle: the unchanged complete
files remain NOT_RUN because required helpers include unsupported CLD/PHP/SEC/SED.
The earlier shared LDA-immediate validation is not evidence for these targets.
