# Testing 6502 ISA

We implemented some instruction tests in assembler in a similar way that RISC-V ISA tests are implemented (and was done in Punxa to verify the repertory).

In punxa_6502 we provide assembler source code that we assemble with our own assembler to avoid unnecessary external dependencies.

There is one test file per instruction mnemonic in [isa/](isa/) (47 files). Both
processor models run the same files with the same protocol
([test_protocol.inc](isa/test_protocol.inc)): `test_case` records the scenario
being checked and `final_result` is 1 (pass) or 255 (fail).

## Instruction support per model

| Model | ISA test result (2026-11-10) | Notes |
| --- | --- | --- |
| SingleCycle (algorithmic) | **47/47 PASS** | Includes EOR, LSR, CPX, BVC, BVS, CLI, SEI and CLV, added 2026-11-10 |
| MultiCycle (structural) | **39/47 PASS** | EOR, LSR, CPX, BVC, BVS, CLI, SEI and CLV are **not implemented yet**; their 8 files fail with `op .. not handled` |

Instructions added to SingleCycle on 2026-11-10, with the addressing modes
exercised by their tests:

| Instruction | Test file | Addressing modes tested | Cases |
| --- | --- | --- | --- |
| EOR | [test_logic_EOR.asm](isa/test_logic_EOR.asm) | #, zp, zp,X, abs, abs,X, abs,Y, (zp,X), (zp),Y | 15 |
| LSR | [test_bitmap_LSR.asm](isa/test_bitmap_LSR.asm) | A, zp, zp,X, abs, abs,X | 12 |
| CPX | [test_arith_CPX.asm](isa/test_arith_CPX.asm) | #, zp, abs | 12 |
| BVC | [test_ctrflow_BVC.asm](isa/test_ctrflow_BVC.asm) | rel (taken/not taken, forward/backward, page crossing, +127/-128) | 8 |
| BVS | [test_ctrflow_BVS.asm](isa/test_ctrflow_BVS.asm) | rel (taken/not taken, forward/backward, page crossing, +127/-128) | 8 |
| CLI | [test_mcu_CLI.asm](isa/test_mcu_CLI.asm) | implied (uses SEI to set I=1) | 3 |
| SEI | [test_mcu_SEI.asm](isa/test_mcu_SEI.asm) | implied | 3 |
| CLV | [test_mcu_CLV.asm](isa/test_mcu_CLV.asm) | implied | 4 |

CMP zp,X was already covered by case 5 of [test_arith_CMP.asm](isa/test_arith_CMP.asm).

## Single cycle algorithmic design

This model is the behavioral model described with the algorithmic py4hw design style, which currently is not synthesizable.


To run the tests do

```
python tb_ISA_tests.py -c "runAllTests()"
```

***Summary***

<pre>
test_arith      100.0 %  |█████████████████████████████████████████████|
test_bitmap     100.0 %  |█████████████████████████████████████████████|
test_ctrflow    100.0 %  |█████████████████████████████████████████████|
test_data       100.0 %  |█████████████████████████████████████████████|
test_logic      100.0 %  |█████████████████████████████████████████████|
test_mcu        100.0 %  |█████████████████████████████████████████████|
</pre>

The detailed current output is:

```
Test test_arith_ADC.asm             = OK
Test test_arith_CMP.asm             = OK
Test test_arith_CPX.asm             = OK
Test test_arith_CPY.asm             = OK
Test test_arith_DEC.asm             = OK
Test test_arith_DEX.asm             = OK
Test test_arith_DEY.asm             = OK
Test test_arith_INC.asm             = OK
Test test_arith_INX.asm             = OK
Test test_arith_INY.asm             = OK
Test test_arith_SBC.asm             = OK
Test test_bitmap_ASL.asm            = OK
Test test_bitmap_LSR.asm            = OK
Test test_bitmap_ROR.asm            = OK
Test test_ctrflow_BCC.asm           = OK
Test test_ctrflow_BEQ.asm           = OK
Test test_ctrflow_BNE.asm           = OK
Test test_ctrflow_BVC.asm           = OK
Test test_ctrflow_BVS.asm           = OK
Test test_ctrflow_JMP.asm           = OK
Test test_ctrflow_JSR.asm           = OK
Test test_ctrflow_RTS.asm           = OK
Test test_data_LDA.asm              = OK
Test test_data_LDX.asm              = OK
Test test_data_LDY.asm              = OK
Test test_data_PHA.asm              = OK
Test test_data_PHP.asm              = OK
Test test_data_PLA.asm              = OK
Test test_data_STA.asm              = OK
Test test_data_STX.asm              = OK
Test test_data_STY.asm              = OK
Test test_data_TAX.asm              = OK
Test test_data_TAY.asm              = OK
Test test_data_TSX.asm              = OK
Test test_data_TXA.asm              = OK
Test test_data_TXS.asm              = OK
Test test_data_TYA.asm              = OK
Test test_logic_AND.asm             = OK
Test test_logic_EOR.asm             = OK
Test test_logic_ORA.asm             = OK
Test test_mcu_CLC.asm               = OK
Test test_mcu_CLD.asm               = OK
Test test_mcu_CLI.asm               = OK
Test test_mcu_CLV.asm               = OK
Test test_mcu_SEC.asm               = OK
Test test_mcu_SED.asm               = OK
Test test_mcu_SEI.asm               = OK
Total: 47 Correct: 47 (100.0 %)
```

