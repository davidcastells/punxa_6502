# -*- coding: utf-8 -*-
"""
Self-checking ISA tests for the punxa 6502.

Same workflow as the ATmega328P version:

    # whole suite (from the isa_tests folder)
    python tb_ISA_tests.py -c "runAllTests()"

    # interactively (e.g. in Spyder / IPython)
    >>> prepareTest('test_data_LDA.asm')
    >>> step()                 # execute one instruction
    >>> hex(cpu.pc)
    >>> runTest('test_data_LDA.asm')

Every test is an .asm file in isa/ that must export three symbols:
    test_case     byte updated by the test with the scenario being checked
    final_result  byte: 1 = all passed, 255 = failed
    end           address of the instruction where the test finishes
"""

import contextlib
import math
import os
import sys
from pathlib import Path

import py4hw
import punxa_6502 as punxa
from punxa_6502.assembly import assemble_file
from punxa_6502.interactive_commands import *

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
ex_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'isa')

PROGRAM_START = 0x0200
MEMORY_SIZE = 0x10000
step_limit = 10000          # maximum instructions per test
MAX_CLOCKS_PER_INSTRUCTION = 100

# Leave empty to run every test_<group>_*.asm found in isa/.
# Or restrict it, e.g. ['test_data', 'test_arith'].
selected_prefixes = []

# Filled in by prepareTest(), so they can be inspected interactively
hw = None
cpu = None
mem = None
symbols = None


# --------------------------------------------------------------------------
# Building the system
# --------------------------------------------------------------------------
def prepareTest(file):
    """Assemble isa/<file>, build the CPU + 64 KiB memory and load the program."""
    global hw, cpu, mem, symbols

    program = assemble_file(Path(ex_dir) / file, origin=PROGRAM_START,
                            include_dirs=(Path(ex_dir),))
    symbols = dict(program.symbols)

    for name in ('test_case', 'final_result', 'end'):
        if name not in symbols:
            raise Exception(f"Test does not export symbol '{name}'")

    if PROGRAM_START + len(program.code) > MEMORY_SIZE:
        raise Exception('Program does not fit in memory')

    hw = py4hw.HWSystem()

    reset = hw.wire('reset')
    irq = hw.wire('irq')
    nmi = hw.wire('nmi')

    cpu_port = punxa.MemoryInterface(hw, 'cpu_port', 8, 16)
    mem_port = punxa.MemoryInterface(hw, 'mem_port', 8, 22)

    mem = punxa.SparseMemory(hw, 'main_memory', 8, 32, mem_port, mem_base=0)
    punxa.MultiplexedBus(hw, 'bus', cpu_port, [(mem_port, 0)])

    cpu = punxa.MultiCycle6502(hw, 'cpu', cpu_port, reset, irq, nmi, PROGRAM_START)
    
    # Load program and clear the result slots
    mem.reallocArea(0, MEMORY_SIZE, verbose=False)
    for offset, byte in enumerate(program.code):
        mem.writeByte(PROGRAM_START + offset, byte)
    mem.writeByte(symbols['test_case'], 0)
    mem.writeByte(symbols['final_result'], 0)

    import punxa_6502.interactive_commands as ci
    ci._ci_hw = hw
    ci._ci_cpu = cpu
    ci._ci_mem = mem
    
    return hw, cpu, mem, symbols


# # --------------------------------------------------------------------------
# # Running
# # --------------------------------------------------------------------------
# def step():
#     """Clock the CPU until one instruction has been retired."""
#     simulator = hw.getSimulator()
#     retired = cpu.getRetiredInstructions()

#     for _ in range(MAX_CLOCKS_PER_INSTRUCTION):
#         simulator.clk(1)
#         if cpu.getRetiredInstructions() != retired:
#             return

#     raise Exception('CPU did not retire an instruction')


def runTest(file, verbose=False):
    """Run one test. Returns normally if it passes, raises if it fails."""
    prepareTest(file)

    step_count = 0

    # The CPU prints an instruction trace; hide it unless verbose
    with open(os.devnull, 'w') as null:
        with contextlib.redirect_stdout(sys.stdout if verbose else null):
            while cpu.getRegister('PC') != symbols['end']:
                step()
                step_count += 1
                if step_count > step_limit:
                    raise Exception('Step count > limit')

    test_case = mem.readByte(symbols['test_case'])
    final_result = mem.readByte(symbols['final_result'])

    print('FINAL RESULT:', final_result, '\tTest case:', test_case)

    if final_result == 255:
        raise Exception(f'Failed in test case {test_case}')
    if final_result != 1:
        raise Exception(f'Protocol error: final_result = 0x{final_result:02X}')


def getPrefix(name):
    """test_data_LDA.asm -> test_data"""
    parts = name.split('_')
    return 'test_' + parts[1].lower() if len(parts) > 2 else 'uncategorized'


def computeAllTests():
    files = sorted(os.listdir(ex_dir), key=str.lower)
    files = [name for name in files
             if name.lower().endswith('.asm') and name.startswith('test_')
             and (not selected_prefixes
                  or any(name.startswith(p) for p in selected_prefixes))]

    ret = {}
    for f in files:
        print('Run test', f, end=' ')
        try:
            runTest(f)
            print('PASSED')
            ret[f] = 'OK'
        except Exception as e:
            print('FAILED')
            ret[f] = ('FAILED', e)

    return ret


def asciiProgressBar(n, t):
    p = n * 100 / t
    pl = 45
    pok = math.ceil(pl * n / t)
    pko = pl - pok

    sok = '█' * pok
    sko = '░' * pko
    sp = '{:.1f} %'.format(p)
    return '{:8} |{}{}|'.format(sp, sok, sko)


def runAllTests():
    ret = computeAllTests()

    prefixes = selected_prefixes or sorted({getPrefix(t) for t in ret})

    nOK = 0
    nTotal = 0
    groupResults = {}

    for prefix in prefixes:
        nOKGroup = 0
        nTotalGroup = 0

        for t in [name for name in ret if getPrefix(name) == prefix]:
            nTotal += 1
            nTotalGroup += 1
            if ret[t] == 'OK':
                print('Test {:30} = {}'.format(t, ret[t]))
                nOK += 1
                nOKGroup += 1
            else:
                print('Test {:30} = {} - {}'.format(t, ret[t][0], ret[t][1]))

        groupResults[prefix] = (nOKGroup, nTotalGroup)

    if nTotal == 0:
        print('No tests found in', ex_dir)
        return ret

    print('Total: {} Correct: {} ({:.1f} %)'.format(nTotal, nOK, nOK * 100 / nTotal))
    print(asciiProgressBar(nOK, nTotal))

    for prefix in prefixes:
        nOKGroup, nTotalGroup = groupResults[prefix]
        print('Group: {} Total: {} Correct: {} ({:.1f} %)'.format(
            prefix, nTotalGroup, nOKGroup, nOKGroup * 100 / max(nTotalGroup, 1)))

    for prefix in prefixes:
        nOKGroup, nTotalGroup = groupResults[prefix]
        print(f'{prefix:15}', asciiProgressBar(nOKGroup, max(nTotalGroup, 1)))

    return ret


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) > 1:
        if sys.argv[1] == '-c':
            eval(sys.argv[2])
            os._exit(0)
