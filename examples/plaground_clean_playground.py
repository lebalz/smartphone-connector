import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
score = 0
device.clear_playground()

device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=50,
    images='images',
    image='waterfall'
)
device.sleep(1)

device.add_circle(
    image='firefox',
    size=10
)

device.sleep(2)

device.clean_playground()
device.configure_playground(
    width=200,
    image='explosion'
)

device.disconnect()
