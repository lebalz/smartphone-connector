import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, Colors
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')
score = 0
device.clear_playground()
device.configure_playground(
    width=100,
    height=60,
    images='images',
    color=Colors.ALICEBLUE,
    image='waterfall'
)
device.add_sprite(
    id='cookie',
    width=20,
    height=20,
    pos_x=10,
    pos_y=10,
    image='cookie'
)
for rotation in range(360):
    device.update_sprite(id='cookie', rotate=rotation)
    device.sleep(0.1)
device.disconnect()
