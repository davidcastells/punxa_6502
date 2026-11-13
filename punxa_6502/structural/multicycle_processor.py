# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 16:32:44 2025

@author: dcr
"""
import py4hw
import punxa_6502
from punxa_6502.structural.alu import ALU
#from alu import ALUBehavioral
from punxa_6502.structural.alu import ALUStructural

   
        
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
        ControlUnit6502Behavioral(self, 'control', reset, status, control)
        
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
        return self.children['control'].getRetiredInstructions()
        
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
        
class ControlUnit6502Behavioral(py4hw.Logic):
    
    DATA_ALU = 0
    DATA_MEM = 1
    
    MEM_PC = 0
    MEM_MAR = 1
    MEM_ZP = 2
    MEM_SP = 3
    
    OPCODE_BRK =        0x00
    OPCODE_ORA_INDX =   0x01
    OPCODE_ORA_ZP =     0x05
    OPCODE_ASL_ZP =     0x06
    OPCODE_PHP =        0x08
    OPCODE_ORA_IMM =    0x09
    OPCODE_ASL_ACC =    0x0A
    OPCODE_ORA_ABS =    0x0D
    OPCODE_ASL_ABS =    0x0E
    OPCODE_BPL_REL =    0x10
    OPCODE_ORA_INDY =   0x11
    OPCODE_ORA_ZPX =    0x15
    OPCODE_ASL_ZPX =    0x16
    OPCODE_CLC =        0x18
    OPCODE_ORA_ABSY =   0x19
    OPCODE_ORA_ABSX =   0x1D
    OPCODE_ASL_ABSX =   0x1E
    OPCODE_JSR_ABS =    0x20
    OPCODE_AND_INDX =   0x21
    OPCODE_BIT_ZP =     0x24
    OPCODE_AND_ZP =     0x25
    OPCODE_ROL_ZP =     0x26
    OPCODE_PLP =        0x28
    OPCODE_AND_IMM =    0x29
    OPCODE_ROL_ACC =    0x2A
    OPCODE_BIT_ABS =    0x2C
    OPCODE_AND_ABS =    0x2D
    OPCODE_ROL_ABS =    0x2E
    OPCODE_BMI_REL =    0x30
    OPCODE_AND_INDY =   0x31
    OPCODE_AND_ZPX =    0x35
    OPCODE_ROL_ZPX =    0x36
    OPCODE_SEC =        0x38
    OPCODE_AND_ABSY =   0x39
    OPCODE_AND_ABSX =   0x3D
    OPCODE_ROL_ABSX =   0x3E
    OPCODE_RTI =        0x40
    OPCODE_EOR_INDX =   0x41
    # # 0x42, 0x43, 0x44 are illegal/undocumented
    OPCODE_EOR_ZP =     0x45
    OPCODE_LSR_ZP =     0x46
    # # 0x47 is illegal/undocumented
    OPCODE_PHA =        0x48
    
    OPCODE_EOR_IMM =    0x49
    OPCODE_LSR_ACC =    0x4A
    # # 0x4B is illegal/undocumented
    OPCODE_JMP_ABS =    0x4C
    OPCODE_EOR_ABS =    0x4D
    OPCODE_LSR_ABS =    0x4E
    # # 0x4F is illegal/undocumented

    # # Row 0x50-0x5F
    OPCODE_BVC_REL =    0x50
    OPCODE_EOR_INDY =   0x51
    # # 0x52, 0x53, 0x54 are illegal/undocumented
    OPCODE_EOR_ZPX =    0x55
    OPCODE_LSR_ZPX =    0x56
    # # 0x57 is illegal/undocumented
    OPCODE_CLI =        0x58
    OPCODE_EOR_ABSY =   0x59
    # # 0x5A, 0x5B, 0x5C are illegal/undocumented
    OPCODE_EOR_ABSX =   0x5D
    OPCODE_LSR_ABSX =   0x5E
    # # 0x5F is illegal/undocumented

    # # Row 0x60-0x6F
    OPCODE_RTS =        0x60
    OPCODE_ADC_INDX =   0x61
    # # 0x62, 0x63, 0x64 are illegal/undocumented
    OPCODE_ADC_ZP =     0x65
    OPCODE_ROR_ZP =     0x66
    # # 0x67 is illegal/undocumented
    OPCODE_PLA =        0x68
    OPCODE_ADC_IMM =    0x69
    OPCODE_ROR_ACC =    0x6A
    OPCODE_JMP_IND =    0x6C
    OPCODE_ADC_ABS =    0x6D
    OPCODE_ROR_ABS =    0x6E
    # # 0x6F is illegal/undocumented

    # # Row 0x70-0x7F
    OPCODE_BVS_REL =    0x70
    OPCODE_ADC_INDY =   0x71
    # # 0x72, 0x73, 0x74 are illegal/undocumented
    OPCODE_ADC_ZPX =    0x75
    OPCODE_ROR_ZPX =    0x76
    # # 0x77 is illegal/undocumented
    OPCODE_SEI =        0x78
    OPCODE_ADC_ABSY =   0x79
    # # 0x7A, 0x7B, 0x7C are illegal/undocumented
    OPCODE_ADC_ABSX =   0x7D
    OPCODE_ROR_ABSX =   0x7E
    # # 0x7F is illegal/undocumented

    # # Row 0x80-0x8F
    # # 0x80 is illegal/undocumented
    OPCODE_STA_INDX =   0x81
    # # 0x82, 0x83 are illegal/undocumented
    OPCODE_STY_ZP =     0x84
    OPCODE_STA_ZP =     0x85
    OPCODE_STX_ZP =     0x86
    OPCODE_DEY =        0x88
    OPCODE_TXA =        0x8A
    OPCODE_STY_ABS =    0x8C
    OPCODE_STA_ABS =    0x8D
    OPCODE_STX_ABS =    0x8E
    OPCODE_BCC_REL =    0x90
    OPCODE_STA_INDY =   0x91
    OPCODE_STY_ZPX =    0x94
    OPCODE_STA_ZPX =    0x95
    OPCODE_STX_ZPY =    0x96
    OPCODE_TYA =        0x98
    OPCODE_STA_ABSY =   0x99
    OPCODE_TXS =        0x9A
    OPCODE_STA_ABSX =   0x9D
    OPCODE_LDY_IMM =    0xA0
    OPCODE_LDA_INDX =   0xA1
    OPCODE_LDX_IMM =    0xA2
    OPCODE_LDY_ZP =     0xA4
    OPCODE_LDA_ZP =     0xA5
    OPCODE_LDX_ZP =     0xA6
    OPCODE_TAY =        0xA8
    OPCODE_LDA_IMM =    0xA9
    OPCODE_TAX =        0xAA
    OPCODE_LDY_ABS =    0xAC
    OPCODE_LDA_ABS =    0xAD
    OPCODE_LDX_ABS =    0xAE
    OPCODE_BCS_REL =    0xB0
    OPCODE_LDA_INDY =   0xB1
    # # 0xB2, 0xB3, B4 (illegal/undocumented) (LDY ZP,X was 0xB4 - this is for 65C02)
    OPCODE_LDY_ZPX =    0xB4 # This is a 65C02 legal opcode, but was illegal on NMOS. Assuming you want legal NMOS.
    OPCODE_LDA_ZPX =    0xB5
    OPCODE_LDX_ZPY =    0xB6
    
    # # 0xB7 is illegal/undocumented
    OPCODE_CLV =        0xB8
    OPCODE_LDA_ABSY =   0xB9
    OPCODE_TSX =        0xBA
    # # 0xBB is illegal/undocumented
    OPCODE_LDY_ABSX =   0xBC
    OPCODE_LDA_ABSX =   0xBD
    OPCODE_LDX_ABSY =   0xBE
    # # 0xBF is illegal/undocumented

    # # Row 0xC0-0xCF
    OPCODE_CPY_IMM =    0xC0
    OPCODE_CMP_INDX =   0xC1
    # # 0xC2, 0xC3 are illegal/undocumented
    OPCODE_CPY_ZP =     0xC4
    OPCODE_CMP_ZP =     0xC5
    OPCODE_DEC_ZP =     0xC6
    # # 0xC7 is illegal/undocumented
    OPCODE_INY =        0xC8
    OPCODE_CMP_IMM =    0xC9
    OPCODE_DEX =        0xCA
    # # 0xCB is illegal/undocumented
    OPCODE_CPY_ABS =    0xCC
    OPCODE_CMP_ABS =    0xCD
    OPCODE_DEC_ABS =    0xCE
    # # 0xCF is illegal/undocumented

    OPCODE_BNE_REL =    0xD0
    OPCODE_CMP_INDY =   0xD1
    # # 0xD2, 0xD3, 0xD4 are illegal/undocumented
    # _OPCODE_MAP[0xD5] = ('CMP', ADDRESSING_ZEROPAGEX)
    OPCODE_CMP_ZPX =    0xD5
    OPCODE_DEC_ZPX =    0xD6
    # # 0xD7 is illegal/undocumented
    OPCODE_CLD =        0xD8
    OPCODE_CMP_ABSY =   0xD9
    # # 0xDA, 0xDB, 0xDC are illegal/undocumented
    OPCODE_CMP_ABSX =   0xDD
    OPCODE_DEC_ABSX =   0xDE
    # # 0xDF is illegal/undocumented

    # # Row 0xE0-0xEF
    OPCODE_CPX_IMM =    0xE0
    OPCODE_SBC_INDX =   0xE1
    # # 0xE2, 0xE3 are illegal/undocumented
    OPCODE_CPX_ZP =     0xE4
    OPCODE_SBC_ZP =     0xE5
    OPCODE_INC_ZP =     0xE6
    # # 0xE7 is illegal/undocumented
    OPCODE_INX =        0xE8
    OPCODE_SBC_IMM =    0xE9
    OPCODE_NOP =        0xEA
    OPCODE_CPX_ABS =    0xEC
    OPCODE_SBC_ABS =    0xED
    OPCODE_INC_ABS =    0xEE
    OPCODE_BEQ_REL =    0xF0
    OPCODE_SBC_INDY =   0xF1
    # # 0xF2, 0xF3, 0xF4 are illegal/undocumented
    OPCODE_SBC_ZPX =    0xF5
    OPCODE_INC_ZPX =    0xF6
    # # 0xF7 is illegal/undocumented
    OPCODE_SED =        0xF8
    OPCODE_SBC_ABSY =   0xF9
    # # 0xFA, 0xFB, 0xFC are illegal/undocumented
    OPCODE_SBC_ABSX =   0xFD
    OPCODE_INC_ABSX =   0xFE

    
    def __init__(self, parent, name:str, reset, status, control):
        
        super().__init__(parent, name)

        self.addIn('reset', reset)

        for key in status.keys():
            self.addIn(key, status[key])

        
        for key in control.keys():
            self.addOut(key, control[key])
            
            
        self.status = status
        self.control = control
        
        self.retired = 0
        
        self.co = self.run()
        
    def getRetiredInstructions(self):
        return self.retired
    
    def clock(self):
        next(self.co)
        
        
    def resetCycle(self):
        control = self.control
        control['sel_databus'].prepare(0)
        control['sel_memory'].prepare(0)
        control['e_PC_lo'].prepare(0)
        control['e_PC_hi'].prepare(0)
        
        yield
        
    def run(self):
        yield from self.resetCycle()
        
        while (True):
            yield from self.fetchIR()
            yield from self.decodeAndExecute()
            
            self.retired += 1
            yield
            #yield from self.incpc()
            #yield from self.fetchOperand()
            #yield from self.execute()
        
    def fetchIR(self):
        # Some debug
        pc = self.parent.children['datapath']._wires['q_PC'].get()

        if (pc in self.parent.inv_symbols.keys()):
            print('{}:'.format(self.parent.inv_symbols[pc]))

        print(f'{pc:04X} - ', end='')
        # We just fetch one instruction from the PC address
        control = self.control
        control['sel_memory'].prepare(0) # select PC for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_IR'].prepare(1)
        yield
        control['e_IR'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        ir = self.status['q_IR'].get()
        print(f'{ir:02X} ', end='')
    
    def fetchA(self):
        control = self.control
        control['sel_memory'].prepare(0) # select PC for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_A'].prepare(1)
        yield
        control['e_A'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        r = self.parent.children['datapath']._wires['q_A'].get()
        print(f'{r:02X} ', end='')

    def fetchX(self):
        control = self.control
        control['sel_memory'].prepare(0) # select PC for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_X'].prepare(1)
        yield
        control['e_X'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        r = self.parent.children['datapath']._wires['q_X'].get()
        print(f'{r:02X} ', end='')

    def fetchY(self):
        control = self.control
        control['sel_memory'].prepare(0) # select PC for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_Y'].prepare(1)
        yield
        control['sel_databus'].prepare(self.DATA_ALU) 
        control['e_Y'].prepare(0)
        yield
        r = self.parent.children['datapath']._wires['q_Y'].get()
        print(f'{r:02X} ', end='')
        
    def fetchMAR_A(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_memory'].prepare(self.MEM_PC) 
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_A'].prepare(1)
        yield
        control['e_A'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield

    def fetchMAR_MBR(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_memory'].prepare(self.MEM_PC) 
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_MBR'].prepare(1)
        yield
        control['e_MBR'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield

    def fetchMAR_PC_lo(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_memory'].prepare(self.MEM_PC) 
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_PC_lo'].prepare(1)
        yield
        control['e_PC_lo'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield


    def fetchMAR_PC_hi(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_memory'].prepare(self.MEM_PC) 
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_PC_hi'].prepare(1)
        yield
        control['e_PC_hi'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        
    def fetchMAR_X(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_memory'].prepare(self.MEM_PC) 
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_X'].prepare(1)
        yield
        control['e_X'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        
    def fetchMAR_Y(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_memory'].prepare(self.MEM_PC) 
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_Y'].prepare(1)
        yield
        control['e_Y'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        
    def fetchMBR(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
    
        control = self.control
        control['sel_memory'].prepare(self.MEM_PC) # select PC for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_MBR'].prepare(1)
        yield
        control['e_MBR'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        print(f'{r:02X} ', end='')

    def fetchZP_A(self):    
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_A'].prepare(1)
        yield
        control['e_A'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        
    def fetchZP_MAR_hi(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
    
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_MAR_hi'].prepare(1)
        yield
        control['e_MAR_hi'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        
    def fetchZP_MBR(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
    
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_MBR'].prepare(1)
        yield
        control['e_MBR'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        #r = self.parent._wires['q_MBR'].get()
        #print(f'{r:02X} ', end='')

    

    def fetchZP_X(self):
        #pc = self.parent._wires['q_PC'].get()
        #print(f'Fetch ops {pc:04X}')
    
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_X'].prepare(1)
        yield
        control['e_X'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        
    def fetchZP_Y(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM)
        control['e_Y'].prepare(1)
        yield
        control['e_Y'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU)
        yield
        
    def storeA(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC) # select ZP for address
        control['mem_write'].prepare(0)
        control['alu_sel_A'].prepare(0)
        yield        

    def storeMBR(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC) # select ZP for address
        control['mem_write'].prepare(0)
        control['alu_sel_MBR'].prepare(0)
        yield        

    def storeMBR_ZP(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC)
        control['mem_write'].prepare(0)
        control['alu_sel_MBR'].prepare(0)
        yield
        
    def storeX(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_X'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC) # select ZP for address
        control['mem_write'].prepare(0)
        control['alu_sel_X'].prepare(0)
        yield        
        
    def storeY(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_MAR) # select MAR for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_Y'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC) # select ZP for address
        control['mem_write'].prepare(0)
        control['alu_sel_Y'].prepare(0)
        yield    
        
    def storeA_ZP(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC) # select ZP for address
        control['mem_write'].prepare(0)
        control['alu_sel_A'].prepare(0)
        yield        

    def storeX_ZP(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_X'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC) # select ZP for address
        control['mem_write'].prepare(0)
        control['alu_sel_X'].prepare(0)
        yield        
        
    def storeY_ZP(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_ZP) # select ZP for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_Y'].prepare(1)
        yield
        control['sel_memory'].prepare(self.MEM_PC)
        control['mem_write'].prepare(0)
        control['alu_sel_Y'].prepare(0)
        yield
        
    def fetchMAR_lo(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_PC) # select PC for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_MAR_lo'].prepare(1)
        yield
        control['e_MAR_lo'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        r = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        print(f'{r:02X} ', end='')
        
    def fetchMAR_hi(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_PC) # select PC for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_MAR_hi'].prepare(1)
        yield
        control['e_MAR_hi'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
        r = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        print(f'{r:02X} ', end='')

    def executeADC_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluADD_MBR()       # A = A + M + C, update C, N, Z, V
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\tADC ${b:02X}{a:02X} \t--> A={r:02X} N={n} V={v} Z={z} C={c}')
        
    def executeADC_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry goes into MAR_hi)
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluADD_MBR()       # A = A + M + C, update C, N, Z, V
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\tADC ${b:02X}{a:02X},X \t--> A={r:02X} N={n} V={v} Z={z} C={c}')
        
    def executeADC_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + X (carry goes into MAR_hi)
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluADD_MBR()       # A = A + M + C, update C, N, Z, V
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\tADC ${b:02X}{a:02X},Y \t--> A={r:02X} N={n} V={v} Z={z} C={c}')
        
        
    def executeADC_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()      # loads the immediate in MBR
        yield from self.aluADD_MBR()
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tADC #{m:02X} \t--> A={a:02X} N={n} V={v} Z={z} C={c}')

    def executeADC_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page base -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()            # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        yield from self.fetchMAR_MBR()           # M = mem[pointer] -> MBR
        yield from self.aluADD_MBR()             # A = A + M + C, update C, N, Z, V
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tADC $({a:02X},X) \t--> A={r:02X} N={n} V={v} Z={z} C={c}')        
        
    def executeADC_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()              # zero-page pointer address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()              # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()           # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()    # MAR = 16-bit pointer
        yield from self.addY_to_MAR()              # MAR = pointer + Y (16-bit, carry into MAR_hi)
        yield from self.fetchMAR_MBR()             # M = mem[MAR] -> MBR
        yield from self.aluADD_MBR()               # A = A + M + C, update C, N, Z, V
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tADC $({a:02X}),Y \t--> A={r:02X} N={n} V={v} Z={z} C={c}')
        
    def executeADC_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()          # M = mem[0x00:MAR_lo] -> MBR
    
        # A = A + M + C, update C/N/Z
        control = self.control
        control['alu_op'].prepare(ALU.OP_ADD)
        control['alu_sel_MBR'].prepare(1)
        control['e_A'].prepare(1)
        control['e_C'].prepare(1)
        control['sel_C'].prepare(0)
        control['e_V'].prepare(1)
        control['sel_V'].prepare(0)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
        control['e_C'].prepare(0)
        control['e_V'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
    
        yield from self.incPC()
    
        addr = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        m    = self.parent.children['datapath']._wires['q_MBR'].get()
        a    = self.parent.children['datapath']._wires['q_A'].get()
        c    = self.status['q_C'].get()
        z    = self.status['q_Z'].get()
        n    = self.status['q_N'].get()
        print(f'\t\tADC ${addr:02X} = {m:02X} \t--> A={a:02X} C={c} N={n} Z={z}')
        
    def executeADC_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluADD_MBR()       # A = A + M + C, update C, N, Z, V
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tADC ${m:02X},X \t--> A={a:02X} N={n} V={v} Z={z} C={c}')
        
    def executeAND_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluAND_MBR()       # A = A & M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tAND ${b:02X}{a:02X} = {m:02X} \t--> A={r:02X} N={n} Z={z}')
        
    def executeAND_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry into MAR_hi), A is preserved
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluAND_MBR()       # A = A & M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tAND ${b:02X}{a:02X},X = {m:02X} \t--> A={r:02X} N={n} Z={z}')
        
    def executeAND_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + Y (carry into MAR_hi), A is preserved
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluAND_MBR()       # A = A & M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tAND ${b:02X}{a:02X},Y = {m:02X} \t--> A={r:02X} N={n} Z={z}')
        
    def executeAND_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        yield from self.aluAND_MBR()
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tAND #{m:02X} \t--> A={a:02X} N={n} Z={z}')
        
    def executeAND_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page base -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()            # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()              # (ptr + 1) & 0xFF, wraps in zero page
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        yield from self.fetchMAR_MBR()           # M = mem[pointer] -> MBR
        yield from self.aluAND_MBR()             # A = A & M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tAND $({a:02X},X) = {m:02X} \t--> A={r:02X} N={n} Z={z}')
        
    def executeAND_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()              # zero-page pointer address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()              # pointer low byte -> MBR
        yield from self.incMAR_lo()                # (ptr + 1) & 0xFF, wraps in zero page
        yield from self.fetchZP_MAR_hi()           # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()    # MAR = 16-bit pointer
        yield from self.addY_to_MAR()              # MAR = pointer + Y (carry into MAR_hi)
        yield from self.fetchMAR_MBR()             # M = mem[MAR] -> MBR
        yield from self.aluAND_MBR()               # A = A & M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tAND $({a:02X}),Y = {m:02X} \t--> A={r:02X} N={n} Z={z}')
        
    def executeAND_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_MBR()
        yield from self.aluAND_MBR()
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        a = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tAND ${m:02X} \t--> (A={a}) (N={n}) (Z={z})')
        
    def executeAND_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        base = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF, A is preserved
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluAND_MBR()       # A = A & M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tAND ${base:02X},X = {m:02X} \t--> A={a:02X} N={n} Z={z}')
        
    def executeASL_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.pushA()                # save A on the stack (MAR still holds the address)
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR
        yield from self.transferMBR_to_A()     # A = M
        yield from self.aluASL_A()             # A = M << 1, C = old bit 7, update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA()               # mem[MAR] = A
        yield from self.popA()                 # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tASL ${b:02X}{a:02X} \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeASL_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()          # MAR = base + X (carry into MAR_hi), A is preserved
        yield from self.pushA()                # save A on the stack (MAR still holds the address)
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR
        yield from self.transferMBR_to_A()     # A = M
        yield from self.aluASL_A()             # A = M << 1, C = old bit 7, update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA()               # mem[MAR] = A
        yield from self.popA()                 # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tASL ${b:02X}{a:02X},X \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeASL_ACC(self):
        yield from self.aluASL_A()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\t\tASL A\t\t--> A={a:02X} C={c} N={n} Z={z}')
        
    def executeASL_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.fetchZP_A()            # A = M
        yield from self.aluASL_A()             # A = M << 1, C = old bit 7, update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA_ZP()            # mem[0x00:MAR_lo] = A
        yield from self.transferMAR_hi_to_A()  # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tASL ${m:02X} \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeASL_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()          # MAR_lo = (base + X) & 0xFF, A is preserved
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.fetchZP_A()            # A = M
        yield from self.aluASL_A()             # A = M << 1, C = old bit 7, update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA_ZP()            # mem[0x00:MAR_lo] = A
        yield from self.transferMAR_hi_to_A()  # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tASL ${m:02X},X \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeBCC_REL(self):
        yield from self.incPC()
        yield from self.fetchMBR()         # signed offset -> MBR
        yield from self.incPC()            # PC now points to the next instruction
        c = self.status['q_C'].get()
        if (c == 0):
            yield from self.addMBR_to_PC() # PC = PC + signed offset
        w = self.parent.children['datapath']._wires['q_MBR'].get()
        w = py4hw.IntegerHelper.c2_to_signed(w, 8)
        print(f'\t\tBCC {w:3} \t--> (C={c})')
        
    def executeBEQ_REL(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        yield from self.incPC()
        z = self.status['q_Z'].get()
        if (z):
            pc = self.parent.children['datapath']._wires['q_PC'].get()
            #print(f'PC before add {pc:04X}')
            yield from self.addMBR_to_PC()
            pc = self.parent.children['datapath']._wires['q_PC'].get()
            #print(f'PC after add {pc:04X}')
        #else: 
        #    yield from self.incPC()  
        w = self.parent.children['datapath']._wires['q_MBR'].get()
        w = py4hw.IntegerHelper.c2_to_signed(w, 8)
        print(f'\t\tBEQ {w:3} \t--> (Z={z})' )

    def executeBNE_REL(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        yield from self.incPC()
        z = self.status['q_Z'].get()
        if (z == 0):
            yield from self.addMBR_to_PC()
        #else: 
        #    yield from self.incPC()  
        w = self.parent.children['datapath']._wires['q_MBR'].get()
        w = py4hw.IntegerHelper.c2_to_signed(w, 8)

        print(f'\t\tBNE {w:3} \t--> (Z={z})' )

    def executeBPL_REL(self):
        yield from self.incPC()
        yield from self.fetchMBR()         # signed offset -> MBR
        yield from self.incPC()            # PC now points to the next instruction
        n = self.status['q_N'].get()
        if (n == 0):
            yield from self.addMBR_to_PC() # PC = PC + signed offset
        w = self.parent.children['datapath']._wires['q_MBR'].get()
        w = py4hw.IntegerHelper.c2_to_signed(w, 8)
        print(f'\t\tBPL {w:3} \t--> (N={n})')

    def executeBVC_REL(self):
        yield from self.incPC()
        yield from self.fetchMBR()         # signed offset -> MBR
        yield from self.incPC()            # PC now points to the next instruction
        v = self.status['q_V'].get()
        if (v == 0):
            yield from self.addMBR_to_PC() # PC = PC + signed offset
        w = self.parent.children['datapath']._wires['q_MBR'].get()
        w = py4hw.IntegerHelper.c2_to_signed(w, 8)
        print(f'\t\tBVC {w:3} \t--> (V={v})')

    def executeBVS_REL(self):
        yield from self.incPC()
        yield from self.fetchMBR()         # signed offset -> MBR
        yield from self.incPC()            # PC now points to the next instruction
        v = self.status['q_V'].get()
        if (v):
            yield from self.addMBR_to_PC() # PC = PC + signed offset
        w = self.parent.children['datapath']._wires['q_MBR'].get()
        w = py4hw.IntegerHelper.c2_to_signed(w, 8)
        print(f'\t\tBVS {w:3} \t--> (V={v})')

    def executeBRK(self):
        yield from self.incPC()            # skip the padding byte...
        yield from self.incPC()            # ...so PC = BRK address + 2
        yield from self.pushPC_hi()
        yield from self.pushPC_lo()
        yield from self.pushP()            # B and bit 5 are set in the pushed byte
        yield from self.setI()             # I is set after pushing the old P
        yield from self.loadVector_to_MAR()
        yield from self.fetchMAR_PC_lo()   # PC_lo = mem[$FFFE]
        yield from self.incMAR_lo()        # $FFFF
        yield from self.fetchMAR_PC_hi()   # PC_hi = mem[$FFFF]
        pc = self.parent.children['datapath']._wires['q_PC'].get()
        print(f'\t\tBRK \t\t--> PC={pc:04X}')
        
    def executeCLC(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_OR)
        control['e_C'].prepare(1)
        yield
        control['e_C'].prepare(0)
        yield
        
        yield from self.incPC()
        c = self.status['q_C'].get()
        print(f'\t\tCLC \t\t--> (C={c})' )

    def executeCLD(self):
        control = self.control
        control['d_D'].prepare(0)
        control['e_D'].prepare(1)
        yield
        control['e_D'].prepare(0)
        yield

        yield from self.incPC()
        d = self.status['q_D'].get()
        print(f'\t\tCLD \t\t--> (D={d})')

    def executeCLI(self):
        control = self.control
        control['d_I'].prepare(0)          # I input comes straight from d_I (sel_flags=0)
        control['e_I'].prepare(1)
        yield
        control['e_I'].prepare(0)
        yield

        yield from self.incPC()
        i = self.status['q_I'].get()
        print(f'\t\tCLI \t\t--> (I={i})')

    def executeCLV(self):
        control = self.control
        control['d_V'].prepare(0)
        control['sel_V'].prepare(1)        # take V from the CU, not the ALU
        control['e_V'].prepare(1)
        yield
        control['sel_V'].prepare(0)        # back to the ALU overflow (ADC/SBC rely on it)
        control['e_V'].prepare(0)
        yield

        yield from self.incPC()
        v = self.status['q_V'].get()
        print(f'\t\tCLV \t\t--> (V={v})')

    def executeCMP_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluCMP_MBR()       # flags from A - M, A unchanged
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tCMP ${b:02X}{a:02X} \t--> C={c} N={n} Z={z}')
        
    def executeCMP_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry goes into MAR_hi)
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluCMP_MBR()       # flags from A - M, A unchanged
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tCMP ${b:02X}{a:02X},X \t--> C={c} N={n} Z={z}')
        
    def executeCMP_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + Y (carry goes into MAR_hi)
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluCMP_MBR()       # flags from A - M, A unchanged
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tCMP ${b:02X}{a:02X},Y \t--> C={c} N={n} Z={z}')
        
    def executeCMP_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        a = self.parent.children['datapath']._wires['q_MBR'].get()
        yield from self.aluCMP_MBR()
        yield from self.incPC()        
        print(f'\t\tCMP #{a:02X} ')
        
    def executeCMP_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # zero-page base -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()      # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()   # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()   # MAR = pointer
        yield from self.fetchMAR_MBR()     # M = mem[pointer] -> MBR
        yield from self.aluCMP_MBR()       # flags from A - M, A unchanged
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCMP $({a:02X},X) \t--> C={c} N={n} Z={z}')
        
    def executeCMP_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()              # zero-page pointer address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()              # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()           # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()    # MAR = 16-bit pointer
        yield from self.addY_to_MAR()              # MAR = pointer + Y
        yield from self.fetchMAR_MBR()             # M = mem[MAR] -> MBR
        yield from self.aluCMP_MBR()               # flags from A - M (A unchanged)
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCMP $({a:02X}),Y \t--> C={c} N={n} Z={z}')
        
    def executeCMP_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluCMP_MBR()       # flags from A - M, A unchanged
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCMP ${m:02X} \t--> C={c} N={n} Z={z}')

    def executeCMP_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluCMP_MBR()       # flags from A - M, A unchanged
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCMP ${m:02X},X \t--> C={c} N={n} Z={z}')

    def executeCPX_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR (MAR is now free)
        yield from self.transferA_to_MAR_lo()  # park A in the now-unused MAR_lo
        yield from self.transferX_to_A()       # A = X (its N/Z update is overwritten by the CMP)
        yield from self.aluCMP_MBR()           # flags from X - M
        yield from self.transferMAR_lo_to_A()  # restore A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tCPX ${b:02X}{a:02X} \t--> C={c} N={n} Z={z}')

    def executeCPX_IMM(self):
        # save A to MAR_lo to load X into A to do the comparison
        # because (a) input of the ALU is hardcoded to A
        yield from self.incPC()
        yield from self.transferA_to_MAR_lo()
        yield from self.transferX_to_A()       # A = X (its N/Z update is overwritten by the CMP)
        yield from self.fetchMBR()
        a = self.parent.children['datapath']._wires['q_MBR'].get()
        yield from self.aluCMP_MBR()           # flags from X - M
        yield from self.transferMAR_lo_to_A()  # restore A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCPX #{a:02X} \t--> C={c} N={n} Z={z}')

    def executeCPX_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()          # M = mem[0x00:MAR_lo] -> MBR
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.transferX_to_A()       # A = X (its N/Z update is overwritten by the CMP)
        yield from self.aluCMP_MBR()           # flags from X - M
        yield from self.transferMAR_hi_to_A()  # restore A
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCPX ${m:02X} \t--> C={c} N={n} Z={z}')

    def executeCPY_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR (MAR is now free)
        yield from self.transferA_to_MAR_lo()  # park A in the now-unused MAR_lo
        yield from self.transferY_to_A()       # A = Y
        yield from self.aluCMP_MBR()           # flags from Y - M
        yield from self.transferMAR_lo_to_A()  # restore A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tCPY ${b:02X}{a:02X} \t--> C={c} N={n} Z={z}')
        
    def executeCPY_IMM(self):
        # save A to MAR_lo to load Y into A to do the comparison
        # because (a) input of the ALU is hardcoded to A
        yield from self.incPC()
        yield from self.transferA_to_MAR_lo()
        yield from self.transferY_to_A()
        yield from self.fetchMBR()
        a = self.parent.children['datapath']._wires['q_MBR'].get()
        yield from self.aluCMP_MBR()
        yield from self.transferMAR_lo_to_A()
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCPY #{a:02X} \t--> C={c} N={n} Z={z}')
        
    def executeCPY_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()          # M = mem[0x00:MAR_lo] -> MBR
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.transferY_to_A()       # A = Y
        yield from self.aluCMP_MBR()           # flags from Y - M
        yield from self.transferMAR_hi_to_A()  # restore A
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tCPY ${m:02X} \t--> C={c} N={n} Z={z}')

    def executeDEC_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.decMBR()           # MBR = M - 1, update N and Z
        yield from self.storeMBR()         # write back through MAR
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tDEC ${b:02X}{a:02X} \t--> M={r:02X} N={n} Z={z}')
        
    def executeDEC_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry goes into MAR_hi)
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.decMBR()           # MBR = M - 1, update N and Z
        yield from self.storeMBR()         # write back to the same address
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tDEC ${b:02X}{a:02X},X \t--> M={r:02X} N={n} Z={z}')    
    
    def executeDEC_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.decMBR()           # MBR = M - 1, update N and Z
        yield from self.storeMBR_ZP()      # write the result back
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tDEC ${m:02X} \t--> M={r:02X} N={n} Z={z}')
        
    def executeDEC_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.decMBR()           # MBR = M - 1, update N and Z
        yield from self.storeMBR_ZP()      # write back to the same address
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tDEC ${m:02X},X \t--> M={r:02X} N={n} Z={z}')
        
    def executeDEX(self):
        yield from self.decX()
        yield from self.incPC()
        print(f'\t\t\tDEX')

    def executeDEY(self):
        yield from self.decY()
        yield from self.incPC()
        print(f'\t\t\tDEY')

    def executeEOR_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluXOR_MBR()       # A = A ^ M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tEOR ${b:02X}{a:02X} = {m:02X} \t--> A={r:02X} N={n} Z={z}')

    def executeEOR_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry into MAR_hi), A is preserved
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluXOR_MBR()       # A = A ^ M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tEOR ${b:02X}{a:02X},X \t--> [{mar:04X}]={m:02X} A={r:02X} N={n} Z={z}')

    def executeEOR_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + Y (carry into MAR_hi), A is preserved
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluXOR_MBR()       # A = A ^ M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tEOR ${b:02X}{a:02X},Y \t--> [{mar:04X}]={m:02X} A={r:02X} N={n} Z={z}')

    def executeEOR_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()         # immediate operand -> MBR
        yield from self.aluXOR_MBR()       # A = A ^ M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tEOR #{m:02X} \t--> A={a:02X} N={n} Z={z}')

    def executeEOR_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page base -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()            # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()              # (ptr + 1) & 0xFF, wraps in zero page
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()           # M = mem[pointer] -> MBR
        yield from self.aluXOR_MBR()             # A = A ^ M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tEOR $({a:02X},X) \t--> [{mar:04X}]={m:02X} A={r:02X} N={n} Z={z}')

    def executeEOR_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page pointer address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()              # (ptr + 1) & 0xFF, wraps in zero page
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        yield from self.addY_to_MAR()            # MAR = pointer + Y (carry into MAR_hi)
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()           # M = mem[MAR] -> MBR
        yield from self.aluXOR_MBR()             # A = A ^ M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tEOR $({a:02X}),Y \t--> [{mar:04X}]={m:02X} A={r:02X} N={n} Z={z}')

    def executeEOR_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluXOR_MBR()       # A = A ^ M, update N and Z
        yield from self.incPC()
        addr = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tEOR ${addr:02X} = {m:02X} \t--> A={a:02X} N={n} Z={z}')

    def executeEOR_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        base = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF, A is preserved
        mar = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluXOR_MBR()       # A = A ^ M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tEOR ${base:02X},X \t--> [{mar:02X}]={m:02X} A={a:02X} N={n} Z={z}')

    def executeINC_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()
        yield from self.incMBR()
        yield from self.storeMBR()
        print(f'\t\t\tINC ${b:02X}{a:02X}')

    def executeINC_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry goes into MAR_hi)
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.incMBR()           # MBR = M + 1, update N and Z
        yield from self.storeMBR()         # write back to the same address
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tINC ${b:02X}{a:02X},X \t--> M={r:02X} N={n} Z={z}')
    def executeINC_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.incMBR()           # MBR = M + 1, update N and Z
        yield from self.storeMBR_ZP()      # write the result back
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tINC ${m:02X} \t--> M={r:02X} N={n} Z={z}')
        
    def executeINC_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.incMBR()           # MBR = M + 1, update N and Z
        yield from self.storeMBR_ZP()      # write back to the same address
        yield from self.incPC()
        r = self.parent.children['datapath']._wires['q_MBR'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tINC ${m:02X},X \t--> M={r:02X} N={n} Z={z}')
        
    def executeINX(self):
        yield from self.incX()
        x = self.parent.children['datapath']._wires['q_X'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        yield from self.incPC()
        print(f'\t\tINX\t\t--> X={x:02X} N={n} Z={z}')

    def executeINY(self):
        yield from self.incY()
        yield from self.incPC()
        print(f'\t\tINY')
        
    def executeLDA_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        print(f'\tLDA ${mar:04X}\t-->[{mar:04X}]={a:02X}')
        
    def executeLDA_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()
        yield from self.fetchMAR_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        print(f'\tLDA ${b:02X}{a:02X},X ')
        
    def executeLDA_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()
        yield from self.fetchMAR_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        print(f'\tLDA ${b:02X}{a:02X},X ')
        
        
    def executeLDA_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()
        yield from self.fetchZP_MBR() # should go to MAR_lo
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi() 
        yield from self.transferMBR_to_MAR_lo()
        yield from self.fetchMAR_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        print(f'\t\tLDA $({a:02X},X)')
        
    
    def executeLDA_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR() # should go to MAR_lo
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi() 
        yield from self.transferMBR_to_MAR_lo()
        yield from self.addY_to_MAR()
        yield from self.fetchMAR_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        print(f'\tLDA $({a:02X}),Y ')


        
    def executeLDA_IMM(self):
        yield from self.incPC()
        yield from self.fetchA()
        yield from self.saveFlagsA()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\t\tLDA #{a:02X}\t\t--> A={a:02X} N={n} Z={z}')


    def executeLDA_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        print(f'\t\tLDA ${x:02X} ')

    def executeLDA_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()
        yield from self.fetchZP_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        a_val = self.parent.children['datapath']._wires['q_A'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\t\tLDA ${a:02X},X \t--> A={a_val:02X} N={n} Z={z}')
        
    def executeLDX_IMM(self):
        yield from self.incPC()
        yield from self.fetchX()
        yield from self.saveFlagsX()
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_X'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\t\tLDX #{x:02X}\t\t--> X={x:02X} N={n} Z={z}')

    def executeLDX_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_X()
        yield from self.saveFlagsX()
        yield from self.incPC()
        print(f'\tLDX ${b:02X}{a:02X}')

    def executeLDX_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + Y (carry goes into MAR_hi)
        yield from self.fetchMAR_X()       # X = mem[MAR]
        yield from self.saveFlagsX()       # update N and Z from X
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_X'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\tLDX ${b:02X}{a:02X},Y \t--> X={x:02X} N={n} Z={z}')
        
    def executeLDX_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_X()
        yield from self.saveFlagsX()
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_X'].get()
        print(f'\t\tLDX ${x:02X} ')
        
    def executeLDX_ZPY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addY_to_MAR()      # MAR_lo = (base + Y) & 0xFF
        yield from self.fetchZP_X()        # X = mem[0x00:MAR_lo]
        yield from self.saveFlagsX()       # update N and Z from X
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_X'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\t\tLDX ${m:02X},Y \t--> X={x:02X} N={n} Z={z}')
    
    def executeLDY_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_Y()
        yield from self.saveFlagsY()
        yield from self.incPC()
        print(f'\tLDY ${b:02X}{a:02X}')
        
    def executeLDY_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry goes into MAR_hi)
        yield from self.fetchMAR_Y()       # Y = mem[MAR]
        yield from self.saveFlagsY()       # update N and Z from X
        yield from self.incPC()
        y = self.parent.children['datapath']._wires['q_Y'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\tLDY ${b:02X}{a:02X},Y \t--> Y={y:02X} N={n} Z={z}')

    def executeLDY_IMM(self):
        yield from self.incPC()
        yield from self.fetchY()
        yield from self.saveFlagsY()
        yield from self.incPC()
        y = self.parent.children['datapath']._wires['q_Y'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()

        print(f'\t\tLDY #{y:02X}\t\t--> Y={y:02X} N={n} Z={z}')

    def executeLDY_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_Y()        # Y = mem[0x00:MAR_lo]
        yield from self.saveFlagsY()       # update N and Z from Y
        yield from self.incPC()
        y = self.parent.children['datapath']._wires['q_Y'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\t\tLDY ${m:02X} \t--> Y={y:02X} N={n} Z={z}')

    def executeLDY_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_Y()        # Y = mem[0x00:MAR_lo]
        yield from self.saveFlagsY()       # update N and Z from Y
        yield from self.incPC()
        y = self.parent.children['datapath']._wires['q_Y'].get()
        n = self.status['q_N'].get()
        z = self.status['q_Z'].get()
        print(f'\t\tLDY ${m:02X},X \t--> Y={y:02X} N={n} Z={z}')        
        
    # LSR reuses the ALU ROR path: ROR shifts q_C into bit 7, so clearing C first
    # gives {0, M[7:1]} with C = old M[0] and N = 0. No dedicated ALU op is needed.

    def executeLSR_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.pushA()                # save A on the stack (MAR still holds the address)
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR
        yield from self.transferMBR_to_A()     # A = M
        yield from self.setC(0)                # shift a 0 into bit 7
        yield from self.aluROR_A()             # A = {0, M[7:1]}, C = old M[0], N = 0, update Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA()               # mem[MAR] = A
        yield from self.popA()                 # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tLSR ${b:02X}{a:02X} \t--> M={r:02X} C={c} N={n} Z={z}')

    def executeLSR_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()          # MAR = base + X (carry into MAR_hi), A is preserved
        yield from self.pushA()                # save A on the stack (MAR still holds the address)
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR
        yield from self.transferMBR_to_A()     # A = M
        yield from self.setC(0)                # shift a 0 into bit 7
        yield from self.aluROR_A()             # A = {0, M[7:1]}, C = old M[0], N = 0, update Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA()               # mem[MAR] = A
        yield from self.popA()                 # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tLSR ${b:02X}{a:02X},X \t--> M={r:02X} C={c} N={n} Z={z}')

    def executeLSR_ACC(self):
        yield from self.setC(0)                # shift a 0 into bit 7
        yield from self.aluROR_A()             # A = {0, A[7:1]}, C = old A[0], N = 0, update Z
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\t\tLSR A\t\t--> A={a:02X} C={c} N={n} Z={z}')

    def executeLSR_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.fetchZP_A()            # A = M
        yield from self.setC(0)                # shift a 0 into bit 7
        yield from self.aluROR_A()             # A = {0, M[7:1]}, C = old M[0], N = 0, update Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA_ZP()            # mem[0x00:MAR_lo] = A
        yield from self.transferMAR_hi_to_A()  # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tLSR ${m:02X} \t--> M={r:02X} C={c} N={n} Z={z}')

    def executeLSR_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()          # MAR_lo = (base + X) & 0xFF, A is preserved
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.fetchZP_A()            # A = M
        yield from self.setC(0)                # shift a 0 into bit 7
        yield from self.aluROR_A()             # A = {0, M[7:1]}, C = old M[0], N = 0, update Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA_ZP()            # mem[0x00:MAR_lo] = A
        yield from self.transferMAR_hi_to_A()  # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tLSR ${m:02X},X \t--> M={r:02X} C={c} N={n} Z={z}')

    def executeJMP_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        yield from self.transferMAR_to_PC()
        pc = self.parent.children['datapath']._wires['q_PC'].get()
        print(f'\tJMP {pc:04X} ')
        
    def executeJMP_IND(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        
        yield from self.fetchMAR_PC_lo()
        yield from self.incMAR_lo() # should be incMAR to allow page crossing
        yield from self.fetchMAR_PC_hi()
        print(f'\tJMP $({b:02X}{a:02X}) ')

    def executeJSR_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        yield from self.pushPC_hi()
        yield from self.pushPC_lo()
        yield from self.transferMAR_to_PC()
        pc = self.parent.children['datapath']._wires['q_PC'].get()
        print(f'\tJSR {pc:04X} ')

    def executeORA_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluOR_MBR()        # A = A | M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tORA ${b:02X}{a:02X} = {m:02X} \t--> A={r:02X} N={n} Z={z}')
    
    def executeORA_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry into MAR_hi), A is preserved
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.aluOR_MBR()        # A = A | M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tORA ${b:02X}{a:02X},X \t-->{mar:02X}={m:02X} A={r:02X} N={n} Z={z}')
        
    def executeORA_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + Y (carry into MAR_hi), A is preserved
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluOR_MBR()        # A = A | M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tORA ${b:02X}{a:02X},Y \t-->{mar:02X}={m:02X} A={r:02X} N={n} Z={z}')
        
    def executeORA_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        yield from self.aluOR_MBR()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tORA #{a:02X} \t--> (A={a:02X}) (N={n}) (Z={z})')
    
    def executeORA_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page base -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()            # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()           # M = mem[pointer] -> MBR
        yield from self.aluOR_MBR()              # A = A | M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tORA $({a:02X},X) \t--> [{mar:04X}]={m:02X} A={r:02X} N={n} Z={z}')
    
    def executeORA_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page pointer address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        yield from self.addY_to_MAR()            # MAR = pointer + Y
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()           # M = mem[MAR] -> MBR
        yield from self.aluOR_MBR()              # A = A | M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tORA $({a:02X}),Y \t--> [{mar:04X}]={m:02X} A={r:02X} N={n} Z={z}')
        
    def executeORA_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_MBR()
        yield from self.aluOR_MBR()
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tORA ${m:02X} \t--> (A={a:02X}) (N={n}) (Z={z})')
        
    def executeORA_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        base = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF, A is preserved
        mar = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluOR_MBR()        # A = A | M, update N and Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tORA ${base:02X},X \t--> {mar:04X}={m:02X} A={a:02X} N={n} Z={z}')
        
    def executePHA(self):
        yield from self.pushA()
        yield from self.incPC()    
        print(f'\t\tPHA')
        
    def executePHP(self):
        yield from self.pushP()
        yield from self.incPC()
        p = self.parent.children['datapath']._wires['q_P'].get()
        print(f'\t\tPHP\t\t--> P={p:02X}')
        
    def executePLA(self):
        yield from self.popA()
        yield from self.saveFlagsA()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tPLA\t\t--> A={a:02X} N={n} Z={z}')

    def executeROR_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.pushA()                # save A on the stack (MAR still holds the address)
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR
        yield from self.transferMBR_to_A()     # A = M
        yield from self.aluROR_A()             # A = {C, M[7:1]}, C = old M[0], update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA()               # mem[MAR] = A
        yield from self.popA()                 # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tROR ${b:02X}{a:02X} \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeROR_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()          # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()          # MAR = base + X (carry into MAR_hi), A is preserved
        yield from self.pushA()                # save A on the stack (MAR still holds the address)
        yield from self.fetchMAR_MBR()         # M = mem[MAR] -> MBR
        yield from self.transferMBR_to_A()     # A = M
        yield from self.aluROR_A()             # A = {C, M[7:1]}, C = old M[0], update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA()               # mem[MAR] = A
        yield from self.popA()                 # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\tROR ${b:02X}{a:02X},X \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeROR_ACC(self):
        yield from self.aluROR_A()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\t\tROR A\t\t--> A={a:02X} C={c} N={n} Z={z}')
        
    def executeROR_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.fetchZP_A()            # A = M
        yield from self.aluROR_A()             # A = {C, M[7:1]}, C = old M[0], update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA_ZP()            # mem[0x00:MAR_lo] = A
        yield from self.transferMAR_hi_to_A()  # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tROR ${m:02X} \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeROR_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # base zero-page address -> MAR_lo
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()          # MAR_lo = (base + X) & 0xFF, A is preserved
        yield from self.transferA_to_MAR_hi()  # park A (MAR_hi is unused in zero page)
        yield from self.fetchZP_A()            # A = M
        yield from self.aluROR_A()             # A = {C, M[7:1]}, C = old M[0], update N and Z
        r = self.parent.children['datapath']._wires['q_A'].get()
        yield from self.storeA_ZP()            # mem[0x00:MAR_lo] = A
        yield from self.transferMAR_hi_to_A()  # restore the real A
        yield from self.incPC()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tROR ${m:02X},X \t--> M={r:02X} C={c} N={n} Z={z}')
        
    def executeRTI(self):
        yield from self.popMBR()      # P -> MBR
        yield from self.restoreFlags()     # C Z I D V N <- MBR bits (B and bit 5 ignored)
        yield from self.popPC_lo()
        yield from self.popPC_hi()         # no incPC: BRK already pushed the return address
        pc = self.parent.children['datapath']._wires['q_PC'].get()
        print(f'\t\tRTI \t\t--> PC={pc:04X}')
        
    def executeRTS(self):
        yield from self.popPC_lo()
        yield from self.popPC_hi()
        yield from self.incPC()    
        print(f'\t\tRTS')
        
    def executeSBC_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluSUB_MBR()       # A = A - M - (1 - C), update C, N, Z, V
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\tSBC ${b:02X}{a:02X} = {m:02X} \t--> A={r:02X} C={c} N={n} Z={z} V={v}')
        
    def executeSBC_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry into MAR_hi), A is preserved
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluSUB_MBR()       # A = A - M - (1 - C), update C, N, Z, V
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\tSBC ${b:02X}{a:02X},X = {m:02X} \t--> A={r:02X} C={c} N={n} Z={z} V={v}')
    
    def executeSBC_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + Y (carry into MAR_hi), A is preserved
        yield from self.fetchMAR_MBR()     # M = mem[MAR] -> MBR
        yield from self.aluSUB_MBR()       # A = A - M - (1 - C), update C, N, Z, V
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\tSBC ${b:02X}{a:02X},Y = {m:02X} \t--> A={r:02X} C={c} N={n} Z={z} V={v}')
        
    def executeSBC_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()         # operand -> MBR
        yield from self.aluSUB_MBR()       # A = A - M - (1 - C), update C, N, Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tSBC #{m:02X} \t--> A={a:02X} C={c} N={n} Z={z} V={v}')
        
    def executeSBC_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page base -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()            # MAR_lo = (base + X) & 0xFF
        ax = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        yield from self.fetchMAR_MBR()           # M = mem[pointer] -> MBR
        yield from self.aluSUB_MBR()             # A = A - M - (1 - C), update C, N, Z, V
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tSBC $({a:02X},X) \t--> [{ax:04X}]={m:02X} A={r:02X} C={c} N={n} Z={z} V={v}')
    
    def executeSBC_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()              # zero-page pointer address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR()              # pointer low byte -> MBR
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi()           # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()    # MAR = 16-bit pointer
        yield from self.addY_to_MAR()              # MAR = pointer + Y (carry into MAR_hi)
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        yield from self.fetchMAR_MBR()             # M = mem[MAR] -> MBR
        yield from self.aluSUB_MBR()               # A = A - M - (1 - C), update C, N, Z, V
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        r = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tSBC $({a:02X}),Y \t--> [{mar:04X}]={m:02X} A={r:02X} C={c} N={n} Z={z} V={v}')
        
    def executeSBC_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()          # zero-page address -> MAR_lo
        yield from self.fetchZP_MBR()          # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluSUB_MBR()           # A = A - M - (1 - C), update C, N, Z
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        v = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tSBC ${m:02X} = {v:02X} \t--> A={a:02X} C={c} N={n} Z={z} V={v}')

    def executeSBC_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        base = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF, A is preserved
        yield from self.fetchZP_MBR()      # M = mem[0x00:MAR_lo] -> MBR
        yield from self.aluSUB_MBR()       # A = A - M - (1 - C), update C, N, Z, V
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        v = self.status['q_V'].get()
        print(f'\t\tSBC ${base:02X},X = {m:02X} \t--> A={a:02X} C={c} N={n} Z={z} V={v}')

    def executeSEC(self):
        control = self.control
        # A compared with A: A + ~A + 1 = 0x100, so the carry out is always 1
        control['alu_op'].prepare(ALU.OP_CMP)
        control['alu_sel_A'].prepare(1)
        control['d_C'].prepare(1)
        control['sel_C'].prepare(1)
        control['e_C'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(0)
        control['d_C'].prepare(0)
        control['sel_C'].prepare(0)
        control['e_C'].prepare(0)
        yield

        yield from self.incPC()
        c = self.status['q_C'].get()
        print(f'\t\tSEC \t\t--> (C={c})')
        
    def executeSED(self):
        control = self.control
        control['d_D'].prepare(1)
        control['e_D'].prepare(1)
        yield
        control['d_D'].prepare(0)
        control['e_D'].prepare(0)
        yield

        yield from self.incPC()
        d = self.status['q_D'].get()
        print(f'\t\tSED \t\t--> (D={d})')

    def executeSEI(self):
        yield from self.setI()             # d_I=1, e_I=1 for one cycle, then restored
        yield from self.incPC()
        i = self.status['q_I'].get()
        print(f'\t\tSEI \t\t--> (I={i})')

    def executeSTA_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        yield from self.storeA()
        yield from self.incPC()
        mar = self.parent.children['datapath']._wires['q_MAR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        
        print(f'\tSTA ${mar:04X} \t-->[{mar:04X}]={a:02X}')
        
    def executeSTA_ABSX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addX_to_MAR()      # MAR = base + X (carry into MAR_hi), A is preserved
        yield from self.storeA()           # mem[MAR] = A
        yield from self.incPC()
        print(f'\tSTA ${b:02X}{a:02X},X ')
        
    def executeSTA_ABSY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base address low byte -> MAR_lo
        yield from self.incPC()
        yield from self.fetchMAR_hi()      # base address high byte -> MAR_hi
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.addY_to_MAR()      # MAR = base + Y (carry into MAR_hi), A is preserved
        yield from self.storeA()           # mem[MAR] = A
        yield from self.incPC()
        print(f'\tSTA ${b:02X}{a:02X},Y ')
        
    def executeSTA_INDX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()            # zero-page base -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()            # MAR_lo = (base + X) & 0xFF
        yield from self.fetchZP_MBR()            # pointer low byte -> MBR
        yield from self.incMAR_lo()              # (ptr + 1) & 0xFF, wraps in zero page
        yield from self.fetchZP_MAR_hi()         # pointer high byte -> MAR_hi
        yield from self.transferMBR_to_MAR_lo()  # MAR = 16-bit pointer
        yield from self.storeA()                 # mem[MAR] = A
        yield from self.incPC()
        print(f'\t\tSTA $({a:02X},X)')
        
    def executeSTA_INDY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.fetchZP_MBR() # should go to MAR_lo
        yield from self.incMAR_lo()
        yield from self.fetchZP_MAR_hi() 
        yield from self.transferMBR_to_MAR_lo()
        yield from self.addY_to_MAR()
        yield from self.storeA()
        yield from self.incPC()
        print(f'\tSTA $({a:02X}),Y ')

    def executeSTA_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.storeA_ZP()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        print(f'\t\tSTA ${a:02X} ')

    def executeSTA_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()
        yield from self.storeA_ZP()
        yield from self.incPC()
        print(f'\t\tSTA ${a:02X},X ')

    def executeSTX_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        yield from self.storeX()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        print(f'\tSTX ${b:02X}{a:02X} ')
    
    def executeSTX_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.storeX_ZP()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        print(f'\t\tSTX ${a:02X} ')
    
    def executeSTX_ZPY(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addY_to_MAR()      # MAR_lo = (base + Y) & 0xFF
        yield from self.storeX_ZP()        # mem[0x00:MAR_lo] = X
        yield from self.incPC()
        print(f'\t\tSTX ${a:02X},Y ')
        
    def executeSTY_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        yield from self.storeY()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        print(f'\tSTY ${b:02X}{a:02X} ')
    
    def executeSTY_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # zero-page address -> MAR_lo
        yield from self.storeY_ZP()        # mem[0x00:MAR_lo] = Y
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        print(f'\t\tSTY ${a:02X} ')
        
    def executeSTY_ZPX(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()      # base zero-page address -> MAR_lo
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        yield from self.addX_to_MAR()      # MAR_lo = (base + X) & 0xFF
        yield from self.storeY_ZP()        # mem[0x00:MAR_lo] = Y
        yield from self.incPC()
        print(f'\t\tSTY ${a:02X},X ')
        
    def executeTAX(self):
        yield from self.incPC()
        yield from self.transferA_to_X()
        yield from self.saveFlagsX()
        x = self.parent.children['datapath']._wires['q_X'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tTAX\t\t--> X={x:02X} (N={n}) (Z={z})')

    def executeTAY(self):
        yield from self.incPC()
        yield from self.transferA_to_Y()
        yield from self.saveFlagsY()
        y = self.parent.children['datapath']._wires['q_Y'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\t\tTAY\t\t\t--> Y={y:02X} (N={n}) (Z={z})')
    
    def executeTSX(self):
        yield from self.incPC()
        yield from self.transferS_to_X()
        x = self.parent.children['datapath']._wires['q_X'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tTSX\t\t--> X={x:02X} (N={n}) (Z={z})')

    def executeTXA(self):
        yield from self.incPC()
        yield from self.transferX_to_A()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\t\tTXA\t\t\t--> A={a:02X} (N={n}) (Z={z})')
        
    def executeTXS(self):
        yield from self.incPC()
        yield from self.transferX_to_S()
        s = self.parent.children['datapath']._wires['q_SP'].get()
        print(f'\t\tTXS\t\t--> SP={s:02X}')
        
    def executeTYA(self):
        yield from self.incPC()
        yield from self.transferY_to_A()
        yield from self.saveFlagsA()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\t\tTYA\t\t\t--> A={a:02X} (N={n}) (Z={z})')

    def aluADD_MBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_ADD)
        control['alu_sel_MBR'].prepare(1)
        control['e_A'].prepare(1)
        control['e_C'].prepare(1)
        control['sel_C'].prepare(0) # alu C
        control['e_V'].prepare(1)
        control['sel_V'].prepare(0) # alu V
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
        control['e_C'].prepare(0)
        control['sel_C'].prepare(0)
        control['e_V'].prepare(0)
        control['sel_V'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def aluASL_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_ADD_NO_CARRY)   # A + A = A << 1
        control['alu_sel_A'].prepare(1)
        control['e_A'].prepare(1)
        control['e_C'].prepare(1)    # C = old bit 7
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(0)
        control['e_A'].prepare(0)
        control['e_C'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def aluCMP_MBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_CMP)
        control['alu_sel_MBR'].prepare(1)
        control['e_C'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_C'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_N'].prepare(0)
        yield

    def aluAND_MBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_AND)
        control['alu_sel_MBR'].prepare(1)
        control['e_A'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def aluOR_MBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_OR)
        control['alu_sel_MBR'].prepare(1)
        control['e_A'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def aluXOR_MBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_XOR)
        control['alu_sel_MBR'].prepare(1)
        control['e_A'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield

    def aluROR_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_ROR)
        control['e_A'].prepare(1)
        control['e_C'].prepare(1)    # C = old bit 0
        control['e_N'].prepare(1)    # N = old C
        control['e_Z'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['e_A'].prepare(0)
        control['e_C'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def aluSUB_MBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_SUB)      # A + ~M + C
        control['alu_sel_MBR'].prepare(1)
        control['e_A'].prepare(1)
        control['e_C'].prepare(1)                  # C = 1 when no borrow
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_V'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
        control['e_C'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_V'].prepare(0)
        yield
        
    def transferA_to_X(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        control['e_X'].prepare(1)
        yield
        control['alu_sel_A'].prepare(0)
        control['e_X'].prepare(0)
        yield

    def transferA_to_Y(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        control['e_Y'].prepare(1)
        yield
        control['alu_sel_A'].prepare(0)
        control['e_Y'].prepare(0)
        yield
        
    def transferS_to_X(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_SP'].prepare(1)
        control['e_X'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_SP'].prepare(0)
        control['e_X'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def transferX_to_S(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_X'].prepare(1)
        control['e_SP'].prepare(1)
        yield
        control['alu_sel_X'].prepare(0)
        control['e_SP'].prepare(0)
        yield
        
    def transferX_to_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_X'].prepare(1)
        control['e_A'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_X'].prepare(0)
        control['e_A'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield

    def transferMAR_to_PC(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MAR_lo'].prepare(1)
        control['e_PC_lo'].prepare(1)
        yield
        control['alu_sel_MAR_lo'].prepare(0)
        control['e_PC_lo'].prepare(0)
        control['alu_sel_MAR_hi'].prepare(1)
        control['e_PC_hi'].prepare(1)
        yield
        control['alu_sel_MAR_hi'].prepare(0)
        control['e_PC_hi'].prepare(0)
        yield

    def transferA_to_MAR_lo(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        control['alu_sel_A'].prepare(0)
        control['e_MAR_lo'].prepare(0)
        yield

    def transferA_to_MAR_hi(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        control['e_MAR_hi'].prepare(1)
        yield
        control['alu_sel_A'].prepare(0)
        control['e_MAR_hi'].prepare(0)
        yield
        
    def transferA_to_MBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        control['e_MBR'].prepare(1)
        yield
        control['alu_sel_A'].prepare(0)
        control['e_MBR'].prepare(0)
        yield
        
    def transferMAR_lo_to_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MAR_lo'].prepare(1)
        control['e_A'].prepare(1)
        yield
        control['alu_sel_MAR_lo'].prepare(0)
        control['e_A'].prepare(0)
        yield
        
    def transferMAR_hi_to_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MAR_hi'].prepare(1)
        control['e_A'].prepare(1)
        yield
        control['alu_sel_MAR_hi'].prepare(0)
        control['e_A'].prepare(0)
        yield
        
    def transferMBR_to_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(1)
        control['e_A'].prepare(1)
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
        yield
    
    def transferMBR_to_MAR_lo(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_MAR_lo'].prepare(0)
        yield
        
    def transferPC_lo_to_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_PC_lo'].prepare(1)
        control['e_A'].prepare(1)
        yield
        control['alu_sel_PC_lo'].prepare(0)
        control['e_A'].prepare(0)
        yield
    
    def transferY_to_A(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_Y'].prepare(1)
        control['e_A'].prepare(1)
        yield
        control['alu_sel_Y'].prepare(0)
        control['e_A'].prepare(0)
        yield
        
    def saveFlagsA(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_A'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def saveFlagsX(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_X'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_X'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield

    def saveFlagsY(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_Y'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_Y'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield

    def saveFlags(self):
        control = self.control
        control['e_C'].prepare(1)
        control['sel_C'].prepare(0) # alu C
        control['e_V'].prepare(1)
        control['sel_V'].prepare(0) # alu V
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['e_C'].prepare(0)
        control['sel_C'].prepare(0)
        control['e_V'].prepare(0)
        control['sel_V'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
    
        
    def setC(self, value):
        control = self.control
        control['d_C'].prepare(value)
        control['sel_C'].prepare(1)      # take the value from the CU, not the ALU
        control['e_C'].prepare(1)
        yield
        control['d_C'].prepare(0)
        control['sel_C'].prepare(0)      # back to the ALU carry
        control['e_C'].prepare(0)
        yield
        
    def setI(self):
        control = self.control
        control['d_I'].prepare(1)
        control['e_I'].prepare(1)
        yield
        control['d_I'].prepare(0)
        control['e_I'].prepare(0)
        yield
        
    def loadVector_to_MAR(self):
        control = self.control
        # 0 - 1 = 0xFF into both MAR_lo and MAR_hi
        control['alu_op'].prepare(ALU.OP_DEC)
        control['e_MAR_lo'].prepare(1)
        control['e_MAR_hi'].prepare(1)
        yield
        control['e_MAR_lo'].prepare(0)
        control['e_MAR_hi'].prepare(0)
        yield
        # MAR_lo = 0xFF - 1 = 0xFE
        control['alu_sel_MAR_lo'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MAR_lo'].prepare(0)
        control['e_MAR_lo'].prepare(0)
        yield
        
    def addX_to_MAR(self):
        # save A to MAR_lo
        yield from self.transferA_to_MBR()
        # put PC_lo to A
        yield from self.transferMAR_lo_to_A()
        
        # Check negative value
        control = self.control
        status = self.status
        
        # we should add
        control['alu_op'].prepare(ALU.OP_ADD_NO_CARRY)
        control['alu_sel_X'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        if self.status['alu_C'].get():
            control['alu_op'].prepare(ALU.OP_INC)
            control['alu_sel_X'].prepare(0)
            control['e_MAR_lo'].prepare(0)
            control['alu_sel_MAR_hi'].prepare(1)
            control['e_MAR_hi'].prepare(1)
            yield
            control['alu_op'].prepare(ALU.OP_BYPASS)
            control['alu_sel_MAR_hi'].prepare(0)
            control['e_MAR_hi'].prepare(0)
            yield
        else:
            control['alu_op'].prepare(ALU.OP_BYPASS)
            control['alu_sel_X'].prepare(0)
            control['e_MAR_lo'].prepare(0)
            yield
            
        yield from self.transferMBR_to_A()

    def addY_to_MAR(self):
        # save A to MAR_lo
        yield from self.transferA_to_MBR()
        # put PC_lo to A
        yield from self.transferMAR_lo_to_A()
        
        # Check negative value
        control = self.control
        status = self.status
        
        # we should add
        control['alu_op'].prepare(ALU.OP_ADD_NO_CARRY)
        control['alu_sel_Y'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        if self.status['alu_C'].get():
            control['alu_op'].prepare(ALU.OP_INC)
            control['alu_sel_Y'].prepare(0)
            control['e_MAR_lo'].prepare(0)
            control['alu_sel_MAR_hi'].prepare(1)
            control['e_MAR_hi'].prepare(1)
            yield
            control['alu_op'].prepare(ALU.OP_BYPASS)
            control['alu_sel_MAR_hi'].prepare(0)
            control['e_MAR_hi'].prepare(0)
            yield
        else:
            control['alu_op'].prepare(ALU.OP_BYPASS)
            control['alu_sel_Y'].prepare(0)
            control['e_MAR_lo'].prepare(0)
            yield
            
        yield from self.transferMBR_to_A()
        
    def addMBR_to_PC(self):
        # save A to MAR_lo
        yield from self.transferA_to_MAR_lo()
        # put PC_lo to A
        yield from self.transferPC_lo_to_A()
        
        # Check negative value
        control = self.control
        status = self.status
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(1)
        yield
        if (status['alu_N'].get()):
            # We should add
            control['alu_op'].prepare(ALU.OP_ADD_NO_CARRY)
            control['alu_sel_MBR'].prepare(1)
            control['e_PC_lo'].prepare(1)
            yield
            if self.status['alu_C'].get() == 0:
                control['alu_op'].prepare(ALU.OP_DEC)
                control['alu_sel_MBR'].prepare(0)
                control['e_PC_lo'].prepare(0)
                control['alu_sel_PC_hi'].prepare(1)
                control['e_PC_hi'].prepare(1)
                yield
                control['alu_op'].prepare(ALU.OP_BYPASS)
                control['alu_sel_PC_hi'].prepare(0)
                control['e_PC_hi'].prepare(0)
                yield
            else:
                control['alu_op'].prepare(ALU.OP_BYPASS)
                control['alu_sel_MBR'].prepare(0)
                control['e_PC_lo'].prepare(0)
                yield

        else:
            # we should add
            control['alu_op'].prepare(ALU.OP_ADD_NO_CARRY)
            control['alu_sel_MBR'].prepare(1)
            control['e_PC_lo'].prepare(1)
            yield
            if self.status['alu_C'].get():
                control['alu_op'].prepare(ALU.OP_INC)
                control['alu_sel_MBR'].prepare(0)
                control['e_PC_lo'].prepare(0)
                control['alu_sel_PC_hi'].prepare(1)
                control['e_PC_hi'].prepare(1)
                yield
                control['alu_op'].prepare(ALU.OP_BYPASS)
                control['alu_sel_PC_hi'].prepare(0)
                control['e_PC_hi'].prepare(0)
                yield
            else:
                control['alu_op'].prepare(ALU.OP_BYPASS)
                control['alu_sel_MBR'].prepare(0)
                control['e_PC_lo'].prepare(0)
                yield
            
        yield from self.transferMAR_lo_to_A()
        
    def decMBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_DEC)
        control['alu_sel_MBR'].prepare(1)
        control['e_MBR'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(0)
        control['e_MBR'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_N'].prepare(0)
        yield
         
    def incMAR_lo(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_INC)
        control['alu_sel_MAR_lo'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        control['alu_sel_MAR_lo'].prepare(0)
        control['e_MAR_lo'].prepare(0)
        yield
        
    def incPC(self):
        # To inc pc we can reuse the ALU
        # PC_low = PC_low + 1
        # if carry...
        # PC_High = PC_High + 1
        control = self.control
        control['alu_op'].prepare(ALU.OP_INC)
        control['alu_sel_PC_lo'].prepare(1)
        control['e_PC_lo'].prepare(1)
        yield        
        if self.status['alu_C'].get():
            control['alu_op'].prepare(ALU.OP_INC)
            control['alu_sel_PC_lo'].prepare(0)
            control['e_PC_lo'].prepare(0)
            control['alu_sel_PC_hi'].prepare(1)
            control['e_PC_hi'].prepare(1)
            yield
            control['alu_op'].prepare(ALU.OP_BYPASS)
            control['alu_sel_PC_hi'].prepare(0)
            control['e_PC_hi'].prepare(0)
            yield
        else:
            control['alu_op'].prepare(ALU.OP_BYPASS)
            control['alu_sel_PC_lo'].prepare(0)
            control['e_PC_lo'].prepare(0)
            yield
        
    def incSP(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_INC)
        control['alu_sel_SP'].prepare(1)
        control['e_SP'].prepare(1)
        yield
        control['alu_sel_SP'].prepare(0)
        control['e_SP'].prepare(0)
        yield
        
    def incMBR(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_INC)
        control['alu_sel_MBR'].prepare(1)
        control['e_MBR'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_MBR'].prepare(0)
        control['e_MBR'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_N'].prepare(0)
        yield

   
        
    def incX(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_INC)
        control['alu_sel_X'].prepare(1)
        control['e_X'].prepare(1)
        #control['e_C'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)

        yield
        control['alu_sel_X'].prepare(0)
        control['e_X'].prepare(0)
        #control['e_C'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_N'].prepare(0)
        yield


    def incY(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_INC)
        control['alu_sel_Y'].prepare(1)
        control['e_Y'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)
        yield
        control['alu_sel_Y'].prepare(0)
        control['e_Y'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_N'].prepare(0)
        yield


    def decX(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_DEC)
        control['alu_sel_X'].prepare(1)
        control['e_X'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_X'].prepare(0)
        control['e_X'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_N'].prepare(0)

        yield

    def decY(self):
        # update the N and Z flags here
        control = self.control
        control['alu_op'].prepare(ALU.OP_DEC)
        control['alu_sel_Y'].prepare(1)
        control['e_Y'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_Y'].prepare(0)
        control['e_Y'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
        yield
        
    def decSP(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_DEC)
        control['alu_sel_SP'].prepare(1)
        control['e_SP'].prepare(1)
        yield
        control['alu_sel_SP'].prepare(0)
        control['e_SP'].prepare(0)
        yield
    
    
        
    def popPC_lo(self):
        yield from self.incSP()
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_PC_lo'].prepare(1)
        yield
        control['e_PC_lo'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield
    
    def popA(self):
        yield from self.incSP()
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_A'].prepare(1)
        yield
        control['e_A'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield

    def popPC_hi(self):
        yield from self.incSP()
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM) 
        control['e_PC_hi'].prepare(1)
        yield
        control['e_PC_hi'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU) 
        yield

    def popMBR(self):
        yield from self.incSP()
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_read'].prepare(1)
        yield
        yield
        control['mem_read'].prepare(0)
        control['sel_databus'].prepare(self.DATA_MEM)
        control['e_MBR'].prepare(1)
        yield
        control['e_MBR'].prepare(0)
        control['sel_databus'].prepare(self.DATA_ALU)
        yield

    def restoreFlags(self):
        control = self.control
        flags = ('e_C', 'e_Z', 'e_N', 'e_V', 'e_D', 'e_I')
        control['sel_flags'].prepare(1)          # take the flag bits from MBR
        for e in flags:
            control[e].prepare(1)
        yield
        control['sel_flags'].prepare(0)
        for e in flags:
            control[e].prepare(0)
        yield
        
    def pushA(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_A'].prepare(1)
        yield
        control['mem_write'].prepare(0)
        control['alu_sel_A'].prepare(0)
        yield
        yield from self.decSP()
        
    def pushPC_lo(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_PC_lo'].prepare(1)
        yield
        control['mem_write'].prepare(0)
        control['alu_sel_PC_lo'].prepare(0)
        yield
        yield from self.decSP()

    def pushPC_hi(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_PC_hi'].prepare(1)
        yield
        control['mem_write'].prepare(0)
        control['alu_sel_PC_hi'].prepare(0)
        yield
        yield from self.decSP()
        
    def pushP(self):
        control = self.control
        control['sel_memory'].prepare(self.MEM_SP) # select stack for address
        control['mem_write'].prepare(1)
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_P'].prepare(1)
        yield
        control['mem_write'].prepare(0)
        control['alu_sel_P'].prepare(0)
        yield
        yield from self.decSP()

    def decodeAndExecute(self):
        control = self.control
        op = self.status['q_IR'].get()
        decoded_ins, decoded_addressing = punxa_6502.ins_to_str(op)
        toread = punxa_6502.OPERAND_SIZE_MAP[decoded_addressing]
        
        #print(f'INS={op:02X} decoded:', decoded_ins, decoded_addressing, 'should read', toread, 'bytes')
        
        if (op == self.OPCODE_ADC_ABS):
            yield from self.executeADC_ABS()
        elif (op == self.OPCODE_ADC_ABSX):
            yield from self.executeADC_ABSX()
        elif (op == self.OPCODE_ADC_ABSY):
            yield from self.executeADC_ABSY()
        elif (op == self.OPCODE_ADC_IMM):
            yield from self.executeADC_IMM()
        elif (op == self.OPCODE_ADC_INDX):
            yield from self.executeADC_INDX()
        elif (op == self.OPCODE_ADC_INDY):
            yield from self.executeADC_INDY()
        elif (op == self.OPCODE_ADC_ZP):
            yield from self.executeADC_ZP()
        elif (op == self.OPCODE_ADC_ZPX):
            yield from self.executeADC_ZPX()
        elif (op == self.OPCODE_AND_ABS):
            yield from self.executeAND_ABS()
        elif (op == self.OPCODE_AND_ABSX):
            yield from self.executeAND_ABSX()
        elif (op == self.OPCODE_AND_ABSY):
            yield from self.executeAND_ABSY()
        elif (op == self.OPCODE_AND_IMM):
            yield from self.executeAND_IMM()
        elif (op == self.OPCODE_AND_INDX):
            yield from self.executeAND_INDX()
        elif (op == self.OPCODE_AND_INDY):
            yield from self.executeAND_INDY()
        elif (op == self.OPCODE_AND_ZP):
            yield from self.executeAND_ZP()
        elif (op == self.OPCODE_AND_ZPX):
            yield from self.executeAND_ZPX()
        elif (op == self.OPCODE_ASL_ABS):
            yield from self.executeASL_ABS()
        elif (op == self.OPCODE_ASL_ABSX):
            yield from self.executeASL_ABSX()
        elif (op == self.OPCODE_ASL_ACC):
            yield from self.executeASL_ACC()
        elif (op == self.OPCODE_ASL_ZP):
            yield from self.executeASL_ZP()
        elif (op == self.OPCODE_ASL_ZPX):
            yield from self.executeASL_ZPX()
        elif (op == self.OPCODE_BCC_REL):
            yield from self.executeBCC_REL()   
        elif (op == self.OPCODE_BEQ_REL):
            yield from self.executeBEQ_REL()
        elif (op == self.OPCODE_BNE_REL):
            yield from self.executeBNE_REL()
        elif (op == self.OPCODE_BPL_REL):
            yield from self.executeBPL_REL()
        elif (op == self.OPCODE_BVC_REL):
            yield from self.executeBVC_REL()
        elif (op == self.OPCODE_BVS_REL):
            yield from self.executeBVS_REL()
        elif (op == self.OPCODE_BRK):
            yield from self.executeBRK()
        elif (op == self.OPCODE_CLC):
            yield from  self.executeCLC()
        elif (op == self.OPCODE_CLD):
            yield from  self.executeCLD()
        elif (op == self.OPCODE_CLI):
            yield from self.executeCLI()
        elif (op == self.OPCODE_CLV):
            yield from self.executeCLV()
        elif (op == self.OPCODE_CMP_ABS):
            yield from self.executeCMP_ABS()
        elif (op == self.OPCODE_CMP_ABSX):
            yield from self.executeCMP_ABSX()
        elif (op == self.OPCODE_CMP_ABSY):
            yield from self.executeCMP_ABSY()            
        elif (op == self.OPCODE_CMP_IMM):
            yield from self.executeCMP_IMM()
        elif (op == self.OPCODE_CMP_INDX):
            yield from self.executeCMP_INDX()
        elif (op == self.OPCODE_CMP_INDY):
            yield from self.executeCMP_INDY()
        elif (op == self.OPCODE_CMP_ZP):
            yield from self.executeCMP_ZP()
        elif (op == self.OPCODE_CMP_ZPX):
            yield from self.executeCMP_ZPX()
        elif (op == self.OPCODE_CPX_ABS):
            yield from self.executeCPX_ABS()
        elif (op == self.OPCODE_CPX_IMM):
            yield from self.executeCPX_IMM()
        elif (op == self.OPCODE_CPX_ZP):
            yield from self.executeCPX_ZP()
        elif (op == self.OPCODE_CPY_ABS):
            yield from self.executeCPY_ABS()
        elif (op == self.OPCODE_CPY_IMM):
            yield from self.executeCPY_IMM()
        elif (op == self.OPCODE_CPY_ZP):
            yield from self.executeCPY_ZP()
        elif (op == self.OPCODE_DEC_ABS):
            yield from self.executeDEC_ABS()
        elif (op == self.OPCODE_DEC_ABSX):
            yield from self.executeDEC_ABSX()
        elif (op == self.OPCODE_DEC_ZP):
            yield from self.executeDEC_ZP()
        elif (op == self.OPCODE_DEC_ZPX):
            yield from self.executeDEC_ZPX()
        elif (op == self.OPCODE_DEX):
            yield from self.executeDEX()
        elif (op == self.OPCODE_DEY):
            yield from self.executeDEY()
        elif (op == self.OPCODE_EOR_ABS):
            yield from self.executeEOR_ABS()
        elif (op == self.OPCODE_EOR_ABSX):
            yield from self.executeEOR_ABSX()
        elif (op == self.OPCODE_EOR_ABSY):
            yield from self.executeEOR_ABSY()
        elif (op == self.OPCODE_EOR_IMM):
            yield from self.executeEOR_IMM()
        elif (op == self.OPCODE_EOR_INDX):
            yield from self.executeEOR_INDX()
        elif (op == self.OPCODE_EOR_INDY):
            yield from self.executeEOR_INDY()
        elif (op == self.OPCODE_EOR_ZP):
            yield from self.executeEOR_ZP()
        elif (op == self.OPCODE_EOR_ZPX):
            yield from self.executeEOR_ZPX()
        elif (op == self.OPCODE_INC_ABS):
            yield from self.executeINC_ABS()
        elif (op == self.OPCODE_INC_ABSX):
            yield from self.executeINC_ABSX()
        elif (op == self.OPCODE_INC_ZP):
            yield from self.executeINC_ZP()
        elif (op == self.OPCODE_INC_ZPX):
            yield from self.executeINC_ZPX()
        elif (op == self.OPCODE_INX):
            yield from self.executeINX()
        elif (op == self.OPCODE_INY):
            yield from self.executeINY()        
        elif (op == self.OPCODE_JMP_ABS):
            yield from self.executeJMP_ABS()
        elif (op == self.OPCODE_JMP_IND):
            yield from self.executeJMP_IND()
        elif (op == self.OPCODE_JSR_ABS):
            yield from self.executeJSR_ABS()    
        elif (op == self.OPCODE_LDA_ABS):
            yield from self.executeLDA_ABS()
        elif (op == self.OPCODE_LDA_ABSX):
            yield from self.executeLDA_ABSX()
        elif (op == self.OPCODE_LDA_ABSY):
            yield from self.executeLDA_ABSY()
        elif (op == self.OPCODE_LDA_IMM):
            yield from self.executeLDA_IMM()
        elif (op == self.OPCODE_LDA_INDX):
            yield from self.executeLDA_INDX()
        elif (op == self.OPCODE_LDA_INDY):
            yield from self.executeLDA_INDY()
        elif (op == self.OPCODE_LDX_ABS):
            yield from self.executeLDX_ABS()
        elif (op == self.OPCODE_LDX_ABSY):
            yield from self.executeLDX_ABSY()
        elif (op == self.OPCODE_LDX_IMM):
            yield from self.executeLDX_IMM()
        elif (op == self.OPCODE_LDX_ZPY):
            yield from self.executeLDX_ZPY()
        elif (op == self.OPCODE_LDA_ZP):
            yield from self.executeLDA_ZP()
        elif (op == self.OPCODE_LDA_ZPX):
            yield from self.executeLDA_ZPX()            
        elif (op == self.OPCODE_LDX_ZP):
            yield from self.executeLDX_ZP()
        elif (op == self.OPCODE_LDY_ABS):
            yield from self.executeLDY_ABS()
        elif (op == self.OPCODE_LDY_ABSX):
            yield from self.executeLDY_ABSX()
        elif (op == self.OPCODE_LDY_IMM):
            yield from self.executeLDY_IMM()
        elif (op == self.OPCODE_LDY_ZP):
            yield from self.executeLDY_ZP()
        elif (op == self.OPCODE_LDY_ZPX):
            yield from self.executeLDY_ZPX()
        elif (op == self.OPCODE_LSR_ABS):
            yield from self.executeLSR_ABS()
        elif (op == self.OPCODE_LSR_ABSX):
            yield from self.executeLSR_ABSX()
        elif (op == self.OPCODE_LSR_ACC):
            yield from self.executeLSR_ACC()
        elif (op == self.OPCODE_LSR_ZP):
            yield from self.executeLSR_ZP()
        elif (op == self.OPCODE_LSR_ZPX):
            yield from self.executeLSR_ZPX()
        elif (op == self.OPCODE_ORA_ABS):
            yield from self.executeORA_ABS()
        elif (op == self.OPCODE_ORA_ABSX):
            yield from self.executeORA_ABSX()
        elif (op == self.OPCODE_ORA_ABSY):
            yield from self.executeORA_ABSY()
        elif (op == self.OPCODE_ORA_IMM):
            yield from self.executeORA_IMM()
        elif (op == self.OPCODE_ORA_INDX):
            yield from self.executeORA_INDX()
        elif (op == self.OPCODE_ORA_INDY):
            yield from self.executeORA_INDY()
        elif (op == self.OPCODE_ORA_ZP):
            yield from self.executeORA_ZP()
        elif (op == self.OPCODE_ORA_ZPX):
            yield from self.executeORA_ZPX()
        elif (op == self.OPCODE_PHA):
            yield from self.executePHA()
        elif (op == self.OPCODE_PHP):
            yield from self.executePHP()
        elif (op == self.OPCODE_PLA):
            yield from self.executePLA()
        elif (op == self.OPCODE_ROR_ABS):
            yield from self.executeROR_ABS()
        elif (op == self.OPCODE_ROR_ABSX):
            yield from self.executeROR_ABSX()
        elif (op == self.OPCODE_ROR_ACC):
            yield from self.executeROR_ACC()
        elif (op == self.OPCODE_ROR_ZP):
            yield from self.executeROR_ZP()             
        elif (op == self.OPCODE_ROR_ZPX):
            yield from self.executeROR_ZPX() 
        elif (op == self.OPCODE_RTI):
            yield from self.executeRTI()            
        elif (op == self.OPCODE_RTS):
            yield from self.executeRTS()
        elif (op == self.OPCODE_SBC_ABS):
            yield from self.executeSBC_ABS()
        elif (op == self.OPCODE_SBC_ABSX):
            yield from self.executeSBC_ABSX()
        elif (op == self.OPCODE_SBC_ABSY):
            yield from self.executeSBC_ABSY()
        elif (op == self.OPCODE_SBC_IMM):
            yield from self.executeSBC_IMM()
        elif (op == self.OPCODE_SBC_INDX):
            yield from self.executeSBC_INDX()
        elif (op == self.OPCODE_SBC_INDY):
            yield from self.executeSBC_INDY()    
        elif (op == self.OPCODE_SBC_ZP):
            yield from self.executeSBC_ZP()
        elif (op == self.OPCODE_SBC_ZPX):
            yield from self.executeSBC_ZPX()
        elif (op == self.OPCODE_SEC):
            yield from self.executeSEC()
        elif (op == self.OPCODE_SED):
            yield from self.executeSED()
        elif (op == self.OPCODE_SEI):
            yield from self.executeSEI()
        elif (op == self.OPCODE_STA_ABS):
            yield from self.executeSTA_ABS()
        elif (op == self.OPCODE_STA_ABSX):
            yield from self.executeSTA_ABSX()
        elif (op == self.OPCODE_STA_ABSY):
            yield from self.executeSTA_ABSY()
        elif (op == self.OPCODE_STA_INDX):
            yield from self.executeSTA_INDX()
        elif (op == self.OPCODE_STA_INDY):
            yield from self.executeSTA_INDY()
        elif (op == self.OPCODE_STA_ZP):
            yield from self.executeSTA_ZP() 
        elif (op == self.OPCODE_STA_ZPX):
            yield from self.executeSTA_ZPX() 
        elif (op == self.OPCODE_STX_ABS):
            yield from self.executeSTX_ABS()
        elif (op == self.OPCODE_STX_ZP):
            yield from self.executeSTX_ZP()
        elif (op == self.OPCODE_STX_ZPY):
            yield from self.executeSTX_ZPY()
        elif (op == self.OPCODE_STY_ABS):
            yield from self.executeSTY_ABS()
        elif (op == self.OPCODE_STY_ZP):
            yield from self.executeSTY_ZP()
        elif (op == self.OPCODE_STY_ZPX):
            yield from self.executeSTY_ZPX()    
        elif (op == self.OPCODE_TAX):
            yield from self.executeTAX()
        elif (op == self.OPCODE_TAY):
            yield from self.executeTAY()
        elif (op == self.OPCODE_TSX):
            yield from self.executeTSX()
        elif (op == self.OPCODE_TXA):
            yield from self.executeTXA()
        elif (op == self.OPCODE_TXS):
            yield from self.executeTXS()
        elif (op == self.OPCODE_TYA):
            yield from self.executeTYA()
        else:
            raise Exception(f'op {op:02X} not handled')
        
    
            
    
        
