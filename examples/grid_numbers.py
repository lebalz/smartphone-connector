import os
import sys
from pprint import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')

device.set_grid([1, 2, 3, 4], base_color='blue')
device.sleep(1)

device.disconnect()
