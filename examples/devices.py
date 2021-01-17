import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_address import SERVER_ADDRESS
import pprint

device = Connector(SERVER_ADDRESS, 'FooBar')


def on_devices(data: DevicesMsg):
    for d in data:
        print(d)
    print(list(filter(lambda d: d['device_id'].startswith('game-')
                      and ('is_silent' not in d or not d['is_silent']), data)))


device.on_devices = on_devices

device.sleep(15)

device.disconnect()
