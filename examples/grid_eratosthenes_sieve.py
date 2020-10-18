import os
import sys
from pprint import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, GridPointerMsg
from examples.server_adress import SERVER_ADRESS

GRID_W = 20
GRID_H = 20

device = Connector(SERVER_ADRESS, 'FooBar')
# set up white grid
device.setup_grid(GRID_H, GRID_W, enumerate=True)


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
    updates = 0
    for num in range(data.number * 2, GRID_H * GRID_W + 1, data.number):
        if device.get_grid_at(cell_number=num) != 'red':
            updates = updates + 1
            device.update_cell(cell_number=num, color='red')
    print(updates)


device.on_pointer = on_pointer

device.wait()
