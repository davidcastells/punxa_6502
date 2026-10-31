# Testing 6502 ISA

We implemented some instruction tests in assembler in a similar way that RISC-V ISA tests are implemented (and was done in Punxa to verify the repertory).

In punxa_6502 we provide assembler code that we assemble with our own assembler.

To run the tests do

```
python tb_ISA_tests.py -c "runAllTests()"
```

***Summary***

<pre>
test_arith      70.0 %   |████████████████████████████████░░░░░░░░░░░░░|
test_bitmap     0.0 %    |░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
test_ctrflow    83.3 %   |██████████████████████████████████████░░░░░░░|
test_data       87.5 %   |████████████████████████████████████████░░░░░|
test_logic      50.0 %   |███████████████████████░░░░░░░░░░░░░░░░░░░░░░|
test_mcu        100.0 %  |█████████████████████████████████████████████|
</pre>

The detailed current output is:

```
Test test_arith_ADC.asm             = OK
Test test_arith_CMP.asm             = OK
Test test_arith_CPY.asm             = OK
Test test_arith_DEC.asm             = OK
Test test_arith_DEX.asm             = OK
Test test_arith_DEY.asm             = OK
Test test_arith_INC.asm             = FAILED - Failed in test case 5
Test test_arith_INX.asm             = FAILED - Failed in test case 5
Test test_arith_INY.asm             = FAILED - Failed in test case 2
Test test_arith_SBC.asm             = OK
Test test_bitmap_ASL.asm            = FAILED - Failed in test case 4
Test test_bitmap_ROR.asm            = FAILED - Failed in test case 9
Test test_ctrflow_BCC.asm           = OK
Test test_ctrflow_BEQ.asm           = OK
Test test_ctrflow_BNE.asm           = OK
Test test_ctrflow_JMP.asm           = FAILED - Failed in test case 5
Test test_ctrflow_JSR.asm           = OK
Test test_ctrflow_RTS.asm           = OK
Test test_data_LDA.asm              = FAILED - Failed in test case 30
Test test_data_LDA_Immediate.asm    = OK
Test test_data_LDX.asm              = OK
Test test_data_LDY.asm              = OK
Test test_data_PHA.asm              = OK
Test test_data_PHP.asm              = OK
Test test_data_PLA.asm              = FAILED - Failed in test case 1
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
Test test_logic_ORA.asm             = FAILED - Failed in test case 13
Test test_mcu_CLC.asm               = OK
Test test_mcu_CLD.asm               = OK
Test test_mcu_SEC.asm               = OK
Test test_mcu_SED.asm               = OK
Total: 40 Correct: 31 (77.5 %)
```
