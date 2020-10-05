import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
import numpy as np
from server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')

grid1 = np.transpose([[1, 2, 3], [1, 2, 3], [1, 2, 3]])
device.set_grid(grid1,
                base_color='red'
                )
assert grid1.tolist() == device.get_grid
print('ok')

grid2 = np.transpose([[1, 2, 3], [1, 2, 3]])
device.set_grid(grid2,
                base_color='red'
                )
assert grid2.tolist() == device.get_grid
print('ok2')
device.disconnect()
