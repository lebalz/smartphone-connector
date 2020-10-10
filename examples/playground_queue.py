import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, AccMsg, KeyMsg, Colors
from random import randint
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
WIDTH = 400
HEIGHT = 300
SHIFT_X = 0
SHIFT_Y = 0

QUEUE_SIZE = 30
positions = [(0.0, 0.0)]
form = 'round'


def update_position(dx: float, dy: float):
    new_x = positions[-1][0] - dx * 2
    new_y = positions[-1][1] - dy * 2
    if new_x > WIDTH - 2:
        new_x = WIDTH - 2
    elif new_x < 0:
        new_x = 0
    if new_y > HEIGHT - 2:
        new_y = HEIGHT - 2
    elif new_y < 0:
        new_y = 0
    positions.append((new_x, new_y))
    if len(positions) > QUEUE_SIZE:
        positions.pop(0)


def update_players():
    player_idx = 1
    with device.update_sprites() as update:
        for pos in reversed(positions):
            update(
                id=f'sprite{player_idx}',
                pos_x=pos[0],
                pos_y=pos[1],
            )
            player_idx += 1


def on_acc(data: AccMsg):
    update_position(data.x, data.y)
    update_players()


def on_key(data: KeyMsg):
    global form
    if (data.key == 'home'):
        if form == 'round':
            form = 'rectangle'
        else:
            form = 'round'
        for sprite_nr in range(1, QUEUE_SIZE + 1):
            device.update_sprite(id=f'sprite{sprite_nr}', color=Colors.random(), form=form)


device.clear_playground()
device.configure_playground(
        width=WIDTH,
        height=HEIGHT,
        shift_x=SHIFT_X,
        shift_y=SHIFT_Y
)

with device.add_sprites() as add:
    for sprite_nr in range(1, QUEUE_SIZE + 1):
        add(
            id=f'sprite{sprite_nr}',
            color=Colors.random(),
            form=form,
            height=5 + QUEUE_SIZE - sprite_nr,
            width=5 + QUEUE_SIZE - sprite_nr,
            collision_detection=False,
            pos_x=WIDTH * sprite_nr / QUEUE_SIZE,
            pos_y=HEIGHT * sprite_nr / QUEUE_SIZE,
        )

device.on_acceleration = on_acc
device.on_key = on_key
device.wait()
