import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, AccMsg, KeyMsg, Colors
from random import randint
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')
device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=50
)

id = device.add_circle(
    pos_x=0,
    pos_y=0,
    radius=5,
    color=Colors.RED
)

pos_x = 0


def on_key(data: KeyMsg):
    global pos_x
    if (data.key == 'right'):
        device.move_to(id, [pos_x + 5, 0], time=1, via=[pos_x + 2.5, 30])
        pos_x = pos_x + 5
    if (data.key == 'left'):
        device.move_to(id, [pos_x - 5, 0], time=1, via=[pos_x - 2.5, 30])
        pos_x = pos_x - 5


device.on('key', on_key)
device.on('auto_movement_pos', lambda d: print(d.object))

device.sleep()
