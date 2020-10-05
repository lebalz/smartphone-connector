import os
import sys
from pprint import pprint
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')

device.set_grid(
    """
    99999999999999
    99999....99999
    99999....99999
    99999....99999
    99999....99999
    9............9
    9............9
    9............9
    9............9
    99999....99999
    99999....99999
    99999....99999
    99999....99999
    99999999999999
    """,
    base_color='red'
)
device.sleep(1)
pprint(device.get_grid)
device.set_grid_at(0, 0, 'red')
pprint(device.get_grid)
device.set_grid_at(0, 14, 'red')
pprint(device.get_grid)

device.set_grid(
    [
        '99999999999999',
        '99999    99999',
        '99999    99999',
        '99999    99999',
        '99999    99999',
        '9            9',
        '9            9',
        '9            9',
        '9            9',
        '99999    99999',
        '99999    99999',
        '99999    99999',
        '99999    99999',
        '99999999999999'
    ],
    base_color='blue'
)
pprint(device.get_grid)

device.sleep(1)
device.set_grid(
    [
        ['red', 'green', 'blue'],
        ['#ff00ff', '#ff3300', '#00ff22'],
        ['rgb(122,255,233)', 'rgb(122,255,33)', 'rgb(122,55,233)'],
        ['rgba(122,255,233,0.3)', 'rgba(122,255,233, 0.6)', 'rgba(122,255,233, 1)']
    ]
)
pprint(device.get_grid)


device.set_grid_at(1, 2, (255, 2, 2))
device.sleep(1)

device.disconnect()