## Multi-cycle structural design

This model is the model that contains a datapath described with the structural py4hw design style.
The datapath is synthesizable.

The eight instructions added to SingleCycle on 2026-11-10 (EOR, LSR, CPX, BVC,
BVS, CLI, SEI, CLV) are not implemented in MultiCycle yet, so their test files
fail. `test_mcu_CLI.asm` fails on SEI (`$78`), which it uses as a setup helper,
before reaching CLI. The other 39 files pass.


To run the tests do

```
python  tb_ISA_tests_Multicycle.py -c "runAllTests()"
```

***Summary***

<pre>
test_arith      90.9 %   |█████████████████████████████████████████░░░░|
test_bitmap     66.7 %   |██████████████████████████████░░░░░░░░░░░░░░░|
test_ctrflow    75.0 %   |██████████████████████████████████░░░░░░░░░░░|
test_data       100.0 %  |█████████████████████████████████████████████|
test_logic      66.7 %   |██████████████████████████████░░░░░░░░░░░░░░░|
test_mcu        57.1 %   |██████████████████████████░░░░░░░░░░░░░░░░░░░|
</pre>

The detailed current output is:

```
Test test_arith_ADC.asm             = OK
Test test_arith_CMP.asm             = OK
Test test_arith_CPX.asm             = FAILED - op E0 not handled
Test test_arith_CPY.asm             = OK
Test test_arith_DEC.asm             = OK
Test test_arith_DEX.asm             = OK
Test test_arith_DEY.asm             = OK
Test test_arith_INC.asm             = OK
Test test_arith_INX.asm             = OK
Test test_arith_INY.asm             = OK
Test test_arith_SBC.asm             = OK
Test test_bitmap_ASL.asm            = OK
Test test_bitmap_LSR.asm            = FAILED - op 4A not handled
Test test_bitmap_ROR.asm            = OK
Test test_ctrflow_BCC.asm           = OK
Test test_ctrflow_BEQ.asm           = OK
Test test_ctrflow_BNE.asm           = OK
Test test_ctrflow_BVC.asm           = FAILED - op 50 not handled
Test test_ctrflow_BVS.asm           = FAILED - op 70 not handled
Test test_ctrflow_JMP.asm           = OK
Test test_ctrflow_JSR.asm           = OK
Test test_ctrflow_RTS.asm           = OK
Test test_data_LDA.asm              = OK
Test test_data_LDX.asm              = OK
Test test_data_LDY.asm              = OK
Test test_data_PHA.asm              = OK
Test test_data_PHP.asm              = OK
Test test_data_PLA.asm              = OK
Test test_data_STA.asm              = OK
Test test_data_STX.asm              = OK
Test test_data_STY.asm              = OK
Test test_data_TAX.asm              = OK
Test test_data_TAY.asm              = OK
Test test_data_TSX.asm              = OK
Test test_data_TXA.asm              = OK
Test test_data_TXS.asm              = OK
Test test_data_TYA.asm              = OK
Test test_logic_AND.asm             = OK
Test test_logic_EOR.asm             = FAILED - op 49 not handled
Test test_logic_ORA.asm             = OK
Test test_mcu_CLC.asm               = OK
Test test_mcu_CLD.asm               = OK
Test test_mcu_CLI.asm               = FAILED - op 78 not handled
Test test_mcu_CLV.asm               = FAILED - op B8 not handled
Test test_mcu_SEC.asm               = OK
Test test_mcu_SED.asm               = OK
Test test_mcu_SEI.asm               = FAILED - op 78 not handled
Total: 47 Correct: 39 (83.0 %)
```

## Known issues (not fixed yet)

These are pre-existing and unrelated to the 2026-11-10 instruction work.

- **Legacy pytest files.** `test_runner_assembly.py` and `test_testbench.py`
  call runner functions (`prepare_program`, `run_file_result`, `execute_test`,
  `discover_tests`, `main`, `TestResult`, ...) that were removed from
  `tb_ISA_tests.py` in commit `4b310c9` ("standarization of ISA tests"). They
  report 79 failures (25 test functions plus subtests), identically on the
  committed code before and after the 2026-11-10 changes. `test_assembly.py`
  passes. The `.asm` ISA suites above are not affected.
- **SingleCycle 16-bit address wrap.** Absolute,X and Absolute,Y compute
  `add + X` / `add + Y` without masking to 16 bits
  ([singlecycle_processor.py](../../punxa_6502/algorithmic/singlecycle_processor.py),
  lines 179 and 186), so e.g. `$FFFF,X` addresses beyond 64 KiB. Found by code
  reading; no test exercises it.
- **SingleCycle branch PC wrap.** Taken branches do `pc += offset` without
  wrapping at `$FFFF` (same file, lines 298-322). Found by code reading; no
  test exercises it.
- **Captured output on Windows.** When the runner output is redirected to a
  file or pipe, add `-u` (and `PYTHONIOENCODING=utf-8` for the progress bars):
  the runners end with `os._exit(0)`, which discards buffered output, and the
  `█` bars cannot be encoded in cp1252. The per-test lines are printed before
  the bars, so results are still readable when only the bars fail.
