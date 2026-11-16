# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 12:29:47 2026

@author: dcr
"""

import py4hw

from .alu import ALUStructural

class DataPathStructural(py4hw.Logic):
    def __init__(self, parent, name:str, reset, resetAddress, memory_address, write_data, be, read_data, status, control):
        super().__init__(parent, name)
        
        reset = self.addIn('reset', reset)
        
        self.addOut('memory_address', memory_address)
        self.addOut('write_data', write_data)
        self.addOut('be', be)
        self.addIn('read_data', read_data)
        
        for key in status.keys():
            self.addOut(key, status[key])
        
        for key in control.keys():
            self.addIn(key, control[key])
            
        q_PC_lo = self.wire('q_PC_lo', 8)
        q_PC_hi = self.wire('q_PC_hi', 8)
        q_PC = self.wire('q_PC', 16)
        
        q_MAR_lo = self.wire('q_MAR_lo', 8)
        q_MAR_hi = self.wire('q_MAR_hi', 8)
        q_MAR = self.wire('q_MAR', 16)
        q_MBR = self.wire('q_MBR', 8)
        
        mbr_bit = self.wires('mbr_bit', 8, 1)
        
        # Public registers
        control['e_A'] = self.controlIn('e_A')
        control['e_X'] = self.controlIn('e_X')
        control['e_Y'] = self.controlIn('e_Y')
        control['e_SP'] = self.controlIn('e_SP')
        
        control['e_N'] = self.controlIn('e_N')
        control['e_V'] = self.controlIn('e_V')
        control['e_B'] = self.controlIn('e_B')
        control['e_D'] = self.controlIn('e_D')
        control['e_I'] = self.controlIn('e_I')
        control['e_Z'] = self.controlIn('e_Z')
        control['e_C'] = self.controlIn('e_C')
        
        # internal registers (not exposed to the user)
        control['e_PC_lo'] = self.controlIn('e_PC_lo')
        control['e_PC_hi'] = self.controlIn('e_PC_hi')
        control['e_MAR_lo'] = self.controlIn('e_MAR_lo')
        control['e_MAR_hi'] = self.controlIn('e_MAR_hi')
        control['e_IR'] = self.controlIn('e_IR')
        control['e_MBR'] = self.controlIn('e_MBR')
        
        q_A = self.wire('q_A', 8)
        q_X = self.wire('q_X', 8)
        q_Y = self.wire('q_Y', 8)
        q_SP = self.wire('q_SP', 8)
        q_P = self.wire('q_P', 8)
                
        status['q_IR'] = self.statusOut('q_IR', 8)
        
        control['sel_C'] = self.controlIn('sel_C')
        control['sel_V'] = self.controlIn('sel_V')
        control['sel_flags'] = self.controlIn('sel_flags')
        
        control['d_B'] = self.controlIn('d_B')
        control['d_C'] = self.controlIn('d_C')     
        control['d_D'] = self.controlIn('d_D')
        
        control['d_I'] = self.controlIn('d_I')
        control['d_V'] = self.controlIn('d_V')
        
        status['q_B'] = self.statusOut('q_B')
        status['q_C'] = self.statusOut('q_C')
        status['q_D'] = self.statusOut('q_D')
        status['q_Z'] = self.statusOut('q_Z')
        status['q_N'] = self.statusOut('q_N')
        status['q_I'] = self.statusOut('q_I')
        status['q_V'] = self.statusOut('q_V')

        databus = self.wire('databus', 8)
        
        py4hw.Reg(self, 'PC_lo', databus, q_PC_lo, reset=reset, reset_value=(resetAddress & 0XFF), enable=control['e_PC_lo'])
        py4hw.Reg(self, 'PC_hi', databus, q_PC_hi, reset=reset, reset_value=((resetAddress >> 8) & 0xFF), enable=control['e_PC_hi'])
        py4hw.Reg(self, 'MAR_lo', databus, q_MAR_lo, reset=reset, enable=control['e_MAR_lo'])
        py4hw.Reg(self, 'MAR_hi', databus, q_MAR_hi, reset=reset, enable=control['e_MAR_hi'])
        py4hw.Reg(self, 'IR', databus, status['q_IR'], reset=reset, enable=control['e_IR'])
        py4hw.Reg(self, 'MBR', databus, q_MBR, reset=reset, enable=control['e_MBR'])
        
        py4hw.BitsLSBF(self, 'mbr_bit', q_MBR, mbr_bit)
        
        py4hw.ConcatenateLSBF(self, 'PC', [q_PC_lo, q_PC_hi], q_PC)
        py4hw.ConcatenateLSBF(self, 'MAR', [q_MAR_lo, q_MAR_hi], q_MAR)
        
        b = self.wire('b', 8)
        q_alu = self.wire('q_alu', 8)
        
        control['alu_sel_PC_lo'] = self.controlIn('alu_sel_PC_lo')
        control['alu_sel_PC_hi'] = self.controlIn('alu_sel_PC_hi')
        control['alu_sel_MAR_lo'] = self.controlIn('alu_sel_MAR_lo')
        control['alu_sel_MAR_hi'] = self.controlIn('alu_sel_MAR_hi')
        control['alu_sel_A'] = self.controlIn('alu_sel_A')
        control['alu_sel_X'] = self.controlIn('alu_sel_X')
        control['alu_sel_Y'] = self.controlIn('alu_sel_Y')
        control['alu_sel_SP'] = self.controlIn('alu_sel_SP')
        control['alu_sel_MBR'] = self.controlIn('alu_sel_MBR')
        control['alu_sel_P'] = self.controlIn('alu_sel_P')
        
        control['alu_op'] = self.controlIn('alu_op', 4)
        
        status['alu_C'] = self.statusOut('alu_C') # this carry is the output of the ALU
        status['alu_V'] = self.statusOut('alu_V') # this overflow is the output of the ALU
        status['alu_Z'] = self.statusOut('alu_Z')
        status['alu_N'] = self.statusOut('alu_N')
        
        py4hw.Select(self, 'select_b', 
                     [control['alu_sel_PC_lo'], 
                      control['alu_sel_PC_hi'],  
                      control['alu_sel_MAR_lo'], 
                      control['alu_sel_MAR_hi'],  
                      control['alu_sel_A'], 
                      control['alu_sel_X'], 
                      control['alu_sel_Y'], 
                      control['alu_sel_SP'], 
                      control['alu_sel_MBR'],
                      control['alu_sel_P']],
                     [q_PC_lo, q_PC_hi, q_MAR_lo, q_MAR_hi, q_A, q_X, q_Y, q_SP, q_MBR, q_P], b)
        
        ALUStructural(self, 'alu', q_A, b, q_alu, status['q_C'], control['alu_op'], status['alu_C'], status['alu_V'])
        
        # direct flags
        py4hw.Bit(self, 'alu_N', q_alu, 7, status['alu_N'])
        py4hw.EqualConstant(self, 'alu_Z', q_alu, 0, status['alu_Z'])
        
        py4hw.Reg(self, 'A', databus, q_A, reset=reset, enable=control['e_A'])
        py4hw.Reg(self, 'X', databus, q_X, reset=reset, enable=control['e_X'])
        py4hw.Reg(self, 'Y', databus, q_Y, reset=reset, enable=control['e_Y'])
        py4hw.Reg(self, 'SP', databus, q_SP, reset=reset, enable=control['e_SP'])
        
        c_pre_next = self.wire('c_pre_next')
        v_pre_next = self.wire('v_pre_next')
        py4hw.Mux2(self, 'c_pre_next', sel=control['sel_C'], sel0=status['alu_C'], sel1=control['d_C'], r=c_pre_next)
        py4hw.Mux2(self, 'v_pre_next', sel=control['sel_V'], sel0=status['alu_V'], sel1=control['d_V'], r=v_pre_next)

        c_next = self.wire('c_next')
        z_next = self.wire('z_next')
        i_next = self.wire('i_next')
        d_next = self.wire('d_next')
        b_next = self.wire('b_next')
        v_next = self.wire('v_next')
        n_next = self.wire('n_next')
        
        
        py4hw.Mux2(self, 'c_next', sel=control['sel_flags'], sel0=c_pre_next, sel1=mbr_bit[0], r=c_next)
        py4hw.Mux2(self, 'z_next', sel=control['sel_flags'], sel0=status['alu_Z'], sel1=mbr_bit[1], r=z_next)
        py4hw.Mux2(self, 'i_next', sel=control['sel_flags'], sel0=control['d_I'], sel1=mbr_bit[2], r=i_next)
        py4hw.Mux2(self, 'd_next', sel=control['sel_flags'], sel0=control['d_D'], sel1=mbr_bit[3], r=d_next)
        py4hw.Mux2(self, 'b_next', sel=control['sel_flags'], sel0=control['d_B'], sel1=mbr_bit[4], r=b_next)
        py4hw.Mux2(self, 'v_next', sel=control['sel_flags'], sel0=v_pre_next, sel1=mbr_bit[6], r=v_next)
        py4hw.Mux2(self, 'n_next', sel=control['sel_flags'], sel0=status['alu_N'], sel1=mbr_bit[7], r=n_next)
        
        
        py4hw.Reg(self, 'C', c_next, status['q_C'], reset=reset, enable=control['e_C'])
        py4hw.Reg(self, 'Z', z_next, status['q_Z'], reset=reset, enable=control['e_Z'])
        py4hw.Reg(self, 'I', i_next, status['q_I'], reset=reset, enable=control['e_I'])
        py4hw.Reg(self, 'D', d_next, status['q_D'], reset=reset, enable=control['e_D'])
        py4hw.Reg(self, 'B', b_next, status['q_B'], reset=reset, enable=control['e_B'])
        py4hw.Reg(self, 'V', v_next, status['q_V'], reset=reset, enable=control['e_V'])
        py4hw.Reg(self, 'N', n_next, status['q_N'], reset=reset, enable=control['e_N'])
        

        # P = N V 1 B D I Z C   (bit 7 .. bit 0)
        # PHP always pushes bits 4 (B) and 5 as 1
        one1 = self.wire('one1')
        py4hw.Constant(self, 'one1', 1, one1)
        
        py4hw.ConcatenateMSBF(self, 'P', [status['q_N'], status['q_V'], one1, one1, status['q_D'], status['q_I'], status['q_Z'], status['q_C']   ], q_P)

        zero8 = self.wire('zero8', 8)
        one8 = self.wire('one8', 8)
        py4hw.Constant(self, 'zero8', 0, zero8)
        py4hw.Constant(self, 'one8', 1, one8)
        
        q_zero = self.wire('q_zero', 16)
        q_stack = self.wire('q_stack', 16)
        
        control['sel_databus'] = self.controlIn('sel_databus')
        control['sel_memory'] = self.controlIn('sel_memory', 2)
        
        py4hw.ConcatenateLSBF(self, 'q_zero', [q_MAR_lo, zero8], q_zero)
        py4hw.ConcatenateLSBF(self, 'q_stack', [q_SP, one8], q_stack)
        
        py4hw.Mux2(self, 'databus', control['sel_databus'], q_alu, read_data, databus)
        py4hw.Mux(self, 'addressbus', control['sel_memory'], [q_PC, q_MAR, q_zero, q_stack], memory_address)
        
        py4hw.Buf(self, 'write_data', q_alu, write_data)
        py4hw.Buf(self, 'be', one8, be)
        
    def controlIn(self, name, w=1):
        ww = self.parent.wire(name, w)
        return self.addIn(name, ww)
    
    def statusOut(self, name, w=1):
        ww = self.parent.wire(name, w)
        return self.addOut(name, ww)
