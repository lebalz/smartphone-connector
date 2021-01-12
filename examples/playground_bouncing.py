import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from random import random, randint
from examples.server_address import SERVER_ADDRESS


device = Connector(SERVER_ADDRESS, "FooBar")

# aktuellen Playground (=Zeichenfläche) löschen
device.clear_playground()

# Playground konfigurieren
device.configure_playground(
    width=250,
    height=160,
    origin_x=125,   # der Ursprung soll in der Mitte liegen
    origin_y=80,
    images='images',
    image='explosion',
    color='white'  # weisser Hintergrund
)
x = 0


def on_collision(data: SpriteCollisionMsg):
    if data.overlap == 'out':
        return
    for s in data.sprites:
        if 'direction' in s:
            device.update_circle(id=s.id, direction=[-s.direction[0], -s.direction[1]])


def on_sprite_out(data: SpriteOutMsg):
    if data.device_nr != device.client_device.device_nr:
        return
    data.sprite.pos_x = 0
    data.sprite.pos_y = 0
    data.sprite.speed = 1
    device.add_sprite(**data.sprite)


def on_border_overlap(data: BorderOverlapMsg):
    if data.device_nr != device.client_device.device_nr:
        return

    if 'sprite' in data and 'direction' in data.sprite:
        if data.border in ['right', 'left']:
            device.update_circle(
                id=data.id,
                direction=[-data.sprite.direction[0], data.sprite.direction[1]],
                speed=data.sprite.speed + 1
            )
        elif data.border in ['top', 'bottom']:
            device.update_circle(
                id=data.id,
                direction=[data.sprite.direction[0], -data.sprite.direction[1]],
                speed=data.sprite.speed + 1
            )


device.on_sprite_collision = on_collision
device.on_border_overlap = on_border_overlap
device.on_sprite_removed = on_sprite_out
device.on_sprite_clicked = lambda d: device.update_sprite(id=d.id, pos_x=0, pos_y=0, speed=1)

with device.add_sprites() as add:
    for i in range(300):
        add(
            pos_x=0,
            pos_y=0,
            form='round',
            direction=[2 * (random() - 0.5), 2 * (random() - 0.5)],
            speed=randint(1, 10),
            color=random_color(),
            radius=2,
            collision_detection=False,
            clickable=True
        )
device.wait()
