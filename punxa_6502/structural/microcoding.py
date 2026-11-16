# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 18:48:21 2026

@author: dcr
"""

import py4hw

from .sequencer import Sequencer

class MicrocodedControlUnit6502(py4hw.Logic):
    
    def __init__(self, parent, name:str, reset, status, control):        
        super().__init__(parent, name)

        self.addIn('reset', reset)

        for key in status.keys():
            self.addIn(key, status[key])

        
        for key in control.keys():
            self.addOut(key, control[key])
            
            
        self.status = status
        self.control = control
        
        # INS_EXE = 0
        # INS_JC =  1     # conditional jump
        # INS_JMP = 2     # jump 
        # INS_JSR = 3     # jump subroutine
        # INS_RET = 4     # ret subroutine
        
        rom_add_w = 11
        
        ins = self.wire('ins', 3)
        cond = self.wire('cond')
        dispatch = self.wire('dispatch')
        pc = self.wire('pc', rom_add_w )
        rom_address = self.wire('rom_address', rom_add_w )
        address = self.wire('address', rom_add_w )
        oe = self.wire('oe')
        
        fetch = self.wire('fetch')
        finish_dispatch = self.wire('finish_dispatch')
        set_dispatch= self.wire('set_dispatch')
        
        py4hw.Or2(self, 'set_dispatch', fetch, finish_dispatch, set_dispatch)
        py4hw.Not(self, 'fetch', dispatch, fetch)
        
        # We start by executing fetch 
        py4hw.Reg(self, 'dispatch', d=fetch, q=dispatch, enable=set_dispatch, reset=reset, reset_value=1)
        py4hw.Mux2(self, 'rom_address', sel=dispatch, sel0=status['q_IR'], sel1=pc, r=rom_address)
        
        
        
        # build condition mux
        nstatus = len(status) - 1 # ignore q_IR
        
        import math
        nsw = int(math.ceil(math.log2(nstatus * 2))) 
        nstatus_p2 = 1 << nsw
        
        sel_cond = self.wire('sel_cond', nsw)
        
        # We ignore q_IR from status signals
        # We have to build a condition mux, but we need 
        # both the positive and the negated value of the 
        # status signals
        list_status_keys = list(status.keys())
        list_status_keys.remove('q_IR')
        
        mux_wires = []
        for key in list_status_keys:
            negated_status = self.wire(f'n_{key}')
            py4hw.Not(self, f'n_{key}', status[key], negated_status)
            mux_wires.append(status[key])
            mux_wires.append(negated_status)
        
        # fill the rest with zero
        zero = self.wire('zero')
        py4hw.Constant(self, 'zero', 0, zero)
        
        for i in range(len(mux_wires), nstatus_p2):
            mux_wires.append(zero)
            
        py4hw.Mux(self, 'cond_mux', sel=sel_cond, ins=mux_wires, r=cond)
        

        # With control signals we have to add finish_dispatch and use
        # the oe signal to enable them only in EXE instructions
        extended_control = {}
        extended_control['finish_dispatch'] = finish_dispatch
        
        for key_c in control.keys():
            c = control[key_c]
            enabled_c = self.wire(f'exe_{c.name}')
            py4hw.And2(self, f'exe_{c.name}', enabled_c, oe, c)
            extended_control[key_c] = enabled_c
            
        
        rom_control = self.wire('rom_control', len(extended_control.keys()))
        py4hw.BitsLSBF(self, 'control', rom_control, list(extended_control.values()))

        # @todo WE SHOULD AUTOMATICALLY BUILD THE ROM        
        # ANALYZING THE CODE OF THE ALGORITHMIC MODEL IMPLEMENTATION
        # TAKING INTO ACCOUNT THAT INSTEAD OF THE HUGE IF/ELSE STRUCTURE
        # WE SHOULD USE A VECTORED APPROACH HERE. THE FIRST 256 POSITIONS
        # SHOULD CONTAIN JMP INSTRUCTIONS TO THE INSTRUCTION SUBPROGRAM

        control_keys = list(extended_control.keys())
        control_widths = {}
        nc = 0
        for key in control_keys:
            control_widths[key] = extended_control[key].getWidth()
            nc += extended_control[key].getWidth()

        cond_index = {'q_B': 0, 'q_C':1, 'q_D':2, 'q_Z':3, 'q_N':4, 'q_I':5, 'q_V':6,
                      'alu_C':7, 'alu_V':8, 'alu_Z':9, 'alu_N':10 }
            
        na = rom_add_w # the address of the ROM memory is stored
        nac = max(nc, na) # number of address or control bits
        rom_line= self.wire('rom_line', 3 + nsw + nac)
        
        from .python2microcode import Python2SequencerROM
        from .multicycle_processor import ControlUnit6502Behavioral
        rom = Python2SequencerROM(control_widths, cond_index, nsw, nac, 
                                  addr_width=rom_add_w , baseline={'alu_op': 0})
        rom.analyzeClass(ControlUnit6502Behavioral)
        fetch_addr = rom.address_of('fetchIR')      # 257 with the current layout

        print(*rom.warnings, sep='\n')
        contents, line_width = rom.contents(), rom.line_width   # feeds AsynchronousROM and the rom_line wire
        
        print('Expected ROM Line width=', 3+nsw+nac)
        print('ROM Line width=', line_width)

        MicrocodingROM(self, 'rom', rom_address, rom_line, contents, **rom.rom_metadata())
        
        Sequencer(self, 'seq', reset, ins, cond, address, pc, oe, 3, reset_pc=fetch_addr)
        
        # ROM Line structure
        # instruction (3 bits) | condition (nsw bits) | address / control (nac bits)
        py4hw.Range(self, 'rom_control', rom_line, nc-1, 0, rom_control)
        py4hw.Range(self, 'address', rom_line, na-1, 0, address)
        py4hw.Range(self, 'cond', rom_line, nac+nsw-1, nac, sel_cond)
        py4hw.Range(self, 'ins', rom_line, nac+3+nsw-1, nac+nsw, ins)


class MicrocodingROM(py4hw.AsynchronousROM):

    def __init__(self, parent, name, address, data, contents,
                 layout=None, nsw=0, nac=0, labels=None,
                 ins_names=None, cond_names=None):
        """
        layout:     ordered {signal: (lsb, width)} of the control fields
        nsw, nac:   widths of the condition-select field and of the shared
                    address/control field (line = ins | cond | addr/ctrl)
        labels:     {rom_address: 'label1,label2'}
        ins_names:  {ins_value: 'EXE'}
        cond_names: {cond_value: 'q_Z'}  (odd values are inverted: '!q_Z')
        """
        super().__init__(parent, name, address, data, contents)
        self.layout = dict(layout or {})
        self.nsw, self.nac = nsw, nac
        self.labels = labels or {}
        self.ins_names = ins_names or {}
        self.cond_names = cond_names or {}
        self._tree = None          # set by tkinter_gui, cleared on destroy
        self._shown = None         # last address shown in the GUI
        self._pending = False      # an update is already scheduled

    def propagate(self):
        super().propagate()        # normal ROM behavior: data = contents[address]
        if self._tree is not None and not self._pending:
            self._pending = True
            try:
                self._tree.after_idle(self._update_selection)
            except Exception:
                self._pending = False   # widget is going away

    SCROLL_MARGIN = 3

    def _update_selection(self):
        self._pending = False
        tree = self._tree
        if tree is None:
            return
        a = self.read_address.get()
        items = tree.get_children()
        if a >= len(items):
            return
        self._shown = a
        item = items[a]
        tree.selection_set(item)
        tree.focus(item)
        self._scroll_to_row(a)
        
    def _viewport(self):
        """(first_row_index, visible_row_count) or None if not laid out yet."""
        tree = self._tree
        first_item = ''
        for y in range(0, 80):                    # skip the heading
            first_item = tree.identify_row(y)
            if first_item:
                break
        if not first_item:
            return None
        bb = tree.bbox(first_item)
        if not bb:
            return None
        _, y, _, rowh = bb
        if rowh <= 0:
            return None

        # real bottom edge = smallest bottom among the tree and all its ancestors
        bottom = tree.winfo_rooty() + tree.winfo_height()
        w = tree.master
        while w is not None:
            b = w.winfo_rooty() + w.winfo_height() - getattr(self, '_reserved', 0)
            bottom = min(bottom, b)
            w = w.master
        top = tree.winfo_rooty() + y
        visible = max(1, int((bottom - top) // rowh))
        return tree.index(first_item), visible

    def _scroll_to_row(self, a):
        vp = self._viewport()
        if vp is None:
            return
        
        first, visible = vp
        last = first + visible - 1
        m = min(self.SCROLL_MARGIN, (visible - 1) // 2)

        if first + m <= a <= last - m:
            return                                 # comfortably visible

        if first - visible <= a <= last + visible:
            delta = (a - m - first) if a < first + m else (a - (last - m))
        else:
            delta = a - visible // 2 - first       # far jump: center

        if delta:
            self._tree.yview_scroll(delta, 'units')
            
    def on_button_click(self):
        pass

    # ----- decoding of one ROM line -----
    def decode_line(self, v):
        ins = (v >> (self.nac + self.nsw)) & 0x7
        cond = (v >> self.nac) & ((1 << self.nsw) - 1) if self.nsw else 0
        addr = v & ((1 << self.nac) - 1)
        ctrl = {k: (v >> lsb) & ((1 << w) - 1) for k, (lsb, w) in self.layout.items()}
        return ins, cond, addr, ctrl

    def cond_text(self, cond):
        name = self.cond_names.get(cond >> 1)
        if name is None:
            return ''
        return ('!' if cond & 1 else '') + name

    # target as hex address, with the label of the target line in parentheses
    def target_text(self, addr):
        lbl = self.labels.get(addr, '')
        return '{:04X} ({})'.format(addr, lbl) if lbl else '{:04X}'.format(addr)
    
    def tkinter_gui(self, parent):
        from tkinter import ttk
        import tkinter as tk

        frame = ttk.Frame(parent, padding="10")

        signals = list(self.layout.keys())
        fixed = ["address", "label", "ins", "cond", "target"]
        columns = fixed + signals
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        self.tree = tree

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # headings and widths
        fixed_width = dict(address=70, label=150, ins=90, cond=90, target=70)
        for col in fixed:
            tree.heading(col, text=col)
            tree.column(col, anchor="w" if col == "label" else "center",
                        width=fixed_width[col], stretch=False)
        for k in signals:
            w = self.layout[k][1]
            tree.heading(k, text=k)
            tree.column(k, anchor="center", stretch=False,
                        width=max(8 * len(k), 10 * w) + 16)

        # data: self.data is assumed to hold the ROM words, as in the original code
        words = getattr(self, 'contents', self.data)
        for i in range(len(words)):
            ins, cond, addr, ctrl = self.decode_line(words[i])
            ins_name = self.ins_names.get(ins, '?')
            is_exe = (ins_name == 'EXE')

            if ins_name == 'JC':
                cond_s = '{} ({})'.format(cond, self.cond_text(cond))
            else:
                cond_s = '{}'.format(cond)

            # jump lines use the address/control bits as the target address
            target = '' if is_exe or ins_name == 'RET' else self.target_text(addr)


            controls = []
            for k in signals:
                w = self.layout[k][1]
                controls.append(format(ctrl[k], '0{}b'.format(w)) if is_exe else '')

            tree.insert("", "end", values=(
                "{:04X}".format(i),
                self.labels.get(i, ''),
                '{} ({})'.format(ins, ins_name),
                cond_s,
                target,
                *controls))

        self._tree = tree

        def on_destroy(_event):
            self._tree = None

        tree.bind('<Destroy>', on_destroy)
        self._update_selection()       # show the current line right away
        
        # edit controls (unchanged)
        label = ttk.Label(frame, text="Selected Item:")
        edit_box = ttk.Entry(frame)
        button = ttk.Button(frame, text="Update", command=self.on_button_click)

        tree.grid(column=0, row=0, columnspan=3, sticky="nsew", padx=10, pady=10)
        vsb.grid(column=3, row=0, sticky="ns")
        hsb.grid(column=0, row=1, columnspan=3, sticky="ew", padx=10)

        label.grid(column=0, row=2, padx=10, pady=5, sticky="w")
        edit_box.grid(column=1, row=2, padx=10, pady=5, sticky="ew")
        button.grid(column=2, row=2, padx=10, pady=5, sticky="e")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        return frame