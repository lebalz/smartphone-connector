import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from examples.server_adress import SERVER_ADRESS
from smartphone_connector import Connector

device = Connector(SERVER_ADRESS, 'FooBar')

device.clear_playground()
device.configure_playground(100, 100, -50, -50, color="#FF3366")
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
        add(-25, i * 2, -45, i * 2, line_width=1, color="lightblue")

device.sleep(1)
device.remove_line(id)
device.disconnect()
