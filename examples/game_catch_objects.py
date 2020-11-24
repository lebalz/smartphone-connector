import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
score = 3
player_x = 0


def setup():
    global score, player_x
    score = 3
    player_x = 0
    device.clear_playground()
    device.configure_playground(width=100, height=180, color='black', origin_x=50, origin_y=180)
    device.add_rectangle(id='player', color='white', width=20, height=6, pos_x=player_x,
                         pos_y=-150, anchor=[0.5, 0], collision_detection=True)

    device.add_text(
        id='score',
        pos_x=-40,
        pos_y=-10,
        font_color='white',
        font_size=2,
        text='Score: 3'
    )


def on_key(data: KeyMsg):
    print(data)


def on_border_overlap(data: BorderOverlapMsg):
    global score
    if score <= 0:
        return
    if data.border == 'bottom':
        if data.id.startswith('star'):
            score = score - 1

        if score <= 0:
            answer = device.input('Lost!! Want to restart?')
            if answer:
                score = 3
                setup()
                device.sleep(1)
            else:
                device.disconnect()
        device.update_text(
            id='score',
            text=f'Score: {score}'
        )


def add_star():
    device.add_circle(
        id=f'star{randint(999, 99999)}',
        text=f'★',
        font_color=random_color(),
        font_size=10,
        direction=[0, -1],
        speed=4,
        pos_x=randint(-50, 50),
        pos_y=0,
        radius=3,
        border_color='blue'
    )


def add_bomb():
    device.add_circle(
        id=f'bomb{randint(999, 99999)}',
        text='☢',
        font_color=random_color(),
        font_size=10,
        radius=3,
        direction=[0, -1],
        speed=6,
        pos_x=randint(-50, 50),
        pos_y=0,
        border_color='blue'
    )


def on_catch(data: SpriteCollisionMsg):
    global score
    print(score)
    sprite = data.objects[1]
    if sprite.id.startswith('star'):
        score = score + 1
        device.remove_object(sprite.id)
    elif sprite.id.startswith('bomb'):
        score = score - 5
        device.update_object(id=sprite.id, text='☸', font_size=50)

    device.update_text(
        id='score',
        text=f'Score: {score}'
    )


def on_acc(data: DataFrame):
    global player_x
    player_x = player_x - data.acceleration.x
    if player_x > 50:
        player_x = 50
    elif player_x < -50:
        player_x = -50

    device.update_object(
        id='player',
        pos_x=player_x
    )


setup()

device.on('border_overlap', on_border_overlap)
device.on('collision', on_catch)
device.on('key', on_key)

device.subscribe_async(add_star, 1)
device.subscribe_async(add_bomb, 5)
device.subscribe_async(on_acc, 0.05)


device.wait()
