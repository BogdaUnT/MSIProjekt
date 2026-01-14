from common.value import Value
from abc import ABCMeta, abstractmethod

"""
    Blok funkcyjny z wejściami i wyjściami
"""
class Block(metaclass=ABCMeta):
    """
        Konstruktor bloku funkcyjnego

        @param _name Nazwa bloku. Musi być niepowtarzalna w ramach obiektu nadrzędnego.
    """
    def __init__(self, _name):
        self.name = _name
        self.ins = []
        self.outs = []

    """
        Wyzwolenie kroku obliczeń
    """
    @abstractmethod
    def calculate(self):
        pass

    """
        Dodanie wejścia

        @param _input Zmienna typu Value
        @param _del Opóźnienie. Wartości historyczne inicjalizowane są zmienną Value(0). Domyślnie: None
    """
    def add_input(self, _input, _del=None):
        vector = [_input]
        if _del is not None:
            for i in range(0, _del):
                vector.append(Value(0))
        self.ins.append(vector)

    """
        Wejście aktualne (bez opóźnień)

        @param _num Numer wejścia

        @return Zmienna (Value)
    """
    def input(self, _num):
        return self.ins[_num][0]

    """
        Wartość wejścia aktualnego (bez opóźnień)

        @param _num Numer wejścia

        @return Wartość
    """
    def input_val(self, _num):
        return self.ins[_num][0].get()

    """
        Wartość wejścia opóźnionego

        @param _num Numer wejścia
        @param _del Opóźnienie

        @return Wartość
    """
    def input_val_del(self, _num, _del):
        return self.ins[_num][_del].get()

    """
        Dodanie wyjścia

        @param _obj Zmienna typu Value. Gdy niepodana to inicjalizowana Value(_init). Domyślnie: None
        @param _del Opóźnienie. Wartości historyczne inicjalizowane są zmienną Value(_init). Domyślnie: None
        @param _init Wartość domyślna. Domyślnie: 0
    """
    def add_output(self, _obj=None, _del=None, _init=0):
        if _obj is not None:
            vector = [_obj]
        else:
            vector = [Value(_init)]
        if _del is not None:
            for i in range(0, _del):
                if _obj is not None:
                    vector.append(_obj)
                else:
                    vector.append(Value(_init))
        self.outs.append(vector)

    """
        Wyjście aktualne (bez opóźnień)

        @param _num Numer wyjścia

        @return Zmienna (Value)
    """
    def output(self, _num):
        return self.outs[_num][0]

    """
        Wyjście opóźnione

        @param _num Numer wyjścia
        @param _del Opóźnienie

        @return Zmienna (Value)
    """
    def output_del(self, _num, _del):
        return self.outs[_num][_del]

    """
        Wartość wyjścia aktualnego (bez opóźnień)

        @param _num Numer wyjścia

        @return Wartość
    """
    def output_val(self, _num, _val=None):
        if _val is None:
            return self.outs[_num][0].get()
        else:
            self.outs[_num][0].set(_val)
            return 0

    """
        Wartość wyjścia opóźnionego

        @param _num Numer wyjścia
        @param _del Opóźnienie

        @return Wartość
    """
    def output_val_del(self, _num, _del, _val=None):
        if _val is None:
            return self.outs[_num][_del].get()
        else:
            self.outs[_num][_del].set(_val)
            return 0

    """
        Aktualizacja stanu (przeszłych wartości wejść i wyjść)
    """
    def state_update(self):
        for j in range(0, len(self.ins)):
            for i in range(len(self.ins[j])-1, 0, -1):
                self.ins[j][i].set( self.ins[j][i-1].get() )

        for j in range(0, len(self.outs)):
            for i in range(len(self.outs[j])-1, 0, -1):
                self.outs[j][i].set( self.outs[j][i-1].get() )

    """
        Inicjalizacja - ustawienie wartości początkowych/domyślnych
    """
    def init_sim(self):
        for j in range(0, len(self.ins)):
            for i in range(0, len(self.ins[j])):
                self.ins[j][i].init()

        for j in range(0, len(self.outs)):
            for i in range(0, len(self.outs[j])):
                self.outs[j][i].init()

"""
    Blok funkcyjny z okresem próbkowania
"""
class SampledBlock(Block):
    """
        Konstruktor bloku funkcyjnego z okresem próbkowania

        @param _name Nazwa bloku. Musi być niepowtarzalna w ramach obiektu nadrzędnego.
        @param _tp Okres próbkowania. Wykorzystywany do obliczania zaleśnoci dynamicznych
    """
    def __init__(self, _name, _tp):
        super().__init__(_name)
        self.tp = _tp