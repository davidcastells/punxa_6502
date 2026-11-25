# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 16:32:44 2025

@author: dcr
"""
import py4hw
import punxa_6502

from punxa_6502.structural.datapath import DataPathStructural
from .microcoding import MicrocodedControlUnit6502
   
        
class MultiCycle6502(py4hw.Logic):
    
    def __init__(self, parent, name:str, memory:punxa_6502.MemoryInterface, 
                 reset, irq, nmi, resetAddress):
        
        super().__init__(parent, name)

        self.reset = self.addIn('reset', reset)
        self.irq = self.addIn('irq', irq)
        self.nmi = self.addIn('nmi', nmi)
        
        self.mem = self.addInterfaceSource('memory', memory)

        status = {}
        control = {}
        
        
        control['mem_read'] = memory.read
        control['mem_write'] = memory.write
        
        DataPathStructural(self, 'datapath', reset, resetAddress, memory.address, memory.write_data, memory.be, memory.read_data, status, control)
        MicrocodedControlUnit6502(self, 'control', reset, status, control)
        
        self.symbols = {}
        self.control = control
        self.status = status
        
        
    def loadSymbols(self, symbols):
         self.symbols = symbols
         self.inv_symbols = {}
         for key in symbols.keys():
             val = symbols[key]
             self.inv_symbols[val] = key
             
    def getRetiredInstructions(self):
        return self.children['control'].children['retired'].v
        
    def getRegister(self, r):
        r = r.upper()
        if (r == 'PC'):
            return self.children['datapath']._wires['q_PC'].get() 
        elif (r == 'A'):
            return self.children['datapath']._wires['q_A'].get() 
        elif (r == 'X'):
            return self.children['datapath']._wires['q_X'].get() 
        elif (r == 'Y'):
            return self.children['datapath']._wires['q_Y'].get() 
        elif (r == 'SP'):
            return self.children['datapath']._wires['q_SP'].get() 
        elif (r == 'N'):
            return self.status['q_N'].get() 
        elif (r == 'V'):
            return self.status['q_V'].get() 
        elif (r == 'B'):
            return self.status['q_B'].get() 
        elif (r == 'D'):
            return self.status['q_D'].get() 
        elif (r == 'I'):
            return self.status['q_I'].get() 
        elif (r == 'C'):
            return self.status['q_C'].get() 
        elif (r == 'Z'):
            return self.status['q_Z'].get() 
        else:
            raise Exception(f'register {r} not known')
        

    
            
    
        
