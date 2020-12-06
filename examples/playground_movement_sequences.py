import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, AccMsg, KeyMsg, Colors
from random import randint
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=50
)

id = device.add_circle(
    pos_x=0,
    pos_y=40,
    radius=5,
    color=Colors.RED,
    direction=[0, -1],
    speed=1,
    time_span=4
)

device.sleep(3)

speed = 1

device.update_circle(
    id=id,
    movements={
        'repeat': 2,
        'movements': [
            {
                'direction': [1, 0],
                'distance': 10,
                'speed': speed
            },
            {
                'direction': [0, 1],
                'speed': speed,
                'time_span': 0.5
            },
            {
                'direction': [-1, 0],
                'distance': 10,
                'speed': speed
            }, {
                'direction': [0, -1],
                'time_span': 0.5,
                'speed': speed
            }
        ]
    }
)
device.sleep(1)
device.update_circle(
    id=id,
    movements={
        'movements': [
            {
                'direction': [0, 1],
                'distance': 10,
                'speed': 10
            },
            {
                'direction': [0, -1],
                'distance': 10,
                'speed': 10
            }
        ]
    }
)

device.disconnect()
