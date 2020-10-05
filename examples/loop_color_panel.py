import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
while True:
    device.set_color('yellow')
    device.sleep(0.5)
    device.set_color('black')
    device.sleep(0.5)
