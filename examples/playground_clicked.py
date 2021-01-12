import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_address import SERVER_ADDRESS
import random
DT = 2

device = Connector(SERVER_ADDRESS, 'FooBar')

device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=50
)
device.add_circle(
    id='ball',
    color='red',
    pos_x=0,
    pos_y=0,
    radius=10,
    clickable=True
)


def say_hi():
    print('Hiii', time_s())


def say_hi2(data):
    print('Hiii2', time_s())


def update_pos():
    print('pos', time_s())
    device.remove('object_clicked')
    device.update_circle(
        id='ball',
        pos_x=random.randint(-50, 50)
    )


def update_color():
    print('color', time_s())
    device.update_circle(
        id='ball',
        color=random_color()
    )


device.on('object_clicked', say_hi)
device.on('object_clicked', say_hi2)
device.on('object_clicked', update_pos)
device.on('object_clicked', update_color)
device.on_sprite_clicked = update_color
device.subscribe_async(update_color, 1.5)
