from smartphone_connector import Connector

device = Connector('https://io.lebalz.ch', 'FooBar')

date = device.prompt('Wenn weimer abmachä?', input_type='datetime')
device.notify(f'Okey, dämfau am {date}', display_time=5)
device.sleep(1)
device.disconnect()
