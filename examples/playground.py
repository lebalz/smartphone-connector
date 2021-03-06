import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, DictX, KeyMsg, Colors
from examples.server_address import SERVER_ADDRESS

DT = 2

device = Connector(SERVER_ADDRESS, 'FooBar')
player = DictX({
  'color': 'yellow',
  'form': 'round',
  'height': 10,
  'width': 10,
  'id': 'player1',
  'collision_detection': True,
  'pos_x': 0,
  'pos_y': 0,
  'clickable': True
})


def on_key(data: KeyMsg):
    if data.key == 'right':
        player.pos_x += DT
        device.update_sprite(id='player1', pos_x=player.pos_x)
    if data.key == 'left':
        player.pos_x -= DT
        device.update_sprite(id='player1', pos_x=player.pos_x)
    if data.key == 'up':
        player.pos_y += DT
        device.update_sprite(id='player1', pos_y=player.pos_y)
    if data.key == 'down':
        player.pos_y -= DT
        device.update_sprite(id='player1', pos_y=player.pos_y)
    if data.key == 'home':
        if player.form == 'round':
            player.form = 'rectangle'
        else:
            player.form = 'round'
        device.update_sprite(id='player1', form=player.form)


device.on_key = on_key
device.on_sprite_collision = lambda data: print(data)
device.configure_playground(
    width=100,
    height=100,
    shift_x=0,
    shift_y=0,
    color=Colors.ALICEBLUE
)
with device.add_sprites() as add:

    add(**player)
    add(
        color='red',
        direction=[1, 1],
        form='round',
        height=5,
        width=5,
        id='asdfa1',
        pos_x=0,
        pos_y=0,
        speed=2,
        reset_time=True
    )
    add(
        color='blue',
        direction=[1, 1],
        form='round',
        height=5,
        width=5,
        id='asdfa2',
        pos_x=0,
        pos_y=0,
        speed=1,
        reset_time=True
    )
    add(
        color='green',
        direction=[1, 1],
        form='round',
        height=5,
        width=5,
        id='asdfa3',
        pos_x=1,
        pos_y=1,
        speed=0.1,
        reset_time=True
    )
