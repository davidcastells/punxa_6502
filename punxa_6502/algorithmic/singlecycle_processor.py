import py4hw

import punxa_6502


# Info from
# https://www.masswerk.at/6502/6502_instruction_set.html
# https://retrogamecoders.com/6502-processor/6502-instructions/

class SingleCycle6502(py4hw.Logic):
    
    def __init__(self, parent, name:str, memory:punxa_6502.MemoryInterface, 
                 reset, irq, nmi, resetAddress):
                 
         super().__init__(parent, name)
         
         self.reset = self.addIn('reset', reset)
         self.irq = self.addIn('irq', irq)
         self.nmi = self.addIn('nmi', nmi)
         
         self.mem = self.addInterfaceSource('memory', memory)
         self.reset_address = resetAddress
         self.pc = resetAddress
         
         self.X = 0
         self.Y = 0
         self.A = 0
         
         self.N = 0 # negative flag
         self.V = 0 # overflow
         self.D = 0 # decimal
         self.I = 0 # disable interrupts
         self.Z = 0 # zero flag
         self.C = 0 # carry flag
         
         self.SP = 0
         
         self.retired = 0
         
         self.symbols = {}
         
         self.co = self.run()
         
    def clock(self):
        next(self.co)
        
    def run(self):
        if (self.reset_address == 0):
            yield from self.fetchResetAddress()
        
        while (True):
            pc = self.pc
            yield from self.fetch()            
            self.decode()
            yield from self.fetchOperands()
            
            if (self.operandLen == 0):
                ops = ''
            elif (self.operandLen == 1):
                ops = f'{self.operand[0]:02X}'
            elif (self.operandLen == 2):
                ops = f'{self.operand[0]:02X} {self.operand[1]:02X}'
                
            print(f'{pc:04X} = 0x{self.ins:02X} {ops:10} - ', end='' )
            
            yield from self.execute()

            self.retired += 1
            
            yield

    def getRetiredInstructions(self):
        return self.retired
    
    def fetchResetAddress(self):
        low = yield from self.memoryRead(0xFFFC)
        high = yield from self.memoryRead(0xFFFD)
        
        self.pc = high << 8 | low
        
        print(f'Reset Address: 0x{self.pc:04X}')
        
    def fetch(self):
        if (self.pc in self.symbols.keys()):
            print('{}:'.format(self.symbols[self.pc]))
            
        self.ins = yield from self.memoryRead(self.pc)
        self.pc += 1
        
    def decode(self):
        self.decoded_ins, self.decoded_addressing = punxa_6502.ins_to_str(self.ins)

    def fetchOperands(self):

        toread_map = {punxa_6502.ADDRESSING_IMPLIED : 0, 
                      punxa_6502.ADDRESSING_ACCUMULATOR: 0,
                      punxa_6502.ADDRESSING_IMMEDIATE: 1,
                      punxa_6502.ADDRESSING_ZEROPAGE: 1,
                      punxa_6502.ADDRESSING_ZEROPAGEX: 1,
                      punxa_6502.ADDRESSING_ZEROPAGEY: 1,
                      punxa_6502.ADDRESSING_ABSOLUTE: 2,
                      punxa_6502.ADDRESSING_ABSOLUTEX: 2,
                      punxa_6502.ADDRESSING_ABSOLUTEY: 2,
                      punxa_6502.ADDRESSING_INDIRECT: 2,
                      punxa_6502.ADDRESSING_INDIRECTX: 1,
                      punxa_6502.ADDRESSING_INDIRECTY: 1,
                      punxa_6502.ADDRESSING_RELATIVE: 1,
                      }        
        toread = toread_map[self.decoded_addressing]
        
        self.operandLen = toread
        self.operand = []
        for i in range(toread):
            v = yield from self.memoryRead(self.pc)
            self.operand.append(v)
            self.pc += 1
        
    def push8(self, v):
        # push a value and return the pointer to the stack where it was written
        add = 0x0100 | self.SP
        self.SP = (self.SP - 1) & 0xFF
        
        yield from self.memoryWrite(add, v)
        
        return add
    
    def pop8(self):
        # push a value and return the pointer to the stack where it was written
        self.SP = (self.SP + 1) & 0xFF
        add = 0x0100 | self.SP
        
        v = yield from self.memoryRead(add)
        
        return v, add

    def execute(self):
        op = self.decoded_ins
        addressing = self.decoded_addressing
        v = self.operand
        w = 0
        ws = ''
        ms = ''

        isStore = (op in ['STA', 'STX', 'STY'])
                   
        if (addressing == punxa_6502.ADDRESSING_IMPLIED):
            w = 0
            ws = '     '
        elif (addressing == punxa_6502.ADDRESSING_ACCUMULATOR): 
            w = self.A
            ws = '     '
        elif (addressing == punxa_6502.ADDRESSING_IMMEDIATE): 
            w = v[0]
            ws = f'#{w:02X}    '
        elif (addressing == punxa_6502.ADDRESSING_RELATIVE): 
            w = py4hw.IntegerHelper.c2_to_signed(v[0], 8)
            if (w >= 0):
                ws = f'+{w:4}  '
            else:
                ws = f'{w:4}  '                
        elif (addressing == punxa_6502.ADDRESSING_ABSOLUTE):
            add = v[0] | v[1] << 8
            ws = f'{add:04X}  '
            if not(isStore):
                w = yield from self.memoryRead(add)
                ms = f'[{add:04X}]={w:02X} '
        elif (addressing == punxa_6502.ADDRESSING_ABSOLUTEX):
            add = v[0] | v[1] << 8
            ws = f'{add:04X},X'
            add0 = add
            add = add + self.X
            w = yield from self.memoryRead(add)
            ms = f'[{add0:04X}+{self.X:02X}]={w:02X} '
        elif (addressing == punxa_6502.ADDRESSING_ABSOLUTEY):
            add = v[0] | v[1] << 8
            ws = f'{add:04X},Y'
            add0 = add
            add = add + self.Y
            w = yield from self.memoryRead(add)
            ms = f'[{add0:04X}+{self.Y:02X}]={w:02X} '
        elif (addressing == punxa_6502.ADDRESSING_INDIRECT):
            add = v[0]
            ws = f'(${add:02X})'
            add0 = add
            ptr_lo = yield from self.memoryRead(add)
            ptr_hi = yield from self.memoryRead(add+1)
            ptr = ptr_hi << 8 | ptr_lo
            w = yield from self.memoryRead(ptr)
            add = ptr
            ms = f'[{add0:04X}]={ptr:04X}->[{ptr:04X}]={w:02X} '
        elif (addressing == punxa_6502.ADDRESSING_INDIRECTX):
            add = v[0]
            ws = f'(${add:02X},X)'
            add0 = add
            add += self.X
            ptr_lo = yield from self.memoryRead(add)
            ptr_hi = yield from self.memoryRead(add+1)
            ptr = ptr_hi << 8 | ptr_lo
            w = yield from self.memoryRead(ptr)
            add = ptr
            ms = f'[{add0:04X}+{self.X:02X}]={ptr:04X}->[{ptr:04X}]={w:02X} '
        elif (addressing == punxa_6502.ADDRESSING_INDIRECTY):
            add = v[0]
            ws = f'(${add:02X}),Y'
            add0 = add
            ptr_lo = yield from self.memoryRead(add)
            ptr_hi = yield from self.memoryRead(add+1)
            ptr = ptr_hi << 8 | ptr_lo

            add = ptr + self.Y
            w = yield from self.memoryRead(add)
            ms = f'[{add0:04X}]={ptr:04X}->[{ptr:04X}+{self.Y:02X}]={w:02X} '
            
        elif (addressing == punxa_6502.ADDRESSING_ZEROPAGE): 
            add = v[0]
            w = yield from self.memoryRead(add) 
            ws = f'${add:02X}  '
            ms = f'[{add:04X}]={w:02X} '
        elif (addressing == punxa_6502.ADDRESSING_ZEROPAGEX): 
            add = v[0]
            ws = f'${add:02X},X'
            add0 = add
            add = (add + self.X) & 0xFF
            w = yield from self.memoryRead(add)
            ms = f'[{add0:04X}+{self.X:02X}]={w:02X} '
        elif (addressing == punxa_6502.ADDRESSING_ZEROPAGEY): 
            add = v[0]
            ws = f'${add:02X},Y'
            add0 = add
            add = (add + self.Y) & 0xFF
            w = yield from self.memoryRead(add)            
            ms = f'[{add0:04X}+{self.Y:02X}]={w:02X} '
        else:
            print('UNHANDLED ADDRESSING', addressing)
        
        # ---------------------------------------------------------------------
        
        if (op == 'ADC'):
            sA = (self.A >> 7) & 0x01
            sM = (w >> 7) & 0x01            

            if (self.D):
                # decimal mode
                Rlo = (self.A & 0xF) + (w & 0xF) + self.C                
                Rloc = (Rlo > 9) & 1
                if (Rloc): Rlo -= 0xA
                Rhi = (self.A >> 4) + (w >> 4) + Rloc
                Rhic = (Rhi > 9) & 1
                if (Rhic): Rhi -= 0xA
                R = Rhi << 4 | Rlo
                print()
                print('low', self.A & 0xF, w & 0xF, self.C)
                print('high', (self.A >> 4) , (w >> 4) , Rloc)
                print('rs', Rlo, Rloc, Rhi, Rhic, R)
            else:
                R = self.A + w + self.C
                self.C = R >> 8


            sR = (R >> 7) & 0x01            
            self.V = ((sA ^ sR) & (sM ^ sR))

            self.A = R & 0xFF
            self.N = self.A >> 7
            self.Z = (self.A == 0) & 1

            print(f'ADC {ws}\t--> {ms}A={self.A:02X} C={self.C} N={self.N} Z={self.Z} D={self.D}')
        elif (op == 'AND'):
            self.A = self.A & w
            self.N = self.A >> 7
            self.Z = (self.A == 0) & 1
            print(f'AND {ws} \t--> {ms}A={self.A:02X} N={self.N} Z={self.Z}')
        elif (op == 'ASL'):
            self.C = self.A >> 7
            self.A = self.A << 1
            self.N = self.A >> 7
            self.Z = (self.A == 0) & 1
            print(f'ASL {ws} \t--> {ms}A={self.A:02X} N={self.N} Z={self.Z}')
        elif (op == 'BCC'):
            if (self.C == 0):
                self.pc += w
                print(f'BCC {w:3} \t--> (C={self.C}) pc={self.pc:04X}' )
            else:
                print(f'BCC {w:3} \t--> (C={self.C})' )
        elif (op == 'BEQ'):
            if (self.Z):
                self.pc += w
                print(f'BEQ {w:3} \t--> (Z={self.Z}) pc={self.pc:04X}' )
            else:
                print(f'BEQ {w:3} \t--> (Z={self.Z})' )
        elif (op == 'BNE'):
            if (self.Z == 0):
                self.pc += w
                print(f'BNE {w:3} \t--> (Z={self.Z}) pc={self.pc:04X}' )
            else:
                print(f'BNE {w:3} \t--> (Z={self.Z})' )
        elif (op == 'CLC'):
            self.C = 0
            print('CLC     \t--> C=0')
        elif (op == 'CLD'):
            self.D = 0
            print(f'CLD {ws} \t--> {ms}D={self.D}')            
        elif (op == 'CMP'):
            cmp = (self.A - w) & 0xFF
            self.C = (self.A >= w) & 1
            self.Z = (self.A == w) & 1
            self.N = (cmp >> 7) & 1
            print(f'CMP {ws}\t--> {ms}C={self.C} N={self.N} Z={self.Z}')
        elif (op == 'CPY'):
            cmp = (self.Y - w) & 0xFF
            self.C = (self.Y >= w) & 1
            self.Z = (self.Y == w) & 1
            self.N = (cmp >> 7) & 1
            print(f'CPY {ws}\t--> C={self.C} N={self.N} Z={self.Z}')
        elif (op == 'DEC'):
            R = w - 1;
            self.N = R >> 7
            self.Z = (R == 0) & 1
            yield from self.memoryWrite(add, R)
            print(f'DEC \t\t--> {ms} [{add:04X}]={R:02X} N={self.N} Z={self.Z}')
        elif (op == 'DEX'):
            self.X = (self.X - 1) & 0xFF
            self.N = self.X >> 7
            self.Z = (self.X == 0) & 1
            print(f'DEX \t\t--> X={self.X:02X} N={self.N} Z={self.Z}')            
        elif (op == 'DEY'):
            self.Y = (self.Y - 1) & 0xFF
            self.N = self.Y >> 7
            self.Z = (self.Y == 0) & 1
            print(f'DEY \t\t--> Y={self.Y:02X} N={self.N} Z={self.Z}')            
        elif (op == 'INC'):
            R = w + 1;
            self.N = R >> 7
            self.Z = (R == 0) & 1
            yield from self.memoryWrite(add, R)
            print(f'INC \t\t--> {ms} [{add:04X}]={R:02X} N={self.N} Z={self.Z}')
        elif (op == 'INX'):
            self.X = (self.X + 1) & 0xFF
            self.N = self.X >> 7
            self.Z = (self.X & 1) ^ 1
            print(f'INX \t\t--> X={self.X:02X} N={self.N} Z={self.Z}')
        elif (op == 'INY'):
            self.Y += 1
            self.N = self.Y >> 7
            self.Z = (self.Y & 1) ^ 1
            print(f'INY \t\t--> Y={self.Y:02X} N={self.N} Z={self.Z}')            
        elif (op == 'JMP'):
            self.pc = add
            print(f'JMP {ws}\t--> pc={self.pc:04X}' )
        elif (op == 'JSR'):
            ra = self.pc -1
            rah = ra >> 8
            ral = ra & 0xFF
            self.pc = add
            sph = yield from self.push8(rah)            
            spl = yield from self.push8(ral)
            print(f'JSR {ws}\t--> [{sph:04X}]={rah:02X} [{spl:04X}]={ral:02X} pc={self.pc:04X}')            
        elif (op == 'LDA'):
            self.A = w
            self.N = w >> 7
            self.Z = (self.A == 0) & 1
            print(f'LDA {ws} \t--> {ms}A={w:02X} N={self.N} Z={self.Z}')
        elif (op == 'LDX'):
            self.X = w
            self.N = w >> 7
            self.Z = (self.X == 0) & 1
            print(f'LDX {ws} \t--> {ms}X={w:02X} N={self.N} Z={self.Z}')
        elif (op == 'LDY'):
            self.Y = w
            self.N = w >> 7
            self.Z = (self.Y == 0) & 1
            print(f'LDY {ws} \t--> {ms}Y={w:02X} N={self.N} Z={self.Z}')
        elif (op == 'ORA'):
            self.A = self.A | w
            self.N = self.A >> 7
            self.Z = (self.A == 0) & 1
            print(f'ORA {ws} \t--> {ms}A={self.A:02X} N={self.N} Z={self.Z}')
        elif (op == 'ROR'):
            pC = self.C
            self.C = w & 1
            self.A = pC << 7 | w >>1 
            self.N = pC
            self.Z = (self.A == 0) & 1
            print(f'ROR {ws} \t--> {ms}A={self.A:02X} N={self.N} Z={self.Z}')
        elif (op == 'SBC'):
            sA = (self.A >> 7) & 1
            sM = (w >> 7) & 1
            
            if (self.D):
                # The 6502 manual (W65C02S) states for decimal mode:
                # "The BCD subtraction effectively adds 0x99 to the operand and then performs a normal BCD addition with the carry bit."
                # A better approach is to use the two's complement and adjust for decimal.
                # A - M - (1 - C)
                
                borrow_in = 1 - self.C

                Rlo = (self.A & 0xF) - (w & 0xF) - borrow_in
                
                # Check for borrow from low nibble
                if Rlo < 0:
                    Rlo += 10
                    borrow_from_low = 1
                else:
                    borrow_from_low = 0
                
                Rhi = (self.A >> 4) - (w >> 4) - borrow_from_low
                if Rhi < 0:
                    Rhi += 10
                    self.C = 0 # Carry clear means borrow occurred
                else:
                    self.C = 1 # Carry set means no borrow occurred
                
                R = (Rhi << 4) | (Rlo & 0xF) 

            else:
                # Binary mode subtraction
                # R = A - w - (1 - C)
                # This is equivalent to R = A + (~w) + C
                effective_w = w ^ 0xFF # One's complement
                R = self.A + effective_w + self.C

                # The carry flag for SBC is set if no borrow occurred.
                # If R >= 0x100, then no borrow occurred (carry is set).
                self.C = (R >> 8) & 0x01 # Carry is bit 8

            sR = (R >> 7) & 0x01

            #self.V = ((sA ^ sR) & (sM ^ sR)) 
            self.V = ((sA ^ sR) & ((sM ^ 0x01) ^ sR)) # sM ^ 0x01 effectively inverts the sign of M for V flag calculation

            self.A = R & 0xFF
            self.N = (self.A >> 7) & 0x01
            self.Z = (self.A == 0) & 0x01

            print(f'SBC {ws}\t--> {ms}A={self.A:02X} C={self.C} N={self.N} Z={self.Z} D={self.D} V={self.V}')

        elif (op == 'SEC'):
            self.C = 1
            print(f'SEC {ws} \t--> {ms}C={self.C}')            
        elif (op == 'SED'):
            self.D = 1
            print(f'SED {ws} \t--> {ms}D={self.D}')            
        elif (op == 'STA'):
            yield from self.memoryWrite(add, self.A)
            print(f'STA {ws} \t--> [{add:04X}]={self.A:02X}')
        elif (op == 'STX'):
            yield from self.memoryWrite(add, self.X)
            print(f'STX {ws} \t--> [{add:04X}]={self.X:02X}')
        elif (op == 'STY'):
            yield from self.memoryWrite(add, self.Y)
            print(f'STY {ws} \t--> [{add:04X}]={self.Y:02X}')
        elif (op == 'TAX'):
            self.X = self.A
            self.N = self.X >> 7
            self.Z = (self.X == 0) & 1
            print(f'TAX \t\t--> Y={self.Y:02X} N={self.N} Z={self.Z}')
        elif (op == 'TAY'):
            self.Y = self.A
            self.N = self.Y >> 7
            self.Z = (self.Y == 0) & 1
            print(f'TAY \t\t--> Y={self.Y:02X} N={self.N} Z={self.Z}')
        elif (op == 'TSX'):
            self.X = self.SP
            self.N = self.X >> 7
            self.Z = (self.X == 0) & 1
            print(f'TSX \t\t--> X=0x{self.X:02X} N={self.N} Z={self.Z}')
        elif (op == 'TXA'):
            self.A = self.X            
            self.N = self.A >> 7
            self.Z = (self.A == 0) & 1
            print(f'TXA \t\t--> A={self.A:02X} N={self.N} Z={self.Z}')
        elif (op == 'TXS'):
            self.SP = self.X            
            print(f'TXS \t\t--> SP={self.SP:02X}')
        elif (op == 'TYA'):
            self.A = self.Y
            self.N = self.A >> 7
            self.Z = (self.A == 0) & 1
            print(f'TYA \t\t--> A={self.Y:02X} N={self.N} Z={self.Z}')
        elif (op == 'PHA'):
            spa = yield from self.push8(self.A)
            print(f'PHA \t\t--> SP[{spa:04X}]={self.A:02X}')
        elif (op == 'PHP'):
            # info from https://www.nesdev.org/wiki/Status_flags
            P = (self.N << 7) | (self.V << 6) | (1 <<5) | (1 << 4) | (self.D << 3) | (self.I << 2) | (self.Z << 1) | (self.C)
            spa = yield from self.push8(P)
            print(f'PHP \t\t--> [{spa:04X}]={P:02X} SP={self.SP:02X}')
            
        elif (op == 'PLA'):
            self.A, spa = yield from self.pop8()
            print(f'PLA \t\t--> [{spa:04X}]={self.A:02X} A={self.A:02X} SP={self.SP:02X} ')
            
        elif (op == 'RTS'):
            self.SP = (self.SP + 1) & 0xFF
            spl = 0x0100 | self.SP
            
            ral = yield from self.memoryRead(spl)

            self.SP = (self.SP + 1) & 0xFF
            sph = 0x0100 | self.SP
            
            rah = yield from self.memoryRead(sph)
            
            self.pc = rah << 8 | ral
            self.pc += 1
            
            print(f'RTS \t\t--> SP[{sph:04X}]={rah:02X} SP[{spl:04X}]={ral:02X} pc={self.pc:04X}')
            
        else:
            print('UNHANDLED', self.decoded_ins, self.decoded_addressing)
            
        yield


    def memoryRead(self, address):
        
        self.mem.address.prepare(address)
        self.mem.read.prepare(1)
        self.mem.write.prepare(0)
        yield
        yield
        self.mem.read.prepare(0)
        yield
        return self.mem.read_data.get()

    def memoryWrite(self, address, v):
        
        self.mem.address.prepare(address)
        self.mem.write.prepare(1)
        self.mem.read.prepare(0)
        self.mem.write_data.prepare(v)
        self.mem.be.prepare(1)
        yield
        self.mem.write.prepare(0)
        self.mem.be.prepare(0)
        yield

    def getRegister(self, r):
        r = r.upper()
        if (r == 'PC'):
            return self.pc 
        elif (r == 'A'):
            return self.A
        elif (r == 'X'):
            return self.X
        elif (r == 'Y'):
            return self.Y
        elif (r == 'SP'):
            return self.SP
        else:
            raise Exception(f'register {r} not known')
        
         # self.N = 0 # negative flag
         # self.V = 0 # overflow
         # self.D = 0 # decimal
         # self.I = 0 # disable interrupts
         # self.Z = 0 # zero flag
         # self.C = 0 # carry flag
