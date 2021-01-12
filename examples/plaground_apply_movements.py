import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')
score = 0
device.clear_playground()
device.configure_playground(
    width=100,
    height=50,
    origin_x=20,
    origin_y=25,
    color=Colors.ALICEBLUE,
)
device.add_circle(
    id='flappy',
    radius=2,
    pos_x=0,
    pos_y=0,
    color=Colors.REBECCAPURPLE,
    z_index=99999999,
    collision_detection=True
)
with device.apply_movements(id='flappy') as movement:
    movement(direction=[1, 1], time_span=1, speed=0.2)
    movement(direction=[0, 1], distance=20, speed=5)
    movement(movement='absolute', pos=[50, 0], time=2)
    movement(movement='absolute', pos=[0, 0], speed=1)
    movement(direction=[-1, -1], time_span=1, speed=2)

device.disconnect()
