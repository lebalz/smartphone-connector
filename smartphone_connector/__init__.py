from __future__ import annotations
import socketio
import logging
import time
from datetime import datetime
import random
from inspect import signature
from typing import Union, Literal, Callable, List, Dict, Optional, TypeVar


Any = object()

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
INFORMATION_MSG = 'information_msg'
SET_NEW_DEVICE_NR = 'set_new_device_nr'

INPUT_PROMPT = 'input_prompt'
NOTIFICATION = 'notification'

EVENTS = Union[
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
    ERROR_MSG,
    INFORMATION_MSG,
    SET_NEW_DEVICE_NR
]

INPUT_TYPE = Literal['text', 'number', 'datetime', 'date', 'time', 'select']


def time_s() -> float:
    '''
    returns the current time in seconds since epoche
    '''
    return (time.time_ns() // 1000000) / 1000.0


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


class TimeStampedMsg(DictX):
    time_stamp: float


class BaseMsg(TimeStampedMsg):
    device_id: str
    device_nr: int


class Device(DictX):
    device_id: str
    is_client: bool
    device_nr: int
    socket_id: str


class DevicesMsg(TimeStampedMsg):
    devices: List[Device]


class DeviceJoinedMsg(BaseMsg):
    room: str
    device: Device


class DeviceLeftMsg(BaseMsg):
    room: str
    device: Device


class BaseSendMsg(DictX):
    device_id: Optional[str]
    device_nr: Optional[int]
    time_stamp: Optional[float]


class DataMsg(BaseMsg):
    type: Literal['key', 'acceleration', 'gyro', 'pointer', 'notification']


class KeyMsg(DataMsg):
    type: Literal['key']
    key: Literal['up', 'right', 'down', 'left', 'home']


class PointerData(BaseMsg):
    context: Literal['color', 'grid']


class ColorPointer(PointerData):
    type: Literal['pointer']
    context: Literal['color']
    x: int
    y: int
    width: int
    height: int
    displayed_at: float


class GridPointer(PointerData):
    type: Literal['pointer']
    context: Literal['grid']
    row: int
    column: int
    color: str
    displayed_at: float


class Acc(BaseMsg):
    x: float
    y: float
    z: float
    interval: float


class Gyro(BaseMsg):
    alpha: float
    beta: float
    gamma: float
    absolute: bool


class AccMsg(Acc):
    type: Literal['acceleration']


class GyroMsg(Gyro):
    type: Literal['gyro']


class ErrorMsg(BaseMsg):
    type: EVENTS
    msg: str
    err: Union[str, dict]


class InformationMsg(TimeStampedMsg):
    message: str
    action: BaseSendMsg


class InputResponseMsg(DataMsg):
    type: Literal['input_response']
    response: str
    displayed_at: float


class AlertConfirmMsg(DataMsg):
    type: Literal['alert_confirm']
    displayed_at: float


def flatten(list_of_lists: List[List]) -> List:
    return [y for x in list_of_lists for y in x]


def to_datetime(data: TimeStampedMsg) -> datetime:
    '''
    extracts the datetime from a data package. if the field `time_stamp` is not present,
    the current datetime will be returned
    '''
    if 'time_stamp' not in data:
        return datetime.now()
    ts = data['time_stamp']
    # convert time_stamp from ms to seconds
    if ts > 1000000000000:
        ts = ts / 1000.0
    return datetime.fromtimestamp(ts)


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


def try_or(func, default=None, expected_exc=(Exception,)):
    try:
        return func()
    except expected_exc:
        return default


T = TypeVar('T')


def first(filter_func: Callable[[T], bool], list_: List[T]) -> T:
    return next((item for item in list_ if try_or(lambda: filter_func(item), False)), None)


class Connector:
    __last_time_stamp: float = -1
    __last_sub_time: float = 0
    data: Dict[str, List[BaseMsg]] = DictX({})
    __devices: DevicesMsg = {'time_stamp': time_s(), 'devices': []}
    device: Device = DictX({})
    __server_url: str
    __device_id: str
    __info_messages: List[InformationMsg] = []
    sio: socketio.Client = socketio.Client()
    room_members: List[Device] = []
    joined_rooms: List[str]

    # callback functions

    on_key: Callable[[Any, KeyMsg, Optional[Connector]], None] = None
    on_pointer: Callable[[Any, Union[ColorPointer, GridPointer], Optional[Connector]], None] = None
    on_acceleration: Callable[[Any, AccMsg, Optional[Connector]], None] = None
    on_gyro: Callable[[Any, GyroMsg, Optional[Connector]], None] = None
    on_sensor: Callable[[Any, Union[GyroMsg, AccMsg], Optional[Connector]], None] = None

    on_data: Callable[[Any, DataMsg, Optional[Connector]], None] = None
    on_broadcast_data: Callable[[Any, DataMsg, Optional[Connector]], None] = None
    on_all_data: Callable[[Any, List[DataMsg], Optional[Connector]], None] = None
    on_device: Callable[[Any, Device, Optional[Connector]], None] = None
    on_client_device: Callable[[Any, Union[Device, None], Optional[Connector]], None] = None
    on_devices: Callable[[Any, List[Device], Optional[Connector]], None] = None
    on_error: Callable[[Any, ErrorMsg, Optional[Connector]], None] = None
    on_room_joined: Callable[[Any, DeviceJoinedMsg, Optional[Connector]], None] = None
    on_room_left: Callable[[Any, DeviceLeftMsg, Optional[Connector]], None] = None

    __responses: List[InputResponseMsg] = []
    __alerts: List[AlertConfirmMsg] = []

    @property
    def devices(self) -> List[Device]:
        return self.__devices['devices']

    @property
    def server_url(self):
        return self.__server_url

    @property
    def device_id(self):
        return self.__device_id

    @property
    def current_time_stamp(self):
        ts = time_s()
        if ts == self.__last_time_stamp:
            self.__last_sub_time += 0.000001
            return ts + self.__last_sub_time
        self.__last_sub_time = 0
        self.__last_time_stamp = ts
        return ts

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
        self.sio.on(INFORMATION_MSG, self.__on_information)
        self.sio.on(ROOM_JOINED, self.__on_room_joined)
        self.sio.on(ROOM_LEFT, self.__on_room_left)
        self.joined_rooms = [device_id]
        self.connect()

    @property
    def client_device(self):
        return first(lambda device: device['is_client'] and device['device_id'] == self.device_id, self.devices)

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
            data['time_stamp'] = self.current_time_stamp

        if 'device_id' not in data:
            data['device_id'] = self.device_id

        if broadcast:
            data['broadcast'] = True

        if type(unicast_to) == int:
            if 'broadcast' in data:
                del data['broadcast']
            data['unicast_to'] = unicast_to

        self.sio.emit(event, data)

    def send(self, data: DataMsg, broadcast: bool = False, unicast_to: int = None):
        '''
        Emits a new_data event
        Parameters
        ----------
        data : DataMsg
            the data to send, fields 'time_stamp' and 'device_id' are added when they are not present

        Optional
        --------
        broadcast : bool
            wheter to send this message to all connected devices

        unicast_to : int
            the device number to which this message is sent exclusively. When set, boradcast has no effect.
        '''
        self.emit(ADD_NEW_DATA, data=data, broadcast=broadcast, unicast_to=unicast_to)

    def alert(self, message: str, unicast_to: int = None):
        '''
        alerts the user by an alert which the user must confirm. This is a blocking call, the 
        script will not proceed until the user confirmed the message.
        Parameters
        ----------
        message : str
            notification message to show
        '''
        self.notify(message=message, alert=True, unicast_to=unicast_to)

    def print(self, message: str, display_time: float = -1, alert: bool = False, broadcast: bool = False, unicast_to: int = None):
        '''
        Notify the device - when not alerting, the call is non-blocking and the next command will be executed immediately. 
        Parameters
        ----------
        message : str
            the notification message
        display_time : int
            time in seconds to show the notification, -1 show until dismiss, ignored when alert is True
        alert : bool
            user must confirm message, blocking call

        Optional
        --------
        broadcast : bool
            wheter to send this message to all connected devices

        unicast_to : int
            the device number to which this message is sent exclusively. When set, boradcast has no effect.
        '''
        return self.notify(message, display_time=display_time, alert=alert, broadcast=broadcast, unicast_to=unicast_to)

    def notify(self, message: str, display_time: float = -1, alert: bool = False, broadcast: bool = False, unicast_to: int = None):
        '''
        Notify the device - when not alerting, the call is non-blocking and the next command will be executed immediately. 
        Parameters
        ----------
        message : str
            the notification message
        display_time : int
            time in seconds to show the notification, -1 show until dismiss, ignored when alert is True
        alert : bool
            user must confirm message, blocking call

        Optional
        --------
        broadcast : bool
            wheter to send this message to all connected devices

        unicast_to : int
            the device number to which this message is sent exclusively. When set, boradcast has no effect.
        '''
        ts = self.current_time_stamp

        self.emit(
            ADD_NEW_DATA,
            data={
                'type': NOTIFICATION,
                'time_stamp': ts,
                'message': message,
                'alert': alert,
                'time': display_time * 1000
            },
            broadcast=broadcast,
            unicast_to=unicast_to
        )
        if not alert:
            return
        alert_msg = False
        while not alert_msg:
            self.sleep(0.01)
            alert_msg = next((res for res in self.__alerts if res['time_stamp'] == ts), False)
        self.__alerts.remove(alert_msg)

    def input(self, question: str, input_type: INPUT_TYPE = 'text', options: List[str] = None, unicast_to: int = None) -> Union[str, None]:
        '''
        Parameters
        ----------
        question : str
            what should the user be prompted for?

        input_type : 'text', 'number', 'datetime', 'date', 'time', 'select'
            to use the correct html input type

        Optional
        --------
        options: List[str]
            required when input_type is 'select' - a list with the selection-options
        unicast_to : int
            the device number to which this message is sent exclusively.

        Return
        ------
        str, None

            When the user canceled the prompt, None is returned
        '''
        return self.prompt(question, input_type=input_type, options=options, unicast_to=unicast_to)

    def select(self, question: str, options: List[str]):
        '''
        Parameters
        ----------
        question : str
            what should the user be prompted for?
        options: List[str]
            a list with the options a user can select
        
        Optional
        --------
        unicast_to : int
            the device number to which this message is sent exclusively.

        Retrun
        ------
        str, None

            the selected value. None is returned when the prompt is canceled
        '''
        return self.prompt(question, input_type='select', options=options)

    def prompt(self, question: str, input_type: INPUT_TYPE = 'text', options: List[str] = None, unicast_to: int = None) -> Union[str, None]:
        '''
        Parameters
        ----------
        question : str
            what should the user be prompted for?

        input_type : 'text', 'number', 'datetime', 'date', 'time', 'select'
            to use the correct html input type

        Optional
        --------
        options: List[str]
            required when input_type is 'select' - a list with the selection-options
        unicast_to : int
            the device number to which this message is sent exclusively.

        Return
        ------
        str, None

            When the user canceled the prompt, None is returned 
        '''
        ts = self.current_time_stamp

        if input_type == 'datetime':
            input_type = 'datetime-local'

        self.emit(
            ADD_NEW_DATA,
            {
                'type': INPUT_PROMPT,
                'question': question,
                'input_type': input_type,
                'options': options,
                'time_stamp': ts
            },
            unicast_to=unicast_to
        )
        response = False

        while not response:
            self.sleep(0.01)
            response = next((res for res in self.__responses if res['time_stamp'] == ts), False)

        self.__responses.remove(response)

        if 'response' in response:
            return response['response']

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
        return list(filter(lambda device: device['is_client'], self.devices))

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

        data = self.data_list if device_id == '__ALL_DEVICES__' else self.data[device_id]

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

        data = self.data_list if device_id == '__ALL_DEVICES__' else self.data[device_id]

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

    def set_device_nr(self, new_device_nr: int, device_id: str = None, current_device_nr: int = None, max_wait: float = 5) -> bool:
        '''
        Parameters
        ----------
        new_device_nr : int
            the new device number that is assigned to according device

        Optional
        --------
        device_id : str (default: this.device_id)
            assigns the new number to the first client device with the (currently) smallest device_nr

        current_device_nr : int
            sets the new device nr on this device.
            When set, `device_id` has no effect.

        max_wait : float (default: 5)
            number of seconds to retry assignment

        Return
        ------
        bool wheter the assignment was succesfull or not.
        '''
        ts = time_s()
        self.__info_messages.clear()
        self.emit(
            SET_NEW_DEVICE_NR,
            {
                'time_stamp': ts,
                'new_device_nr': new_device_nr,
                'device_id': device_id or self.device_id,
                'current_device_nr': current_device_nr
            }
        )
        result_msg = None
        while result_msg is None and (time_s() - ts) < max_wait:
            info_cnt = len(self.__info_messages)

            if info_cnt > 0 and self.__info_messages[info_cnt - 1].action['time_stamp'] == ts:
                result_msg = self.__info_messages[info_cnt - 1]
            else:
                self.sleep(0.1)

        if result_msg is not None and result_msg['message'] == 'Success':
            return True

        time_left = max_wait - (time_s() - ts)
        if time_left > 0 and 'should_retry' in result_msg and result_msg['should_retry']:
            return self.set_device_nr(new_device_nr, device_id=device_id, current_device_nr=current_device_nr, max_wait=time_left)

        return False

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
            if data['type'] == 'input_response':
                self.__responses.append(data)
            if data['type'] == 'alert_confirm':
                self.__alerts.append(data)

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

    def __on_information(self, data: InformationMsg):
        self.__info_messages.append(DictX(data))

    def __on_device(self, device: Device):
        device = DictX(device)
        if 'device_id' not in device or 'socket_id' not in device:
            return
        if self.sio.sid == device['socket_id']:
            self.device = device
            self.emit(GET_ALL_DATA)
            old_device_instance = first(lambda d: d['socket_id'] == device['socket_id'], self.room_members)
            if old_device_instance:
                self.room_members.remove(old_device_instance)
            self.room_members.append(device)
            self.__callback('on_device', device)

    def __on_devices(self, data: DevicesMsg):
        data = DictX(data)
        data['devices'] = list(map(lambda device: DictX(device), data['devices']))
        had_client_device = self.client_device is not None
        self.__devices = data
        if self.on_client_device:
            has_client_device = self.client_device is not None
            if (had_client_device and not has_client_device) or (has_client_device and not had_client_device):
                self.__callback('on_client_device', self.client_device)

        self.__callback('on_devices', self.devices)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    smartphone = Connector('http://localhost:5000', 'FooBar')
    # smartphone = Connector('https://io.lebalz.ch', 'FooBar')
    t0 = time_s()
    smartphone.print(
        """Hiiii
        mother fucker
        """)
    smartphone.print('aasd1')
    smartphone.print('aasd2')
    smartphone.print('aasd3')
    smartphone.print('aasd4')
    smartphone.print('aasd5')
    smartphone.print('aasd6')
    smartphone.print('aasd7')
    smartphone.print('aasd8')
    smartphone.print('aasd9')
    smartphone.print('aasd10')
    response = smartphone.input("Hallo", input_type="select", options=["+", ":", "-", "*"])

    # print('set deivce nr: ', smartphone.set_device_nr(13))

    # draw a 3x3 checker board
    smartphone.set_grid([
        ['black', 'white', 'black'],
        ['white', 'black', 'white'],
        ['black', 'white', 'black'],
    ], broadcast=True)

    smartphone.on_key = lambda data, c: logging.info(f'on_key: {data}, len: {len(c.all_data())}')
    smartphone.on_broadcast_data = lambda data: logging.info(f'on_broadcast_data: {data}')
    smartphone.on_data = lambda data: logging.info(f'on_data: {data}')
    smartphone.on_all_data = lambda data: logging.info(f'on_all_data: {data}')
    smartphone.on_device = lambda data: logging.info(f'on_device: {data}')
    smartphone.on_devices = lambda data: logging.info(f'on_devices: {data}')
    smartphone.on_acceleration = lambda data: logging.info(f'on_acceleration: {data}')
    smartphone.on_gyro = lambda data: logging.info(f'on_gyro: {data}')
    smartphone.on_sensor = lambda data: logging.info(f'on_sensor: {data}')
    smartphone.on_room_joined = lambda data: logging.info(f'on_room_joined: {data}')
    smartphone.on_room_left = lambda data: logging.info(f'on_room_left: {data}')
    smartphone.on_pointer = lambda data: logging.info(f'on_pointer: {data}')
    smartphone.on_client_device = lambda data: logging.info(f'on_client_device: {data}')
    smartphone.on_error = lambda data: logging.info(f'on_error: {data}')

    time.sleep(2)
    response = smartphone.input('Name? ')
    smartphone.print(f'Name: {response} ')
    smartphone.notify('notify hiii', alert=True)
    print(smartphone.joined_room_count)
    print(smartphone.client_count)
    print(smartphone.device_count)

    print('\n')
    print('data: ', smartphone.all_data())
    print('data: ', smartphone.all_data(data_type='grid'))
    print('latest data: ', smartphone.latest_data())
    print('time_stamp', to_datetime(smartphone.latest_data()))
    print('latest data: ', smartphone.latest_data(data_type='key'))
    print('broadcast data: ', smartphone.all_broadcast_data())
    print('broadcast data: ', smartphone.all_broadcast_data(data_type='grid'))
    print('latest broadcast data: ', smartphone.latest_broadcast_data())
    print('latest broadcast data: ', smartphone.latest_broadcast_data(data_type='key'))
    print('cnt device', smartphone.device_count)
    print('cnt room', smartphone.room_member_count)
    print('cnt clients', smartphone.client_count)
    print('cnt joined rooms', smartphone.joined_room_count)
    print('pointer_data', smartphone.pointer_data())
    print('data_list', smartphone.data_list)
    print('color_pointer_data', smartphone.color_pointer_data())
    print('grid_pointer_data', smartphone.grid_pointer_data())
    print('gyro_data', smartphone.gyro_data())
    print('acceleration_data', smartphone.acceleration_data())
    print('key_data', smartphone.key_data())
    print('latest_pointer', smartphone.latest_pointer())
    print('latest_color_pointer', smartphone.latest_color_pointer())
    print('latest_grid_pointer', smartphone.latest_grid_pointer())
    print('latest_gyro', smartphone.latest_gyro())
    print('latest_acceleration', smartphone.latest_acceleration())
    print('latest_key', smartphone.latest_key())

    smartphone.sleep(2)
    smartphone.disconnect()
