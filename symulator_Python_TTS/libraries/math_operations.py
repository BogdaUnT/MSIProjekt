import numpy as np
import math

from common.block import Block

class SumDiff(Block):
    def __init__(self, _name, _w):
        super().__init__(_name)
        self.w = _w
        self.add_output()

    def calculate(self):
        val = 0
        for i in range(0, len(self.ins)):
            val = val + self.input_val(i)*self.w[i]
        self.output_val(0, val )

class Gain(Block):
    def __init__(self, _name, _k):
        super().__init__(_name)
        self.k= _k
        self.add_output()

    def calculate(self):
        self.output_val(0, self.input_val(0)*self.k )

class MulDiv(Block):
    def __init__(self, _name, _w):
        super().__init__(_name)
        self.w = _w
        self.add_output()

    def calculate(self):
        val = 1
        for i in range(0, len(self.ins)):
            w = self.w[i]
            # val = val * pow( self.input_val(i), int(np.sign(w))) * abs(w)
            val = val * self.input_val(i) ** int(np.sign(w)) * abs(w)
        self.output_val(0, val )

class Pow(Block):
    def __init__(self, _name, _exponent):
        super().__init__(_name)
        self.exponent = _exponent
        self.add_output()

    def calculate(self):
        self.output_val(0, pow( self.input_val(0), self.exponent ))

class Sign(Block):
    def __init__(self, _name):
        super().__init__(_name)
        self.add_output()

    def calculate(self):
        x = self.input_val(0)
        if x > 0:
            self.output_val(0, 1)
        else:
            if x < 0:
                self.output_val(0, -1)
            else:
                self.output_val(0, 0)

class Abs(Block):
    def __init__(self, _name):
        super().__init__(_name)
        self.add_output()

    def calculate(self):
        self.output_val(0, abs(self.input_val(0)))

class Equation(Block):
    def __init__(self, _name, _coef):
        super().__init__(_name)
        self.coef = _coef
        self.add_output()

    def calculate(self):
        y = 0
        x = self.input_val(0)
        for i in range(0, len(self.coef)):
            y += self.coef[i]*pow(x,i)
        self.output_val(0, y)

class Exp(Block):
    def __init__(self, _name):
        super().__init__(_name)
        self.add_output()

    def calculate(self):
        self.output_val(0, math.exp(self.input_val(0)))