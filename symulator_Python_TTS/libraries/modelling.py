from tensorflow import keras
from common.block import Block
from numpy import array

class KerasModelFirstOrder(Block):
    def __init__(self, _name, _model, _mode):
        super().__init__(_name)
        self.add_output(None, 1, 0.018)

        self.mode = _mode
        self.model = keras.models.load_model('../output/'+_model+'.keras')

    def add_input(self, _input, _del=1):
        super().add_input(_input, _del)

    def calculate(self):
        match self.mode:
            case 'std':
                features = array([[self.input_val_del(0, 1), self.input_val_del(1, 1)]])
            case 'mro':
                features = array([[self.input_val_del(0, 1), self.output_val_del(0, 1)]])
            case _:
                features = 0
        self.output_val(0, self.model.predict(features, verbose=None)[0][0])