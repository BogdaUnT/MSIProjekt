from common.block import Block

class LookupTable1D(Block):
    def __init__(self, _name, _mode, _x, _y, _repeat = False):
        super().__init__(_name)
        self.mode = _mode
        self.x = _x
        self.y = _y
        self.repeat = _repeat
        self.add_output()

    def calculate(self):
        char_x = self.x
        char_y = self.y

        x = self.input_val(0)
        if self.repeat:
            x = x % self.x[-1]

        y = char_y[len(char_y)-1]
        match self.mode:
            case 'linear':
                if x <= char_x[0]:
                    y = char_y[0]
                else:
                    for i in range(1, len(char_x)):
                        if x<= char_x[i]:
                            m = (char_y[i]-char_y[i-1])/(char_x[i]-char_x[i-1])
                            y = m*x +  char_y[i] - m*char_x[i]
                            break
            case 'last':
                y = char_y[ len(char_x)-1 ]
                for i in range(0, len(char_x)-1):
                  if x < char_x[i+1]:
                    y = char_y[i]
                    break
        self.output_val(0, y )

class Limiter(Block):
    def __init__(self, _name, _lim):
        super().__init__(_name)
        self.lim = _lim
        self.add_output()
        self.add_output()

    def calculate(self):
        x = self.input_val(0)
        if x <= self.lim[0]:
            self.output_val(0, self.lim[0])
            self.output_val(1, -1)
        else:
            if x>= self.lim[1]:
                self.output_val(0, self.lim[1])
                self.output_val(1, 1)
            else:
                self.output_val(0, x)
                self.output_val(1, 0)
