# -*- coding: utf-8 -*-
"""
Created on Sun Nov  8 16:35:58 2026

@author: dcr
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

MEMORY_SIZE = 0x10000
step_limit = 10000          # maximum instructions per test


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
def buildHW():
    """Assemble isa/<file>, build the CPU + 64 KiB memory and load the program."""
    global hw, cpu, mem, symbols, wvf

    
    hw = py4hw.HWSystem()

    reset = hw.wire('reset')
    irq = hw.wire('irq')
    nmi = hw.wire('nmi')

    cpu_port = punxa.MemoryInterface(hw, 'cpu_port', 8, 16)
    mem_port = punxa.MemoryInterface(hw, 'mem_port', 8, 22)

    mem = punxa.SparseMemory(hw, 'main_memory', 8, 32, mem_port, mem_base=0)
    punxa.MultiplexedBus(hw, 'bus', cpu_port, [(mem_port, 0)])

    cpu = punxa.MultiCycle6502(hw, 'cpu', cpu_port, reset, irq, nmi, 0)
    
    
    return hw, cpu, mem


hw, cpu, mem = buildHW()

datapath = cpu.children['datapath']

gen = py4hw.VerilogGenerator(hw)
rtl = gen.getVerilogForHierarchy(datapath)

print(rtl)