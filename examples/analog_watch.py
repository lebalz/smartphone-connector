import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, SpriteClickedMsg, Colors, time_s
from examples.server_adress import SERVER_ADRESS
from math import cos, sin, pi, radians

device = Connector(SERVER_ADRESS, 'FooBar')

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
        line_width=0.1
    )

for deg in range(0, 360, 30):
    device.add_line(
        x1=sin(radians(deg)) * (RADIUS - 5),
        y1=cos(radians(deg)) * (RADIUS - 5),
        y2=cos(radians(deg)) * RADIUS,
        x2=sin(radians(deg)) * RADIUS,
        line_width=0.3
    )

device.add_line(
    id='hour',
    x1=0,
    y1=0,
    x2=0,
    y2=RADIUS - 3,
    color='black',
    line_width=1
)
device.add_line(
    id='minute',
    x1=0,
    y1=0,
    x2=0,
    y2=RADIUS,
    color='black',
    line_width=0.4
)
device.add_line(
    id='seconds',
    x1=0,
    y1=0,
    x2=0,
    y2=RADIUS,
    color='red',
    line_width=0.3
)
device.add_circle(
    id='circle',
    radius=2,
    pos_x=0,
    pos_y=RADIUS - 2,
    color='red',
)


hours = int(device.input("Uhrzeit: Stunden", input_type="number"))

device.update_line(
    id='hour',
    x2=sin(radians(30 * hours)) * (RADIUS - 6),
    y2=cos(radians(30 * hours)) * (RADIUS - 6)
)
minutes = int(device.input("Uhrzeit: Stunden", input_type="number"))
device.update_line(
    id='minute',
    x2=sin(radians(6 * minutes)) * RADIUS,
    y2=cos(radians(6 * minutes)) * RADIUS
)
seconds = int(device.input("Uhrzeit: Stunden", input_type="number"))
device.update_line(
    id='seconds',
    x2=sin(radians(6 * seconds)) * RADIUS,
    y2=cos(radians(6 * seconds)) * RADIUS
)
device.update_circle(
    id='circle',
    pos_x=sin(radians(6 * seconds)) * (RADIUS - 2),
    pos_y=cos(radians(6 * seconds)) * (RADIUS - 2)
)
device.disconnect()
