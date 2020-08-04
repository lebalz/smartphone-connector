import socketio
import logging
import time
from typing import overload, Union, TypedDict, Literal, Callable, List, Dict


DEVICE = 'device'
DEVICES = 'devices'
ALL_DATA = 'all_data'
ADD_NEW_DATA = 'new_data'
NEW_DATA = 'new_data'
CLEAR_DATA = 'clear_data'
NEW_DEVICE = 'new_device'
GET_ALL_DATA = 'get_all_data'
GET_DEVICES = 'get_devices'

EVENTS = Literal[
    DEVICE,
    DEVICES,
    ALL_DATA,
    ADD_NEW_DATA,
    NEW_DATA,
    CLEAR_DATA,
    NEW_DEVICE,
    GET_ALL_DATA,
    GET_DEVICES
]


class Device(TypedDict):
    deviceId: str
    isController: bool
    deviceNr: int
    socketId: str


class BaseMsg(TypedDict):
    deviceId: str
    timeStamp: int


class KeyMsg(BaseMsg):
    type: Literal['key']
    key: Literal['up', 'right', 'down', 'left']


class DictX(dict):
    '''
    dict with the ability to access keys over dot notation,
    e.g.

    ```py
    data = DictX({
        "foo": "bar"
    })

    print(data.foo)     # use dot to get
    data.foo = 'blaa'   # use dot to assign
    del data.foo        # use dot to delete
    ```
    credits: https://dev.to/0xbf/use-dot-syntax-to-access-dictionary-key-python-tips-10ec
    '''

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return '<DictX ' + dict.__repr__(self) + '>'


class Connector:
    start_time_ns = time.time_ns()
    data: Dict[str, List[BaseMsg]] = {}
    devices: List[Device] = []
    device: Device = {}
    server_url: str
    device_id: str
    sio = socketio.Client()
    onKey: Callable[[KeyMsg], None] = None

    def __init__(self, server_url: str, device_id: str):
        self.server_url = server_url
        self.device_id = device_id
        self.sio.on('connect', self.__on_connect)
        self.sio.on('disconnect', self.__on_disconnect)
        self.sio.on(NEW_DATA, self.__on_new_data)
        self.sio.on(ALL_DATA, self.__on_all_data)
        self.sio.on(DEVICE, self.__on_device)
        self.sio.on(DEVICES, self.__on_devices)

        self.connect()

    def emit(self, event: str, data: BaseMsg = {}, broadcast: bool = False):
        if 'timeStamp' not in data:
            data['timeStamp'] = (time.time_ns() - self.start_time_ns) // 1000000

        if 'deviceId' not in data:
            data['deviceId'] = self.device_id

        if broadcast:
            data['broadcast'] = True

        self.sio.emit(event, data)

    def connect(self):
        if self.sio.connected:
            return
        self.sio.connect(self.server_url)
        self.__register()

    def clear_data(self):
        '''
        clears all data of this device
        '''
        self.emit(CLEAR_DATA)

    def set_grid(self, grid: List[List[str]], device_id: str = None, device_nr: int = None, broadcast: bool = False):
        '''
        Parameters
        ----------
        grid : List<List<str>> a 2d array containing the color of each cell

        Optional
        --------
        device_id : str control the device with this id

        device_nr : str control the device with the given number

        broadcast : bool wheter to send this message to all connected devices

        Example
        -------
        draw a 2x2 checker board
        ```py
        set_grid([
            ['white', 'black'],
            ['black', 'white']
        ])
        ```
        '''
        did = self.device_id if (device_id is None) else device_id
        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'grid',
                'grid': grid,
                'deviceId': did,
                'deviceNr': device_nr
            },
            broadcast
        )

    def set_color(self, color: str, device_id: str = None, device_nr: int = None, broadcast: bool = False):
        '''
        Parameters
        ----------
        color : str
            the color of the panel background, can be any valid css color

        Optional
        --------
        device_id : str
            control the device with this id

        device_nr : str
            control the device with the given number

        broadcast : bool wheter to send this message to all connected devices

        Example
        -------
        set the panels background to red
        ```py
        set_panel('red')
        set_panel('#ff0000')                  # => hex color
        set_panel('rgb(255, 0,0)')            # => rgb
        set_panel('hsl(0, 100%, 50%)')        # => hsl
        ```
        '''
        did = self.device_id if device_id is None else device_id
        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'color',
                'color': color,
                'deviceId': did,
                'deviceNr': device_nr
            },
            broadcast
        )

    def disconnect(self):
        if not self.sio.connected:
            return
        self.sio.disconnect()

    def __on_connect(self):
        logging.info('SocketIO connected')

    def __on_disconnect(self):
        logging.info('SocketIO disconnected')

    def __register(self):
        self.emit(NEW_DEVICE)

    def __on_new_data(self, data: BaseMsg):
        data = DictX(data)
        if data.deviceId not in self.data:
            self.data[data.deviceId] = []

        self.data[data.deviceId].append(data)

        if data['type'] == 'key':
            if self.onKey is not None:
                self.onKey(data)

    def __on_all_data(self, data: List[BaseMsg]):
        all_data = map(lambda data : DictX(data), data)
        self.data[data.deviceId] = all_data

    def __on_device(self, device: Device):
        device = DictX(device)
        if (self.sio.sid == device.deviceId):
            self.device = device

    def __on_devices(self, devices: List[Device]):
        devices = map(lambda device : DictX(device), devices)
        self.devices = devices

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    connector = Connector('https://io.lebalz.ch', 'FooBar')

    # draw a 3x3 checker board
    connector.set_grid(
        [
            ['black', 'white', 'black'],
            ['white', 'black', 'white'],
            ['black', 'white', 'black']
        ],
        broadcast=True
    )

    connector.onKey = lambda data: print(data)
    connector.sio.wait()
    connector.disconnect()
