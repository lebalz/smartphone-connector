import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector


device = Connector('https://io.lebalz.ch', 'FooBar')
d = device.latest_acceleration()
drink = device.select('Was wosch trinkä?', ['Pingusirup', 'Wasser', 'Orangensaft'])

food = device.select('Was wosch ässä?', ['Fischstäbli', 'Cordonblö', 'Zürigschnätzlets'])
device.print(f'Bestellung: {food} mit {drink}')
device.disconnect()
