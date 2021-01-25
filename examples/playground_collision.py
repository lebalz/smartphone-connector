import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from examples.server_address import SERVER_ADDRESS
from smartphone_connector import *
from math import sin, cos, pi

device = Connector(SERVER_ADDRESS, 'FooBar')

device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=0
)

device.add_rectangle(
    id='catcher',
    pos_x=0,
    pos_y=20,
    width=30,
    height=10,
    color='blue',
    anchor=[0.5, 0.5],
    collision_detection=True
)


def add_obj():
    device.add_circle(pos_x=0, pos_y=100, color='red', direction=[0, -1], speed=2, radius=5)


# device.set(add_obj, 3)
add_obj()


def on_collision(data: ObjectCollisionMsg):
    print(data.objects[0].id, data.objects[0].pos_y)
    print(data.objects[1].id, data.objects[1].pos_y)


device.on('collision', on_collision)
