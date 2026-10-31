# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 16:32:44 2025

@author: 2016570
"""
import py4hw
import punxa_6502

class ALU(py4hw.Logic):
    OP_BYPASS =         0
    OP_ADD =            1
    OP_ADD_NO_CARRY =   2
    OP_SUB =            3
    OP_INC =            4
    OP_DEC =            5
    OP_OR =             6
    OP_AND =            7
    OP_XOR =            8
    OP_CMP =            9

class ALUBehavioral(ALU):
        
        
    def __init__(self, parent, name:str, a, b, r, c_in, op, c_out):
        # How many operations are supported ?
        # We can consider that A will always be the Accumulator and B can be 
        # selected from a number of options
        #
        
        
        super().__init__(parent, name)
        
        self.a = self.addIn('a', a)        
        self.b = self.addIn('b', b)
        self.c_in = self.addIn('c_in', c_in)
        self.op = self.addIn('op', op)
        
        self.r = self.addOut('r', r)
        self.c_out = self.addOut('c_out', c_out)
        
    def propagate(self):
        if (self.op.get() == ALU.OP_BYPASS):
            self.r.put(self.b.get())
        elif (self.op.get() == ALU.OP_ADD):
            # ADD
            r = self.a.get() + self.b.get() + self.c_in.get()
            self.r.put(r & 0xFF)
            self.c_out.put((r >> 8) & 1)
        elif (self.op.get() == ALU.OP_ADD_NO_CARRY):
            # ADD without carry
            r = self.a.get() + self.b.get() 
            self.r.put(r & 0xFF)
            self.c_out.put((r >> 8) & 1)
        elif (self.op.get() == ALU.OP_SUB):
            # SUB @todo verify
            r = self.a.get() - self.b.get() - (1 - self.c_in.get())
            self.r.put(r & 0xFF)
            self.c_out.put(1 if r >= 0 else 0)
        elif (self.op.get() == ALU.OP_INC):
            self.r.put((self.b.get() + 1) & 0xFF)
            self.c_out.put((self.b.get() + 1) >> 8)
        elif (self.op.get() == ALU.OP_DEC):
            self.r.put((self.b.get() - 1) & 0xFF)
        elif (self.op.get() == ALU.OP_OR):
            self.r.put(self.a.get() | self.b.get())
        elif (self.op.get() == ALU.OP_AND):
            self.r.put(self.a.get() & self.b.get())
        elif (self.op.get() == ALU.OP_XOR):
            self.r.put(self.a.get() ^ self.b.get())
        elif (self.op.get() == ALU.OP_CMP):
            r = self.a.get() - self.b.get()
            
            self.r.put(r)
            self.c_out.put((r != 0) and ((r >> 7) == 0))
        else:
            print('Unhandled ALU op', self.op.get())
        
        
class ALUStructural(py4hw.Logic):
        
    OP_BYPASS =         0
    OP_ADD =            1
    OP_ADD_NO_CARRY =   2
    OP_SUB =            3
    OP_INC =            4
    OP_DEC =            5
    OP_OR =             6
    OP_AND =            7
    OP_XOR =            8
    OP_CMP =            9
    
    
    
        
    def __init__(self, parent, name:str, a, b, r, c_in, op, c_out):
        # How many operations are supported ?
        # We can consider that A will always be the Accumulator and B can be 
        # selected from a number of options
        #
        
        
        super().__init__(parent, name)
        
        self.addIn('a', a)        
        self.addIn('b', b)
        self.addIn('c_in', c_in)
        self.addIn('op', op)
        
        self.addOut('r', r)
        self.addOut('c_out', c_out)
        
        assert(op.getWidth() == 4)
        assert(b.getWidth() == 8)
        assert(r.getWidth() == 8)
        
        
        inv_b = self.wire('inv_b', 8)
        add_a = self.wire('add_a', 8)
        add_b = self.wire('add_b', 8)
        add_r = self.wire('add_r', 8)
        
        alu_c_in = self.wire('alu_c_in')
        use_carry = self.wire('use_carry')
        eff_carry = self.wire('eff_carry')
        force_carry = self.wire('force_carry')
        emit_carry = self.wire('emit_carry')
        alu_c_out = self.wire('alu_c_cout')
        sel_b_a = self.wire('sel_b_a')
        
        zero = self.wire('zero', 8)
        one = self.wire('one', 8)
        minus_one = self.wire('minus_one ', 8)
        
        ops = self.wires('ops', 16, 1)
        py4hw.Decoder(self, 'ops', op, ops)
        
        py4hw.Not(self, 'inv_b', b, inv_b)
        py4hw.Or(self, 'use_carry', [ops[self.OP_ADD], ops[self.OP_SUB]], use_carry)
        py4hw.Buf(self, 'force_carry', ops[self.OP_CMP], force_carry)
        
        py4hw.Or(self, 'sel_b_a', [ops[self.OP_DEC], ops[self.OP_INC]], sel_b_a)
        
        py4hw.Mux2(self, 'select_a', sel_b_a, a, b, add_a)
        py4hw.SelectDefault(self, 'select_b', [ops[self.OP_INC], 
                                               ops[self.OP_DEC],
                                               ops[self.OP_SUB],
                                               ops[self.OP_CMP]],
                            [one, minus_one, inv_b, inv_b], b, add_b)
        
        py4hw.And2(self, 'eff_carry', c_in, use_carry, eff_carry)
        py4hw.Or2(self, 'alu_c_in', eff_carry, force_carry, alu_c_in)
        py4hw.Add(self, 'add', add_a, add_b, add_r, ci=alu_c_in, co = alu_c_out)
        
        py4hw.Constant(self, 'zero', 0, zero)
        py4hw.Constant(self, 'one', 1, one)
        py4hw.Constant(self, 'minus_one', -1, minus_one)
        results = [zero]*16
        
        results[self.OP_BYPASS] = b
        results[self.OP_ADD] = add_r
        results[self.OP_ADD_NO_CARRY] = add_r
        results[self.OP_SUB] = add_r
        results[self.OP_INC] = add_r
        results[self.OP_DEC] = add_r
        results[self.OP_AND] = add_r
        results[self.OP_OR] =  add_r
        results[self.OP_XOR] = add_r
        results[self.OP_CMP] = add_r
        
        
        py4hw.Mux(self, 'mux', op, results, r)
        
        py4hw.Or(self, 'emit_carry', [ops[self.OP_ADD], ops[self.OP_ADD_NO_CARRY], 
                                      ops[self.OP_CMP], ops[self.OP_DEC], 
                                      ops[self.OP_INC], ops[self.OP_SUB]], emit_carry)
        
        py4hw.And2(self, 'c_out', emit_carry, alu_c_out, c_out)
        
        
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
        q_IR = self.wire('q_IR', 8)
        q_MBR = self.wire('q_MBR', 8)
        
        # Public registers
        control['e_A'] = self.controlIn('e_A')
        control['e_X'] = self.controlIn('e_X')
        control['e_Y'] = self.controlIn('e_Y')
        control['e_SP'] = self.controlIn('e_SP')
        
        control['e_N'] = self.controlIn('e_N')
        control['e_O'] = self.controlIn('e_O')
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
        
        
        q_N = self.wire('q_N')
        q_O = self.wire('q_O')
        q_B = self.wire('q_B')
        q_D = self.wire('q_D')
        q_I = self.wire('q_I')
        q_Z = self.wire('q_Z')
        q_C = self.wire('q_C')        
        
        d_N = self.wire('d_N')
        d_O = self.wire('d_O')
        d_B = self.wire('d_B')
        d_D = self.wire('d_D')
        d_I = self.wire('d_I')
        d_Z = self.wire('d_Z')
        d_C = self.wire('d_C')     
        
        status['IR'] = self.statusOut(q_IR)
        status['d_C'] = self.statusOut(d_C)
        status['d_Z'] = self.statusOut(d_Z)
        status['d_N'] = self.statusOut(d_N)
        
        status['q_C'] = self.statusOut(q_C)
        status['q_Z'] = self.statusOut(q_Z)
        status['q_N'] = self.statusOut(q_N)

        databus = self.wire('databus', 8)
        
        py4hw.Reg(self, 'PC_lo', databus, q_PC_lo, reset=reset, reset_value=(resetAddress & 0XFF), enable=control['e_PC_lo'])
        py4hw.Reg(self, 'PC_hi', databus, q_PC_hi, reset=reset, reset_value=((resetAddress >> 8) & 0xFF), enable=control['e_PC_hi'])
        py4hw.Reg(self, 'MAR_lo', databus, q_MAR_lo, reset=reset, enable=control['e_MAR_lo'])
        py4hw.Reg(self, 'MAR_hi', databus, q_MAR_hi, reset=reset, enable=control['e_MAR_hi'])
        py4hw.Reg(self, 'IR', databus, q_IR, reset=reset, enable=control['e_IR'])
        py4hw.Reg(self, 'MBR', databus, q_MBR, reset=reset, enable=control['e_MBR'])
        
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
        
        control['alu_op'] = self.controlIn('alu_op', 4)
        
        py4hw.Select(self, 'select_b', 
                     [control['alu_sel_PC_lo'], 
                      control['alu_sel_PC_hi'],  
                      control['alu_sel_MAR_lo'], 
                      control['alu_sel_MAR_hi'],  
                      control['alu_sel_A'], 
                      control['alu_sel_X'], 
                      control['alu_sel_Y'], 
                      control['alu_sel_SP'], 
                      control['alu_sel_MBR']],
                     [q_PC_lo, q_PC_hi, q_MAR_lo, q_MAR_hi, q_A, q_X, q_Y, q_SP, q_MBR], b)
        
        ALUStructural(self, 'alu', q_A, b, q_alu, q_C, control['alu_op'], d_C)
        
        # direct flags
        py4hw.Bit(self, 'd_N', q_alu, 7, d_N)
        py4hw.EqualConstant(self, 'd_Z', q_alu, 0, d_Z)
        
        py4hw.Reg(self, 'A', databus, q_A, reset=reset, enable=control['e_A'])
        py4hw.Reg(self, 'X', databus, q_X, reset=reset, enable=control['e_X'])
        py4hw.Reg(self, 'Y', databus, q_Y, reset=reset, enable=control['e_Y'])
        py4hw.Reg(self, 'SP', databus, q_SP, reset=reset, enable=control['e_SP'])
        
        py4hw.Reg(self, 'C', d_C, q_C, reset=reset, enable=control['e_C'])
        py4hw.Reg(self, 'Z', d_Z, q_Z, reset=reset, enable=control['e_Z'])
        py4hw.Reg(self, 'N', d_N, q_N, reset=reset, enable=control['e_N'])

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
    
    def statusOut(self, w):
        self.addOut(w.name, w)
        return w
        
        
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
        else:
            raise Exception(f'register {r} not known')
        
class ControlUnit6502Behavioral(py4hw.Logic):
    
    DATA_ALU = 0
    DATA_MEM = 1
    
    MEM_PC = 0
    MEM_MAR = 1
    MEM_ZP = 2
    MEM_SP = 3
    
    OPCODE_BRK = 0x00
    OPCODE_ORA_INDX = 0x01
    OPCODE_ORA_ZP = 0x05
    OPCODE_ASL_ZP = 0x06
    OPCODE_PHP = 0x08
    OPCODE_ORA_IMM = 0x09
    OPCODE_ASL_ACC = 0x0A
    OPCODE_ORA_ABS = 0x0D
    OPCODE_ASL_ABS = 0x0E
    OPCODE_BPL_REL = 0x10
    OPCODE_ORA_INDY = 0x11
    OPCODE_ORA_ZPX = 0x15
    OPCODE_ASL_ZPX = 0x16
    OPCODE_CLC = 0x18
    OPCODE_ORA_ABSY = 0x19
    OPCODE_ORA_ABSX = 0x1D
    OPCODE_ASL_ABSX = 0x1E
    OPCODE_JSR_ABS = 0x20
    OPCODE_AND_INDX = 0x21
    OPCODE_BIT_ZP = 0x24
    OPCODE_AND_ZP = 0x25
    OPCODE_ROL_ZP = 0x26
    OPCODE_PLP = 0x28
    OPCODE_AND_IMM = 0x29
    OPCODE_ROL_ACC = 0x2A
    OPCODE_BIT_ABS = 0x2C
    OPCODE_AND_ABS = 0x2D
    OPCODE_ROL_ABS = 0x2E
    OPCODE_BMI_REL = 0x30
    OPCODE_AND_INDY = 0x31
    OPCODE_AND_ZPX = 0x35
    OPCODE_ROL_ZPX = 0x36
    OPCODE_SEC = 0x38
    OPCODE_AND_ABSY = 0x39
    OPCODE_AND_ABSX = 0x3D
    OPCODE_ROL_ABSX = 0x3E
    # _OPCODE_MAP[0x40] = ('RTI', ADDRESSING_IMPLIED)
    # _OPCODE_MAP[0x41] = ('EOR', ADDRESSING_INDIRECTX)
    # # 0x42, 0x43, 0x44 are illegal/undocumented
    # _OPCODE_MAP[0x45] = ('EOR', ADDRESSING_ZEROPAGE)
    # _OPCODE_MAP[0x46] = ('LSR', ADDRESSING_ZEROPAGE)
    # # 0x47 is illegal/undocumented
    OPCODE_PHA = 0x48
    
    # _OPCODE_MAP[0x49] = ('EOR', ADDRESSING_IMMEDIATE)
    # _OPCODE_MAP[0x4A] = ('LSR', ADDRESSING_ACCUMULATOR)
    # # 0x4B is illegal/undocumented
    OPCODE_JMP_ABS = 0x4C
    # _OPCODE_MAP[0x4D] = ('EOR', ADDRESSING_ABSOLUTE)
    # _OPCODE_MAP[0x4E] = ('LSR', ADDRESSING_ABSOLUTE)
    # # 0x4F is illegal/undocumented

    # # Row 0x50-0x5F
    # _OPCODE_MAP[0x50] = ('BVC', ADDRESSING_RELATIVE)
    # _OPCODE_MAP[0x51] = ('EOR', ADDRESSING_INDIRECTY)
    # # 0x52, 0x53, 0x54 are illegal/undocumented
    # _OPCODE_MAP[0x55] = ('EOR', ADDRESSING_ZEROPAGEX)
    # _OPCODE_MAP[0x56] = ('LSR', ADDRESSING_ZEROPAGEX)
    # # 0x57 is illegal/undocumented
    # _OPCODE_MAP[0x58] = ('CLI', ADDRESSING_IMPLIED)
    # _OPCODE_MAP[0x59] = ('EOR', ADDRESSING_ABSOLUTEY)
    # # 0x5A, 0x5B, 0x5C are illegal/undocumented
    # _OPCODE_MAP[0x5D] = ('EOR', ADDRESSING_ABSOLUTEX)
    # _OPCODE_MAP[0x5E] = ('LSR', ADDRESSING_ABSOLUTEX)
    # # 0x5F is illegal/undocumented

    # # Row 0x60-0x6F
    OPCODE_RTS = 0x60
    # _OPCODE_MAP[0x61] = ('ADC', ADDRESSING_INDIRECTX)
    # # 0x62, 0x63, 0x64 are illegal/undocumented
    # _OPCODE_MAP[0x65] = ('ADC', ADDRESSING_ZEROPAGE)
    # _OPCODE_MAP[0x66] = ('ROR', ADDRESSING_ZEROPAGE)
    # # 0x67 is illegal/undocumented
    OPCODE_PLA = 0x68
    OPCODE_ADC_IMM = 0x69
    OPCODE_ROR_ACC = 0x6A
    OPCODE_JMP_IND = 0x6C
    # _OPCODE_MAP[0x6D] = ('ADC', ADDRESSING_ABSOLUTE)
    # _OPCODE_MAP[0x6E] = ('ROR', ADDRESSING_ABSOLUTE)
    # # 0x6F is illegal/undocumented

    # # Row 0x70-0x7F
    # _OPCODE_MAP[0x70] = ('BVS', ADDRESSING_RELATIVE)
    # _OPCODE_MAP[0x71] = ('ADC', ADDRESSING_INDIRECTY)
    # # 0x72, 0x73, 0x74 are illegal/undocumented
    # _OPCODE_MAP[0x75] = ('ADC', ADDRESSING_ZEROPAGEX)
    # _OPCODE_MAP[0x76] = ('ROR', ADDRESSING_ZEROPAGEX)
    # # 0x77 is illegal/undocumented
    # _OPCODE_MAP[0x78] = ('SEI', ADDRESSING_IMPLIED)
    # _OPCODE_MAP[0x79] = ('ADC', ADDRESSING_ABSOLUTEY)
    # # 0x7A, 0x7B, 0x7C are illegal/undocumented
    # _OPCODE_MAP[0x7D] = ('ADC', ADDRESSING_ABSOLUTEX)
    # _OPCODE_MAP[0x7E] = ('ROR', ADDRESSING_ABSOLUTEX)
    # # 0x7F is illegal/undocumented

    # # Row 0x80-0x8F
    # # 0x80 is illegal/undocumented
    # _OPCODE_MAP[0x81] = ('STA', ADDRESSING_INDIRECTX)
    # # 0x82, 0x83 are illegal/undocumented
    # _OPCODE_MAP[0x84] = ('STY', ADDRESSING_ZEROPAGE)
    OPCODE_STA_ZP = 0x85
    OPCODE_STX_ZP = 0x86
    OPCODE_DEY = 0x88
    OPCODE_TXA = 0x8A
    OPCODE_STY_ABS = 0x8C
    OPCODE_STA_ABS = 0x8D
    OPCODE_STX_ABS = 0x8E
    OPCODE_BCC_REL = 0x90
    OPCODE_STA_INDY = 0x91
    OPCODE_STY_ZPX = 0x94
    OPCODE_STA_ZPX = 0x95
    OPCODE_STX_ZPY = 0x96
    OPCODE_TYA = 0x98
    OPCODE_STA_ABSY = 0x99
    OPCODE_TXS = 0x9A
    OPCODE_STA_ABSX = 0x9D
    OPCODE_LDY_IMM = 0xA0
    OPCODE_LDA_INDX = 0xA1
    OPCODE_LDX_IMM = 0xA2
    OPCODE_LDY_ZP = 0xA4
    OPCODE_LDA_ZP = 0xA5
    OPCODE_LDX_ZP = 0xA6
    OPCODE_TAY = 0xA8
    OPCODE_LDA_IMM = 0xA9
    OPCODE_TAX = 0xAA
    OPCODE_LDY_ABS = 0xAC
    OPCODE_LDA_ABS = 0xAD
    OPCODE_LDX_ABS = 0xAE
    OPCODE_BCS_REL = 0xB0
    OPCODE_LDA_INDY = 0xB1
    # # 0xB2, 0xB3, B4 (illegal/undocumented) (LDY ZP,X was 0xB4 - this is for 65C02)
    # _OPCODE_MAP[0xB4] = ('LDY', ADDRESSING_ZEROPAGEX) # This is a 65C02 legal opcode, but was illegal on NMOS. Assuming you want legal NMOS.
    # _OPCODE_MAP[0xB5] = ('LDA', ADDRESSING_ZEROPAGEX)
    OPCODE_LDX_ZPX = 0xB6
    
    # # 0xB7 is illegal/undocumented
    # _OPCODE_MAP[0xB8] = ('CLV', ADDRESSING_IMPLIED)
    # _OPCODE_MAP[0xB9] = ('LDA', ADDRESSING_ABSOLUTEY)
    OPCODE_TSX = 0xBA
    # # 0xBB is illegal/undocumented
    # _OPCODE_MAP[0xBC] = ('LDY', ADDRESSING_ABSOLUTEX)
    OPCODE_LDA_ABSX = 0xBD
    # _OPCODE_MAP[0xBE] = ('LDX', ADDRESSING_ABSOLUTEY)
    # # 0xBF is illegal/undocumented

    # # Row 0xC0-0xCF
    OPCODE_CPY_IMM = 0xC0
    # _OPCODE_MAP[0xC1] = ('CMP', ADDRESSING_INDIRECTX)
    # # 0xC2, 0xC3 are illegal/undocumented
    # _OPCODE_MAP[0xC4] = ('CPY', ADDRESSING_ZEROPAGE)
    # _OPCODE_MAP[0xC5] = ('CMP', ADDRESSING_ZEROPAGE)
    # _OPCODE_MAP[0xC6] = ('DEC', ADDRESSING_ZEROPAGE)
    # # 0xC7 is illegal/undocumented
    OPCODE_INY = 0xC8
    OPCODE_CMP_IMM = 0xC9
    OPCODE_DEX = 0xCA
    # # 0xCB is illegal/undocumented
    # _OPCODE_MAP[0xCC] = ('CPY', ADDRESSING_ABSOLUTE)
    # _OPCODE_MAP[0xCD] = ('CMP', ADDRESSING_ABSOLUTE)
    # _OPCODE_MAP[0xCE] = ('DEC', ADDRESSING_ABSOLUTE)
    # # 0xCF is illegal/undocumented

    OPCODE_BNE_REL = 0xD0
    # _OPCODE_MAP[0xD1] = ('CMP', ADDRESSING_INDIRECTY)
    # # 0xD2, 0xD3, 0xD4 are illegal/undocumented
    # _OPCODE_MAP[0xD5] = ('CMP', ADDRESSING_ZEROPAGEX)
    # _OPCODE_MAP[0xD6] = ('DEC', ADDRESSING_ZEROPAGEX)
    # # 0xD7 is illegal/undocumented
    OPCODE_CLD = 0xD8
    # _OPCODE_MAP[0xD9] = ('CMP', ADDRESSING_ABSOLUTEY)
    # # 0xDA, 0xDB, 0xDC are illegal/undocumented
    # _OPCODE_MAP[0xDD] = ('CMP', ADDRESSING_ABSOLUTEX)
    # _OPCODE_MAP[0xDE] = ('DEC', ADDRESSING_ABSOLUTEX)
    # # 0xDF is illegal/undocumented

    # # Row 0xE0-0xEF
    # _OPCODE_MAP[0xE0] = ('CPX', ADDRESSING_IMMEDIATE)
    # _OPCODE_MAP[0xE1] = ('SBC', ADDRESSING_INDIRECTX)
    # # 0xE2, 0xE3 are illegal/undocumented
    # _OPCODE_MAP[0xE4] = ('CPX', ADDRESSING_ZEROPAGE)
    # _OPCODE_MAP[0xE5] = ('SBC', ADDRESSING_ZEROPAGE)
    # _OPCODE_MAP[0xE6] = ('INC', ADDRESSING_ZEROPAGE)
    # # 0xE7 is illegal/undocumented
    OPCODE_INX = 0xE8
    OPCODE_SBC_IMM = 0xE9
    OPCODE_NOP = 0xEA
    OPCODE_CPX_ABS = 0xEC
    OPCODE_SBC_ABS = 0xED
    OPCODE_INC_ABS = 0xEE
    OPCODE_BEQ_REL = 0xF0
    # _OPCODE_MAP[0xF1] = ('SBC', ADDRESSING_INDIRECTY)
    # # 0xF2, 0xF3, 0xF4 are illegal/undocumented
    # _OPCODE_MAP[0xF5] = ('SBC', ADDRESSING_ZEROPAGEX)
    # _OPCODE_MAP[0xF6] = ('INC', ADDRESSING_ZEROPAGEX)
    # # 0xF7 is illegal/undocumented
    # _OPCODE_MAP[0xF8] = ('SED', ADDRESSING_IMPLIED)
    # _OPCODE_MAP[0xF9] = ('SBC', ADDRESSING_ABSOLUTEY)
    # # 0xFA, 0xFB, 0xFC are illegal/undocumented
    # _OPCODE_MAP[0xFD] = ('SBC', ADDRESSING_ABSOLUTEX)
    # _OPCODE_MAP[0xFE] = ('INC', ADDRESSING_ABSOLUTEX)

    
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

        if (pc in self.parent.symbols.keys()):
            print('{}:'.format(self.parent.symbols[pc]))

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
        ir = self.parent.children['datapath']._wires['q_IR'].get()
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
        r = self.parent.children['datapath']._wires['q_X'].get()
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
        control['alu_op'].prepare(ALU.OP_BYPASS)
        control['alu_sel_Y'].prepare(1)
        control['e_C'].prepare(1)
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['alu_sel_Y'].prepare(0)
        control['e_C'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
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
        
    def executeADC_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        yield from self.aluADD_MBR()
        yield from self.saveFlags()
        yield from self.incPC()
        m = self.parent.children['datapath']._wires['q_MBR'].get()
        a = self.parent.children['datapath']._wires['q_A'].get()
        c = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tADC #{m:02X} \t--> A={a:02X} C={c} N={n} Z={z}')

    def executeAND_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_MBR()
        yield from self.aluAND_MBR()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        a = self.status['q_C'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tAND ${m:02X} \t--> (A={a}) (N={n}) (Z={z})')
        
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

    def executeCLC(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_OR)
        control['e_C'].prepare(1)
        yield
        control['e_C'].prepare(0)
        yield
        
        yield from self.incPC()
        c = self.status['q_C'].get()
        print(f'\t\t\tCLC \t\t--> (C={c})' )

    def executeCMP_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        a = self.parent.children['datapath']._wires['q_MBR'].get()
        yield from self.aluCMP_MBR()
        yield from self.incPC()
        
        print(f'\t\tCMP #{a:02X} ')

        
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
        
        
        
    def executeDEX(self):
        yield from self.decX()
        yield from self.incPC()
        print(f'\t\t\tDEX')

    def executeDEY(self):
        yield from self.decY()
        yield from self.incPC()
        print(f'\t\t\tDEY')

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

    def executeINX(self):
        yield from self.incX()
        yield from self.incPC()
        print(f'\t\t\tINX')

    def executeINY(self):
        yield from self.incY()
        yield from self.incPC()
        print(f'\t\t\tINY')
        
    def executeLDA_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        yield from self.fetchMAR_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        print(f'\tLDA ${b:02X}{a:02X}')
        
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
        n = self.parent.children['datapath']._wires['q_N'].get()
        z = self.parent.children['datapath']._wires['q_Z'].get()
        print(f'\t\tLDA #{a:02X}\t\t--> A={a:02X} N={n} Z={z}')


    def executeLDA_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_A()
        yield from self.saveFlagsA()
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        print(f'\t\tLDA ${x:02X} ')

    def executeLDX_IMM(self):
        yield from self.incPC()
        yield from self.fetchX()
        yield from self.saveFlagsX()
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_X'].get()
        n = self.parent.children['datapath']._wires['q_N'].get()
        z = self.parent.children['datapath']._wires['q_Z'].get()
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

    def executeLDX_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_X()
        yield from self.saveFlagsX()
        yield from self.incPC()
        x = self.parent.children['datapath']._wires['q_X'].get()
        print(f'\t\tLDX ${x:02X} ')
        
    def executeLDY_IMM(self):
        yield from self.incPC()
        yield from self.fetchY()
        yield from self.saveFlagsY()
        yield from self.incPC()
        y = self.parent.children['datapath']._wires['q_Y'].get()
        n = self.parent.children['datapath']._wires['q_N'].get()
        z = self.parent.children['datapath']._wires['q_Z'].get()

        print(f'\t\tLDY #{y:02X}\t\t--> Y={y:02X} N={n} Z={z}')

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
        yield from self.pushPC_lo()
        yield from self.pushPC_hi()
        yield from self.transferMAR_to_PC()
        pc = self.parent.children['datapath']._wires['q_PC'].get()
        print(f'\tJSR {pc:04X} ')

    
    def executeORA_IMM(self):
        yield from self.incPC()
        yield from self.fetchMBR()
        yield from self.aluOR_MBR()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tORA #{a:02X} \t--> (A={a:02X}) (N={n}) (Z={z})')
    
    def executeORA_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.fetchZP_MBR()
        yield from self.aluOR_MBR()
        m = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        a = self.status['q_A'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\tORA ${m:02X} \t--> (A={a:02X}) (N={n}) (Z={z})')

    def executePHA(self):
        yield from self.pushA()
        yield from self.incPC()    
        print(f'\t\t\tPHA')
        
    def executePLA(self):
        yield from self.popA()
        yield from self.incPC()
        print(f'\t\t\tPLA')
        
    def executeRTS(self):
        yield from self.popPC_hi()
        yield from self.popPC_lo()
        yield from self.incPC()    
        print(f'\t\t\tRTS')

    def executeSTA_ABS(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.incPC()
        yield from self.fetchMAR_hi()
        yield from self.storeA()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        b = self.parent.children['datapath']._wires['q_MAR_hi'].get()
        print(f'\tSTA ${b:02X}{a:02X} ')
        
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

    def executeSTX_ZP(self):
        yield from self.incPC()
        yield from self.fetchMAR_lo()
        yield from self.storeX_ZP()
        yield from self.incPC()
        a = self.parent.children['datapath']._wires['q_MAR_lo'].get()
        print(f'\t\tSTX ${a:02X} ')
        
    def executeTAX(self):
        yield from self.incPC()
        yield from self.transferA_to_X()
        yield from self.saveFlagsX()
        x = self.parent.children['datapath']._wires['q_X'].get()
        z = self.status['q_Z'].get()
        n = self.status['q_N'].get()
        print(f'\t\t\tTAX\t\t\t--> X={x:02X} (N={n}) (Z={z})')

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
        print(f'\t\t\tTSX')

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
        print(f'\t\t\tTXS\t\t\t--> SP={s:02X}')
        
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
        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_A'].prepare(0)
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
        yield
        control['alu_sel_SP'].prepare(0)
        control['e_X'].prepare(0)
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
        yield
        control['alu_sel_X'].prepare(0)
        control['e_A'].prepare(0)
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
        control['e_N'].prepare(1)
        control['e_Z'].prepare(1)
        yield
        control['e_C'].prepare(0)
        control['e_N'].prepare(0)
        control['e_Z'].prepare(0)
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
        control['alu_op'].prepare(ALU.OP_ADD)
        control['alu_sel_X'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        if self.status['d_C'].get():
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
        control['alu_op'].prepare(ALU.OP_ADD)
        control['alu_sel_Y'].prepare(1)
        control['e_MAR_lo'].prepare(1)
        yield
        if self.status['d_C'].get():
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
        if (status['d_N'].get()):
            # We should add
            control['alu_op'].prepare(ALU.OP_ADD_NO_CARRY)
            control['alu_sel_MBR'].prepare(1)
            control['e_PC_lo'].prepare(1)
            yield
            if self.status['d_C'].get() == 0:
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
            if self.status['d_C'].get():
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
        if self.status['d_C'].get():
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
        control['e_C'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)

        yield
        control['alu_sel_MBR'].prepare(0)
        control['e_MBR'].prepare(0)
        control['e_C'].prepare(0)
        control['e_Z'].prepare(0)
        control['e_N'].prepare(0)
        yield

    def incX(self):
        control = self.control
        control['alu_op'].prepare(ALU.OP_INC)
        control['alu_sel_X'].prepare(1)
        control['e_X'].prepare(1)
        control['e_C'].prepare(1)
        control['e_Z'].prepare(1)
        control['e_N'].prepare(1)

        yield
        control['alu_sel_X'].prepare(0)
        control['e_X'].prepare(0)
        control['e_C'].prepare(0)
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

    def decodeAndExecute(self):
        control = self.control
        op = self.status['IR'].get()
        decoded_ins, decoded_addressing = punxa_6502.ins_to_str(op)
        toread = punxa_6502.OPERAND_SIZE_MAP[decoded_addressing]
        
        #print(f'INS={op:02X} decoded:', decoded_ins, decoded_addressing, 'should read', toread, 'bytes')
        
        if (op == self.OPCODE_ADC_IMM):
            yield from self.executeADC_IMM()
        elif (op == self.OPCODE_AND_ZP):
            yield from self.executeAND_ZP()
        elif (op == self.OPCODE_BEQ_REL):
            yield from self.executeBEQ_REL()
        elif (op == self.OPCODE_BNE_REL):
            yield from self.executeBNE_REL()
        elif (op == self.OPCODE_CLC):
            yield from  self.executeCLC()
        elif (op == self.OPCODE_CMP_IMM):
            yield from self.executeCMP_IMM()
        elif (op == self.OPCODE_CPY_IMM):
            yield from self.executeCPY_IMM()
        elif (op == self.OPCODE_DEX):
            yield from self.executeDEX()
        elif (op == self.OPCODE_DEY):
            yield from self.executeDEY()
        elif (op == self.OPCODE_INC_ABS):
            yield from self.executeINC_ABS()
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
        elif (op == self.OPCODE_LDA_IMM):
            yield from self.executeLDA_IMM()
        elif (op == self.OPCODE_LDA_INDY):
            yield from self.executeLDA_INDY()
        elif (op == self.OPCODE_LDX_ABS):
            yield from self.executeLDX_ABS()
        elif (op == self.OPCODE_LDX_IMM):
            yield from self.executeLDX_IMM()
        elif (op == self.OPCODE_LDA_ZP):
            yield from self.executeLDA_ZP()
        elif (op == self.OPCODE_LDX_ZP):
            yield from self.executeLDX_ZP()
        elif (op == self.OPCODE_LDY_IMM):
            yield from self.executeLDY_IMM()
        elif (op == self.OPCODE_ORA_IMM):
            yield from self.executeORA_IMM()
        elif (op == self.OPCODE_ORA_ZP):
            yield from self.executeORA_ZP()
        elif (op == self.OPCODE_PHA):
            yield from self.executePHA()
        elif (op == self.OPCODE_PLA):
            yield from self.executePLA()
        elif (op == self.OPCODE_RTS):
            yield from self.executeRTS()
        elif (op == self.OPCODE_STA_ABS):
            yield from self.executeSTA_ABS()
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
        elif (op == self.OPCODE_STY_ABS):
            yield from self.executeSTY_ABS()
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
        
    
            
    
        
