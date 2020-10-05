import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
dimension = 1
device.set_grid([['white']])

while True:
    for i in range(dimension):

        device.set_grid_at(i, dimension, 'white' if dimension % 2 == 0 else 'black')
        device.set_grid_at(dimension, i, 'black' if dimension % 2 == 0 else 'white')
        device.sleep(0.05)
    dimension = dimension + 1

    if dimension > 50:
        device.set_grid([['white']])
        dimension = 1
        device.sleep(1)
