from common.block import *

class BasicLogic(Block):
    def __init__(self, _name, _oper):
        super().__init__(_name)
        self.oper = _oper
        self.add_output()

    def calculate(self):
        val = bool(self.input_val(0))
        match self.oper:
            case 'not':
                self.output_val(0, int(not val))
            case 'and':
                for i in range(1, len(self.ins)):
                    val = val and bool(self.input_val(i))
                self.output_val(0, int(val))
            case 'nand':
                for i in range(1, len(self.ins)):
                    val = val and bool(self.input_val(i))
                self.output_val(0, int(not val))
            case 'or':
                for i in range(1, len(self.ins)):
                    val = val or bool(self.input_val(i))
                self.output_val(0, int(val))
            case 'nor':
                val = bool(self.input_val(0))
                for i in range(1, len(self.ins)):
                    val = val or bool(self.input_val(i))
                self.output_val(0, int(not val))
            case _:
                self.output_val(0, 0)

class Rel(Block):
    def __init__(self, _name, _oper):
        super().__init__(_name)
        self.oper = _oper
        self.add_output()

    def calculate(self):
        match self.oper:
            case '<':
                self.output_val(0, int(self.input_val(0) < self.input_val(1)))
            case '<=':
                self.output_val(0, int(self.input_val(0) <= self.input_val(1)))
            case '>=':
                self.output_val(0, int(self.input_val(0) >= self.input_val(1)))
            case '>':
                self.output_val(0, int(self.input_val(0) > self.input_val(1)))
            case _:
                self.output_val(0, 0)