# 6502 ISA tests

Self-checking assembly tests for the punxa 6502 processor models, in the style
of the RISC-V ISA tests. Each file in [isa/](isa/) tests one instruction
(47 files). The files are assembled with our own assembler, so no external
tools are needed.

Every test uses the shared protocol in [test_protocol.inc](isa/test_protocol.inc):
`test_case` holds the number of the case being checked, and `final_result` is
`1` when all cases pass or `255` when one fails.

## Running the tests

Run these commands from this folder (`test/isa_tests`).

| Model | Whole suite |
| --- | --- |
| SingleCycle (algorithmic, not synthesizable) | `python tb_ISA_tests.py -c "runAllTests()"` |
| MultiCycle (structural datapath, synthesizable) | `python tb_ISA_tests_Multicycle.py -c "runAllTests()"` |

To run one file with an instruction trace:

```
python tb_ISA_tests_Multicycle.py -c "runTest('test_logic_EOR.asm', verbose=True)"
```

If a test fails, the message names the failing case (`Failed in test case N`).

If you redirect the output to a file or pipe, use `python -u`, because the
runners exit with `os._exit(0)`, which throws away buffered output. On Windows
also set `PYTHONIOENCODING=utf-8`, so the progress bars can be printed.

## Current results (2026-11-11)

| Model | Result |
| --- | --- |
| SingleCycle | **47/47 PASS** |
| MultiCycle | **47/47 PASS** |

The 47 files contain 405 test cases and cover 137 opcode/addressing-mode
combinations. Both models run every combination.

## More information

- [COVERAGE.md](COVERAGE.md): what each test checks, untested instructions,
  coverage gaps and known issues.
- [MULTICYCLE_COMPATIBILITY.md](MULTICYCLE_COMPATIBILITY.md): how the
  MultiCycle model implements the instructions, and its limitations.
- [BATCH6_SUMMARY.md](BATCH6_SUMMARY.md) and [LDA_REVIEW.md](LDA_REVIEW.md):
  historical notes from building the suite.
