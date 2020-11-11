import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from examples.server_adress import SERVER_ADRESS
from smartphone_connector import Connector

device = Connector(SERVER_ADRESS, 'FooBar')

device.clear_playground()
device.configure_playground(100, 100, 50, 50, color="white")
device.add_circle(pos_x=0, pos_y=0, radius=5, color='red')
device.add_square(pos_x=0, pos_y=0, size=10, color='yellow', text='hi', clickable=True)
device.add_rectangle(pos_x=-20, pos_y=-40, width=10, height=5, color='orange', text='hi', clickable=True, z_index=999)
device.add_square(pos_x=15, pos_y=0, size=10, color='red', anchor=[0.5, 0.5])
device.add_text(text='1', pos_x=-20, pos_y=10)
device.add_text(text='1', pos_x=-20, pos_y=10, background_color='unset')
device.add_text(text='Hello', pos_x=-20, pos_y=0, border_color='red')
device.add_text(text='Hello', pos_x=-20, pos_y=0, border_color='red', rotate=90, anchor=[0, 1])
device.add_text(text='Hello My Friend', pos_x=-20, pos_y=-10, clickable=True)
device.add_text(text='Hello There', pos_x=-40, pos_y=-40, font_color='white', font_size=10)
device.add_text(text='Hello There', pos_x=-40, pos_y=-40, font_color='white', font_size=10, rotate=-90)
device.add_circle(pos_x=0, pos_y=0, radius=5, color='red', clickable=True)

device.on_sprite_clicked = lambda x: print(x)
device.sleep(10)
device.disconnect()
