import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_address import SERVER_ADDRESS

device = Connector(SERVER_ADDRESS, 'FooBar')

date = device.prompt('Wenn weimer abmachä?', input_type='datetime')

device.notify(f'Okey, dämfau am {date}', display_time=5, alert=True)
device.notify(f'Hallo', alert=True, broadcast=True)
device.disconnect()
