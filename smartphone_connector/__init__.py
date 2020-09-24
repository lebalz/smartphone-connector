from __future__ import annotations
import logging
from build.lib.smartphone_connector import PlaygroundConfiguration
from .timings import CancleSubscription, ThreadJob
from .helpers import *
import socketio
from inspect import signature
from typing import overload, cast, Any, Union, Literal, Callable, List, Optional, Tuple, Any, Final
from copy import deepcopy
from itertools import repeat
from dataclasses import dataclass
from .types import *


class SocketEvents:
    DEVICE: Final[str] = 'device'
    DEVICES: Final[str] = 'devices'
    ALL_DATA: Final[str] = 'all_data'
    ADD_NEW_DATA: Final[str] = 'new_data'
    NEW_DATA: Final[str] = 'new_data'
    CLEAR_DATA: Final[str] = 'clear_data'
    NEW_DEVICE: Final[str] = 'new_device'
    GET_ALL_DATA: Final[str] = 'get_all_data'
    GET_DEVICES: Final[str] = 'get_devices'
    JOIN_ROOM: Final[str] = 'join_room'
    LEAVE_ROOM: Final[str] = 'leave_room'
    ROOM_LEFT: Final[str] = 'room_left'
    ROOM_JOINED: Final[str] = 'room_joined'
    ERROR_MSG: Final[str] = 'error_msg'
    INFORMATION_MSG: Final[str] = 'information_msg'
    SET_NEW_DEVICE_NR: Final[str] = 'set_new_device_nr'


class DataType:
    KEY: Final[str] = 'key'
    GRID: Final[str] = 'grid'
    GRIDUPDATE: Final[str] = 'grid_update'
    COLOR: Final[str] = 'color'
    ACCELERATION: Final[str] = 'acceleration'
    GYRO: Final[str] = 'gyro'
    POINTER: Final[str] = 'pointer'
    NOTIFICATION: Final[str] = 'notification'
    INPUT_PROMPT: Final[str] = 'input_prompt'
    INPUTRESPONSE: Final[str] = 'input_response'
    UNKNOWN: Final[str] = 'unknown'
    ALLDATA: Final[str] = 'all_data'
    ALERTCONFIRM: Final[str] = 'alert_confirm'
    SPRITE: Final[str] = 'sprite'
    SPRITES: Final[str] = 'sprites'
    SPRITECOLLISION: Final[str] = 'sprite_collision'
    SPRITEOUT: Final[str] = 'sprite_out'
    PLAYGROUNDCONFIG: Final[str] = 'playground_config'


class INPUT_TYPE:
    TEXT: Final[str] = 'text'
    NUMBER: Final[str] = 'number'
    DATETIME: Final[str] = 'datetime'
    DATE: Final[str] = 'date'
    TIME: Final[str] = 'time'
    SELECT: Final[str] = 'select'


