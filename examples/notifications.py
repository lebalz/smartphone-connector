from smartphone_connector import Connector
from examples.server_adress import SERVER_ADRESS

device = Connector(SERVER_ADRESS, 'FooBar')

date = device.prompt('Wenn weimer abmachä?', input_type='datetime')

device.notify(f'Okey, dämfau am {date}', display_time=5, alert=True)
device.sleep(1)
device.disconnect()
