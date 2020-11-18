import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import *
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar1')


def on_data(data: DataMsg):
    print(data)

    if data.type == 'message':
        print(data.message)
        response = device.input(f'{data.message}\nAntwort:')
        device.send_to(
            'FooBar2',
            {
                'type': 'message',
                'message': response
            }
        )


device.on_data = on_data
device.send_to(
    'FooBar1',
    {
        'type': 'message',
        'message': 'Hallo wie gehts?'
    }
)

device.on_border_overlap = lambda x: print(x)
device.on_sprite_out = lambda x: print(x)
device.on_sprite_removed = lambda x: print(x)

device.wait()
