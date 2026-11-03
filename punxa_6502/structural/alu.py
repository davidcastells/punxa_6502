# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 17:33:37 2026

@author: dcr
"""

import py4hw

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
    OP_ROR =            10

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
        elif (self.op.get() == ALU.OP_ROR):
            a = self.a.get()
            self.r.put(((self.c_in.get() << 7) | (a >> 1)) & 0xFF)
            self.c_out.put(a & 1)
        else:
            print('Unhandled ALU op', self.op.get())
        
        
class ALUStructural(ALU):
        
    def __init__(self, parent, name:str, a, b, r, c_in, op, c_out, v_out):
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
        self.addOut('v_out', v_out)
        
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
        
        and_r = self.wire('and_r', 8)
        or_r = self.wire('or_r', 8)
        xor_r = self.wire('xor_r', 8)
        py4hw.And2(self, 'and_r', a, b, and_r)
        py4hw.Or2(self, 'or_r', a, b, or_r)
        py4hw.Xor2(self, 'xor_r', a, b, xor_r)
        
        py4hw.Constant(self, 'zero', 0, zero)
        py4hw.Constant(self, 'one', 1, one)
        py4hw.Constant(self, 'minus_one', -1, minus_one)
        results = [zero]*16
        
        # @todo substitute this by Bits
        a_bits = self.wires('a_bits', 8, 1)
        for i in range(8):
            py4hw.Bit(self, f'a_bit{i}', a, i, a_bits[i])
        ror_r = self.wire('ror_r', 8)
        py4hw.ConcatenateLSBF(self, 'ror_r', a_bits[1:] + [c_in], ror_r)
        
        results[self.OP_BYPASS] = b
        results[self.OP_ADD] = add_r
        results[self.OP_ADD_NO_CARRY] = add_r
        results[self.OP_SUB] = add_r
        results[self.OP_INC] = add_r
        results[self.OP_DEC] = add_r
        results[self.OP_AND] = and_r
        results[self.OP_OR] =  or_r
        results[self.OP_XOR] = xor_r
        results[self.OP_CMP] = add_r
        results[self.OP_ROR] = ror_r
        
        py4hw.Mux(self, 'mux', op, results, r)
        
        py4hw.Or(self, 'emit_carry', [ops[self.OP_ADD], ops[self.OP_ADD_NO_CARRY], 
                                      ops[self.OP_CMP], ops[self.OP_DEC], 
                                      ops[self.OP_INC], ops[self.OP_SUB]], emit_carry)
        
        c_out_add = self.wire('c_out_add')
        py4hw.And2(self, 'c_out_add', emit_carry, alu_c_out, c_out_add)
        py4hw.Mux2(self, 'c_out', ops[self.OP_ROR], c_out_add, a_bits[0], c_out)
     
        # Overflow calculation
        a7 = self.wire('a7')
        b7 = self.wire('b7')
        r7 = self.wire('r7')
        diff_sign = self.wire('diff_sign')
        same_sign = self.wire('same_sign')
        diff_res = self.wire('diff_res')
        ov_en = self.wire('ov_en')
        ov_raw = self.wire('ov_raw')

        py4hw.Bit(self, 'a7', add_a, 7, a7)
        py4hw.Bit(self, 'b7', add_b, 7, b7)
        py4hw.Bit(self, 'r7', add_r, 7, r7)
        py4hw.Xor2(self, 'diff_sign', a7, b7, diff_sign)
        py4hw.Not(self, 'same_sign', diff_sign, same_sign)
        py4hw.Xor2(self, 'diff_res', a7, r7, diff_res)
        py4hw.Or(self, 'ov_en', [ops[self.OP_ADD], ops[self.OP_SUB]], ov_en)
        py4hw.And2(self, 'ov_raw', same_sign, diff_res, ov_raw)
        py4hw.And2(self, 'v_out', ov_raw, ov_en, v_out)