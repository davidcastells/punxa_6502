# MultiCycle compatibility

Updated 2026-11-11. This file describes the MultiCycle model
([multicycle_processor.py](../../punxa_6502/structural/multicycle_processor.py))
and its known limitations. For test coverage, see [COVERAGE.md](COVERAGE.md).

## Status

- **47/47 ISA test files pass**, the same result as SingleCycle.
- Every opcode/mode pair covered by the suite (137 pairs) runs on MultiCycle.
- One-off cross-check on 2026-11-11: the two models were run side by side on
  all 47 files. After every instruction, PC, A, X, Y, SP and the N/V/D/I/Z/C
  flags were compared, and all 64 KiB of memory was compared at the end of each
  file. The only differences were:
  - the SingleCycle DEC flag issue (see [COVERAGE.md](COVERAGE.md#known-issues));
  - the temporary stack write described under limitation 1 below.

  The comparison script is not part of the repository.

## How the model is built

- **Datapath (`DataPathStructural`).** Structural py4hw and synthesizable.
  - Registers: A, X, Y, SP, PC, MAR, MBR, IR and the flags.
  - An 8-bit ALU (`ALUStructural` in
    [alu.py](../../punxa_6502/structural/alu.py)).
  - One shared data bus.
- **Control unit (`ControlUnit6502Behavioral`).** Behavioral.
  - Every instruction is a Python generator. Each `yield` is one clock cycle.
  - `decodeAndExecute()` selects an `execute<MNEMONIC>_<MODE>()` method
    from the opcode.
  - Opcodes that have no method stop the CPU with `op XX not handled`.
- **ALU input A is wired to the A register.** To operate on X, Y or a memory
  byte, the control unit first parks A somewhere else, does the operation, and
  then restores A:
  - zero-page and immediate forms park A in an unused MAR byte;
  - absolute forms of ASL, LSR and ROR park A on the stack (see limitation 1).

## Instructions added on 2026-11-11

These were added to the control unit only. The datapath and ALU were not
changed.

| Instruction | How it is implemented |
| --- | --- |
| EOR (all 8 modes) | Same address sequences as ORA, with the ALU's XOR operation (new helper `aluXOR_MBR`). |
| LSR (`A`, `zp`, `zp,X`, `abs`, `abs,X`) | Clear C, then use the existing rotate-right (ROR) path. Rotating with C=0 gives the logical shift: bit 7 = 0, C = old bit 0, N = 0. |
| CPX (`#`, `zp`, `abs`) | Same as CPY: park A, copy X into A, compare, restore A. |
| BVC, BVS | Same as BCC, testing V instead of C. |
| SEI, CLI | Set or clear I through the existing `d_I`/`e_I` controls. |
| CLV | Clear V by selecting the control-unit value (`sel_V=1`, `d_V=0`) for one cycle. `sel_V` is then reset to 0, because ADC and SBC need the ALU's overflow. |

## Instruction support

| Status | Instructions |
| --- | --- |
| Implemented and tested | The 47 instructions in [COVERAGE.md](COVERAGE.md#tested-instructions), all their addressing modes |
| Implemented, not tested | BPL, BRK, RTI |
| Not implemented (`op XX not handled`) | BCS, BMI, BIT, ROL, PLP, NOP |

## Limitations

1. **Absolute read-modify-write forms write to the stack.**
   - **Which instructions:** `ASL`, `LSR` and `ROR` in `abs` and `abs,X` mode.
   - **What happens:** they save A with a push to `$0100+SP` and restore it
     with a pull. The free stack byte at `$0100+SP` is left holding the value
     of A. SP itself ends unchanged.
   - **Difference from a real 6502:** a real 6502 does not write to the stack
     here.
   - **When it matters:** programs that only use the stack through push and
     pull are not affected. Only code that reads a byte below SP after one of
     these instructions would see the difference. The test suite does not do
     this.
   - **Not affected:** the zero-page forms and INC/DEC.
   - **What a fix needs:** somewhere other than the stack to keep A during the
     operation, which means a datapath change.
2. **Timing is not cycle-accurate.** Instructions take more clock cycles than
   on a real 6502. The slowest tested instruction is LSR `abs,X` at 50 clocks.
   The test runner allows 100 clocks per instruction.
3. **No decimal mode.** ADC and SBC ignore the D flag and always use binary
   arithmetic. The suite does not test decimal mode.
4. **Interrupts and reset.**
   - The `irq` and `nmi` inputs are not connected to the control unit.
   - The reset sequence runs only once, at startup. The test runner builds a
     new CPU for every file.
   - After reset, I is 0. A real NMOS 6502 sets I to 1.

## Test tooling

- **Runner:** [tb_ISA_tests_Multicycle.py](tb_ISA_tests_Multicycle.py).
- **Legacy files:** [multicycle_adapter.py](multicycle_adapter.py) and
  [test_multicycle_testbench.py](test_multicycle_testbench.py). They call
  `execute_test`, which no longer exists in the runner, so
  `test_multicycle_testbench.py` reports 7 failures. These failures are
  unrelated to the CPU.

## History

The Phase B3 review (2026-10-22) listed many missing MultiCycle instructions and
defects. Examples include missing CLD/PHP/SEC/SED, missing addressing modes,
AND/OR selecting the adder result, the JSR/RTS byte order, and PLA/TSX/TXA not
updating flags. All of these are now covered by passing tests. The exception is
the runtime reset issue, which is limitation 4 above. The old B3 tables are
available in the Git history of this file.
