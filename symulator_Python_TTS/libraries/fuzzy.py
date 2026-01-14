from fuzzylogic.classes import Domain, Set, Rule
from fuzzylogic.functions import R, S, triangular
from common.block import Block

"""
    Prosty regulator rozmyty z dwoma wejściami: e, de
    i jednym wyjściem dCV.
"""
# Simple fuzzy kontroller with 2 inputs: e, de
# and 1 output: dCV

class SimpleFuzzyController(Block):
    def __init__(self, _name):
        super().__init__(_name)

        prec = 0.001
        self.e_dom = Domain("e", -1, 1, prec)
        self.e_dom.N = S(-1, 1)
        self.e_dom.P = R(-1, 1)

        self.de_dom = Domain("de", -1, 1, prec)
        self.de_dom.N = S(-1, 1)
        self.de_dom.P = R(-1, 1)

        self.dcv_dom = Domain("dCV", -1-prec, 1+prec, prec)
        self.dcv_dom.N = triangular(-1-prec, -1+prec)
        self.dcv_dom.Z = triangular(-prec, prec)
        self.dcv_dom.P = triangular(1-prec, 1+prec)

        R1 = Rule({(self.e_dom.N, self.de_dom.N): self.dcv_dom.N})
        R2 = Rule({(self.e_dom.N, self.de_dom.P): self.dcv_dom.Z})
        R3 = Rule({(self.e_dom.P, self.de_dom.N): self.dcv_dom.Z})
        R4 = Rule({(self.e_dom.P, self.de_dom.P): self.dcv_dom.P})
        self.rules = R1 | R2 | R3 | R4

        self.add_output()

    def calculate(self):
        ke = self.input_val(0)
        kde = self.input_val(1)
        kdcv = self.input_val(2)
        e = self.input_val(3)
        de = self.input_val(4)
        values = {self.e_dom: e/ke, self.de_dom: de/kde}
        self.output_val(0, self.rules(values)*kdcv )