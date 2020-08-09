from __future__ import annotations
import socketio
import logging
import time
import datetime
import math
import random
from inspect import signature
from typing import overload, Union, TypedDict, Literal, Callable, List, Dict, Optional


DEVICE = 'device'
DEVICES = 'devices'
ALL_DATA = 'all_data'
ADD_NEW_DATA = 'new_data'
NEW_DATA = 'new_data'
CLEAR_DATA = 'clear_data'
NEW_DEVICE = 'new_device'
GET_ALL_DATA = 'get_all_data'
GET_DEVICES = 'get_devices'
JOIN_ROOM = 'join_room'
LEAVE_ROOM = 'leave_room'
ROOM_LEFT = 'room_left'
ROOM_JOINED = 'room_joined'
ERROR_MSG = 'error_msg'

EVENTS = Literal[
    DEVICE,
    DEVICES,
    ALL_DATA,
    ADD_NEW_DATA,
    NEW_DATA,
    CLEAR_DATA,
    NEW_DEVICE,
    GET_ALL_DATA,
    GET_DEVICES,
    JOIN_ROOM,
    LEAVE_ROOM,
    ROOM_LEFT,
    ROOM_JOINED,
    ERROR_MSG
]


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


class Device(TypedDict):
    device_id: str
    is_controller: bool
    device_nr: int
    socket_id: str


class DeviceJoinedMsg(TypedDict):
    room: str
    device: Device


class DeviceLeftMsg(TypedDict):
    room: str
    device: Device


class TimeStampedMsg(TypedDict):
    time_stamp: int


class BaseMsg(TimeStampedMsg):
    device_id: str
    device_nr: int


class BaseSendMsg(TypedDict):
    device_id: Optional[str]
    device_nr: Optional[int]
    time_stamp: Optional[int]


class DataMsg(BaseMsg):
    type: Literal['key', 'acceleration', 'gyro', 'pointer', 'notification']


class KeyMsg(DataMsg):
    type: Literal['key']
    key: Literal['up', 'right', 'down', 'left', 'home']


class PointerData(TypedDict):
    context: Literal['color', 'grid']


class ColorPointer(PointerData):
    type: Literal['pointer']
    context: Literal['color']
    x: int
    y: int
    width: int
    height: int


class GridPointer(PointerData):
    type: Literal['pointer']
    context: Literal['grid']
    row: int
    column: int
    color: str


class Acc(TypedDict):
    x: float
    y: float
    z: float
    interval: float


class Gyro(TypedDict):
    alpha: float
    beta: float
    gamma: float
    absolute: bool


class AccMsg(Acc):
    type: Literal['acceleration']


class GyroMsg(Gyro):
    type: Literal['gyro']


class ErrorMsg(TypedDict):
    type: EVENTS
    msg: str
    err: Union[str, dict]


def flatten(list_of_lists: List[List]) -> List:
    return [y for x in list_of_lists for y in x]


def to_datetime(data: TimeStampedMsg) -> datetime.datetime:
    '''
    extracts the datetime from a data package. if the field `time_stamp` is not present,
    the current datetime will be returned
    '''
    if 'time_stamp' not in data:
        return datetime.datetime.now()
    ts = data['time_stamp']
    # convert time_stamp from ms to seconds
    if ts > 1000000000000:
        ts = ts / 1000.0
    return datetime.datetime.fromtimestamp(ts)


def random_color() -> str:
    '''
    Returns
    -------
    str
        random rgb color, colors ranging between 0 and 255

    Example
    -------
        rgb(127, 1, 36)
    '''
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    return f'rgb({r}, {g}, {b})'


