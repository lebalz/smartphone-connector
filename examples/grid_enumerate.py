import os
import sys
from pprint import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')

device.set_grid(
    """
    99999999999999
    99999....99999
    99999....99999
    99999....99999
    99999....99999
    9............9
    9............9
    9............9
    9............9
    99999....99999
    99999....99999
    99999....99999
    99999....99999
    99999999999999
    """,
    base_color='blue',
    enumerate=True
)
device.sleep(1)
device.set_grid_at(20, 20, 'red')
device.sleep(1)
device.set_grid("""
90
09
""", enumerate=True)
device.sleep(1)
device.set_grid_at(cellNumber=1, color='blue')
device.sleep(1)
device.set_grid_at(cellNumber=2, color='green')
device.sleep(1)
device.set_grid_at(cellNumber=3, color='red')
device.sleep(1)
device.set_grid_at(cellNumber=4, color='yellow')
device.sleep(1)
device.set_grid_at(cellNumber=15, color='wheat')
device.sleep(1)

device.update_grid(enumerate=False)
device.sleep(1)

device.update_grid(enumerate=True)

device.disconnect()
