import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_adress import SERVER_ADRESS

device_b = Connector(SERVER_ADRESS, 'FooBar2')


def on_data(data: DataMsg):
    print(data)
    if data.type == 'message':
        print(data.message)
        response = device_b.input(f'{data.message}\nAntwort:')
        device_b.send_to(
            'FooBar1',
            {
                'type': 'message',
                'message': response,
            }
        )


device_b.on_data = on_data
device_b.wait()
