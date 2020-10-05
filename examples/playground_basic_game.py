import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, DictX, KeyMsg, AccMsg, random_color, BorderOverlapMsg, SpriteCollisionMsg
from random import randint
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
WIDTH = 100
HEIGHT = 100
SHIFT_X = -50
SHIFT_Y = -50

positions = [(0.0 + SHIFT_X, 0.0 + SHIFT_Y)]
form = 'round'


def on_key(data: KeyMsg):
    global form
    x = positions[-1][0]
    y = positions[-1][1]
    if data.key == 'right':
        positions.append((x + 5, y))
    if data.key == 'left':
        positions.append((x - 5, y))
    if data.key == 'up':
        positions.append((x, y + 5))
    if data.key == 'down':
        positions.append((x, y - 5))
    if data.key == 'home':
        if form == 'round':
            form = 'rectangle'
        else:
            form = 'round'
        device.update_sprite('player1', {'form': form})
        device.update_sprite('player2', {'form': form})
        device.update_sprite('player3', {'form': form})
        return
    update_players()


def update_position(dx: float, dy: float):
    new_x = positions[-1][0] - dx / 2
    new_y = positions[-1][1] - dy / 2
    if new_x > WIDTH - 2 + SHIFT_X:
        new_x = WIDTH - 2 + SHIFT_X
    elif new_x < SHIFT_X:
        new_x = SHIFT_X
    if new_y > HEIGHT - 2 + SHIFT_Y:
        new_y = HEIGHT - 2 + SHIFT_Y
    elif new_y < SHIFT_Y:
        new_y = SHIFT_Y
    positions.append((new_x, new_y))


def update_players():
    updates = [{
        'id': 'player1',
        'movement': 'controlled',
        'pos_x': positions[-1][0],
        'pos_y': positions[-1][1],
    }]
    if len(positions) >= 20:
        updates.append({
            'id': 'player2',
            'movement': 'controlled',
            'pos_x': positions[-20][0],
            'pos_y': positions[-20][1],
        })
    if len(positions) >= 40:
        updates.append({
            'id': 'player3',
            'movement': 'controlled',
            'pos_x': positions[-40][0],
            'pos_y': positions[-40][1],
        })

    device.add_sprites(updates)


def on_acc(data: AccMsg):
    global positions
    update_position(data.x, data.y)
    update_players()


def on_overlap(data: BorderOverlapMsg):
    if data.movement == 'uncontrolled' and data.border == 'bottom':
        device.update_sprite(data.id, {'color': 'red'})


def on_collision(data: SpriteCollisionMsg):
    if data.overlap == 'in' and data.sprites[0].movement == 'controlled' and data.sprites[1].movement == 'controlled':
        device.remove_sprite(data.sprites[1].id)
        return
    for s in data.sprites:
        if s.movement == 'uncontrolled':
            device.update_sprite(s.id, {'color': 'grey', 'text': 'x'})


device.on_key = on_key
device.on_sprite_collision = on_collision
device.on_border_overlap = on_overlap
device.on_acceleration = on_acc


device.clear_playground()
device.configure_playground({
        'width': WIDTH,
        'height': HEIGHT,
        'shift_x': SHIFT_X,
        'shift_y': SHIFT_Y
    })

device.add_sprites([
    {
        'color': 'yellow',
        'form': 'round',
        'height': 10,
        'width': 10,
        'id': 'player1',
        'movement': 'controlled',
        'pos_x': 0 + SHIFT_X,
        'pos_y': 0 + SHIFT_Y
    },
    {
        'color': 'yellow',
        'form': 'round',
        'height': 7,
        'width': 7,
        'id': 'player2',
        'movement': 'controlled',
        'pos_x': 50 + SHIFT_X,
        'pos_y': 50 + SHIFT_Y
    },
    {
        'color': 'yellow',
        'form': 'round',
        'height': 4,
        'width': 4,
        'id': 'player3',
        'movement': 'controlled',
        'pos_x': 70 + SHIFT_X,
        'pos_y': 70 + SHIFT_Y
    }
])

sprite_count = 0
while True:
    sprite_count += 1
    device.sleep(0.5)
    w = randint(2, 10)
    device.add_sprite({
        'color': random_color(),
        'direction': [0, -1],
        'form': 'round',
        'height': randint(2, 10),
        'width': w,
        'id': f'asdfa{sprite_count}',
        'movement': 'uncontrolled',
        'pos_x': randint(0, WIDTH - w) + SHIFT_X,
        'pos_y': HEIGHT + SHIFT_Y,
        'speed': randint(1, 60) / 10
    })
