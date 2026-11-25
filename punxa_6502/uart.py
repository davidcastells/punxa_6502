# -*- coding: utf-8 -*-
"""
Created on Mon Jun  2 12:34:42 2025

@author: dcr
"""

import py4hw
import punxa_6502

class SerialInterface(py4hw.Interface):
    
    def __init__(self, parent:py4hw.Logic, name:str):
        super().__init__(parent, name);
        self.tx = self.addSourceToSink("tx", 1)
        self.rx = self.addSinkToSource("rx", 1)


class Uart6551(py4hw.Logic):
    
    UART_TDR = 0
    
    def __init__(self, parent, name:str, memory:punxa_6502.MemoryInterface, 
                 reset, serial:SerialInterface):
        super().__init__(parent, name)
        
        self.reset = self.addIn('reset', reset)
        
        self.mem = self.addInterfaceSink('memory', memory)
        self.serial = self.addInterfaceSource('serial', serial)
        
        self.console = ''
        
    def clock(self):
        
        if (self.mem.read.get()):
            # print('UART READ')
            pass
        
        if (self.mem.write.get()):
            add = self.mem.address.get()
            wdata = self.mem.write_data.get()
            
            if (add == self.UART_TDR):
                self.console += chr(wdata)
            else:
                print(f'\nUART WRITE add {add:04X} = {wdata:02X}'  )
    
#     Receive Data Register (RDR) / Transmit Data Register (TDR)

# Address: Often the base address of the 6551's memory block (e.g., $F000 or $C300, depending on the system's memory map).
# Read (CPU reads from this address): This reads the received data character from the ACIA's receive buffer.
# Write (CPU writes to this address): This writes a character to the ACIA's transmit buffer, which will then be serialized and sent out the TxD pin.
# Note: This is usually the same memory address for both read and write operations; the R/W line from the CPU determines if it's a read or a write.
# Status Register (SR)

# Address: Base address + 1 (e.g., $F001 or $C301).
# Read (CPU reads from this address): This register provides information about the current state of the UART, including:
# Receive Data Ready (RxDR): Indicates if a new character has been received and is available in the RDR.
# Transmit Data Register Empty (TDRE): Indicates if the transmit buffer is empty and ready to accept a new character for transmission.
# Transmit Shift Register Empty (TSRE): Indicates if the transmit shift register (which actually sends the bits out) is empty.
# Parity Error (PE): Indicates a parity error in the received data.
# Framing Error (FE): Indicates a framing error (missing stop bit) in the received data.
# Overrun Error (OE): Indicates that a new character was received before the previous one was read from the RDR, causing data loss.
# Interrupt Request (IRQ): Indicates if an interrupt is pending (though the specific bits for why an IRQ occurred might vary or be implied).
# Write (CPU writes to this address): Sometimes a soft reset of the ACIA can be triggered by writing to this address, although its primary function is reading status.
# Command Register (CR)

# Address: Base address + 2 (e.g., $F002 or $C302).
# Write (CPU writes to this address): This register is used to control various operational aspects of the UART, such as:
# Enabling/disabling the transmitter and receiver.
# Enabling/disabling receive and transmit interrupts.
# Setting the serial echo mode.
# Controlling the DTR (Data Terminal Ready) and RTS (Request To Send) modem control lines.
# Software reset of the ACIA (different from power-on reset).
# Control Register (CtlR)

# Address: Base address + 3 (e.g., $F003 or $C303).
# Write (CPU writes to this address): This register configures the serial communication parameters:
# Baud Rate Selection: Selects one of 15 programmable baud rates from the on-chip generator or enables an external 16x clock input.
# Word Length: Sets the number of data bits (e.g., 5, 6, 7, 8).
# Number of Stop Bits: Configures 1 or 2 stop bits.
# Parity Generation/Detection: Sets parity (None, Odd, Even, Mark, Space).
# Summary of Register Access and Purpose: