# MultiCycle formal ISA compatibility — Phase B3

Local source review and execution on feature/6502-isa-tests, 2026-10-22.
Execution evidence: [final B3 report](results/phase_b3_2026-10-22_03/REPORT.md)
and summary.json in that directory. Original files were not changed.

## Runtime versus static assessment

Original17: one unique file attempted in B3: LDX = UNSUPPORTED_CPU during
initialization, not an LDX assertion FAIL. The other16 are NOT_RUN in B3.
CLC's actual B2 unsupported result is retained as historical evidence only.
All17 have static CPU blockers; none currently reaches its intended assertions.
The runner retains ERROR as the top-level category and UNSUPPORTED_CPU in its
detail; the table uses UNSUPPORTED_CPU as the requested compatibility outcome.

New shared file test_data_LDA_Immediate.asm: PASS on both models. Five target
cases, one target mnemonic/mode (LDA immediate $A9), A and Z checked; N and
preserved flags not formally covered. Helpers do not count as formal targets.

Notation: G8=#,zp,zp,X,abs,abs,X,abs,Y,(zp,X),(zp),Y; G7=G8 without #;
M4=zp,zp,X,abs,abs,X. C/Z/N/V/D/I are the real flags. Full P also checks PHP
B/unused stack representation; this does not require a physical B register.

Common setup S=LDX#/TXS, CLD, LDA#/STA abs (case/result writes).
LDX instead bootstraps through LDA#/TAX/TXS/CLD. Additional setup below is
in addition to S. Common JMP abs reporting is omitted from helper cells.
Every original file requires missing CLD/PHP, so removing just CLD is insufficient.

