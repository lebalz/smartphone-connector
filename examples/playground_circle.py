import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, Colors
from examples.server_adress import SERVER_ADRESS
from math import sin, cos

DT = 2

device = Connector(SERVER_ADRESS, 'FooBar')
device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    shift_x=-50,
    shift_y=-50,
    color='lightblue'
)

device.add_sprite(
    id='circler',
    height=10,
    width=10,
    form='round',
    speed=1,
    color='yellow'
)

angle = 0
while True:
    device.update_sprite(
        id='circler',
        direction=[cos(angle), sin(angle)],
        color=Colors.next()
    )
    angle += 0.4
    device.sleep(0.05)
