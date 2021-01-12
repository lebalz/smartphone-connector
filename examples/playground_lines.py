import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from examples.server_address import SERVER_ADDRESS
from smartphone_connector import Connector
from math import sin, cos, pi

device = Connector(SERVER_ADDRESS, 'FooBar')

device.clear_playground()
device.configure_playground(
    width=100,
    height=100,
    origin_x=50,
    origin_y=50,
    color="#FF3366"
)
device.add_line(0, 0, 20, 20, line_width=2)
device.add_line(0, 0, 0, 20, line_width=2)
device.add_line(-20, 0, 0, 0, color="white")
device.add_line(0, 20, -20, 20, color="white")
device.add_line(0, 0, 10, 10, color="white")
id = device.add_line(0, 0, 10, 0, color="yellow")
device.sleep(1)
device.update_line(id, x2=0, y2=-10)
with device.add_lines() as add:
    for i in range(30):
        add(x1=-25, y1=i * 2, x2=-45, y2=i * 2, line_width=1, color="lightblue")


device.add_line(0, 0, 10, 0, line_width=2, color='hsla(0, 100%, 50%, 0.5)')
device.add_line(0, 0, 10, 10, line_width=2, color='hsla(120, 100%, 50%, 0.5)')
device.add_line(0, 0, 0, 10, line_width=2, color='hsla(240, 100%, 50%, 0.5)')

device.add_line(0, 0, -10, -10, line_width=2, color='hsla(90, 100%, 50%, 0.5)')
device.add_line(0, 0, -10, 0, line_width=2, color='hsla(180, 100%, 50%, 0.5)')


# device.add_line(-1, -1, -10, -10, line_width=2)
# device.add_line(-1, 0, -10, 0, line_width=2)

RADIUS = 20
DT = 6
S = 84
with device.add_lines() as add:
    for i in range(0, 360, DT):
        add(
            x1=RADIUS * cos(i * pi / 180),
            y1=RADIUS * sin(i * pi / 180),
            x2=RADIUS * cos((i + DT) * pi / 180),
            y2=RADIUS * sin((i + DT) * pi / 180),
        )

device.sleep(1)
device.remove_line(id)
device.disconnect()
