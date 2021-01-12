import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, SpriteClickedMsg, Colors
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')
score = 0
device.clear_playground()
device.configure_playground(
    width=100,
    height=180,
    color=Colors.ALICEBLUE,
    images='images'
)
device.add_sprite(
    id='score',
    pos_x=0,
    pos_y=160,
    height=20,
    width=30,
    text=f'Score: {score}',
    form='rectangle',
    color=Colors.LIGHTBLUE
)
device.add_sprite(
    id='cookie',
    pos_x=30,
    pos_y=40,
    height=30,
    width=30,
    form='rectanle',
    color=Colors.BROWN,
    clickable=True,
    image='firefox'
)


def on_sprite_clicked():
    global score
    score = score + 1
    with device.update_sprites() as update:
        update(
            id='score',
            text=f'Score: {score}'
        )
        update(
            id='cookie',
            rotate=score * 5,
            image='firefox'
        )
        if score % 10 == 0:
            update(
                id='cookie',
                image='explosion'
            )


device.on_sprite_clicked = on_sprite_clicked

device.wait()