| Original file | Target / required modes | Additional setup | Assertion helpers | Flags checked | Additional CPU limitations | B3 actual outcome | Intended assertions reachable? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| test_data_LDA.asm | LDA/G8 | LDY#, CLC/SEC, ADC#, SED, pointer RAM | PHP/PLA, AND#, CMP#, BEQ | N/Z; selected C/V/D preservation | Missing zp,X/abs,Y/(zp,X) dispatch, SEC/SED/AND#; V/D state; indexed addressing | NOT_RUN | No, static startup blocker |
| test_data_LDX.asm | LDX/#,zp,zp,Y,abs,abs,Y | Bootstrap above; TAX, LDY#, STA RAM | STX abs, PHP/PLA, AND#, CMP#, BEQ | N/Z | Missing zp,Y/abs,Y, AND# | UNSUPPORTED_CPU: $D8, clock41, retired3, PC0204 | No, observed startup blocker |
| test_data_STA.asm | STA/G7 | STX zp/abs, LDY#, CLC/SEC, SED | PHP/PLA, AND#, LDA memory, CMP#, BEQ; guards | C/Z/N/V/D/I preservation | Missing abs,X/abs,Y/(zp,X), SEC/SED/AND#; LDY C write; indexed addressing | NOT_RUN | No, static startup blocker |
| test_arith_ADC.asm | ADC/G8 | CLC/SEC, LDY#, STX/pointer RAM | PHP/PLA, AND#, CMP#, BEQ | C/Z/N/V, D=0 | Only # dispatched; missing V; arithmetic flag timing suspect | NOT_RUN | No, static startup blocker |
| test_arith_CMP.asm | CMP/G8 | ADC#, CLC/SEC, SED, LDY#, STX | PHP/PLA, ADC#/CLC/BNE equality oracle | C/Z/N, V/D/I preservation, full P | Only # dispatched; SEC/SED/V/D; ADC helper uncertain | NOT_RUN | No, static startup blocker |
| test_logic_AND.asm | AND/G8 | ADC#/CMP# flag seeding, SED, LDY#, STX | PHP/PLA, CMP#, BNE | N/Z; C/V/D/I preservation, full P | Only zp dispatched, ALU routes addition, missing final PC increment | NOT_RUN | No, static startup blocker |
| test_ctrflow_BNE.asm | BNE/rel | ADC#, CLC/SEC, SED | PHP/PLA, AND#, CMP#, BEQ | All six flags preserved | SEC/SED/AND#, V/D/I state; ADC helper uncertain | NOT_RUN | No, static startup blocker |
| test_ctrflow_BEQ.asm | BEQ/rel | ADC#/CMP# flag seeding, SED | PHP/PLA, CMP#, BNE | Full P preserved | SED, V/D/I state; ADC helper uncertain | NOT_RUN | No, static startup blocker |
| test_mcu_CLC.asm | CLC/imp | ADC#/CMP# flag seeding, SED | PHP/PLA, CMP#, BNE | C cleared; others preserved, full P | Third case requires V/D=1; ADC helper uncertain | NOT_RUN (B2: unsupported CLD) | No, static startup blocker |
| test_mcu_SEC.asm | SEC/imp | ADC#/CMP# flag seeding, SED | PHP/PLA, CMP#, BNE | C set; others preserved, full P | SEC has no dispatch; V/D state; ADC helper uncertain | NOT_RUN | No, static startup blocker |
| test_arith_INX.asm | INX/imp | ADC#/CMP# flag seeding | PHP/STX/PLA, CMP#, BNE | N/Z; C/V/D/I preservation, full P | INX writes C; V state; ADC helper uncertain | NOT_RUN | No, static startup blocker |
| test_arith_INC.asm | INC/M4 | ADC#/CMP# flag seeding, SED, LDY#, STX | PHP/PLA, LDA memory, CMP#, BNE; guards | N/Z; C/V/D/I preservation, full P | Only abs dispatched; INC writes C; indexed addressing | NOT_RUN | No, static startup blocker |
| test_bitmap_ASL.asm | ASL/A+M4 | ADC#/CMP# flag seeding, STX | PHP/PLA, LDA memory, CMP#, BNE; guards | C/N/Z; V/D/I preservation, full P | No ASL execution dispatch; V state; ADC helper uncertain | NOT_RUN | No, static startup blocker |
| test_data_PHA.asm | PHA/imp | Explicit SP, ADC#/CMP#, SED, stack guards | PHP/TSX/STX, LDA stack, CMP#, BNE (no PLA oracle) | Full P preserved | PHP/SED/V/D state; helper validation needed | NOT_RUN | No, static startup blocker |
| test_data_PLA.asm | PLA/imp | Explicit SP and RAM frames, ADC#/CMP#, SED | PHP/TSX/STX, LDA stack, CMP#, BNE (no PLA oracle) | N/Z; other flags preserved, full P | PLA omits N/Z update; V/D state | NOT_RUN | No, static startup blocker |
| test_ctrflow_JSR.asm | JSR/abs | Explicit SP, ADC#/CMP#, SED | PHP/TSX/STX, LDA stack, CMP#, BNE | Full P preserved | Return-address stack byte order reversed | NOT_RUN | No, static startup blocker |
| test_ctrflow_RTS.asm | RTS/imp | Manual frames; final nested JSR, ADC#/CMP#, SED | PHP/TSX/STX, LDA stack, CMP#, BNE | Full P preserved | Pop byte order reversed; JSR errors can compensate | NOT_RUN | No, static startup blocker |

INX and ASL source macros contain conditional SED, but their current calls use
D=0; SED is not counted as an executed dependency for those two files.

## CPU compatibility and issue register

M below is [structural/multicycle_processor.py](../../punxa_6502/structural/multicycle_processor.py).
Line numbers refer to the current source. Every issue requires separate CPU
work to remedy; none was fixed, bypassed or exempted in B3.
Static findings are not dynamically confirmed instruction failures.

