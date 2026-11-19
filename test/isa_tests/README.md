# Testing 6502 ISA

We implemented some instruction tests in assembler in a similar way that RISC-V ISA tests are implemented (and was done in Punxa to verify the repertory).

In punxa_6502 we provide assembler source code that we assemble with our own assembler to avoid unnecessary external dependencies.

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
Test test_bitmap_ROL.asm            = OK
Test test_bitmap_ROR.asm            = OK
Test test_ctrflow_BCC.asm           = OK
Test test_ctrflow_BCS.asm           = OK
Test test_ctrflow_BEQ.asm           = OK
Test test_ctrflow_BMI.asm           = OK
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
Test test_data_PLP.asm              = OK
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
Test test_logic_BIT.asm             = OK
Test test_logic_EOR.asm             = OK
Test test_logic_ORA.asm             = OK
Test test_mcu_CLC.asm               = OK
Test test_mcu_CLD.asm               = OK
Test test_mcu_CLI.asm               = OK
Test test_mcu_CLV.asm               = OK
Test test_mcu_NOP.asm               = OK
Test test_mcu_SEC.asm               = OK
Test test_mcu_SED.asm               = OK
Test test_mcu_SEI.asm               = OK
Total: 53 Correct: 53 (100.0 %)
```

## Multi-cycle hybrid design

This model contains the datapath described with the structural py4hw design style and the control unit
described with the algorithmic py4hw design style ([control_unit.py](../../punxa_6502/algorithmic/control_unit.py)).
The datapath is synthesizable.


To run the tests do

```
python tb_ISA_tests_Hybrid.py -c "runAllTests()"
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
Test test_bitmap_ROL.asm            = OK
Test test_bitmap_ROR.asm            = OK
Test test_ctrflow_BCC.asm           = OK
Test test_ctrflow_BCS.asm           = OK
Test test_ctrflow_BEQ.asm           = OK
Test test_ctrflow_BMI.asm           = OK
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
Test test_data_PLP.asm              = OK
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
Test test_logic_BIT.asm             = OK
Test test_logic_EOR.asm             = OK
Test test_logic_ORA.asm             = OK
Test test_mcu_CLC.asm               = OK
Test test_mcu_CLD.asm               = OK
Test test_mcu_CLI.asm               = OK
Test test_mcu_CLV.asm               = OK
Test test_mcu_NOP.asm               = OK
Test test_mcu_SEC.asm               = OK
Test test_mcu_SED.asm               = OK
Test test_mcu_SEI.asm               = OK
Total: 53 Correct: 53 (100.0 %)
```

## Multi-cycle microcoded design

This model uses the same structural datapath. Its control unit is a microcode ROM generated from the
algorithmic control unit.

The ISA tests do not run on this model yet. The runner counts retired instructions with
`getRetiredInstructions()`, which the microcoded control unit does not provide. No results are reported
for this model. This is a limitation of the test setup, not a test result (see
[COVERAGE.md](COVERAGE.md#validation-limitations)).

```
python tb_ISA_tests_Multicycle.py -c "runAllTests()"
```

## More information

- [COVERAGE.md](COVERAGE.md): what each test checks, untested instructions and known issues.
- When redirecting the output to a file, use `python -u`: the runners end with `os._exit(0)`, which
  discards buffered output. On Windows, also set `PYTHONIOENCODING=utf-8` to print the progress bars.
