# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 17:32:10 2025

@author: dcr
"""
import punxa_6502

_ci_cpu = None
_ci_mem = None


def list_commands():
    print('punxa interactive commands:')
    #print('  loadProgram - load a program (elf) in memory')
    #print('  checkpoint  - save the system state in a file')
    #print('  restore     - restore the system state from a file')
    #print('  run         - run the system for a number of clock cycles')
    print('  step        - run an instruction step')
    #print('  tbreak      - set a temporal breakpoint (PC address)')
    #print('  go          - run until the temporal breakpoint is hit')
    print('  regs        - display the core registers of the processor')
    #print('  reportCSR   - display the content of CSRs')
    #print('  console     - display the content of the console')
    #print('  stack       - display the stack from [current] thread')
    print('  dump        - dump (hex) the content of data memory locations')
    
    
    
def dump(address, size=0x100, mem_base=0):
    memory = _ci_mem
    pos = address 
    for i in range((size+15)//16):
        sline = ''
        print('{:016X}:|'.format(pos), end='')
        for j in range(16):
            value = memory.readByte(pos-mem_base)
            print('{:02X}'.format(value), end='')
            if (value >= 32 and value < 127):
                sline += chr(value)
            else:
                sline += '·'
            pos += 1
            
        print('| "{}"'.format(sline))
#    memory.write(32*4+0x00, 0xfe010113) # addi    sp,sp,-32
#    memory.write(32*4+0x04, 0x00112e23) # sw      ra,28(sp)


def step(num=1):
    global hw
    cpu = _ci_cpu
    sim = cpu.parent.getSimulator()
    
    while (num > 0):
        ret = cpu.getRetiredInstructions()
        
        while (ret == cpu.getRetiredInstructions()):
            sim.clk()        

        num -= 1
        
def regs():
    cpu = _ci_cpu
    
    pc = cpu.getRegister('PC')
    a = cpu.getRegister('A')
    x = cpu.getRegister('X')
    y = cpu.getRegister('Y')
    sp = cpu.getRegister('SP')
    
    print(f'PC= {pc:04X}')    
    print(f' A=   {a:02X}')    
    print(f' X=   {x:02X}')    
    print(f' Y=   {y:02X}')    
    print(f'SP=   {sp:02X}')    
    