class Connector:
    __last_time_stamp: float = -1
    __last_sub_time: float = 0
    data: dict[str, list[ClientMsg]] = DictX({})
    __devices = {'time_stamp': time_s(), 'devices': []}
    device: Optional[Device] = None
    __server_url: str
    __device_id: str
    __info_messages: List[InformationMsg] = []
    sio: socketio.Client = socketio.Client()
    room_members: List[Device] = []
    joined_rooms: List[str]
    __main_thread_blocked: bool = False
    __blocked_data_msgs: List[DataMsg] = []
    __last_sent_grid = DictX({
        'grid': [[]],
        'unicast_to': None,
        'device_id': None,
        'broadcast': False,
        'base_color': (255, 0, 0)
    })

    __sprites = []

    # callback functions

    on_key: Union[Callable[[], None], Callable[[KeyMsg], None], Callable[[KeyMsg, Connector], None]]
    on_f1: Union[Callable[[], None], Callable[[KeyMsgF1], None], Callable[[KeyMsgF1, Connector], None]]
    on_f2: Union[Callable[[], None], Callable[[KeyMsgF2], None], Callable[[KeyMsgF2, Connector], None]]
    on_f3: Union[Callable[[], None], Callable[[KeyMsgF3], None], Callable[[KeyMsgF3, Connector], None]]
    on_f4: Union[Callable[[], None], Callable[[KeyMsgF4], None], Callable[[KeyMsgF4, Connector], None]]

    on_pointer: Union[Callable[[Union[ColorPointer, GridPointer]], None],
                      Callable[[Union[ColorPointer, GridPointer], Connector], None]]
    on_acceleration: Union[Callable[[AccMsg], None], Callable[[AccMsg, Connector], None]]
    on_gyro: Union[Callable[[GyroMsg], None], Callable[[GyroMsg, Connector], None]]
    on_sensor: Union[Callable[[Union[GyroMsg, AccMsg]], None],
                     Callable[[Union[GyroMsg, AccMsg], Connector], None]]

    on_data: Union[Callable[[DataMsg], None], Callable[[DataMsg, Connector], None]]
    on_broadcast_data: Union[Callable[[DataMsg], None], Callable[[DataMsg, Connector], None]]
    on_all_data: Union[Callable[[List[DataMsg]], None], Callable[[List[DataMsg], Connector], None]]
    on_device: Union[Callable[[Device], None], Callable[[Device, Connector], None]]
    on_client_device: Union[Callable[[Device], None], Callable[[Device, Connector], None]]
    on_devices: Union[Callable[[List[Device]], None], Callable[[List[Device], Connector], None]]
    on_error: Union[Callable[[ErrorMsg], None], Callable[[ErrorMsg, Connector], None]]
    on_room_joined: Union[Callable[[DeviceJoinedMsg], None], Callable[[DeviceJoinedMsg, Connector], None]]
    on_room_left: Union[Callable[[DeviceLeftMsg], None], Callable[[DeviceLeftMsg, Connector], None]]

    on_sprite_out: Union[Callable[[SpriteOut], None], Callable[[SpriteOut, Connector], None]]
    on_sprite_collision: Union[Callable[[SpriteCollision], None], Callable[[SpriteCollision, Connector], None]]
    __on_notify_subscribers: Union[Callable, Callable[[DataFrame], None], Callable[[DataFrame, Connector], None]]
    __subscription_job: Union[ThreadJob, CancleSubscription]

    __responses: List[InputResponseMsg] = []
    __alerts: List[AlertConfirmMsg] = []

    @ property
    def devices(self) -> List[Device]:
        return self.__devices['devices']

    @ property
    def server_url(self):
        return self.__server_url

    @ property
    def device_id(self):
        return self.__device_id

    @ property
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
        self.sio.on(SocketEvents.NEW_DATA, self.__on_new_data)
        self.sio.on(SocketEvents.ALL_DATA, self.__on_all_data)
        self.sio.on(SocketEvents.DEVICE, self.__on_device)
        self.sio.on(SocketEvents.DEVICES, self.__on_devices)
        self.sio.on(SocketEvents.ERROR_MSG, self.__on_error)
        self.sio.on(SocketEvents.INFORMATION_MSG, self.__on_information)
        self.sio.on(SocketEvents.ROOM_JOINED, self.__on_room_joined)
        self.sio.on(SocketEvents.ROOM_LEFT, self.__on_room_left)
        self.joined_rooms = [device_id]
        self.connect()

    @ property
    def client_device(self):
        return first(lambda device: device['is_client'] and device['device_id'] == self.device_id, self.devices)

    def emit(self, event: str, data: dict = {}, broadcast: bool = False, unicast_to: int = None, device_id: str = None):
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
        self.emit(SocketEvents.ADD_NEW_DATA, data=data, broadcast=broadcast, unicast_to=unicast_to)

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
            SocketEvents.ADD_NEW_DATA,
            data={
                'type': DataType.NOTIFICATION,
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

    def input(self, question: str, input_type: str = 'text', options: List[str] = None, unicast_to: int = None) -> Union[str, None]:
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

    def prompt(self, question: str, input_type: str = 'text', options: List[str] = None, unicast_to: int = None) -> Union[str, None]:
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
            options = cast(Any, options).tolist()

        if input_type == 'datetime':
            input_type = 'datetime-local'

        self.emit(
            SocketEvents.ADD_NEW_DATA,
            {
                'type': DataType.INPUT_PROMPT,
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
        self.emit(SocketEvents.ADD_NEW_DATA, data=data, broadcast=True)

    def unicast_to(self, data: DataMsg, device_nr: int):
        self.emit(SocketEvents.ADD_NEW_DATA, data=data, unicast_to=device_nr)

    def connect(self):
        if self.sio.connected:
            return
        self.sio.connect(self.server_url)
        self.__register()

    def clear_data(self):
        '''
        clears all data of this device
        '''
        self.emit(SocketEvents.CLEAR_DATA)

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
        data = flatten(list(self.data.values()))
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

    @overload
    def all_data(self, data_type: Literal['pointer'], device_id: str = None) -> Union[List[ColorPointer], List[GridPointer]]:
        ...

    @overload
    def all_data(self, data_type: Literal['gyro'], device_id: str = None) -> List[GyroMsg]:
        ...

    @overload
    def all_data(self, data_type: Literal['acceleration'], device_id: str = None) -> List[AccMsg]:
        ...

    @overload
    def all_data(self, data_type: Literal['key'], device_id: str = None) -> List[KeyMsg]:
        ...

    @overload
    def all_data(self, data_type: Literal['key'], device_id: str = None) -> List[KeyMsg]:
        ...

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
            return cast(list[DataMsg], data)

        data = filter(lambda pkg: 'type' in pkg and pkg['type'] == data_type, data)
        return cast(list[DataMsg], list(data))

    def pointer_data(self, device_id: str = '__ALL_DEVICES__') -> Union[List[ColorPointer], List[GridPointer]]:
        return self.all_data('pointer', device_id=device_id)

    def color_pointer_data(self, device_id: str = '__ALL_DEVICES__') -> List[ColorPointer]:
        data = list(filter(lambda pkg: pkg['context'] == 'color', self.pointer_data(device_id=device_id)))
        return cast(List[ColorPointer], data)

    def grid_pointer_data(self, device_id: str = '__ALL_DEVICES__') -> List[GridPointer]:
        data = list(filter(lambda pkg: pkg['context'] == 'grid', self.pointer_data(device_id=device_id)))
        return cast(List[GridPointer], data)

    def gyro_data(self, device_id: str = '__ALL_DEVICES__') -> List[GyroMsg]:
        return self.all_data('gyro', device_id=device_id)

    def acceleration_data(self, device_id: str = '__ALL_DEVICES__') -> List[AccMsg]:
        return self.all_data('acceleration', device_id=device_id)

    def key_data(self, device_id: str = '__ALL_DEVICES__') -> List[KeyMsg]:
        return self.all_data('key', device_id=device_id)

    @overload
    def latest_data(self, data_type: Literal['pointer'], device_id: str = None) -> Union[ColorPointer, GridPointer, None]:
        ...

    @overload
    def latest_data(self, data_type: Literal['gyro'], device_id: str = None) -> Union[None, GyroMsg]:
        ...

    @overload
    def latest_data(self, data_type: Literal['acceleration'], device_id: str = None) -> Union[None, AccMsg]:
        ...

    @overload
    def latest_data(self, data_type: Literal['key'], device_id: str = None) -> Union[None, KeyMsg]:
        ...

    def latest_data(self, data_type: str = None, device_id: str = None) -> Union[dict, None]:
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

    def latest_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[ColorPointer, GridPointer, None]:
        return self.latest_data('pointer', device_id=device_id)

    def latest_color_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[ColorPointer, None]:
        for pkg in reversed(self.data_list):
            has_type = 'type' in pkg and pkg['type'] == 'pointer' and pkg['context'] == 'color'
            is_device = device_id == '__ALL_DEVICES__' or ('device_id' in pkg and device_id == pkg['device_id'])

            if has_type and is_device:
                return cast(ColorPointer, pkg)

    def latest_grid_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[GridPointer, None]:
        for pkg in reversed(self.data_list):
            has_type = 'type' in pkg and pkg['type'] == 'pointer' and pkg['context'] == 'grid'
            is_device = device_id == '__ALL_DEVICES__' or ('device_id' in pkg and device_id == pkg['device_id'])

            if has_type and is_device:
                return cast(GridPointer, pkg)

    def latest_gyro(self, device_id: str = '__ALL_DEVICES__') -> Union[None, GyroMsg]:
        return self.latest_data('gyro', device_id=device_id)

    def latest_acceleration(self, device_id: str = '__ALL_DEVICES__') -> Union[None, AccMsg]:
        return self.latest_data('acceleration', device_id=device_id)

    def latest_key(self, device_id: str = '__ALL_DEVICES__') -> Union[None, KeyMsg]:
        return self.latest_data('key', device_id=device_id)

    def configure_playground(self, config: Union[dict, PlaygroundConfiguration], device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        conf = cast(PlaygroundConfigMsg, config)
        conf['type'] = 'playground_config'
        self.emit(SocketEvents.ADD_NEW_DATA, conf,
                  unicast_to=unicast_to, broadcast=broadcast, device_id=device_id)

    def add_sprites(self, sprites: List[Union[dict, Sprite]], device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        self.__sprites.extend(map(lambda sprite: DictX(sprite), sprites))
        self.emit(
            SocketEvents.ADD_NEW_DATA,
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
            SocketEvents.ADD_NEW_DATA,
            {
                'type': 'sprite',
                'sprite': sprite
            },
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    def update_sprite(self, id: str, update: Union[dict, UpdateSprite], device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        sprite = first(lambda s: s.id == id, self.__sprites)
        if sprite:
            sprite.update(update)
        update.update({
            'id': id,
            'movement': 'controlled'
        })

        self.emit(
            SocketEvents.ADD_NEW_DATA,
            {
                'type': 'sprite',
                'sprite': update
            },
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    @property
    def get_grid(self) -> List[List[Union[str, int, Tuple[R, G, B], Tuple[R, G, B, A]]]]:
        grid = self.__last_sent_grid.grid
        is_2d = len(grid) > 0 and type(grid[0]) != str and hasattr(grid[0], "__getitem__")
        if is_2d:
            return deepcopy(grid)
        return [deepcopy(grid)]

    def set_grid_at(self, row: int, column: int, color: Union[str, int, Tuple[R, G, B], Tuple[R, G, B, A]], device_id: str = None, unicast_to: int = None, broadcast: bool = False, base_color: Optional[Union[str, RgbColor]] = None):
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
        self.__last_sent_grid.grid = grid

        grid_msg = {
            'type': 'grid_update',
            'row': row,
            'column': column,
            'color': color,
            'base_color': base_color,
            'time_stamp': self.current_time_stamp
        }
        self.emit(
            SocketEvents.ADD_NEW_DATA,
            grid_msg,
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    def set_image(self, image: Union[List[str], str], device_id: str = None, unicast_to: int = None, broadcast: bool = False, base_color: Union[str, RgbColor] = None):
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
        return self.set_grid(image, device_id=device_id, unicast_to=unicast_to, broadcast=broadcast, base_color=base_color)

    def reset_grid(self, device_id: str = None, unicast_to: int = None, broadcast: bool = False):
        self.set_grid([['white']], device_id=device_id, unicast_to=unicast_to, broadcast=broadcast)

    def __set_local_grid(self, grid):
        raw_grid = deepcopy(grid)
        is_str = type(raw_grid) == str
        if is_str:
            raw_grid = list(
                map(
                    lambda line: line.strip(),
                    list(
                        filter(
                            lambda l: len(l.strip()) > 0,
                            raw_grid.splitlines(False)
                        )
                    )
                )
            )
        if len(raw_grid) < 1:
            return
        if type(raw_grid[0]) == str:
            for i in range(len(raw_grid)):
                raw_grid[i] = [*raw_grid[i]]

        is_2d = len(raw_grid) > 0 and type(raw_grid[0]) != str and hasattr(raw_grid[0], "__getitem__")
        if is_2d:
            self.__last_sent_grid.grid = list(
                map(
                    lambda row: list(
                        map(
                            lambda raw_color: raw_color,
                            row
                        )
                    ),
                    raw_grid
                )
            )
        elif len(raw_grid) > 0:
            self.__last_sent_grid.grid = list(
                map(
                    lambda raw_color: raw_color,
                    raw_grid
                )
            )

    def set_grid(self, grid: ColorGrid, device_id: str = None, unicast_to: int = None, broadcast: bool = False, base_color: Union[RgbColor, str] = None):
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
            grid = cast(Any, grid).tolist()

        self.__set_local_grid(grid)

        grid_msg = {
            'type': 'grid',
            'grid': grid,
            'base_color': base_color,
            'time_stamp': self.current_time_stamp
        }
        self.emit(
            SocketEvents.ADD_NEW_DATA,
            grid_msg,
            broadcast=broadcast,
            unicast_to=unicast_to,
            device_id=device_id
        )

    def set_color(self, color: CssColorType, device_id: str = None, unicast_to: int = None, broadcast: bool = False):
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
            SocketEvents.ADD_NEW_DATA,
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
            SocketEvents.SET_NEW_DEVICE_NR,
            {
                'time_stamp': ts,
                'new_device_nr': new_device_nr,
                'device_id': device_id or self.device_id,
                'current_device_nr': current_device_nr
            }
        )
        result_msg = None
        while result_msg is None and (time_s() - ts) < max_wait:
            result_msg = first(lambda m: m.action['time_stamp'] == ts, self.__info_messages)

            if result_msg is None:
                self.sleep(0.1)

        if result_msg is not None and result_msg['message'] == 'Success':
            return True

        time_left = max_wait - (time_s() - ts)
        if time_left > 0 and 'should_retry' in cast(dict, result_msg) and result_msg['should_retry']:
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
        data: DataFrame = DataFrame({
            'key': self.latest_key(device_id=self.__device_id) or default('key'),
            'acceleration': self.latest_acceleration(device_id=self.__device_id) or default('acceleration'),
            'gyro': self.latest_gyro(device_id=self.__device_id) or default('gyro'),
            'color_pointer': self.latest_color_pointer(device_id=self.__device_id) or default('color_pointer'),
            'grid_pointer': self.latest_grid_pointer(device_id=self.__device_id) or default('grid_pointer')
        })
        clbk = cast(Callable, self.__on_notify_subscribers)
        if arg_count == 1:
            clbk(data)
        elif arg_count == 2:
            clbk(data, self)

    def subscribe_async(self, callback: Union[Callable, Callable[[DataFrame], None], Callable[[DataFrame, Connector], None]] = None, interval: float = 0.05) -> Union[ThreadJob, CancleSubscription]:
        return self.subscribe(callback=callback, interval=interval, blocking=False)

    def set_update_interval(self, interval: float):
        return self.subscribe(interval=interval, blocking=True)

    def set_timeout(self, callback: Union[Callable, Callable[[DataFrame], None], Callable[[DataFrame, Connector], None]] = None, interval: float = 0.05, blocking=True) -> Union[None, Union[ThreadJob, CancleSubscription]]:
        return self.subscribe(callback=callback, interval=interval, blocking=blocking)

    @ overload
    def subscribe(self, callback: Union[Callable, Callable[[DataFrame], None], Callable[[DataFrame, Connector], None]] = None,
                  interval: float = 0.05, blocking=True) -> Union[ThreadJob, CancleSubscription]:
        ...

    @ overload
    def subscribe(self, callback: Union[Callable, Callable[[DataFrame], None], Callable[[DataFrame, Connector], None]] = None, interval: float = 0.05, blocking=False) -> None:
        ...

    def subscribe(self, callback: Union[Callable, Callable[[DataFrame], None], Callable[[DataFrame, Connector], None]] = None, interval: float = 0.05, blocking: bool = True) -> Union[None, Union[ThreadJob, CancleSubscription]]:
        '''
        blocked : bool wheter the main thread gets blocked or not.
        '''
        self.__on_notify_subscribers = cast(Callable, callback)
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
        self.emit(SocketEvents.JOIN_ROOM, DictX({'room': device_id}))

    def leave_room(self, device_id: str):
        self.emit(SocketEvents.LEAVE_ROOM, DictX({'room': device_id}))

    def __on_connect(self):
        logging.info('SocketIO connected')

    def __on_disconnect(self):
        logging.info('SocketIO disconnected')

    def __register(self):
        self.emit(SocketEvents.NEW_DEVICE)

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

    def __on_new_data(self, data: dict):
        data = DictX(data)
        if 'device_id' not in data:
            return

        if data['device_id'] not in self.data:
            self.data[data['device_id']] = []

        self.data[data['device_id']].append(cast(ClientMsg, data))
        if self.__main_thread_blocked:
            self.__blocked_data_msgs.append(cast(DataMsg, data))
        else:
            self.__distribute_new_data_callback(cast(DataMsg, data))

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
                self.__responses.append(cast(InputResponseMsg, data))
            if data['type'] == 'alert_confirm':
                self.__alerts.append(cast(AlertConfirmMsg, data))
            if data['type'] == 'sprite_out':
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

    def __on_all_data(self, data: dict):
        if 'device_id' not in data:
            return

        data['all_data'] = list(map(lambda pkg: DictX(pkg), data['all_data']))
        self.data[data['device_id']] = data['all_data']
        self.__callback('on_all_data', data)

    def __on_room_left(self, device: dict):
        device = DictX(device)
        if device['room'] == self.device_id:
            if device['device'] in self.room_members:
                self.room_members.remove(device['device'])
                self.__callback('on_room_left', device['device'])

        elif device['device']['device_id'] == self.device_id:
            if device['device'] in self.joined_rooms:
                self.joined_rooms.remove(device['device'])

    def __on_room_joined(self, device: dict):
        device = DictX(device)
        if device['room'] == self.device_id:
            if device['device'] not in self.room_members:
                self.room_members.append(device['device'])
                self.__callback('on_room_joined', device['device'])
        elif device['device']['device_id'] == self.device_id:
            if device['device'] not in self.joined_rooms:
                self.joined_rooms.append(device['device'])

    def __on_error(self, err: DictX):
        err = DictX(err)
        logging.warn(f'Error on Event {err.type}: {err.msg}')

        self.__callback('on_error', err)

    def __on_information(self, data: dict):
        self.__info_messages.append(cast(InformationMsg, DictX(data)))

    def __on_device(self, device: dict):
        device = DictX(device)
        if 'device_id' not in device or 'socket_id' not in device:
            return
        if self.sio.sid == device['socket_id']:
            self.device = cast(Device, device)
            self.emit(SocketEvents.GET_ALL_DATA)
            old_device_instance = first(lambda d: d['socket_id'] == device['socket_id'], self.room_members)
            if old_device_instance:
                self.room_members.remove(old_device_instance)
            self.room_members.append(cast(Device, device))
            self.__callback('on_device', device)

    def __on_devices(self, data: dict):
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
    phone.disconnect()