| ID / kind | Affected behavior / NMOS expectation | Current implementation evidence | Runtime evidence | Impact / CPU change needed |
| --- | --- | --- | --- | --- |
| M1 missing | CLD clears D; PHP pushes status without changing real flags | Constants exist, no execution branches: M:2014-2107 | CLD $D8 actual unsupported in B3 LDX at0204; B2 CLC at0203. PHP not reached | Blocks all17 startup/checking; yes |
| M2 missing | SEC sets C; SED sets D; AND# computes conjunction | No SEC/SED/AND# dispatch, M:2014-2107 | Not run | Setup/mask helpers and SEC target; yes |
| M3 missing | V/D/I state and appropriate updates; PHP synthesizes B/bit5 stack bits | q/d declarations237-248, only C/Z/N Reg311-313 | Not run; undriven I=0 is not implementation proof | Full-P and preservation tests; yes |
| M4 missing modes | Each required target opcode must execute its own addressing semantics | Dispatch2014-2107: LDA5/8, LDX3/5, STA4/7, ADC1/8, CMP1/8, AND1/8, INC1/4, ASL0/5 | Only new LDA# executed; missing modes not exercised | Cannot reuse full multi-mode files; yes |
| D1 static defect | AND/OR/XOR are bitwise operations | Actual ALUStructural instantiated300; results166-168 all select add_r | Not run | Logic target and AND helpers; yes |
| D2 static defect | JSR pushes return high then low; RTS pulls low then high and adds1 | JSR1269-1270 pushes low/high; RTS1308-1309 pops high/low | Not run | Independent stack-layout checks would expose errors; yes |
| D3 static defect | PLA updates N/Z from pulled A | executePLA1302-1305 and popA1948-1961 never save flags | Not run on MultiCycle | PLA target and helper semantics; yes |
| D4 static defect | INX/INC update N/Z, preserve C | incMBR1844 and incX1861 enable C | Not run | Increment flag-preservation checks; yes |
| D5 static defect | Index address addition excludes architectural C | addX_to_MAR1675, addY_to_MAR1709 use OP_ADD; ALU139/151 adds q_C | Not run | Indexed modes may address base+index+C; yes |
| D6 static defect | LDY preserves C | fetchY705 enables C with bypass ALU | Not run | STA's flag seeding and index helpers; yes |
| D7 static defect | TSX/TXA update N/Z | executeTSX1402-1405 and TXA1407-1413 omit flag saves | Not run | Future transfer tests; stack checker snapshots P before TSX, so do not assume it invalidates that snapshot; yes |
| D8 static defect | AND/ORA zp advance to next opcode | AND1008-1017, ORA1286-1295 omit final incPC; ORA1292 also accesses absent status[q_A] (exports252-259) | Not run | Wrong subsequent fetch / possible KeyError; yes |
| D9 static suspicion | ADC flags reflect the same addition that produced A | executeADC995-1000 calls aluADD_MBR1430-1438, clears operand select, then saves flags1653-1662 | Not run | ADC arithmetic/helper oracle cannot yet be trusted; investigate and fix if confirmed |
| I1 implementation limitation | A reusable reset must restart controller coherently | reset input589 not tested by coroutine; resetCycle613 runs only at startup | B1/B2 initial construction works; runtime reset not tested | Fresh CPU per file avoids relying on runtime reset; CPU change for full reset |

No MultiCycle defect was dynamically inferred from SingleCycle LDA30-32,
INX/INC/ASL/PLA failures. Its zero-page pointer helper incMAR_lo1792 differs.
No new dynamic MultiCycle target defect was reproduced in this phase; only
CLD's missing implementation was observed. Helper CMP/BEQ/BNE behavior was
verified locally for equality/inequality and taken/not-taken paths, not all
their modes, Flags or displacement boundaries.

## Smallest useful next CPU work (proposal only)

1. Shared gates: real D state + CLD/SED; PHP stack representation with C/Z/N/V/D/I
   and correct SP; establish explicit initial-I semantics. Merely adding no-op
   CLD/PHP dispatch is insufficient. No test expectations should be changed.
2. Make the actual setup/checking subset reliable: ADC# result/C/Z/N/V timing,
   CMP# (including carry for flag seeding), SEC, correct AND# (dispatch plus ALU), and stack read/write behavior.
   This enables meaningful CLC/SEC/PHA/BEQ/BNE candidate files after checking
   each full dependency list. For the first unchanged CLC file specifically,
   SEC/AND# are not required: prioritize CLD/SED, PHP/stack, ADC#/V, CMP#/C
   and real status representation with its existing LDX#/TXS/PLA helpers.
   CLC case3 requires V/D set and preserved.
3. Repair target-specific defects and add missing modes in small groups:
   PLA and JSR/RTS; load/store indexed/indirect paths; INC/INX; logic and ASL.
   Verify address calculation without consuming C. Do not assume all17 become
   runnable once the common startup blocker is removed.

CPU changes require separate discussion/authorization with David. Stop B3;
do not automatically implement these features or start Phase C.
