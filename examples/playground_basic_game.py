import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, DictX, KeyMsg, AccMsg, random_color, BorderOverlapMsg, SpriteCollisionMsg, Colors
from random import randint
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')
WIDTH = 100
HEIGHT = 100
SHIFT_X = 0
SHIFT_Y = 0

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
        with device.update_sprites() as update:
            update(id='player1', form=form)
            update(id='player2', form=form)
            update(id='player3', form=form)
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
    with device.update_sprites() as update:
        update(id='player1', pos_x=positions[-1][0], pos_y=positions[-1][1])
        if len(positions) >= 20:
            update(
                id='player2',
                pos_x=positions[-20][0],
                pos_y=positions[-20][1],
            )
        if len(positions) >= 40:
            update(
                id='player3',
                pos_x=positions[-40][0],
                pos_y=positions[-40][1],
            )


def on_acc(data: AccMsg):
    global positions
    update_position(data.x, data.y)
    update_players()


def on_overlap(data: BorderOverlapMsg):
    if data.collision_detection and data.border == 'bottom':
        device.update_sprite(id=data.id, color='red')


def on_collision(data: SpriteCollisionMsg):
    if data.overlap == 'in' and data.sprites[0].collision_detection and data.sprites[1].collision_detection:
        device.update_sprite(id=data.sprites[0].id, color='pink')
        return
    for s in data.sprites:
        if not s.collision_detection:
            device.update_sprite(id=s.id, color='grey', text='x')


device.on_key = on_key
device.on_sprite_collision = on_collision
device.on_border_overlap = on_overlap
device.on_acceleration = on_acc


device.clear_playground()
device.configure_playground(
        width=WIDTH,
        height=HEIGHT,
        shift_x=SHIFT_X,
        shift_y=SHIFT_Y,
        color='red'
)

with device.add_sprites() as add:
    add(
        id='player1',
        color='yellow',
        form='round',
        height=10,
        width=10,
        collision_detection=True,
        pos_x=0 + SHIFT_X,
        pos_y=0 + SHIFT_Y
    )
    add(
        id='player2',
        color='yellow',
        form='round',
        height=7,
        width=7,
        collision_detection=True,
        pos_x=50 + SHIFT_X,
        pos_y=50 + SHIFT_Y
    )
    add(
        id='player3',
        color='yellow',
        form='round',
        height=4,
        width=4,
        collision_detection=True,
        pos_x=70 + SHIFT_X,
        pos_y=70 + SHIFT_Y
    )


sprite_count = 0
while True:
    sprite_count += 1
    device.sleep(0.5)
    w = randint(2, 10)
    device.add_sprite(
        color=random_color(),
        direction=[0, -1],
        form='round',
        height=randint(2, 10),
        width=w,
        id=f'asdfa{sprite_count}',
        pos_x=randint(0, WIDTH - w) + SHIFT_X,
        pos_y=HEIGHT + SHIFT_Y,
        speed=randint(1, 60) / 10
    )
