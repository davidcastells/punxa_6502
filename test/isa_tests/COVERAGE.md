# ISA test coverage

Updated 2026-11-19. This covers the SingleCycle, Hybrid and Microcoded models.
For how to run the tests, see [README.md](README.md).

## Summary

| | |
| --- | --- |
| Instructions in the decoder ([instruction_decode.py](../../punxa_6502/instruction_decode.py)) | 56 mnemonics, 151 opcode/mode pairs |
| Instructions with a test file | **53 mnemonics, 148 pairs** |
| Test cases | 468 |
| SingleCycle full suite | **53/53 PASS** |
| Hybrid full suite | **53/53 PASS** |
| Microcoded full suite | Not run ([validation limitations](#validation-limitations)) |
| Instructions without a test | 3 mnemonics, 3 pairs ([list below](#instructions-without-a-test)) |

Every addressing mode of each of the 53 tested instructions runs as the target
instruction in its own file. This was confirmed on SingleCycle by recording the
opcodes that actually executed during a full run.

## How the tests check results

- Expected values are fixed constants. A test never uses the instruction under
  test to compute its own expected result.
- Flags are captured with `PHP` right after the target instruction, and the
  whole status byte is compared (N, V, D, I, Z, C, plus B and bit 5 as pushed
  by PHP).
- Cases that check the stack (ROL cases 13-16, PLP cases 14-15) do not use
  `PHP` after the target instruction, because PHP would overwrite the stack slot
  being checked.
- Most tests also check that registers and memory the instruction should not
  touch are unchanged (A, X, Y, SP, neighbouring bytes, guard bytes).
- Decimal mode is never tested. Tests that do arithmetic clear D first.
- I=0 at program start is the simulator's reset value. Tests that need I=1 set
  it with `SEI`.

Mode names: `#` immediate, `zp` zero page, `abs` absolute, `rel` relative,
`imp` implied, `A` accumulator. All 8 modes = `#`, `zp`, `zp,X`, `abs`, `abs,X`,
`abs,Y`, `(zp,X)`, `(zp),Y`.

## Tested instructions

| Group | Instruction | Test file | Modes tested | Cases | Main checks |
| --- | --- | --- | --- | --- | --- |
| Load/store | LDA | [test_data_LDA.asm](isa/test_data_LDA.asm) | all 8 | 37 | A, N/Z, other flags preserved; indexed and indirect address boundaries |
| Load/store | LDX | [test_data_LDX.asm](isa/test_data_LDX.asm) | `#`, `zp`, `zp,Y`, `abs`, `abs,Y` | 15 | X, N/Z |
| Load/store | LDY | [test_data_LDY.asm](isa/test_data_LDY.asm) | `#`, `zp`, `zp,X`, `abs`, `abs,X` | 12 | Y, N/Z, other state preserved; zp,X wrap, abs,X page crossing |
| Load/store | STA | [test_data_STA.asm](isa/test_data_STA.asm) | all 8 except `#` | 10 | Stored byte and address, guard bytes, A and flags unchanged |
| Load/store | STX | [test_data_STX.asm](isa/test_data_STX.asm) | `zp`, `zp,Y`, `abs` | 8 | Stored byte and address, zp,Y wrap, X and flags unchanged |
| Load/store | STY | [test_data_STY.asm](isa/test_data_STY.asm) | `zp`, `zp,X`, `abs` | 8 | Stored byte and address, zp,X wrap, Y and flags unchanged |
| Transfer | TAX, TAY, TXA, TYA | [TAX](isa/test_data_TAX.asm), [TAY](isa/test_data_TAY.asm), [TXA](isa/test_data_TXA.asm), [TYA](isa/test_data_TYA.asm) | `imp` | 6, 7, 7, 7 | Destination, N/Z, source and other state preserved; chained transfers |
| Transfer | TSX | [test_data_TSX.asm](isa/test_data_TSX.asm) | `imp` | 7 | SP to X, N/Z, SP unchanged |
| Transfer | TXS | [test_data_TXS.asm](isa/test_data_TXS.asm) | `imp` | 7 | X to SP, all flags unchanged; checked through fixed stack writes |
| Stack | PHA | [test_data_PHA.asm](isa/test_data_PHA.asm) | `imp` | 4 | Pushed byte, address, SP decrement and wrap, flags |
| Stack | PHP | [test_data_PHP.asm](isa/test_data_PHP.asm) | `imp` | 9 | Full pushed status byte (B and bit 5 = 1), SP, stack wrap |
| Stack | PLA | [test_data_PLA.asm](isa/test_data_PLA.asm) | `imp` | 5 | Pulled byte, SP, N/Z |
| Stack | PLP | [test_data_PLP.asm](isa/test_data_PLP.asm) | `imp` | 15 | Each flag restored separately, B and bit 5 ignored, SP and $FF to $00 wrap, pulled byte not written back, A/X/Y and guards |
| Arithmetic | ADC | [test_arith_ADC.asm](isa/test_arith_ADC.asm) | all 8 | 15 | Binary A, C/Z/N/V |
| Arithmetic | SBC | [test_arith_SBC.asm](isa/test_arith_SBC.asm) | all 8 | 15 | Binary A, C (borrow), Z/N/V; zp,X wrap, page crossing |
| Compare | CMP | [test_arith_CMP.asm](isa/test_arith_CMP.asm) | all 8 | 10 | C/Z/N, A unchanged, V/D preserved |
| Compare | CPX | [test_arith_CPX.asm](isa/test_arith_CPX.asm) | `#`, `zp`, `abs` | 12 | Equal/less/greater, C/Z/N, incoming C ignored, A/X/Y/SP and operand unchanged |
| Compare | CPY | [test_arith_CPY.asm](isa/test_arith_CPY.asm) | `#`, `zp`, `abs` | 12 | Same checks as CPX, for Y |
| Inc/dec | INC, DEC | [INC](isa/test_arith_INC.asm), [DEC](isa/test_arith_DEC.asm) | `zp`, `zp,X`, `abs`, `abs,X` | 5, 8 | Memory result, N/Z, guards, other state preserved |
| Inc/dec | INX, INY, DEX, DEY | [INX](isa/test_arith_INX.asm), [INY](isa/test_arith_INY.asm), [DEX](isa/test_arith_DEX.asm), [DEY](isa/test_arith_DEY.asm) | `imp` | 6, 6, 8, 6 | Register result, 8-bit wrap, N/Z, other state preserved |
| Logic | AND | [test_logic_AND.asm](isa/test_logic_AND.asm) | all 8 | 10 | A, N/Z, C/V/D preserved |
| Logic | ORA | [test_logic_ORA.asm](isa/test_logic_ORA.asm) | all 8 | 15 | A, N/Z, other state preserved; zero-page pointer wrap |
| Logic | EOR | [test_logic_EOR.asm](isa/test_logic_EOR.asm) | all 8 | 15 | A, N/Z, other state preserved, operand not written; zp,X wrap, page crossing, pointer wrap |
| Logic | BIT | [test_logic_BIT.asm](isa/test_logic_BIT.asm) | `zp`, `abs` | 10 | N/V from memory bits 7/6, Z from A AND M, each flag independently; A, C/D/I and memory unchanged |
| Shift | ASL | [test_bitmap_ASL.asm](isa/test_bitmap_ASL.asm) | `A`, `zp`, `zp,X`, `abs`, `abs,X` | 9 | Result, C/N/Z, memory write-back |
| Shift | LSR | [test_bitmap_LSR.asm](isa/test_bitmap_LSR.asm) | `A`, `zp`, `zp,X`, `abs`, `abs,X` | 12 | Result, C = old bit 0, N = 0, incoming C not shifted in; write-back, A kept, guards |
| Shift | ROR | [test_bitmap_ROR.asm](isa/test_bitmap_ROR.asm) | `A`, `zp`, `zp,X`, `abs`, `abs,X` | 12 | Result, carry in and out, N/Z; write-back, A kept, guards |
| Shift | ROL | [test_bitmap_ROL.asm](isa/test_bitmap_ROL.asm) | `A`, `zp`, `zp,X`, `abs`, `abs,X` | 16 | Result, carry in and out, N/Z, V unchanged; write-back, A kept; stack slot and SP unchanged |
| Branch | BCC, BCS, BEQ, BMI, BNE, BVC, BVS | [BCC](isa/test_ctrflow_BCC.asm), [BCS](isa/test_ctrflow_BCS.asm), [BEQ](isa/test_ctrflow_BEQ.asm), [BMI](isa/test_ctrflow_BMI.asm), [BNE](isa/test_ctrflow_BNE.asm), [BVC](isa/test_ctrflow_BVC.asm), [BVS](isa/test_ctrflow_BVS.asm) | `rel` | 8, 8, 6, 8, 8, 8, 8 | Taken and not taken, forward and backward, page crossing, +127/-128, flags unchanged |
| Jump | JMP | [test_ctrflow_JMP.asm](isa/test_ctrflow_JMP.asm) | `abs`, `(abs)` | 7 | Target address; `($xxFF)` reads its high byte from `$xx00` (NMOS behaviour) |
| Jump | JSR, RTS | [JSR](isa/test_ctrflow_JSR.asm), [RTS](isa/test_ctrflow_RTS.asm) | `abs`, `imp` | 3, 4 | Return address on the stack, SP, nesting, flags |
| Flags | CLC, SEC | [CLC](isa/test_mcu_CLC.asm), [SEC](isa/test_mcu_SEC.asm) | `imp` | 3, 3 | Target flag, other flags and A preserved |
| Flags | CLD, SED | [CLD](isa/test_mcu_CLD.asm), [SED](isa/test_mcu_SED.asm) | `imp` | 6, 6 | Target flag, other flags and A/X/Y/SP preserved |
| Flags | CLI, SEI | [CLI](isa/test_mcu_CLI.asm), [SEI](isa/test_mcu_SEI.asm) | `imp` | 3, 3 | I flag, other flags preserved (CLI uses SEI to set I=1) |
| Flags | CLV | [test_mcu_CLV.asm](isa/test_mcu_CLV.asm) | `imp` | 4 | V flag, other flags preserved, including I=1 |
| Other | NOP | [test_mcu_NOP.asm](isa/test_mcu_NOP.asm) | `imp` | 6 | PC advances by one, consecutive NOPs, registers, flags and memory unchanged |

## Instructions without a test

These 3 instructions are in the decoder but have no test file.

| Instruction | Modes | SingleCycle | Hybrid and Microcoded |
| --- | --- | --- | --- |
| BPL | `rel` | Not implemented | Implemented, untested |
| BRK, RTI | `imp` | Not implemented | Implemented, untested |

The Hybrid and Microcoded models share one control unit
([control_unit.py](../../punxa_6502/algorithmic/control_unit.py)). "Not
implemented" means the CPU stops with `op XX not handled`, in both SingleCycle
and the control unit.

## Coverage gaps

These behaviours are not tested by any file:

- Decimal mode (BCD) for ADC and SBC.
- Interrupts (IRQ, NMI, BRK/RTI) and reset behaviour.
- Setting I=1 with RTI (SEI and PLP are tested).
- Addresses or branch targets that wrap past `$FFFF`.
- Timing (number of clock cycles per instruction).
- Exhaustive input values. The tests use chosen boundary values.

## Known issues

These are problems in how instructions behave. None of them make a test fail.

| Area | Issue | Location |
| --- | --- | --- |
| SingleCycle | `abs,X` and `abs,Y` do not wrap at 16 bits, so `$FFFF,X` gives an address above 64 KiB. | [singlecycle_processor.py](../../punxa_6502/algorithmic/singlecycle_processor.py), lines 179 and 186 |
| SingleCycle | Taken branches do not wrap the PC at `$FFFF`. | same file, lines 296-343 |
| Hybrid and Microcoded | ASL, LSR and ROR in `abs` and `abs,X` save A at `$0100+SP` (`pushA`/`popA`), so they overwrite the free stack slot. The tests do not detect it, because the `PHP` flag capture writes the same slot afterwards. | [control_unit.py](../../punxa_6502/algorithmic/control_unit.py), `executeASL_ABS`, `executeLSR_ABS`, `executeROR_ABS` and their `abs,X` versions |

## Validation limitations

These limit what the tests can check. They are not instruction results.

- **Microcoded model.** The ISA suite does not run on it, so its instructions
  are not validated by execution:
  - The microcoded control unit has no `getRetiredInstructions()`, which the
    runners use to step one instruction at a time.
  - With py4hw `29e7969`, the microcode subroutine stack also overflows
    (`push, full`) on the first instruction.
  - Building the model needs py4hw `13d7cdb` or later, which still reports
    version 2026.9.

  The microcode ROM is generated from the same control unit as the Hybrid
  model, and it builds without errors (1671 of 2048 lines). The Hybrid results
  above therefore cover the control-unit logic, but not the microcode sequencer.
- **Test tooling.** `test_runner_assembly.py` and `test_testbench.py` (79 failures) and `test_multicycle_testbench.py` (7 failures) call runner functions such as `execute_test` that were removed from the runners in commit `4b310c9`. `test_assembly.py` passes. The `.asm` suites are not affected.

Limitations of the multi-cycle implementation are listed in
[MULTICYCLE_COMPATIBILITY.md](MULTICYCLE_COMPATIBILITY.md#limitations). That
file was written before the control unit moved to `algorithmic/control_unit.py`.

## History

The suite was built in stages (Phase A and Batches 1-6, then the instructions
added on 2026-11-10 and 2026-11-11, and BCS, BMI, BIT, ROL, PLP and NOP added
on 2026-11-19). The batch notes are kept in
[BATCH6_SUMMARY.md](BATCH6_SUMMARY.md) and [LDA_REVIEW.md](LDA_REVIEW.md).
The pass/fail numbers in those notes are historical. Many failures recorded
there were fixed later, and the current results above replace them. Earlier
versions of this file are in the Git history.
