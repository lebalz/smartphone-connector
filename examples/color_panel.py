import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector


device = Connector('https://io.lebalz.ch', 'FooBar')
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
