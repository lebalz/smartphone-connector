import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')
d = device.latest_acceleration()
drink = device.select('Was wosch trinkä?', ['Pingusirup', 'Wasser', 'Orangensaft'])

food = device.select('Was wosch ässä?', ['Fischstäbli', 'Cordonblö', 'Zürigschnätzlets'])
device.print(f'Bestellung: {food} mit {drink}', display_time=3)
device.sleep(0.3)
device.disconnect()
