# -*- coding: utf-8 -*-
"""
Created on Sat Nov 14 20:01:46 2026

@author: dcr
"""

import ast, inspect, sys, textwrap
from collections import Counter
from punxa_6502.structural.multicycle_processor import ControlUnit6502Behavioral

# ---------- custom AST nodes ----------
class MicroLine(ast.stmt):                    # one clock cycle = one ROM line
    _fields = ('writes',)
    def __init__(self, writes, lineno=0):
        self.writes, self.lineno = dict(writes), lineno

class CallMicro(ast.stmt):                    # yield from self.method()
    _fields = ('target',)
    def __init__(self, target): self.target = target

class FlagTest(ast.expr):                     # branch on a status flag
    _fields = ('flag', 'pol')
    def __init__(self, flag, pol): self.flag, self.pol = flag, pol

# ---------- pattern helpers ----------
def status_key(n):                            # self.status['k'].get()
    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == 'get' and isinstance(n.func.value, ast.Subscript)
            and ast.unparse(n.func.value.value) in ('self.status', 'status')):
        return n.func.value.slice.value

def prepare_call(s):                          # control['k'].prepare(expr)
    c = s.value if isinstance(s, ast.Expr) else None
    if (isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
            and c.func.attr == 'prepare' and isinstance(c.func.value, ast.Subscript)
            and ast.unparse(c.func.value.value) in ('self.control', 'control')):
        return c.func.value.slice.value, c.args[0]

# ---------- transformers ----------
class StripNoise(ast.NodeTransformer):
    def visit_Expr(self, n):
        v = n.value
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == 'print':
            return None
        return n
    def visit_Assign(self, n):                # keep only status aliases
        return n if status_key(n.value) else None
    def visit_If(self, n):
        self.generic_visit(n)
        return n if (n.body or n.orelse) else None

class BindConstants(ast.NodeTransformer):
    def __init__(self, cls, env): self.cls, self.env = cls, env
    def visit_Attribute(self, n):
        try:
            v = eval(ast.unparse(n), self.env, {'self': self.cls})
        except Exception:
            return self.generic_visit(n)
        return ast.copy_location(ast.Constant(int(v)), n) if isinstance(v, int) else n

class ResolveConditions(ast.NodeTransformer):
    def visit_FunctionDef(self, fn):
        self.alias = {a.targets[0].id: status_key(a.value)
                      for a in ast.walk(fn)
                      if isinstance(a, ast.Assign) and status_key(a.value)}
        return self.generic_visit(fn)
    def visit_If(self, n):
        n.test = FlagTest(*self.cond(n.test))
        self.generic_visit(n)
        return n
    def cond(self, t):
        if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Not):
            f, p = self.cond(t.operand); return f, 1 - p
        if isinstance(t, ast.Compare):
            f, p = self.cond(t.left)
            eq = isinstance(t.ops[0], ast.Eq)
            return f, (p if ((t.comparators[0].value == 1) == eq) else 1 - p)
        if (k := status_key(t)): return k, 1
        if isinstance(t, ast.Name) and t.id in self.alias: return self.alias[t.id], 1
        raise NotImplementedError(f'not a hardware condition: {ast.unparse(t)}')

class GroupCycles(ast.NodeTransformer):
    def __init__(self, signals, warnings): self.signals, self.warn = signals, warnings
    def visit_FunctionDef(self, fn):
        fn.body = self.group(fn.body, {})
        return fn
    def group(self, stmts, pend):
        out = []
        for s in stmts:
            if isinstance(s, ast.Expr) and isinstance(s.value, ast.Yield):
                out.append(MicroLine(pend, s.lineno)); pend = {}
            elif isinstance(s, ast.Expr) and isinstance(s.value, ast.YieldFrom):
                call = s.value.value
                if call.args: raise NotImplementedError(f'line {s.lineno}: call with arguments')
                if pend: raise NotImplementedError(f'line {s.lineno}: writes before call')
                out.append(CallMicro(call.func.attr))
            elif (pc := prepare_call(s)):
                k, arg = pc
                if not isinstance(arg, ast.Constant):
                    raise NotImplementedError(f'line {s.lineno}: non-constant value for {k}')
                self.signals.add(k); pend = {**pend, k: arg.value}
            elif isinstance(s, ast.If):       # writes pending before an if go to both arms
                s.body, s.orelse = self.group(s.body, pend), self.group(s.orelse, pend)
                pend = {}; out.append(s)
            elif isinstance(s, ast.Raise):
                out.append(s)
        if pend: self.warn.append('writes not followed by a yield (dropped): ' + str(pend))
        return out

