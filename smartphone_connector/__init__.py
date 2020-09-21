from __future__ import annotations
import socketio
import logging
import time
from datetime import datetime
import random
from inspect import signature
from typing import Union, Literal, Callable, List, Dict, Optional, TypeVar, Tuple
import threading
from copy import deepcopy
from itertools import repeat


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
    type: Literal['key', 'acceleration', 'gyro', 'pointer', 'notification', 'sprite_collision', 'sprite_out']


class KeyMsg(DataMsg):
    type: Literal['key']
    key: Literal['up', 'right', 'down', 'left', 'home', 'F1', 'F2', 'F3', 'F4']


def default(type: Literal['key', 'acceleration', 'gyro', 'pointer', 'notification']):
    if type == 'key':
        return DictX({
            'type': 'key',
            'time_stamp': 0,
            'device_id': '',
            'device_nr': -999,
            'key': ''
        })
    if type == 'acceleration':
        return DictX({
            'time_stamp': 0,
            'device_id': '',
            'device_nr': -999,
            'x': 0,
            'y': 0,
            'z': 0,
            'interval': 16
        })
    if type == 'gyro':
        return DictX({
            'time_stamp': 0,
            'device_id': '',
            'device_nr': -999,
            'alpha': 0,
            'beta': 0,
            'gamma': 0,
            'absolute': False
        })
    if type == 'color_pointer':
        return DictX({
            'time_stamp': 0,
            'device_id': '',
            'device_nr': -999,
            'type': 'pointer',
            'context': 'color',
            'x': 0,
            'y': 0,
            'width': -1,
            'height': -1,
            'displayed_at': 0
        })
    if type == 'grid_pointer':
        return DictX({
            'time_stamp': 0,
            'device_id': '',
            'device_nr': -999,
            'type': 'pointer',
            'context': 'grid',
            'x': 0,
            'y': 0,
            'width': -1,
            'height': -1,
            'displayed_at': 0
        })
    return DictX({})


class KeyMsgF1(KeyMsg):
    key: Literal['F1']


class KeyMsgF2(KeyMsg):
    key: Literal['F2']


class KeyMsgF3(KeyMsg):
    key: Literal['F3']


class KeyMsgF4(KeyMsg):
    key: Literal['F4']


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


class DataFrame(DictX):
    key: KeyMsg
    acceleration: AccMsg
    gyro: GyroMsg
    color_pointer: ColorPointer
    grid_pointer: GridPointer


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


class GridMsg(DataMsg):
    grid: Union[List[Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]],
                List[List[Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]]]]
    unicast_to: Union[int, None]
    device_id: Union[str, None]
    broadcast: Union[bool, None]
    base_color: Tuple[R, G, B]


class PlaygroundConfiguration:
    unicast_to: Optional[Union[int, None]]
    device_id: Optional[Union[str, None]]
    broadcast: Optional[Union[bool, None]]
    width: Optional[int]
    height: Optional[int]
    shift_x: Optional[int]
    shift_y: Optional[int]


class Sprite(DataMsg):
    id: str
    pos_x: int
    pos_y: int
    width: int
    height: int
    form: Literal['round', 'rectangle']
    color: Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]
    movement: Literal['controlled', 'uncontrolled']


class UpdateSprite(DataMsg):
    pos_x: int
    pos_y: int
    width: int
    height: int
    form: Literal['round', 'rectangle']
    color: Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]


class SpriteCollision(DataMsg):
    type: Literal['sprite_collision']
    sprite_ids: Tuple[str, str]
    time_stamp: float
    overlap: Literal['in', 'out']


class SpriteOut(DataMsg):
    type: Literal['sprite_out']
    sprite_id: str
    time_stamp: float


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


R = int
G = int
B = int
HUE = int


def to_css_color(color: Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]], base_color: Optional[Tuple[R, G, B]] = (255, 0, 0)) -> str:
    if type(color) == str:
        return color
    if type(color) == int:
        if base_color is None or len(base_color) < 3:
            base_color = (255, 0, 0)

        return f'rgba({base_color[0]},{base_color[1]},{base_color[2]},{color / 9})'
    color = list(color)
    if len(color) == 3:
        return f'rgb({color[0]},{color[1]},{color[2]})'
    elif len(color) > 3:
        return f'rgba({color[0]},{color[1]},{color[2]},{color[3]})'
    else:
        raise AttributeError(color)


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


class CancleSubscription:
    __running = True

    @property
    def is_running(self):
        return self.__running

    def cancel(self):
        self.__running = False


