# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 12:48:07 2026

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
