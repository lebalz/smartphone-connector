import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, Colors
from typing import Union, Literal
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
device.clear_playground()
device.configure_playground(
    width=180,
    height=180,
    origin_x=10,
    origin_y=10,
    color=Colors.BISQUE,
)


def color(i: int, j: int) -> Union[Literal['white'], Literal['black']]:
    if i % 2 == 0:
        if j % 2 == 0:
            return 'black'
        else:
            return 'white'
    else:
        if j % 2 == 0:
            return 'white'
        else:
            return 'black'


device.add_text(
    id='x',
    pos_x=20,
    pos_y=-5,
    text=f'x = {0}'
)
device.add_text(
    id='y',
    pos_x=-5,
    pos_y=20,
    text=f'y = {0}',
    rotate=-90
)

for y in range(8):
    device.update_text(
        id='y',
        text=f'y = {y}',
        pos_y=y * 20 + 5
    )
    for x in range(8):
        device.update_text(
            id='x',
            text=f'x = {x}',
            pos_x=x * 20 + 5
        )
        device.add_square(
            pos_x=x * 20,
            pos_y=y * 20,
            size=20,
            color=color(x, y),
            clickable=True
        )
        device.sleep(0.6)

device.disconnect()
