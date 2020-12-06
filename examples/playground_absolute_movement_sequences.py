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
with device.add_objects() as add:
    for i in range(22):
        add(
            form='round',
            pos_x=50 - i * 5,
            pos_y=-40,
            radius=5,
            color=Colors.next(),
            movements={
                'cycle': True,
                'movements': [
                    {
                        'movement': 'absolute',
                        'to': [-50, -40],
                        'speed': 10
                    },
                    {
                        'movement': 'absolute',
                        'to': [50, -40],
                        'time': 0
                    },
                ]
            }
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

device.add_circle(
    pos_x=0,
    pos_y=0,
    radius=5,
    color=Colors.BLACK,
    movements={
        'movements': [
            {
                'movement': 'absolute',
                'to': [-50, 50],
                'time': 5
            }
        ]
    }
)

device.sleep(3)

speed = 10

device.update_circle(
    id=id,
    movements={
        'repeat': 2,
        'movements': [
            {
                'movement': 'absolute',
                'to': [40, 0],
                'speed': speed
            },
            {
                'movement': 'absolute',
                'to': [40, 40],
                'speed': speed
            },
            {
                'movement': 'absolute',
                'to': [-40, -40],
                'speed': speed
            }, {
                'movement': 'absolute',
                'to': [0, 0],
                'speed': speed
            }
        ]
    }
)
device.sleep(1)

time = 1
device.update_circle(
    id=id,
    movements={
        'movements': [
            {
                'movement': 'absolute',
                'to': [40, 0],
                'time': time
            },
            {
                'movement': 'absolute',
                'to': [40, 40],
                'time': time
            },
            {
                'movement': 'absolute',
                'to': [-40, -40],
                'time': time
            }, {
                'movement': 'absolute',
                'to': [0, 0],
                'time': time
            }
        ]
    }
)
device.disconnect()