class ThreadJob(threading.Thread):
    def __init__(self, callback: Callable, interval: float):
        '''runs the callback function after interval seconds'''
        self.callback = callback
        self.event = threading.Event()
        self.interval = interval
        self.__running = False
        super(ThreadJob, self).__init__()

    def cancel(self):
        self.__running = False
        self.event.set()

    @property
    def is_running(self):
        return self.__running

    def run(self):
        self.__running = True
        while not self.event.wait(self.interval):
            self.callback()


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
    __main_thread_blocked: bool = False
    __blocked_data_msgs: List[DataMsg] = []
    __last_sent_grid: GridMsg = DictX({
        'grid': [[]],
        'unicast_to': None,
        'device_id': None,
        'broadcast': False,
        'base_color': (255, 0, 0)
    })

    __sprites: List[Sprite] = []

    # callback functions

    on_key: Callable[[Any, KeyMsg, Optional[Connector]], None] = None
    on_f1: Callable[[Any, Optional[KeyMsgF1], Optional[Connector]], None] = None
    on_f2: Callable[[Any, Optional[KeyMsgF2], Optional[Connector]], None] = None
    on_f3: Callable[[Any, Optional[KeyMsgF3], Optional[Connector]], None] = None
    on_f4: Callable[[Any, Optional[KeyMsgF4], Optional[Connector]], None] = None
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

    on_sprite_out: Callable[[Any, SpriteOut, Optional[Connector]], None] = None
    on_sprite_collision: Callable[[Any, SpriteCollision, Optional[Connector]], None] = None
    __on_notify_subscribers: Callable[[DataFrame, Optional[Connector]], None] = None
    __subscription_job: Union[ThreadJob, CancleSubscription] = None

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

    def emit(self, event: str, data: BaseSendMsg = {}, broadcast: bool = False, unicast_to: int = None, device_id: str = None):
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
            data['device_id'] = device_id or self.device_id

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
            options can be a numpy array too (or any other object implementing `tolist() -> List[List[]]`)

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
            options can be a numpy array too (or any other object implementing `tolist() -> List[List[]]`)

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
            options can be a numpy array too (or any other object implementing `tolist() -> List[List[]]`)

        unicast_to : int
            the device number to which this message is sent exclusively.

        Return
        ------
        str, None

            When the user canceled the prompt, None is returned 
        '''
        ts = self.current_time_stamp

        if callable(getattr(options, 'tolist', None)):
            options = options.tolist()

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

    def configure_playground(self, configuration: PlaygroundConfiguration, device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        configuration['type'] = 'playground_config'
        self.emit(ADD_NEW_DATA, configuration, unicast_to=unicast_to, broadcast=broadcast, device_id=device_id)

    def add_sprites(self, sprites: List[Sprite], device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        self.__sprites.extend(map(lambda sprite: DictX(sprite), sprites))
        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'sprites',
                'sprites': sprites
            },
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    def add_sprite(self, sprite: Sprite, device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        self.__sprites.append(DictX(sprite))
        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'sprite',
                'sprite': sprite
            },
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    def update_sprite(self, id: str, update: UpdateSprite, device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        sprite = first(lambda s: s.id == id, self.__sprites)
        if sprite:
            sprite.update(update)
        update.update({
            'id': id,
            'movement': 'controlled'
        })

        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'sprite',
                'sprite': update
            },
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    @property
    def get_grid(self) -> List[List[Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]]]:
        grid = self.__last_sent_grid.grid
        is_2d = len(grid) > 0 and type(grid[0]) != str and hasattr(grid[0], "__getitem__")
        if is_2d:
            return deepcopy(grid)
        return [deepcopy(grid)]

    def set_grid_at(self, row: int, column: int, color: Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]):
        '''
        sets the color of the current grid at the given row and column
        '''
        grid = self.get_grid

        rows = len(grid)
        if rows == 0:
            grid = [[]]

        while len(grid[0]) <= column:
            for col in grid:
                col.append(0)
        while len(grid) <= row:
            grid.append(list(repeat(0, len(grid[0]))))

        grid[row][column] = color
        return self.set_grid(
            grid,
            base_color=self.__last_sent_grid.base_color,
            broadcast=self.__last_sent_grid.broadcast,
            unicast_to=self.__last_sent_grid.unicast_to,
            device_id=self.__last_sent_grid.device_id
        )

    def set_image(self, image: List[str], device_id: str = None, unicast_to: int = None, broadcast: bool = False, base_color: Optional[Tuple[int, int, int]] = None):
        '''
        Parameters
        ----------
        image : List<str> a list containing strings build up with spaces or values between 0 and 9. When other characters
                    are used, 9 (full color) is used instead

        Optional
        --------
        base_color : Tuple[r, g, b] representing the base rgb color 0-255

        device_id : str control the device with this id

        unicast_to : int control the device with the given number

        broadcast : bool wheter to send this message to all connected devices


        Example
        -------
        write HELLO
        ```py
        image = [
            '9  9 9999 9     9     99999',
            '9  9 9    9     9     9   9',
            '9999 9999 9     9     9   9',
            '9  9 9    9     9     9   9',
            '9  9 9999 99999 99999 99999'
        ]
        phone.set_image(image)
        ```
        '''
        grid = []
        for char_row in image:
            row = []
            for char in char_row:
                try:
                    row.append(int(char))
                except ValueError:
                    if char == ' ':
                        row.append(0)
                    else:
                        row.append(9)
            grid.append(row)
        return self.set_grid(grid, device_id=device_id, unicast_to=unicast_to, broadcast=broadcast, base_color=base_color)

    def set_grid(self, grid: Union[List[Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]], List[List[Union[str, int, Tuple[R, G, B], Tuple[R, G, B, HUE]]]]], device_id: str = None, unicast_to: int = None, broadcast: bool = False, base_color: Optional[Tuple[int, int, int]] = None):
        '''
        Parameters
        ----------
        grid : List<List<str>> a 2d array containing the color of each cell, an rgb, rgba tuple or an integer between 0 and 9
                representing the brightness of the base color

                grid can be a numpy array too (or any other object implementing `tolist() -> List[List[]]`)

        Optional
        --------
        device_id : str control the device with this id

        unicast_to : int control the device with the given number

        broadcast : bool wheter to send this message to all connected devices

        base_color : Tuple[r, g, b] representing the base rgb color 0-255

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
        if callable(getattr(grid, 'tolist', None)):
            grid = grid.tolist()

        raw_grid = grid
        is_2d = len(grid) > 0 and type(grid[0]) != str and hasattr(grid[0], "__getitem__")
        if is_2d:
            grid = list(map(lambda row: list(map(lambda raw_color: to_css_color(raw_color, base_color=base_color), row)), grid))
        elif len(grid) > 0:
            grid = list(map(lambda raw_color: to_css_color(raw_color, base_color=base_color), grid))

        grid_msg = {
            'type': 'grid',
            'grid': grid,
            'time_stamp': self.current_time_stamp
        }
        self.__last_sent_grid = DictX({
            **grid_msg,
            'grid': raw_grid,
            'base_color': base_color,
            'broadcast': broadcast,
            'unicast_to': unicast_to,
            'device_id': device_id

        })
        self.emit(
            ADD_NEW_DATA,
            grid_msg,
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    def set_color(self, color: Union[str, Tuple[R, G, B], Tuple[R, G, B, HUE]], device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        '''
        Parameters
        ----------
        color : str, Tuple
            the color of the panel background, can be any valid css color or rgb values in range 0-255 and optionally the brightness 0-9 

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
        color = to_css_color(color)
        self.emit(
            ADD_NEW_DATA,
            {
                'type': 'color',
                'color': color
            },
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
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
        Sleep for the requested amount of time (in seconds) using the appropriate async model.

        This is a utility function that applications can use to put a task to sleep without having to worry about using the correct call for the selected async mode.
        '''
        self.sio.sleep(seconds)

    def __distribute_dataframe(self):
        if self.__on_notify_subscribers is None:
            return

        arg_count = len(signature(self.__on_notify_subscribers).parameters)
        if arg_count == 0:
            self.__on_notify_subscribers()
            return

        data = DictX({
            'key': self.latest_key(device_id=self.__device_id) or default('key'),
            'acceleration': self.latest_acceleration(device_id=self.__device_id) or default('acceleration'),
            'gyro': self.latest_gyro(device_id=self.__device_id) or default('gyro'),
            'color_pointer': self.latest_color_pointer(device_id=self.__device_id) or default('color_pointer'),
            'grid_pointer': self.latest_grid_pointer(device_id=self.__device_id) or default('grid_pointer')
        })
        if arg_count == 1:
            self.__on_notify_subscribers(data)
        elif arg_count == 2:
            self.__on_notify_subscribers(data, self)

    def subscribe_async(self, callback: Optional[Callable[[Optional[DataFrame], Optional[Connector]], None]] = None, interval: float = 0.05) -> CancleSubscription:
        return self.subscribe(callback, interval, blocking=False)

    def set_update_interval(self, interval: float):
        return self.subscribe(interval=interval, blocking=True)

    def set_timeout(self, callback: Optional[Callable[[Optional[DataFrame], Optional[Connector]], None]] = None, interval: float = 0.05, blocking=True) -> Union[None, CancleSubscription]:
        return self.subscribe(callback=callback, interval=interval, blocking=blocking)

    def subscribe(self, callback: Optional[Callable[[Optional[DataFrame], Optional[Connector]], None]] = None, interval: float = 0.05, blocking=True) -> Union[None, CancleSubscription]:
        '''
        blocked : bool wheter the main thread gets blocked or not.
        '''
        self.__on_notify_subscribers = callback
        if blocking:
            self.__main_thread_blocked = True
            self.__subscription_job = CancleSubscription()
            while self.__subscription_job.is_running:
                t0 = time_s()
                self.__distribute_dataframe()
                data = deepcopy(self.__blocked_data_msgs)
                self.__blocked_data_msgs.clear()
                for d in data:
                    self.__distribute_new_data_callback(d)
                td = time_s() - t0
                if td < interval:
                    self.sleep(interval - td)
            self.__main_thread_blocked = False
        else:
            self.__subscription_job = ThreadJob(self.__distribute_dataframe, interval)
            self.__subscription_job.start()
            return self.__subscription_job

    def cancel_subscription(self):
        if self.__subscription_job is not None:
            self.__subscription_job.cancel()

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
            if arg_count == 0:
                callback()
            elif arg_count == 1:
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
        if self.__main_thread_blocked:
            self.__blocked_data_msgs.append(data)
        else:
            self.__distribute_new_data_callback(data)

    def __distribute_new_data_callback(self, data: DataMsg):
        if 'type' in data:
            if data['type'] == 'key':
                self.__callback('on_key', data)
                if data['key'] == 'F1':
                    self.__callback('on_f1', data)
                elif data['key'] == 'F2':
                    self.__callback('on_f2', data)
                elif data['key'] == 'F3':
                    self.__callback('on_f3', data)
                elif data['key'] == 'F4':
                    self.__callback('on_f4', data)
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
            if data['type'] == 'sprite_out':
                data = DictX(data)
                sprite = first(lambda s: s.id == data.sprite_id, self.__sprites)
                if sprite:
                    print('sprite out', sprite.id)
                    del self.__sprites[self.__sprites.index(sprite)]
                self.__callback('on_sprite_out', data)
            if data['type'] == 'sprite_collision':
                self.__callback('on_sprite_collision', data)

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
    phone = Connector('http://localhost:5000', 'FooBar')

    phone.configure_playground({
        'width': 200,
        'height': 100
    })

    phone.add_sprites([
        {
            'color': 'red',
            'direction': [1, 1],
            'form': 'round',
            'height': 5,
            'width': 5,
            'id': 'asdfa1',
            'movement': 'uncontrolled',
            'pos_x': 0,
            'pos_y': 0,
            'speed': 2
        },
        {
            'color': 'blue',
            'direction': [1, 1],
            'form': 'round',
            'height': 5,
            'width': 5,
            'id': 'asdfa1',
            'movement': 'uncontrolled',
            'pos_x': 0,
            'pos_y': 0,
            'speed': 1
        },
        {
            'color': 'green',
            'direction': [1, 1],
            'form': 'round',
            'height': 5,
            'width': 5,
            'id': 'asdfa1',
            'movement': 'uncontrolled',
            'pos_x': 0,
            'pos_y': 0,
            'speed': 0.5
        }
    ])

    # phone = Connector('https://io.lebalz.ch', 'FooBar')
    response = phone.input("Hallo")

    image = [
        '9  9 9999 9     9     99999',
        '9  9 9    9     9     9   9',
        '9999 9999 9     9     9   9',
        '9  9 9    9     9     9   9',
        '9  9 9999 99999 99999 99999'
    ]

    phone.set_image(image, base_color=(255, 255, 0))
    phone.sleep(5)
    phone.set_grid(
        [[0]], base_color=(255, 255, 0)
    )
    grid = []
    for i in range(10):
        row = []
        for j in range(10):
            row.append((j + i) // 2)
        grid.append(row)
    phone.set_grid(grid, base_color=(255, 255, 0))
    phone.sleep(3)
    phone.set_grid_at(5, 5, 7)
    phone.sleep(1)
    phone.set_grid_at(2, 5, 3)
    t0 = time_s()

    # Screen().tracer(0, 0)

    def on_acc(data: AccMsg):
        print(data)
        # if data.x > 2:
        #     left(2)
        # if data.x < -2:
        #     right(2)
        # forward(2)
        # Screen().update()
    phone.on_acceleration = on_acc
    phone.set_update_interval(0.05)
    # phone.subscribe(
    #     lambda data, c: logging.info(f'subscribed {time_s()}: {data.acceleration.time_stamp}: {data.acceleration.x}'),
    #     0.05,
    #     blocking=False
    # )
    # time.sleep(2)
    # phone.cancel_subscription()

    phone.print('aasd1')
    phone.print('aasd2')
    phone.print('aasd3')
    phone.print('aasd4')
    phone.print('aasd5')
    phone.print('aasd6')
    phone.print('aasd7')
    phone.print('aasd8')
    phone.print('aasd9')
    phone.print('aasd10')
    # response = phone.input("Hallo", input_type="select", options=["+", ":", "-", "*"])

    # print('set deivce nr: ', phone.set_device_nr(13))

    # draw a 3x3 checker board
    phone.set_grid([
        ['black', 'white', 'black'],
        ['white', 'black', 'white'],
        ['black', 'white', 'black'],
    ], broadcast=True)

    phone.on_key = lambda data, c: logging.info(f'on_key: {data}, len: {len(c.all_data())}')
    phone.on_f1 = lambda: logging.info('F1')
    phone.on_f2 = lambda: logging.info('F2')
    phone.on_f3 = lambda: logging.info('F3')
    phone.on_f4 = lambda: logging.info('F4')
    phone.on_broadcast_data = lambda data: logging.info(f'on_broadcast_data: {data}')
    phone.on_data = lambda data: logging.info(f'on_data: {data}')
    phone.on_all_data = lambda data: logging.info(f'on_all_data: {data}')
    phone.on_device = lambda data: logging.info(f'on_device: {data}')
    phone.on_devices = lambda data: logging.info(f'on_devices: {data}')
    phone.on_acceleration = lambda data: logging.info(f'on_acceleration: {data}')
    phone.on_gyro = lambda data: logging.info(f'on_gyro: {data}')
    phone.on_sensor = lambda data: logging.info(f'on_sensor: {data}')
    phone.on_room_joined = lambda data: logging.info(f'on_room_joined: {data}')
    phone.on_room_left = lambda data: logging.info(f'on_room_left: {data}')
    phone.on_pointer = lambda data: logging.info(f'on_pointer: {data}')
    phone.on_client_device = lambda data: logging.info(f'on_client_device: {data}')
    phone.on_error = lambda data: logging.info(f'on_error: {data}')

    t0 = time_s()
    print('slleeeeop')
    phone.sleep(2)

    # response = phone.input('Name? ')
    # phone.print(f'Name: {response} ')
    # phone.notify('notify hiii', alert=True)
    print(phone.joined_room_count)
    print(phone.client_count)
    print(phone.device_count)

    print('\n')
    print('data: ', phone.all_data())
    print('data: ', phone.all_data(data_type='grid'))
    print('latest data: ', phone.latest_data())
    print('time_stamp', to_datetime(phone.latest_data()))
    print('latest data: ', phone.latest_data(data_type='key'))
    print('broadcast data: ', phone.all_broadcast_data())
    print('broadcast data: ', phone.all_broadcast_data(data_type='grid'))
    print('latest broadcast data: ', phone.latest_broadcast_data())
    print('latest broadcast data: ', phone.latest_broadcast_data(data_type='key'))
    print('cnt device', phone.device_count)
    print('cnt room', phone.room_member_count)
    print('cnt clients', phone.client_count)
    print('cnt joined rooms', phone.joined_room_count)
    print('pointer_data', phone.pointer_data())
    print('data_list', phone.data_list)
    print('color_pointer_data', phone.color_pointer_data())
    print('grid_pointer_data', phone.grid_pointer_data())
    print('gyro_data', phone.gyro_data())
    print('acceleration_data', phone.acceleration_data())
    print('key_data', phone.key_data())
    print('latest_pointer', phone.latest_pointer())
    print('latest_color_pointer', phone.latest_color_pointer())
    print('latest_grid_pointer', phone.latest_grid_pointer())
    print('latest_gyro', phone.latest_gyro())
    print('latest_acceleration', phone.latest_acceleration())
    print('latest_key', phone.latest_key())

    # phone.sleep(2)
    # phone.disconnect()
