import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from examples.server_adress import SERVER_ADRESS
from smartphone_connector import Connector

device = Connector(SERVER_ADRESS, 'FooBar')

device.clear_playground()
device.configure_playground(100, 100, -50, -50, color="#FF3366")
device.add_circle(0, 0, 5, color='red')
device.add_square(0, 0, 10, color='yellow', text='hi')
device.add_square(15, 0, 10, color='red', anchor=[0.5, 0.5])
device.add_text('1', -20, 10)
device.add_text('1', -20, 10, background_color='unset')
device.add_text('Hello', -20, 0, border_color='red')
device.add_text('Hello', -20, 0, border_color='red', rotate=90, anchor=[0, 1])
device.add_text('Hello My Friend', -20, -10, clickable=True)
device.add_text('Hello There', -40, -40, font_color='white', font_size=10)
device.add_text('Hello There', -40, -40, font_color='white', font_size=10, rotate=-90)

device.disconnect()
