import numpy as np
import math

from common.block import *

class Const(Block):
    def __init__(self, _name, _const):
        super().__init__(_name)
        self.const = Value(_const)
        self.add_output()

    def calculate(self):
        self.output_val(0, self.const.get() )

class Random(Block):
    def __init__(self, _name, _mean, _stddev):
        super().__init__(_name)
        self.mean = _mean
        self.stddev = _stddev
        self.add_output()

    def calculate(self):
        self.output_val(0, np.random.normal(self.mean, self.stddev) )

class Time(SampledBlock):
    def __init__(self, _name, _tp):
        super().__init__(_name, _tp)
        self.counter = 0
        self.add_output()

    def calculate(self):
        self.output_val(0, self.counter*float(self.tp) )
        self.counter += 1

    def init_sim(self):
        self.counter = 0

class Generator(SampledBlock):
    def __init__(self, _name, _tp, _type, _amp, _bias, _period, _phase, _width=None):
        super().__init__(_name, _tp)
        self.counter = 0
        self.type = Value(_type)
        self.amp = Value(_amp)
        self.bias = Value(_bias)
        self.period = Value(_period)
        self.phase = Value(_phase)
        self.width = Value(_width)
        self.add_output()

    def calculate(self):
        t = self.counter * float(self.tp)
        match self.type.get():
            case 'sine':
                self.output_val(0, self.amp.get() * math.sin(2*math.pi/self.period.get()*t + 2*math.pi*self.phase.get()/360) + self.bias.get() )
            case 'square':
                x_period = ((t+self.phase.get()%360/360*self.period.get())%self.period.get())/self.period.get()
                if x_period < self.width.get():
                    self.output_val(0, self.amp.get() + self.bias.get())
                else:
                    self.output_val(0, -self.amp.get() + self.bias.get())
            case 'saw tooth':
                self.output_val(0, self.amp.get() * (t%self.period.get())/self.period.get() + self.bias.get())
        self.counter += 1

    def init_sim(self):
        self.counter = 0