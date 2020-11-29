import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, SpriteClickedMsg, Colors
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
device.clear_playground()
device.configure_playground(
    width=100,
    height=50,
    origin_x=50,
    origin_y=25
)
device.add_line(-50, -25, 50, 25, color="purple", line_width=0.2)
lw = 0.1
for x in range(-50, 100, 25):
    device.add_circle(pos_x=x, pos_y=x / 2, radius=2, color='red',
                      border_width=lw, border_color='black', border_style='dashed')
    device.add_line(x1=-50, y1=x / 2, x2=50, y2=x / 2)
    device.add_line(x, -25, x, 25)
    lw = lw + 0.3
device.disconnect()
