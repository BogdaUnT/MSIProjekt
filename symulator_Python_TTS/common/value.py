class Value:
    def __init__(self, _x):
        self.val = _x
        self.default = _x

    def set(self, _x):
        self.val = _x

    def get(self):
        return self.val

    def init(self):
        self.val = self.default