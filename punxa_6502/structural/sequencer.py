# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 15:45:05 2026

@author: dcr
"""
import py4hw

class Sequencer(py4hw.Logic):
    
    INS_EXE = 0
    INS_JC =  1     # conditional jump
    INS_JMP = 2     # jump 
    INS_JSR = 3     # jump subroutine
    INS_RET = 4     # ret subroutine

    def __init__(self, parent:py4hw.Logic, name:str, reset:py4hw.Wire,
                 ins:py4hw.Wire, cond:py4hw.Wire,
                 address:py4hw.Wire, pc:py4hw.Wire, 
                 oe:py4hw.Wire,
                 stack_depth=3, reset_pc=0):
        '''
        Micro-program sequencer.

        
        pc :  
        

        Parameters
        ----------
        parent : Logic
            parent.
        name : str
            Instance name.
        reset : Wire
            reset.
        ins : Wire
            Ins:  0=EXE (pc+1), 1=JC (jump if Cond), 2=JMP, 3=JSR (push pc+1), 4=RET (pop).
        cond : Wire
            DESCRIPTION.
        address : Wire
            Address used by the JC, JMP, JSR instructions.
        pc : Wire
            current micro-program address (output of the pc register).
        oe: Wire
            output enable signal, active when executing EXE instructions
        
        stack_depth : TYPE, optional
            The number of positions of the stack. The default is 3.

        Returns
        -------
        None
        '''
        super().__init__(parent, name)
        
        self.addIn('reset', reset)
        self.addIn('ins', ins)
        self.addIn('cond', cond)
        self.addIn('address', address)
        self.addOut('pc', pc)
        self.addOut('oe', oe)
        
        w = address.getWidth()
        
        assert(address.getWidth() == pc.getWidth())
        

        # internal wires
        pc_next = self.wire('pc_next', w)
        pc_next1 = self.wire('pc_next1', w)
        pc_inc = self.wire('pc_inc', w)
        one = self.wire('one', w)
        
        top = self.wire('top', w)
        post_top = self.wire('post_top', w)
        
        push = self.wire('push', 1)
        pop = self.wire('pop', 1)
        is_cond= self.wire('is_cond', 1)
        is_jmp = self.wire('is_jmp', 1)
        active_cond = self.wire('active_cond', 1)
        empty= self.wire('empty', 1)
        full= self.wire('full', 1)
        jmp = self.wire('jmp', 1)

        # pc + 1
        py4hw.Constant(self, 'one', 1, one)
        py4hw.Add(self, 'inc', pc, one, pc_inc)

        # We always push pc + 1
        py4hw.Stack_ShiftRegister(self, 'stack', pc_inc, top, post_top,  push, pop, empty, full, stack_depth)
        
        py4hw.AssertNotAllActive(self, 'pop when empty', [pop, empty])
        py4hw.AssertNotAllActive(self, 'push when full', [push, full])
        
        py4hw.EqualConstant(self, 'is_exe', ins, self.INS_EXE, oe)
        py4hw.EqualConstant(self, 'is_cond', ins, self.INS_JC, is_cond)
        py4hw.EqualConstant(self, 'is_jmp', ins, self.INS_JMP, is_jmp)
        py4hw.EqualConstant(self, 'is_jsr', ins, self.INS_JSR, push)
        py4hw.EqualConstant(self, 'is_pop', ins, self.INS_RET, pop)
        
        py4hw.And2(self, 'active_cond', is_cond, cond, active_cond)
        py4hw.Or(self, 'jmp', [active_cond, is_jmp, push], jmp)

        # next address mux: 0 = pc+1, 1 = external address, 2 = stack top
        # (4th input unused, tied to pc+1)
        py4hw.Mux2(self, 'sel_pop', sel=pop, sel0=pc_next1, sel1=top, r=pc_next)
        py4hw.Mux2(self, 'sel_add', sel=jmp, sel0=pc_inc, sel1=address, r=pc_next1)

        # micro-program counter
        py4hw.Reg(self, 'pc_reg', d=pc_next, q=pc, reset=reset, reset_value=reset_pc)
        
        