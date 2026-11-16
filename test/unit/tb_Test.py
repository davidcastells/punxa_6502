# -*- coding: utf-8 -*-
"""
Created on Wed May 28 13:42:54 2025

@author: 2016570
"""
import py4hw


import punxa_6502 as punxa

from punxa_6502.interactive_commands import *


def buildHw(model):
    global hw
    global cpu
    global mem
    
    hw = py4hw.HWSystem()
    
    reset = hw.wire('reset')
    irq = hw.wire('irq')
    nmi = hw.wire('nmi')
    
    mem_width = 8
    mem_base = 0
    
    port_c = punxa.MemoryInterface(hw, 'port_c', mem_width, 16)
    port_m = punxa.MemoryInterface(hw, 'port_m', mem_width, 22)
    
    memory = punxa.SparseMemory(hw, 'main_memory', mem_width, 32, port_m, mem_base=mem_base)
    
    bus = punxa.MultiplexedBus(hw, 'bus', port_c, [(port_m, mem_base),
                                          #(port_t, test_base),
                                          #(port_d, 0x01BFF00000),
                                          #(port_u, UART_BASE),
                                          #(port_p, 0xFFF1100000),
                                          #(port_l, 0xFFF1020000)
                                          ])
    
    
    if (model == 'sc'):
        cpu = punxa.SingleCycle6502(hw, 'cpu', port_c, reset, irq, nmi, 0)
    elif (model == 'mc'):
        cpu = punxa.MultiCycleAlgorithmicControlUnit6502(hw, 'cpu', port_c, reset, irq, nmi, 0)
    else:
        cpu = punxa.MultiCycle6502(hw, 'cpu', port_c, reset, irq, nmi, 0)
    
        seq = cpu.children['control'].children['seq']
        global wvf
        watch = py4hw.debug.getPorts(seq)
        watch.append(cpu.children['control']._wires['ins'])
        watch.append(cpu.children['control']._wires['sel_cond'])
        watch.append(cpu.children['control']._wires['dispatch'])
        wvf = py4hw.Waveform(hw, 'wvf', watch)
    
    
    memory.reallocArea(0, 0x3000)
    memory.reallocArea(0xFFF0, 0x10)
    
    parser = punxa.ParseHexFile('test.ihx')
        
    for line in parser.lines:
        linetype, address, data = parser.parseLine(line)
        
        #print(linetype, f'{address:04X}', data)
        
        if (linetype == 0x00):
            for i in range(len(data)):
                memory.writeByte(address+i, data[i])    
                
                
    # Load symbols
    symbols = punxa.readSymbols('test.map')
    
    for symbol, add in symbols:
        cpu.symbols[add] = symbol
        
    #for i in range(len(data)):
    #    memory.writeByte(i, data[i])
    #    if (i % 16 == 0):
    #        print(f'\nwriting {i:04X} =', end='')
    #    print(f'{data[i]:02X} ', end='')
    
    print()
    import punxa_6502.interactive_commands as cmd
    cmd._ci_mem = memory
    cmd._ci_cpu = cpu
    
    
    
    
buildHw('mic')
