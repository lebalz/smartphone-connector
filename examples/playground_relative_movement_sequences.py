import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, AccMsg, KeyMsg, Colors
from random import randint
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')
device.clear_playground()

id = device.add_circle(
    pos_x=0,
    pos_y=0,
    radius=5,
    color=Colors.RED
)

device.sleep(3)

speed = 3

device.update_circle(
    id=id,
    movements={
        'repeat': 10,
        'movements': [
            {'movement': 'relative', 'direction': [0, 1], 'distance': 50, 'speed': speed},
            {'movement': 'relative', 'direction': [0, -1], 'distance': 50, 'speed': speed}
        ]
    }
)
device.set_timeout(lambda x: device.update_circle(id=id, pos_x=-50), time=2)
