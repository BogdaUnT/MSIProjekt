import math

from common.block import *

class FirstOrderBlock(SampledBlock):
    def __init__(self, _name, _tp, _init=0):
        super().__init__(_name, _tp)
        self.add_output(None, 1, _init)

    def add_input(self, _input, _del=1):
        super().add_input(_input, _del)

class FirstOrderInertia(FirstOrderBlock):
    def __init__(self, _name, _tp, _k, _t):
        super().__init__(_name, _tp)
        self.k = _k
        self.T = _t
        self.a1 = math.exp(-self.tp/_t)
        self.b0 = _k*(1-self.a1)
        self.first_run = True

    def calculate(self):
        if not self.first_run:
            self.output_val(0, self.b0*self.input_val_del(0, 1) + self.a1*self.output_val_del(0, 1) )
        else:
            self.output_val(0, self.input_val_del(0, 0))
            self.first_run = False

    def init_sim(self):
        self.first_run = True
        super().init_sim()

class FirstOrderIntegrator(FirstOrderBlock):
    def __init__(self, _name, _tp, _k, _t, _lim=None, _init=0):
        super().__init__(_name, _tp, _init)
        self.k = _k
        self.T = _t
        self.b0 = _k*self.tp/_t
        if _lim is not None:
            self.lim_low = _lim[0]
            self.lim_high = _lim[1]
        else:
            self.lim_low = None
            self.lim_high = None

    def calculate(self):
        y = self.b0*self.input_val_del(0, 1) + self.output_val_del(0, 1)
        if self.lim_low is not None and y<self.lim_low:
            self.output_val(0, self.lim_low)
        else:
            if self.lim_high is not None and y>self.lim_high:
                self.output_val(0, self.lim_high)
            else:
                self.output_val(0, y)

class RealDifferentiator(FirstOrderBlock):
    def __init__(self, _name, _tp, _k, _t):
        super().__init__(_name, _tp)
        self.k = _k
        self.T = _t
        self.a1 = -math.exp(-_tp/_t)
        self.b0 = (1+self.a1)*_k/(_t*_tp)
        self.b1 = -self.b0

    def calculate(self):
        self.output_val(0, -self.a1 * self.output_val_del(0, 1) + self.b0*self.input_val(0) +  self.b1 * self.input_val_del(0, 1))