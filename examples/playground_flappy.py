import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
score = 0
device.clear_playground()
device.add_text(
    id='score',
    text='Score: 0',
    pos_x=0,
    pos_y=22,
    z_index=999999
)
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

SPACE = 16


def add_obstacles():
    pos_y = randint(0, 50 - SPACE / 2)
    width = randint(2, 15)
    color = random_color()
    device.add_rectangle(
        pos_x=100,
        pos_y=-25,
        height=(pos_y - SPACE / 2),
        width=width,
        color=color,
        direction=[-1, 0],
        speed=1
    )
    device.add_rectangle(
        pos_x=100,
        pos_y=25,
        anchor=[0, 1],
        height=((50 - pos_y) - SPACE / 2),
        width=width,
        color=color,
        direction=[-1, 0],
        speed=1
    )
    set_score(score + 1)

    device.set_timeout(add_obstacles, time=randint(3, 5))


def on_key(data: KeyMsg):
    if data.key == 'up':
        # device.apply_movement(id='flappy', direction=[0, 1], time_span=0.1, speed=4)
        with device.apply_movements(id='flappy') as movement:
            movement(direction=[0, 1], time_span=0.1, speed=4)
            movement(direction=[0, -1], speed=2)


def set_score(new_score):
    global score
    score = new_score
    device.update_text(id='score', text=f'Score: {score}')


def on_collision(data: ObjectCollisionMsg):
    object = data.objects[1]
    if object.id == 'score':
        return
    device.remove_object(object.id)
    set_score(score - 2)


device.on('key', on_key)
device.on('collision', on_collision)
add_obstacles()
device.wait()
