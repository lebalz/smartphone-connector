import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_address import SERVER_ADDRESS
import random
DT = 2

device = Connector(SERVER_ADDRESS, 'FooBar')

device.on_timer = lambda d: print(d)

device.sleep(20)
device.disconnect()
