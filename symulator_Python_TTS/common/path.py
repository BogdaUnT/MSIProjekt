from common.with_io_vars import WithIOVars

"""
    Tor przetwarzania składający się z bloków funkcyjnych
"""
class Path(WithIOVars):
    """
        Konstruktor toru przetwarzania

        @param _name Nazwa. Musi być niepowtarzalna w ramach obiektu nadrzędnego.
        @param _pr Krotność przetwarzania. Tor obliczany jest co _pr krok.
    """
    def __init__(self, _name, _pr=1):
        super().__init__()
        self.name = _name
        self.blocks = {}
        self.pr = _pr
        self.k = 0

    """
        Dodanie bloku funkcyjnego

        @param _block Obiekt typu Block
    """
    def add_block(self, _block):
        self.blocks[_block.name] = _block
        return _block

    """
        Metoda pomocnicza drukująca wartości wyjść
    """
    def print_outputs(self):
        for key, out in self.out_vars.items():
            print(key+': '+ str(out.get()))

    """
        Wyzwolenie kroku symulacji
    """
    def simulation_step(self):
        if self.k % self.pr == 0:
            for block in self.blocks.values():
                block.calculate()

            for block in self.blocks.values():
                block.state_update()
        self.k += 1

    """
        Inicjalizacja - ustawienie wartości początkowych/domyślnych ścieżki i elementów składowych
    """
    def init_sim(self):
        for block in self.blocks.values():
            block.init_sim()