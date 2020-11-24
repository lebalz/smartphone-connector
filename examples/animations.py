import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=50,
    color=random_color(),
)

device.add_square(
    id='earth',
    pos_x=0,
    pos_y=0,
    size=20,
    color=random_color(),
    anchor=[0.5, 0.5]
)

device.add_circle(
    id='moon',
    pos_x=0,
    pos_y=0,
    size=4,
    color=random_color(),
    anchor=[-5, 0.5]
)

moon_rot = 0


def moon(data: DataFrame):
    global moon_rot
    if data.job is None:
        return
    device.update_circle(
        id='moon',
        rotate=moon_rot
    )
    moon_rot += 6
    if data.job.time_s > 10:
        data.job.stop()


earth_rot = 0


def earth(data: DataFrame):
    global earth_rot
    if data.job is None:
        return
    device.update_square(
        id='earth',
        rotate=earth_rot
    )
    earth_rot -= 12
    if data.job.time_s > 8:
        data.job.stop()


device.animate(moon)
device.animate(earth)
device.sleep(12)
print('done')
device.disconnect()