# ---------- the ROM builder ----------
class Python2SequencerROM:
    INS = dict(EXE=0, JC=1, JMP=2, JSR=3, RET=4)

    def __init__(self, control_widths, cond_index, nsw, nac, addr_width, baseline=None,
                 fetch='fetchIR', dispatch='decodeAndExecute'):
        '''
        Python algorithmic description to sequencer ROM 

        Parameters
        ----------
        control_widths : dictionary
            ordered {signal: bits}, same order as the CU control wires.
        cond_index : dictionary
            {flag: k}; mux input 2k = flag, 2k+1 = not flag..
        addr_width : TYPE, optional
            DESCRIPTION. The default is 12.
        baseline : TYPE, optional
            DESCRIPTION. The default is None.
        fetch : TYPE, optional
            DESCRIPTION. The default is 'fetchIR'.
        dispatch : TYPE, optional
            DESCRIPTION. The default is 'decodeAndExecute'.
        nsw

        Returns
        -------
        None
        '''
        self.cw = control_widths
        #self.cw['finish_dispatch'] = 1
        self.layout, lsb = {}, 0
        
        for k, w in self.cw.items():
            self.layout[k] = (lsb, w)
            lsb += w
            
        self.cond_index = cond_index
        self.nsw = max(1, (2 * len(cond_index) - 1).bit_length())
        self.addr_width = addr_width
        self.nac = max(lsb, addr_width)
        
        assert(nsw == self.nsw)
        assert(nac == self.nac)
        
        self.line_width = 3 + self.nsw + self.nac
        
        self.baseline = {**{k: 0 for k in self.cw}, **(baseline or {})}
        self.fetch, self.dispatch = fetch, dispatch

    # ----- front end -----
    def _parse(self, name):
        src = textwrap.dedent(inspect.getsource(getattr(self.cls, name)))
        return ast.parse(src).body[0]

    def _transform(self, name):
        fn = self._parse(name)
        
        fn = StripNoise().visit(fn)
        fn = BindConstants(self.cls, self.env).visit(fn)
        fn = ResolveConditions().visit(fn)
        fn = GroupCycles(self.signals, self.warnings).visit(fn)

        return fn.body

    def _dispatch_table(self):
        fn = BindConstants(self.cls, self.env).visit(self._parse(self.dispatch))
        node, table = next(n for n in fn.body if isinstance(n, ast.If)), {}
        while node:
            table[node.test.comparators[0].value] = node.body[0].value.value.func.attr
            node = node.orelse[0] if node.orelse and isinstance(node.orelse[0], ast.If) else None
        return table                          # opcodes not here are illegal (the final raise)

    def address_of(self, label):
        for i, l in enumerate(self.lines):
            if label in l['labels']:
                return i
        raise KeyError(label)
        
    def analyzeClass(self, cls, env=None):
        '''
        Analyze the class.

        Parameters
        ----------
        cls : TYPE
            DESCRIPTION.
        env : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        TYPE
            DESCRIPTION.
        '''
        self.cls = cls
        self.env = dict(vars(sys.modules[cls.__module__])) if env is None else env
        self.signals, self.warnings, self.bodies = set(), [], {}
        self.table = self._dispatch_table()

        todo = list(set(self.table.values())) + [self.fetch]
        while todo:
            m = todo.pop()
            if m in self.bodies: continue
            self.bodies[m] = self._transform(m)
            todo += [c.target for s in self.bodies[m] for c in ast.walk(s)
                     if isinstance(c, CallMicro)]

        sites = Counter(c.target for b in self.bodies.values() for s in b
                        for c in ast.walk(s) if isinstance(c, CallMicro))
        self.routines = {m for m, n in sites.items() if n > 1 and m != self.fetch}
        handlers = set(self.table.values())
        if self.routines & handlers:
            self.warnings.append('handler also used as routine')
            
        if (u := self.signals - set(self.cw)):
            self.warnings.append(f'signals not in layout: {u}')

        # ----- back end -----
        self.lines, self.pending, self.nlabel = [], [], 0
        for op in range(256):                 # dispatch table at 0..255
            if op == 0: self.pending.append('TABLE')
            self._add('JMP', target=self.table.get(op, 'JAM'))
        self.pending.append('JAM')
        self._add('JMP', target='JAM')
        self._routine(self.fetch, 'fetch')
        for m in sorted(self.routines):
            self._routine(m, 'ret')
            
        for m in sorted(handlers):
            self._routine(m, 'jmp_fetch')
        self._resolve()
        return self

    # ----- lowering -----
    def _add(self, ins, **kw):
        self.lines.append(dict(ins=ins, labels=self.pending, **kw)); self.pending = []

    def _routine(self, name, tail):
        self.pending.append(name)
        end = self._body(self.bodies[name], dict(self.baseline))
        if tail == 'ret':
            if end != self.baseline: self.warnings.append(f'{name}: exits with residual state')
            self._add('RET')
        elif tail == 'fetch':                 # last cycle of the fetch tail ends the dispatch
            assert self.lines[-1]['ins'] == 'EXE'
            self.lines[-1]['ctrl']['finish_dispatch'] = 1
        else:
            if end != self.baseline: self.warnings.append(f'{name}: exits with residual state')
            self._add('JMP', target=self.fetch)

    def _body(self, stmts, state):
        for s in stmts:
            if isinstance(s, MicroLine):
                state = {**state, **s.writes}
                self._add('EXE', ctrl=dict(state))
            elif isinstance(s, CallMicro):
                if s.target in self.routines:
                    if state != self.baseline:
                        self.warnings.append(f'JSR {s.target} with residual state')
                    self._add('JSR', target=s.target)
                else:
                    state = self._body(self.bodies[s.target], state)
            elif isinstance(s, ast.If):
                state = self._branch(s, state)
            elif isinstance(s, ast.Raise):
                self._add('JMP', target='JAM'); return state
        return state

    def _branch(self, s, state):
        f, pol = s.test.flag, s.test.pol
        if f.startswith('alu_'):
            self.warnings.append(f'line {s.lineno}: branch on combinational flag {f}')
        self.nlabel += 1
        join, then = f'.J{self.nlabel}', f'.T{self.nlabel}'
        idx = 2 * self.cond_index[f] + (0 if pol else 1)
        if not s.orelse:                      # skip the body when the test is false
            self._add('JC', cond=idx ^ 1, target=join)
            end = self._body(s.body, state)
            if end != state: self.warnings.append(f'line {s.lineno}: arm leaves residual state')
        else:
            self._add('JC', cond=idx, target=then)
            e = self._body(s.orelse, state)
            self._add('JMP', target=join)
            self.pending.append(then)
            end = self._body(s.body, state)
            if e != end: self.warnings.append(f'line {s.lineno}: arms join with different state')
        self.pending.append(join)
        return end

    def _resolve(self):
        pos = {l: i for i, ln in enumerate(self.lines) for l in ln['labels']}
        assert not self.pending, 'dangling label'
        for ln in self.lines:
            if 'target' in ln: ln['addr'] = pos[ln['target']]
        if len(self.lines) > 1 << self.addr_width:
            self.warnings.append(f'{len(self.lines)} lines exceed {self.addr_width} address bits')

    # ----- output -----
    def pack(self, ln):
        w = (self.INS[ln['ins']] << (self.nac + self.nsw)) | (ln.get('cond', 0) << self.nac)
        if ln['ins'] == 'EXE':
            for k, v in ln['ctrl'].items():
                if k in self.layout:
                    lsb, wd = self.layout[k]; w |= (v & ((1 << wd) - 1)) << lsb
        else:
            w |= ln.get('addr', 0)
        return w

    def contents(self):
        return [self.pack(l) for l in self.lines]

            
    def listing(self):
        for i, l in enumerate(self.lines):
            ctrl = {k: v for k, v in l.get('ctrl', {}).items() if v != self.baseline.get(k)}
            target = ''
            if l.get('target'):
                target = f"{l['target']} ({l['addr']})"
            print(f"{i:4d} {','.join(l['labels']):14s} {l['ins']:4s} "
                  f"{target} {ctrl or ''}")
            
            
    def rom_metadata(self):
            """Keyword arguments for MicrocodingROM."""
            return dict(
                layout=self.layout,
                nsw=self.nsw,
                nac=self.nac,
                labels={i: ','.join(l['labels']) for i, l in enumerate(self.lines) if l['labels']},
                ins_names={v: k for k, v in self.INS.items()},
                cond_names={v: k for k, v in self.cond_index.items()},
            )