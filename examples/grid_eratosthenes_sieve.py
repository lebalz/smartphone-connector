import os
import sys
from pprint import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, GridPointerMsg
from examples.server_adress import SERVER_ADRESS

GRID_W = 10
GRID_H = 14

device = Connector(SERVER_ADRESS, 'FooBar')
# set up white grid
device.set_grid(['white'])
device.set_grid_at(GRID_W - 1, GRID_H - 1, 'white', enumerate=True)


def on_pointer(data: GridPointerMsg):
    # this is the eratosthenes logic...
    # ignore 1
    if (data.number == 1):
        return
    # ignore when already red since it is not prime
    if (data.color == 'red'):
        return
    # update all grid cells being a multiplicative multiple of the number
    # e.g for 2: 4,6,8,10,12
    for num in range(data.number * 2, GRID_H * GRID_W + 1, data.number):
        device.update_cell(cellNumber=num, color='red')


device.on_pointer = on_pointer

device.wait()
