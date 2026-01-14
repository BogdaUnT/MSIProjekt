"""
    Obiekt ze zmiennymi wejściowymi/wyjściowymi
"""
class WithIOVars:
    """
        Konstruktor obiektu ze zmiennymi wejściowymi/wyjściowymi
    """
    def __init__(self):
        self.in_vars = {}
        self.out_vars = {}

    """
        Dodanie zmiennej wejściowej

        @param _nazwa Nazwa zmiennej
        @param _val Wartość domyślna/początkowa
    """
    def add_in_var(self, _name, _val):
        self.in_vars[_name] = _val

    """
        Zmienna wejściowa

        @param _nazwa Nazwa zmiennej

        @return Zmienna (Value)
    """
    def in_var(self, _name):
        return self.in_vars[_name]

    """
        Ustawienie/Pobranie wartości zmiennej wejściowej

        @param _nazwa Nazwa zmiennej
        @param _val Wartoś. Domyślnie: None  

        @return Wartość jeżeli odczyt lub 0 gdy zapis
    """
    def in_var_val(self, _name, _val=None):
        if _val is None:
            return self.in_vars[_name].get()
        else:
            self.in_vars[_name].set(_val)
            return 0

    """
        Dodanie zmiennej wyjściowej

        @param _nazwa Nazwa zmiennej
        @param _val Wartość domyślna/początkowa
    """
    def add_out_var(self, _name, _val):
        self.out_vars[_name] = _val

    """
        Zmienna wyjściowa

        @param _nazwa Nazwa zmiennej

        @return Zmienna (Value)
    """
    def out_var(self, _name):
        return self.out_vars[_name]

    """
        Pobranie wartości zmiennej wyjściowej

        @param _nazwa Nazwa zmiennej

        @return Wartość
    """
    def out_var_val(self, _name):
        return self.out_vars[_name].get()