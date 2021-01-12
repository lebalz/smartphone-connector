import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, SpriteClickedMsg, Colors, time_s
from examples.server_address import SERVER_ADDRESS
from math import cos, sin, pi, radians

device = Connector(SERVER_ADDRESS, 'FooBar')

RADIUS = 40
device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    shift_x=-50,
    shift_y=-50,
    color=Colors.WHITE
)
device.add_circle(radius=RADIUS, pos_x=0, pos_y=0, border_color="black")
for deg in range(0, 360, 6):
    device.add_line(
        x1=sin(radians(deg)) * (RADIUS - 3),
        y1=cos(radians(deg)) * (RADIUS - 3),
        y2=cos(radians(deg)) * RADIUS,
        x2=sin(radians(deg)) * RADIUS,
        line_width=0.3
    )

for deg in range(0, 360, 30):
    device.add_line(
        x1=sin(radians(deg)) * (RADIUS - 5),
        y1=cos(radians(deg)) * (RADIUS - 5),
        y2=cos(radians(deg)) * RADIUS,
        x2=sin(radians(deg)) * RADIUS,
        line_width=1
    )

device.add_line(
    id='hour',
    x1=0,
    y1=0,
    x2=0,
    y2=RADIUS - 10,
    color='black',
    line_width=2
)
device.add_line(
    id='minute',
    x1=0,
    y1=0,
    x2=0,
    y2=RADIUS - 7,
    color='black',
    line_width=1
)
device.add_line(
    id='seconds',
    x1=0,
    y1=0,
    x2=0,
    y2=RADIUS - 5,
    color='red',
    line_width=0.5
)
device.add_circle(
    id='circle',
    radius=2,
    pos_x=0,
    pos_y=RADIUS - 7,
    color='red',
)


hours = int(device.input("Uhrzeit: Stunden", input_type="number"))

device.update_line(
    id='hour',
    x2=sin(radians(30 * hours)) * (RADIUS - 10),
    y2=cos(radians(30 * hours)) * (RADIUS - 10)
)
minutes = int(device.input("Uhrzeit: Stunden", input_type="number"))
device.update_line(
    id='minute',
    x2=sin(radians(6 * minutes)) * (RADIUS - 7),
    y2=cos(radians(6 * minutes)) * (RADIUS - 7)
)
seconds = int(device.input("Uhrzeit: Stunden", input_type="number"))
seconds = 17
device.update_line(
    id='seconds',
    x2=sin(radians(6 * seconds)) * (RADIUS - 5),
    y2=cos(radians(6 * seconds)) * (RADIUS - 5)
)
device.update_circle(
    id='circle',
    pos_x=sin(radians(6 * seconds)) * (RADIUS - 7),
    pos_y=cos(radians(6 * seconds)) * (RADIUS - 7)
)
device.disconnect()
