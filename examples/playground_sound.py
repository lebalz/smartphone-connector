import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_adress import SERVER_ADRESS
import random
DT = 2

device = Connector(SERVER_ADRESS, 'FooBar')

device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=50,
    audio_tracks='tracks'
)
device.play_sound('helicopter', volume=0.1)

device.sleep(2)
device.play_sound('kling', volume=0.3)
device.sleep(0.2)
device.play_sound('goat', volume=0.1)
device.sleep(1)
device.play_sound('goat', volume=0.5)
device.sleep(1)
device.play_sound('goat', volume=0.9)

device.sleep(3)
device.disconnect()
