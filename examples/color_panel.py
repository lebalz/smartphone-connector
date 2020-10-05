import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')

device.set_color('green')
device.sleep(0.5)
device.set_color('rgb(255,0,0)')
device.sleep(0.5)
device.set_color('rgba(255,0,0, 0.5)')
device.sleep(0.5)
device.set_color(1)
device.sleep(0.5)
device.set_color('6')

device.disconnect()
