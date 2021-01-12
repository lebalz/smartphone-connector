import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')
while True:
    device.set_color('yellow')
    device.sleep(0.5)
    device.set_color('black')
    device.sleep(0.5)
