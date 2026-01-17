from common.block import Block

"""
    Blok funkcyjny reprezentujacy podsystem składający się z bloków funkcyjnych
"""
class Subsystem(Block):
    """
        Konstruktor podsystemu

        @param _name Nazwa. Musi być niepowtarzalna w ramach obiektu nadrzędnego.
        @param _inputs Lista wejść (obiekty Value), które mają zostać dodane do podsystemu
    """
    def __init__(self, _name, _inputs):
        super().__init__(_name)
        self.blocks = {}

        for inpt in _inputs:
            self.add_input(inpt)

    """
        Dodanie bloku funkcyjnego

        @param _block Obiekt typu Block
    """
    def add_block(self, _block):
        self.blocks[_block.name] = _block
        return _block

    """
        Blok funkcyjny

        @param _name Nazwa bloku
        
        @return Blok funkcyjny Block
    """
    def block(self, _name):
        return self.blocks[_name]

    """
        Wyzwolenie kroku obliczeń
    """
    def calculate(self):
        for block in self.blocks.values():
            block.calculate()

    """
        Aktualizacja stanu (przeszłych wartości wejść i wyjść podsystemu oraz bloków składowych)
    """
    def state_update(self):
        super().state_update()
        for block in self.blocks.values():
            block.state_update()

    """
        Inicjalizacja - ustawienie wartości początkowych/domyślnych podsystemu i bloków składowych
    """
    def init_sim(self):
        super().init_sim()
        for block in self.blocks.values():
            block.init_sim()

class Switch(Block):
    def __init__(self, _name, _thr):
        super().__init__(_name)
        self.thr = _thr
        self.add_output()

    def calculate(self):
        ctrl = self.input_val(1)
        if ctrl >= self.thr:
            self.output_val(0, self.input_val(2))
        else:
            self.output_val(0, self.input_val(0))

class MultiSwitch(Block):
    def __init__(self, _name):
        super().__init__(_name)
        self.add_output()

    def calculate(self):
        self.output_val(0, self.input_val( self.input_val(0) ))