class Connector:
    __start_time_ns: int = time.time_ns()
    data: Dict[str, List[BaseMsg]] = DictX({})
    devices: List[Device] = []
    device: Device = DictX({})
    __server_url: str
    __device_id: str
    sio: socketio.Client = socketio.Client()
    room_members: List[Device] = []
    joined_rooms: List[str]

    # callback functions
    on_key: Callable[[KeyMsg, Optional[Connector]], None] = None
    on_pointer: Callable[[Union[ColorPointer, GridPointer], Optional[Connector]], None] = None
    on_acceleration: Callable[[AccMsg, Optional[Connector]], None] = None
    on_gyro: Callable[[GyroMsg, Optional[Connector]], None] = None
    on_sensor: Callable[[Union[GyroMsg, AccMsg], Optional[Connector]], None] = None

    on_data: Callable[[DataMsg, Optional[Connector]], None] = None
    on_broadcast_data: Callable[[DataMsg, Optional[Connector]], None] = None
    on_all_data: Callable[[List[DataMsg], Optional[Connector]], None] = None
    on_device: Callable[[Device, Optional[Connector]], None] = None
    on_client_device: Callable[[Union[Device, None], Optional[Connector]], None] = None
    on_devices: Callable[[List[Device], Optional[Connector]], None] = None
    on_error: Callable[[ErrorMsg, Optional[Connector]], None] = None
    on_room_joined: Callable[[DeviceJoinedMsg, Optional[Connector]], None] = None
    on_room_left: Callable[[DeviceLeftMsg, Optional[Connector]], None] = None

    @property
    def server_url(self):
        return self.__server_url

    @property
    def device_id(self):
        return self.__device_id

    def __init__(self, server_url: str, device_id: str):
        self.__server_url = server_url
        self.__device_id = device_id
        self.sio.on('connect', self.__on_connect)
        self.sio.on('disconnect', self.__on_disconnect)
        self.sio.on(NEW_DATA, self.__on_new_data)
        self.sio.on(ALL_DATA, self.__on_all_data)
        self.sio.on(DEVICE, self.__on_device)
        self.sio.on(DEVICES, self.__on_devices)
        self.sio.on(ERROR_MSG, self.__on_error)
        self.sio.on(ROOM_JOINED, self.__on_room_joined)
        self.sio.on(ROOM_LEFT, self.__on_room_left)
        self.joined_rooms = [device_id]
        self.connect()

    @property
    def client_device(self):
        return next((device for device in self.devices if device['is_controller'] and device['device_id'] == self.device_id), None)

    def emit(self, event: str, data: BaseSendMsg = {}, broadcast: bool = False, unicast_to: int = None):
        '''
        Parameters
        ----------
        event : str
            the event name 

        data : BaseSendMsg
            the data to send, fields 'time_stamp' and 'device_id' are added when they are not present

        Optional
        --------
        broadcast : bool
            wheter to send this message to all connected devices

        unicast_to : int
            the device number to which this message is sent exclusively. When set, boradcast has no effect. 
        '''
        if 'time_stamp' not in data:
            data['time_stamp'] = time.time_ns() // 1000000

        if 'device_id' not in data:
            data['device_id'] = self.device_id

        if broadcast:
            data['broadcast'] = True

        if type(unicast_to) == int:
            if 'broadcast' in data:
                del data['broadcast']
            data['unicast_to'] = unicast_to

        self.sio.emit(event, data)

    def broadcast(self, data: DataMsg):
        self.emit(ADD_NEW_DATA, data=data, broadcast=True)

    def unicast_to(self, data: DataMsg, device_nr: int):
        self.emit(ADD_NEW_DATA, data=data, unicast_to=device_nr)

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

    @property
    def device_count(self) -> int:
        return len(self.devices)

    @property
    def client_devices(self) -> List[Device]:
        return list(filter(lambda device: device['is_controller'], self.devices))

    @property
    def client_count(self) -> int:
        '''
        number of web-clients (or controller-clients) connected to the server
        '''
        return len(self.client_devices)

    @property
    def joined_room_count(self) -> int:
        return len(self.joined_rooms)

    @property
    def room_member_count(self) -> int:
        return len(self.room_members)

    @property
    def data_list(self) -> List[DataMsg]:
        '''
        Returns
        -------
        List[DataMsg] a list of all received messages (inlcuding messages to other device id's), ordered by time_stamp ascending (first element = oldest)
        '''
        data = flatten(self.data.values())
        data = sorted(
            data,
            key=lambda item: item['time_stamp'] if 'time_stamp' in item else 0,
            reverse=False
        )
        return list(data)

    def all_broadcast_data(self, data_type: str = None) -> List[DataMsg]:
        '''
        Returns the broadcasted data (from all devices)
        '''
        data = filter(lambda item: 'broadcast' in item and item['broadcast'], self.data_list)

        if data_type is not None:
            data = filter(lambda pkg: 'type' in pkg and pkg['type'] == data_type, data)

        return list(data)

    def latest_broadcast_data(self, data_type: str = None) -> Union[DataMsg, None]:
        '''
        Return
        ______
        DataMsg, None
            the latest data from all broadcasted data. None is returned when no package is found
        '''

        for pkg in reversed(self.data_list):
            if 'broadcast' in pkg and pkg['broadcast']:
                if data_type is None or ('type' in pkg and pkg['type'] == data_type):
                    return pkg

        return None

    def all_data(self, data_type: str = None, device_id: str = None) -> List[DataMsg]:
        '''
        Returns all data with the given type and from the given device_id.

        Optional
        --------
        data_type : str the type of the data,
                    e.g. for `data_type='key'` all items of the resulting list will
                    be of type `'key'`.
                    By default all data is returned

        device_id :
            str default is the device_id of this connector and only data of this device_id will be returned.
            when set to '__ALL_DEVICES__', the latest data of all devices will be returned
        '''
        if device_id is None:
            device_id = self.device_id

        if device_id == '__ALL_DEVICES__':
            pass
        elif device_id not in self.data:
            return []

        data = self.data_list if device_id is '__ALL_DEVICES__' else self.data[device_id]

        if data_type is None:
            return data

        data = filter(lambda pkg: 'type' in pkg and pkg['type'] == data_type, data)
        return list(data)

    def latest_data(self, data_type: str = None, device_id: str = None) -> Union[DataMsg, None]:
        '''
        Returns the latest data (last received) with the given type and from the given device_id.

        Optional
        --------
        data_type : str the type of the data,
                    e.g. for `data_type='key'` all items of the resulting list will
                    be of type `'key'`.
                    By default all data is returned

        device_id : str
            default is the device_id of this connector. Only data of this device_id is returned.
            when set to '__ALL_DEVICES__', the latest data of all devices will be returned

        Returns
        -------
        DataMsg, None
            when no data is found, None is returned
        '''
        if device_id is None:
            device_id = self.device_id

        if device_id == '__ALL_DEVICES__':
            pass
        elif device_id not in self.data:
            return None

        data = self.data_list if device_id is '__ALL_DEVICES__' else self.data[device_id]

        for pkg in reversed(data):
            if data_type is None or ('type' in pkg and pkg['type'] == data_type):
                return pkg

        return None

    def pointer_data(self, device_id: str = '__ALL_DEVICES__') -> Union[List[ColorPointer], List[GridPointer]]:
        return self.all_data('pointer', device_id=device_id)

    def color_pointer_data(self, device_id: str = '__ALL_DEVICES__') -> List[ColorPointer]:
        return list(filter(lambda pkg: pkg['context'] == 'color', self.pointer_data(device_id=device_id)))

    def grid_pointer_data(self, device_id: str = '__ALL_DEVICES__') -> List[GridPointer]:
        return list(filter(lambda pkg: pkg['context'] == 'grid', self.pointer_data(device_id=device_id)))

    def gyro_data(self, device_id: str = '__ALL_DEVICES__') -> List[GyroMsg]:
        return self.all_data('gyro', device_id=device_id)

    def acceleration_data(self, device_id: str = '__ALL_DEVICES__') -> List[AccMsg]:
        return self.all_data('acceleration', device_id=device_id)

    def key_data(self, device_id: str = '__ALL_DEVICES__') -> List[KeyMsg]:
        return self.all_data('key', device_id=device_id)

    def latest_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[ColorPointer, GridPointer, None]:
        return self.latest_data('pointer', device_id=device_id)

    def latest_color_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[ColorPointer, None]:
        for pkg in reversed(self.data_list):
            has_type = 'type' in pkg and pkg['type'] == 'pointer' and pkg['context'] == 'color'
            is_device = device_id == '__ALL_DEVICES__' or ('device_id' in pkg and device_id == pkg['device_id'])

            if has_type and is_device:
                return pkg

    def latest_grid_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[GridPointer, None]:
        for pkg in reversed(self.data_list):
            has_type = 'type' in pkg and pkg['type'] == 'pointer' and pkg['context'] == 'grid'
            is_device = device_id == '__ALL_DEVICES__' or ('device_id' in pkg and device_id == pkg['device_id'])

            if has_type and is_device:
                return pkg

    def latest_gyro(self, device_id: str = '__ALL_DEVICES__') -> Union[None, GyroMsg]:
        return self.latest_data('gyro', device_id=device_id)

    def latest_acceleration(self, device_id: str = '__ALL_DEVICES__') -> Union[None, AccMsg]:
        return self.latest_data('acceleration', device_id=device_id)

    def latest_key(self, device_id: str = '__ALL_DEVICES__') -> Union[None, KeyMsg]:
        return self.latest_data('key', device_id=device_id)

    def set_grid(self, grid: Union[List[str], List[List[str]]], device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        '''
        Parameters
        ----------
        grid : List<List<str>> a 2d array containing the color of each cell

        Optional
        --------
        device_id : str control the device with this id

        unicast_to : int control the device with the given number

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
        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'grid',
                'grid': grid
            },
            broadcast=broadcast,
            unicast_to=unicast_to
        )

    def set_color(self, color: str, device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        '''
        Parameters
        ----------
        color : str
            the color of the panel background, can be any valid css color

        Optional
        --------
        device_id : str
            control the device with this id

        unicast_to : int
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
        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'color',
                'color': color
            },
            broadcast=broadcast,
            unicast_to=unicast_to
        )

    def clean_data(self):
        '''
        removes all gathered data
        '''
        self.data = DictX({})

    def sleep(self, seconds: float = 0) -> None:
        '''
        Sleep for the requested amount of time using the appropriate async model.

        This is a utility function that applications can use to put a task to sleep without having to worry about using the correct call for the selected async mode.
        '''
        self.sio.sleep(seconds)

    def wait(self):
        '''
        Wait until the connection with the server ends.

        Client applications can use this function to block the main thread during the life of the connection.
        '''
        self.sio.wait()

    def disconnect(self):
        if not self.sio.connected:
            return
        self.sio.disconnect()

    def join_room(self, device_id: str):
        self.emit(JOIN_ROOM, DictX({'room': device_id}))

    def leave_room(self, device_id: str):
        self.emit(LEAVE_ROOM, DictX({'room': device_id}))

    def __on_connect(self):
        logging.info('SocketIO connected')

    def __on_disconnect(self):
        logging.info('SocketIO disconnected')

    def __register(self):
        self.emit(NEW_DEVICE)

    def __callback(self, name, data):
        callback = getattr(self, name)
        if callback is None:
            return
        try:
            arg_count = len(signature(callback).parameters)
            if arg_count == 1:
                callback(data)
            elif arg_count == 2:
                callback(data, self)
        except Exception:
            pass

    def __on_new_data(self, data: DataMsg):
        data = DictX(data)
        if 'device_id' not in data:
            return

        if data['device_id'] not in self.data:
            self.data[data['device_id']] = []

        self.data[data['device_id']].append(data)

        if 'type' in data:
            if data['type'] == 'key':
                self.__callback('on_key', data)
            if data['type'] in ['acceleration', 'gyro']:
                self.__callback('on_sensor', data)
            if data['type'] == 'acceleration':
                self.__callback('on_acceleration', data)
            if data['type'] == 'gyro':
                self.__callback('on_gyro', data)
            if data['type'] == 'pointer':
                self.__callback('on_pointer', data)

        if 'broadcast' in data and data['broadcast'] and self.on_broadcast_data is not None:
            self.__callback('on_broadcast_data', data)
        else:
            self.__callback('on_data', data)

    def __on_all_data(self, data: List[DataMsg]):
        if 'device_id' not in data:
            return

        data['all_data'] = list(map(lambda pkg: DictX(pkg), data['all_data']))
        self.data[data['device_id']] = data['all_data']
        self.__callback('on_all_data', data)

    def __on_room_left(self, device: DeviceLeftMsg):
        device = DictX(device)
        if device['room'] == self.device_id:
            if device['device'] in self.room_members:
                self.room_members.remove(device['device'])
                self.__callback('on_room_left', device['device'])

        elif device['device']['device_id'] == self.device_id:
            if device['device'] in self.joined_rooms:
                self.joined_rooms.remove(device['device'])

    def __on_room_joined(self, device: DeviceJoinedMsg):
        device = DictX(device)
        if device['room'] == self.device_id:
            if device['device'] not in self.room_members:
                self.room_members.append(device['device'])
                self.__callback('on_room_joined', device['device'])
        elif device['device']['device_id'] == self.device_id:
            if device['device'] not in self.joined_rooms:
                self.joined_rooms.append(device['device'])

    def __on_error(self, err: ErrorMsg):
        err = DictX(err)
        logging.warn(f'Error on Event {err.type}: {err.msg}')

        self.__callback('on_error', err)

    def __on_device(self, device: Device):
        device = DictX(device)
        if 'device_id' not in device or 'socket_id' not in device:
            return
        if self.sio.sid == device['socket_id']:
            self.device = device
            self.emit(GET_ALL_DATA)
            if device not in self.room_members:
                self.room_members.append(device)
            self.__callback('on_device', device)

    def __on_devices(self, devices: List[Device]):
        devices = list(map(lambda device: DictX(device), devices))
        had_client_device = self.client_device is not None
        self.devices = devices
        if self.on_client_device:
            has_client_device = self.client_device is not None
            if (had_client_device and not has_client_device) or (has_client_device and not had_client_device):
                self.__callback('on_client_device', self.client_device)

        self.__callback('on_devices', devices)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    connector = Connector('https://io.lebalz.ch', 'FooBar')

    # draw a 3x3 checker board
    connector.set_grid([
        ['black', 'white', 'black'],
        ['white', 'black', 'white'],
        ['black', 'white', 'black'],
    ], broadcast=True)

    connector.on_key = lambda data, c: logging.info(f'on_key: {data}, len: {len(c.all_data())}')
    connector.on_broadcast_data = lambda data: logging.info(f'on_broadcast_data: {data}')
    connector.on_data = lambda data: logging.info(f'on_data: {data}')
    connector.on_all_data = lambda data: logging.info(f'on_all_data: {data}')
    connector.on_device = lambda data: logging.info(f'on_device: {data}')
    connector.on_devices = lambda data: logging.info(f'on_devices: {data}')
    connector.on_acceleration = lambda data: logging.info(f'on_acceleration: {data}')
    connector.on_gyro = lambda data: logging.info(f'on_gyro: {data}')
    connector.on_sensor = lambda data: logging.info(f'on_sensor: {data}')
    connector.on_room_joined = lambda data: logging.info(f'on_room_joined: {data}')
    connector.on_room_left = lambda data: logging.info(f'on_room_left: {data}')
    connector.on_pointer = lambda data: logging.info(f'on_pointer: {data}')
    connector.on_client_device = lambda data: logging.info(f'on_client_device: {data}')
    connector.on_error = lambda data: logging.info(f'on_error: {data}')

    time.sleep(1)
    print(connector.joined_room_count)
    print(connector.client_count)
    print(connector.device_count)

    print('\n')
    print('data: ', connector.all_data())
    print('data: ', connector.all_data(data_type='grid'))
    print('latest data: ', connector.latest_data())
    print('time_stamp', to_datetime(connector.latest_data()))
    print('latest data: ', connector.latest_data(data_type='key'))
    print('broadcast data: ', connector.all_broadcast_data())
    print('broadcast data: ', connector.all_broadcast_data(data_type='grid'))
    print('latest broadcast data: ', connector.latest_broadcast_data())
    print('latest broadcast data: ', connector.latest_broadcast_data(data_type='key'))
    print('cnt device', connector.device_count)
    print('cnt room', connector.room_member_count)
    print('cnt clients', connector.client_count)
    print('cnt joined rooms', connector.joined_room_count)
    print('pointer_data', connector.pointer_data())
    print('data_list', connector.data_list)
    print('color_pointer_data', connector.color_pointer_data())
    print('grid_pointer_data', connector.grid_pointer_data())
    print('gyro_data', connector.gyro_data())
    print('acceleration_data', connector.acceleration_data())
    print('key_data', connector.key_data())
    print('latest_pointer', connector.latest_pointer())
    print('latest_color_pointer', connector.latest_color_pointer())
    print('latest_grid_pointer', connector.latest_grid_pointer())
    print('latest_gyro', connector.latest_gyro())
    print('latest_acceleration', connector.latest_acceleration())
    print('latest_key', connector.latest_key())

    connector.sleep(2)
    connector.disconnect()
