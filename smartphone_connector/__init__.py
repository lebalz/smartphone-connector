from __future__ import annotations
import logging
from .timings import CancleSubscription, ThreadJob
from .helpers import *
import socketio
from inspect import signature
from typing import overload, cast, Any, Union, Literal, Callable, List, Optional, Any
from copy import deepcopy
from itertools import repeat
from .types import *
from .colors import Colors
from random import randint
from contextlib import contextmanager
from pathlib import Path


def noop(x):
    pass


DATA_MSG_THRESHOLD = 5
CHARTEABLE_DATA_MSG_THRESHOLD = 120  # around 2 seconds @ 16ms


def data_threshold(data_type: str) -> int:
    if data_type == DataType.ACCELERATION or data_type == DataType.GYRO:
        return CHARTEABLE_DATA_MSG_THRESHOLD
    return DATA_MSG_THRESHOLD


class Connector:
    __initial_all_data_received = False
    __last_time_stamp: float = -1
    __last_sub_time: float = 0
    __record_data: bool = False
    data: dict[str, dict[str, list[ClientMsg]]] = DictX({})
    __current_data_frame: dict[str, DataFrame] = DictX({})
    __latest_data: DataFrame = default_data_frame()
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
    __playground_config: PlaygroundConfig = DictX({
        'width': 100,
        'height': 100,
        'shift_x': 0,
        'shift_y': 0
    })

    __sprites = []
    __lines = []

    # callback functions

    on_key: Union[Callable[[], None], Callable[[KeyMsg], None], Callable[[KeyMsg, Connector], None]] = noop
    on_f1: Union[Callable[[], None], Callable[[KeyMsgF1], None], Callable[[KeyMsgF1, Connector], None]] = noop
    on_f2: Union[Callable[[], None], Callable[[KeyMsgF2], None], Callable[[KeyMsgF2, Connector], None]] = noop
    on_f3: Union[Callable[[], None], Callable[[KeyMsgF3], None], Callable[[KeyMsgF3, Connector], None]] = noop
    on_f4: Union[Callable[[], None], Callable[[KeyMsgF4], None], Callable[[KeyMsgF4, Connector], None]] = noop

    on_pointer: Union[Callable[[Union[ColorPointer, GridPointer]], None],
                      Callable[[Union[ColorPointer, GridPointer], Connector], None]] = noop
    on_acceleration: Union[Callable[[AccMsg], None], Callable[[AccMsg, Connector], None]] = noop
    on_gyro: Union[Callable[[GyroMsg], None], Callable[[GyroMsg, Connector], None]] = noop
    on_sensor: Union[Callable[[Union[GyroMsg, AccMsg]], None],
                     Callable[[Union[GyroMsg, AccMsg], Connector], None]] = noop

    on_data: Union[Callable[[DataMsg], None], Callable[[DataMsg, Connector], None]] = noop
    on_broadcast_data: Union[Callable[[DataMsg], None], Callable[[DataMsg, Connector], None]] = noop
    on_all_data: Union[Callable[[List[DataMsg]], None], Callable[[List[DataMsg], Connector], None]] = noop
    on_device: Union[Callable[[Device], None], Callable[[Device, Connector], None]] = noop
    on_client_device: Union[Callable[[Device], None], Callable[[Device, Connector], None]] = noop
    on_devices: Union[Callable[[List[Device]], None], Callable[[List[Device], Connector], None]] = noop
    on_error: Union[Callable[[ErrorMsg], None], Callable[[ErrorMsg, Connector], None]] = noop
    on_room_joined: Union[Callable[[DeviceJoinedMsg], None], Callable[[DeviceJoinedMsg, Connector], None]] = noop
    on_room_left: Union[Callable[[DeviceLeftMsg], None], Callable[[DeviceLeftMsg, Connector], None]] = noop

    on_sprite_out: Union[Callable[[SpriteOutMsg], None], Callable[[SpriteOutMsg, Connector], None]] = noop
    on_sprite_removed: Union[Callable[[SpriteRemovedMsg], None], Callable[[SpriteRemovedMsg, Connector], None]] = noop
    on_sprite_collision: Union[Callable[[SpriteCollisionMsg], None],
                               Callable[[SpriteCollisionMsg, Connector], None]] = noop
    on_overlap_in: Union[Callable[[SpriteCollisionMsg], None],
                         Callable[[SpriteCollisionMsg, Connector], None]] = noop
    on_overlap_out: Union[Callable[[SpriteCollisionMsg], None],
                          Callable[[SpriteCollisionMsg, Connector], None]] = noop
    on_border_overlap: Union[Callable[[BorderOverlapMsg], None], Callable[[BorderOverlapMsg, Connector], None]] = noop
    on_sprite_clicked: Union[Callable[[SpriteClickedMsg], None], Callable[[SpriteClickedMsg, Connector], None]] = noop

    __on_notify_subscribers: Union[Callable[[], None], Callable[[
        DataFrame], None], Callable[[DataFrame, Connector], None]] = noop
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

    @property
    def sprites(self) -> List[Sprite]:
        return self.__sprites

    def get_sprite(self, id: str = None) -> Union[Sprite, None]:
        '''returns the sprite with the given id

        if no id is provided, the first sprite is returned

        if the sprite is not found, None is returned
        '''
        if len(self.sprites) == 0:
            return None
        if id is None:
            return self.sprites[0]
        return first(lambda s: s.id == id, self.sprites)

    get_circle = get_sprite
    get_ellipse = get_sprite
    get_square = get_sprite
    get_rectangle = get_sprite
    get_object = get_sprite

    def __init__(self, server_url: str, device_id: str):
        device_id = device_id.strip()
        self.__server_url = server_url
        self.__device_id = device_id
        self.__current_data_frame[device_id] = default_data_frame()
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

    def emit(self, event: str, data: dict = {}, **delivery_opts):
        '''
        Parameters
        ----------
        event : str
            the event name

        data : BaseSendMsg
            the data to send, fields 'time_stamp' and 'device_id' are added when they are not present

        Optional
        --------
        device_id : str
            if you want to change the receiver device_id explicitely

        broadcast : bool
            wheter to send this message to all connected devices

        unicast_to : int
            the device number to which this message is sent exclusively. When set, boradcast has no effect.
        '''
        if 'time_stamp' not in data:
            data['time_stamp'] = self.current_time_stamp

        if 'device_id' in delivery_opts:
            data['device_id'] = delivery_opts['device_id']

        if 'device_id' not in data:
            data['device_id'] = self.device_id

        if 'broadcast' in delivery_opts and delivery_opts['broadcast']:
            data['broadcast'] = True

        if 'unicast_to' in delivery_opts and type(delivery_opts['unicast_to']) == int:
            if 'broadcast' in data:
                del data['broadcast']
            data['unicast_to'] = delivery_opts['unicast_to']

        self.sio.emit(event, data)

    def send(self, data: DataMsg, **delivery_opts):
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
        self.emit(SocketEvents.NEW_DATA, data=data, **delivery_opts)

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

    def print(self, message: str, display_time: float = -1, alert: bool = False, **delivery_opts):
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
        return self.notify(message, display_time=display_time, alert=alert, **delivery_opts)

    def notify(self, message: str, display_time: float = -1, alert: bool = False, **delivery_opts):
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
            SocketEvents.NEW_DATA,
            data={
                'type': DataType.NOTIFICATION,
                'time_stamp': ts,
                'message': message,
                'alert': alert,
                'time': display_time * 1000
            },
            **delivery_opts
        )
        if not alert:
            return
        alert_msg = False
        while not alert_msg:
            self.sleep(0.01)
            alert_msg = first(lambda msg: msg['time_stamp'] == ts, self.__alerts)
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
            SocketEvents.NEW_DATA,
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
        self.emit(SocketEvents.NEW_DATA, data=data, broadcast=True)

    def unicast_to(self, data: DataMsg, device_nr: int):
        self.emit(SocketEvents.NEW_DATA, data=data, unicast_to=device_nr)

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
    def data_list(self) -> List[ClientMsg]:
        '''
        Returns
        -------
        List[ClientMsg] a list of all received messages (inlcuding messages to other device id's), ordered by time_stamp ascending (first element = oldest)
        '''
        all_data: List[ClientMsg] = []
        for dev_id in self.data:
            for dtype in self.data[dev_id]:
                all_data.extend(self.data[dev_id][dtype])
        all_data.sort(key=lambda d: d['time_stamp'])
        return all_data

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
    def all_data(self, data_type: DataType = None, device_id: str = None) -> List[ClientMsg]:
        ...

    def all_data(self, data_type: str = None, device_id: str = None) -> List[ClientMsg]:
        '''
        Returns
        -------
        List[ClientMsg] a list of received messages ordered by time_stamp ascending (first element=oldest)

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

        dev_ids = [device_id]
        if device_id == '__ALL_DEVICES__':
            dev_ids = self.data.keys()
        elif device_id not in self.data:
            return []

        all_data: List[ClientMsg] = []
        for dev_id in dev_ids:
            data_types = self.data[dev_id].keys() if data_type is None else [data_type]
            for dtype in data_types:
                if dtype in self.data[dev_id]:
                    all_data.extend(self.data[dev_id][dtype])
        all_data.sort(key=lambda d: d['time_stamp'])
        return all_data

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

    def latest_data(self, data_type: DataType = None, device_id: str = None) -> Union[ClientMsg, None]:
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
            raw = deepcopy(self.__latest_data)
        else:
            raw = deepcopy(self.__current_data_frame[device_id]) if (device_id in self.__current_data_frame) else None

        if raw is None:
            if data_type is None:
                return default('key')
            return default(data_type)

        if data_type is None:
            srted = sorted(raw.values(), reverse=True, key=lambda x: x['time_stamp'])
            return srted[0]

        if data_type in raw:
            return raw[data_type]
        return default(data_type)

    def latest_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[ColorPointer, GridPointer, None]:
        return self.latest_data(device_id=device_id, data_type='pointer')

    def latest_color_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[ColorPointer, None]:
        return self.latest_data(device_id=device_id, data_type='color_pointer')

    def latest_grid_pointer(self, device_id: str = '__ALL_DEVICES__') -> Union[GridPointer, None]:
        return self.latest_data(device_id=device_id, data_type='color_pointer')

    def latest_gyro(self, device_id: str = '__ALL_DEVICES__') -> Union[None, GyroMsg]:
        return self.latest_data(device_id=device_id, data_type=DataType.GYRO)

    def latest_acceleration(self, device_id: str = '__ALL_DEVICES__') -> Union[None, AccMsg]:
        return self.latest_data(device_id=device_id, data_type=DataType.ACCELERATION)

    def latest_key(self, device_id: str = '__ALL_DEVICES__') -> Union[None, KeyMsg]:
        return self.latest_data(device_id=device_id, data_type=DataType.KEY)

    @property
    def pointer(self) -> PointerDataMsg:
        return self.latest_pointer(device_id=self.device_id)

    @property
    def color_pointer(self) -> ColorPointerMsg:
        return self.latest_color_pointer(device_id=self.device_id)

    @property
    def grid_pointer(self) -> GridPointerMsg:
        return self.latest_grid_pointer(device_id=self.device_id)

    @property
    def gyro(self) -> GyroMsg:
        return self.latest_gyro(device_id=self.device_id)

    @property
    def acceleration(self) -> AccMsg:
        return self.latest_acceleration(device_id=self.device_id)

    @property
    def key(self) -> KeyMsg:
        return self.latest_key(device_id=self.device_id)

    def configure_playground(self,
                             width: Optional[Number] = None,
                             height: Optional[Number] = None,
                             origin_x: Optional[Number] = None,
                             origin_y: Optional[Number] = None,
                             shift_x: Optional[Number] = None,
                             shift_y: Optional[Number] = None,
                             color: Optional[Union[Colors, str]] = None,
                             images: Optional[Union[Path, str]] = None,
                             image: Optional[str] = None,
                             **delivery_opts):
        '''
        Optional
        --------
        width : Number
            width of the playground (this has no units - it defines your playground unit)

        height : Number
            height of the playground (this has no units - it defines your playground unit)

        origin_x : Number
            the x coordinate of the origin of your playground. By default it is in the lower left corner at 0, 0. You can define it in
            your playground coordinates.

        origin_y : Number
            the y coordinate of the origin of your playground. By default it is in the lower left corner at 0, 0. You can define it in
            your playground coordinates.

        shift_x : Number
            How many units should the playground be shifted horizontally? Same as the negative value of origin_x.
            Only one of both should be set

        shift_y : Number
            How many units should the playground be shifted vertically? Same as the negative value of origin_y
            Only one of both should be set

        '''
        if origin_x is not None:
            shift_x = -origin_x
        if origin_y is not None:
            shift_y = -origin_y
        raw_images = []
        if images is not None:
            images = Path(images)
            if images.is_absolute():
                pass
            else:
                rpath = Path.cwd().rglob(str(images))
                try:
                    while True:
                        new_p = next(rpath)
                        if new_p.is_dir():
                            images = new_p
                            break
                except:
                    pass

            if not images.is_dir():
                raise f'Image path {images} not found'
            for img in images.iterdir():
                if img.suffix in ['.jpg', '.jpeg', '.png', '.svg']:
                    raw = img.read_bytes()
                    name = img.stem
                    file_type = img.suffix
                    raw_images.append({'name': name, 'image': raw, 'type': file_type[1:]})

        playground_config = without_none({
                'width': width,
                'height': height,
                'shift_x': shift_x if shift_x is not None else 0,
                'shift_y': shift_y if shift_y is not None else 0,
                'color': color,
                'image': image,
                'images': raw_images
            })
        self.__playground_config = playground_config
        config = {
            'type': DataType.PLAYGROUND_CONFIG,
            'config': playground_config
        }
        self.emit(SocketEvents.NEW_DATA, config, **delivery_opts)

    @contextmanager
    def add_sprites(self, **delivery_opts):
        sprites = []

        def sprite(
                id: Optional[str] = None,
                clickable: Optional[bool] = None,
                collision_detection: Optional[bool] = None,
                color: Optional[Union[Colors, str]] = None,
                border_color: Optional[Union[Colors, str]] = None,
                direction: Optional[List[Number]] = None,
                distance: Optional[Number] = None,
                form: Optional[Union[SpriteForm, Literal['round', 'rectangle']]] = None,
                height: Optional[Number] = None,
                pos_x: Optional[Number] = None,
                pos_y: Optional[Number] = None,
                size: Optional[Number] = None,
                radius: Optional[Number] = None,
                anchor: Optional[Tuple[Number, Number]] = None,
                reset_time: Optional[Number] = None,
                speed: Optional[Number] = None,
                text: Optional[str] = None,
                font_color: Optional[str] = None,
                font_size: Optional[Number] = None,
                image: Optional[str] = None,
                time_span: Optional[Number] = None,
                width: Optional[Number] = None,
                rotate: Optional[Number] = None,
                z_index: Optional[int] = None,
                **rest) -> str:
            '''
            Optional
            --------
            id : str
                unique id. When already present, this sprite will be updated.

            form : 'round' | 'rectangle'
                the form of the sprite

            width : Number
                the width of the sprite in playground units

            height : Number
                the height of the sprite in playground units

            pos_x : Number
                the x position in playground units

            pos_y : Number
                the y position in playground units

            size : Number
                set the width and height to the same size

            radius : Number
                set the width and height to 2 * radius

            anchor : Tuple[Number, Number]
                the anchor (center) of the sprite: range from 0 (left/bottom) to 1 (right/top)

            color : str
                the color of the sprite

            clickable : bool
                wheter an event is delivered when the sprite is clicked

            collision_detection : bool
                wheter to report collisions with other sprites or not. Collision-Detection can be costly,
                so use it with care.

            direction : [x: Number, y: Number]
                the direction of the sprite. In combination with a speed value, the sprite will be advanced
                for each display refresh in this direction.

            distance : Number
                the sprite will disappear after the given distance (in auto-movement mode) is reached.

            reset_time : bool
                wheter to reset the start time on an update. Resets the time_span or distance
                for auto-movement sprites.

            speed : Number
                makes a sprite auto-movable.

            text : str
                the text that is displayed on the sprite.

            image : str
                name of the image to be displayed. The image must be set when the playground is configured. No file ending expected.

            rotate : Number
                degrees to rotate the sprite clockwise 

            time_span : Number
                the time a sprite lives
            '''
            if size is not None:
                width = size
                height = size

            if radius is not None:
                width = radius * 2
                height = radius * 2

            next_id = id if id is not None else f'sprite{randint(10000, 99999)}'
            s = {
                'id': next_id,
                'clickable': clickable,
                'collision_detection': collision_detection,
                'color': color,
                'border_color': border_color,
                'direction': direction,
                'distance': distance,
                'form': form,
                'height': height,
                'pos_x': pos_x,
                'pos_y': pos_y,
                'anchor': anchor,
                'reset_time': reset_time,
                'speed': speed,
                'text': text,
                'font_color': font_color,
                'font_size': font_size,
                'image': image,
                'rotate': rotate,
                'time_span': time_span,
                'z_index': z_index,
                'width': width
            }
            sprites.append(without_none(s))
            return next_id

        try:
            yield sprite
        except:
            sprites = []
            raise
        else:
            for s in sprites:
                to_update = first(lambda spr: spr['id'] == s['id'], self.__sprites)
                if to_update is not None:
                    to_update.update(s)
                else:
                    self.__sprites.append(DictX(s))
            self.emit(
                SocketEvents.NEW_DATA,
                {
                    'type': DataType.SPRITES,
                    'sprites': sprites
                },
                **delivery_opts
            )

    update_sprites = add_sprites
    add_objects = add_sprites
    update_objects = add_sprites

    def add_circle(
            self,
            pos_x: Optional[Number] = None,
            pos_y: Optional[Number] = None,
            radius: Optional[Number] = None,
            color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
            id: Optional[str] = None,
            anchor: Optional[Tuple[Number, Number]] = None,
            clickable: Optional[bool] = None,
            collision_detection: Optional[bool] = None,
            direction: Optional[List[Number]] = None,
            distance: Optional[Number] = None,
            reset_time: Optional[Number] = None,
            speed: Optional[Number] = None,
            text: Optional[str] = None,
            font_color: Optional[str] = None,
            font_size: Optional[Number] = None,
            image: Optional[str] = None,
            time_span: Optional[Number] = None,
            rotate: Optional[Number] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        '''
        Optional
        --------
        id : str
            unique id. When already present, this sprite will be updated.

        radius : Number
            the width of the circle in playground units

        pos_x : Number
            the x position in playground units

        pos_y : Number
            the y position in playground units

        anchor : Tuple[Number, Number]
            the anchor (center) of the circle: range from 0 (left/bottom) to 1 (right/top)

        color : str
            the color of the circle

        clickable : bool
            wheter an event is delivered when the circle is clicked

        collision_detection : bool
            wheter to report collisions with other circles or not. Collision-Detection can be costly,
            so use it with care.

        direction : [x: Number, y: Number]
            the direction of the circle. In combination with a speed value, the circle will be advanced
            for each display refresh in this direction.

        distance : Number
            the circle will disappear after the given distance (in auto-movement mode) is reached.

        reset_time : bool
            wheter to reset the start time on an update. Resets the time_span or distance
            for auto-movement circles.

        speed : Number
            makes a circle auto-movable.

        text : str
            the text that is displayed on the circle.

        image : str
            name of the image to be displayed. The image must be set when the playground is configured. No file ending expected.

        rotate : Number
            degrees to rotate the circle clockwise

        time_span : Number
            the time a circle lives
        '''
        return self.add_sprite(
            id=id,
            form='round',
            clickable=clickable,
            collision_detection=collision_detection,
            color=color,
            direction=direction,
            distance=distance,
            height=radius * 2 if radius is not None else None,
            width=radius * 2 if radius is not None else None,
            pos_x=pos_x,
            pos_y=pos_y,
            anchor=anchor,
            reset_time=reset_time,
            speed=speed,
            text=text,
            image=image,
            time_span=time_span,
            rotate=rotate,
            border_color=border_color,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            **delivery_opts
        )

    update_circle = add_circle

    def add_ellipse(
            self,
            pos_x: Optional[Number] = None,
            pos_y: Optional[Number] = None,
            height: Optional[Number] = None,
            width: Optional[Number] = None,
            color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
            id: Optional[str] = None,
            anchor: Optional[Tuple[Number, Number]] = None,
            clickable: Optional[bool] = None,
            collision_detection: Optional[bool] = None,
            direction: Optional[List[Number]] = None,
            distance: Optional[Number] = None,
            reset_time: Optional[Number] = None,
            speed: Optional[Number] = None,
            text: Optional[str] = None,
            font_color: Optional[str] = None,
            font_size: Optional[Number] = None,
            image: Optional[str] = None,
            time_span: Optional[Number] = None,
            rotate: Optional[Number] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        '''
        Optional
        --------
        id : str
            unique id. When already present, this sprite will be updated.

        width : Number
            the width of the ellipse in playground units

        height : Number
            the height of the ellipse in playground units

        pos_x : Number
            the x position in playground units

        pos_y : Number
            the y position in playground units

        anchor : Tuple[Number, Number]
            the anchor (center) of the ellipse: range from 0 (left/bottom) to 1 (right/top)

        color : str
            the color of the ellipse

        clickable : bool
            wheter an event is delivered when the ellipse is clicked

        collision_detection : bool
            wheter to report collisions with other ellipses or not. Collision-Detection can be costly,
            so use it with care.

        direction : [x: Number, y: Number]
            the direction of the ellipse. In combination with a speed value, the ellipse will be advanced
            for each display refresh in this direction.

        distance : Number
            the ellipse will disappear after the given distance (in auto-movement mode) is reached.

        reset_time : bool
            wheter to reset the start time on an update. Resets the time_span or distance
            for auto-movement ellipses.

        speed : Number
            makes a ellipse auto-movable.

        text : str
            the text that is displayed on the ellipse.

        image : str
            name of the image to be displayed. The image must be set when the playground is configured. No file ending expected.

        rotate : Number
            degrees to rotate the ellipse clockwise

        time_span : Number
            the time a ellipse lives
        '''
        return self.add_sprite(
            id=id,
            form='round',
            clickable=clickable,
            collision_detection=collision_detection,
            color=color,
            direction=direction,
            distance=distance,
            height=height,
            width=width,
            pos_x=pos_x,
            pos_y=pos_y,
            anchor=anchor,
            reset_time=reset_time,
            speed=speed,
            text=text,
            image=image,
            time_span=time_span,
            rotate=rotate,
            border_color=border_color,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            **delivery_opts
        )
    update_ellips = add_ellipse

    def add_square(
            self,
            pos_x: Number = None,
            pos_y: Number = None,
            size: Number = None,
            color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
            anchor: Optional[Tuple[Number, Number]] = None,
            id: Optional[str] = None,
            clickable: Optional[bool] = None,
            collision_detection: Optional[bool] = None,
            direction: Optional[List[Number]] = None,
            distance: Optional[Number] = None,
            reset_time: Optional[Number] = None,
            speed: Optional[Number] = None,
            text: Optional[str] = None,
            font_color: Optional[str] = None,
            font_size: Optional[Number] = None,
            image: Optional[str] = None,
            time_span: Optional[Number] = None,
            rotate: Optional[Number] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        '''
        Optional
        --------
        id : str
            unique id. When already present, this square will be updated.

        size : Number
            the size of the square in playground units

        pos_x : Number
            the x position in playground units

        pos_y : Number
            the y position in playground units

        anchor : Tuple[Number, Number]
            the anchor (center) of the square: range from 0 (left/bottom) to 1 (right/top)

        color : str
            the color of the square

        clickable : bool
            wheter an event is delivered when the square is clicked

        collision_detection : bool
            wheter to report collisions with other squares or not. Collision-Detection can be costly,
            so use it with care.

        direction : [x: Number, y: Number]
            the direction of the square. In combination with a speed value, the square will be advanced
            for each display refresh in this direction.

        distance : Number
            the square will disappear after the given distance (in auto-movement mode) is reached.

        reset_time : bool
            wheter to reset the start time on an update. Resets the time_span or distance
            for auto-movement squares.

        speed : Number
            makes a square auto-movable.

        text : str
            the text that is displayed on the square.

        image : str
            name of the image to be displayed. The image must be set when the playground is configured. No file ending expected.

        rotate : Number
            degrees to rotate the square clockwise

        time_span : Number
            the time a square lives
        '''
        return self.add_sprite(
            id=id,
            form='rectangle',
            height=size,
            width=size,
            clickable=clickable,
            collision_detection=collision_detection,
            color=color,
            direction=direction,
            distance=distance,
            pos_x=pos_x,
            pos_y=pos_y,
            anchor=anchor,
            reset_time=reset_time,
            speed=speed,
            text=text,
            image=image,
            time_span=time_span,
            rotate=rotate,
            border_color=border_color,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            **delivery_opts
        )

    update_square = add_square

    def add_rectangle(
            self,
            pos_x: Number = None,
            pos_y: Number = None,
            width: Number = None,
            height: Number = None,
            color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
            anchor: Optional[Tuple[Number, Number]] = None,
            id: Optional[str] = None,
            clickable: Optional[bool] = None,
            collision_detection: Optional[bool] = None,
            direction: Optional[List[Number]] = None,
            distance: Optional[Number] = None,
            reset_time: Optional[Number] = None,
            speed: Optional[Number] = None,
            text: Optional[str] = None,
            font_color: Optional[str] = None,
            font_size: Optional[Number] = None,
            image: Optional[str] = None,
            time_span: Optional[Number] = None,
            rotate: Optional[Number] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        '''
        Optional
        --------
        id : str
            unique id. When already present, this rectangle will be updated.

        width : Number
            the width of the rectangle in playground units

        height : Number
            the height of the rectangle in playground units

        pos_x : Number
            the x position in playground units

        pos_y : Number
            the y position in playground units

        anchor : Tuple[Number, Number]
            the anchor (center) of the rectangle: range from 0 (left/bottom) to 1 (right/top)

        color : str
            the color of the rectangle

        clickable : bool
            wheter an event is delivered when the rectangle is clicked

        collision_detection : bool
            wheter to report collisions with other rectangles or not. Collision-Detection can be costly,
            so use it with care.

        direction : [x: Number, y: Number]
            the direction of the rectangle. In combination with a speed value, the rectangle will be advanced
            for each display refresh in this direction.

        distance : Number
            the rectangle will disappear after the given distance (in auto-movement mode) is reached.

        reset_time : bool
            wheter to reset the start time on an update. Resets the time_span or distance
            for auto-movement rectangles.

        speed : Number
            makes a rectangle auto-movable.

        text : str
            the text that is displayed on the rectangle.

        image : str
            name of the image to be displayed. The image must be set when the playground is configured. No file ending expected.

        rotate : Number
            degrees to rotate the rectangle clockwise

        time_span : Number
            the time a rectangle lives
        '''
        return self.add_sprite(
            id=id,
            form='rectangle',
            height=height,
            width=width,
            clickable=clickable,
            collision_detection=collision_detection,
            color=color,
            direction=direction,
            distance=distance,
            pos_x=pos_x,
            pos_y=pos_y,
            anchor=anchor,
            reset_time=reset_time,
            speed=speed,
            text=text,
            image=image,
            time_span=time_span,
            rotate=rotate,
            border_color=border_color,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            **delivery_opts
        )

    update_rectangle = add_rectangle

    def add_text(
            self,
            text: str,
            pos_x: Optional[Number] = None,
            pos_y: Optional[Number] = None,
            height: Optional[Number] = None,
            background_color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
            font_color: Optional[str] = None,
            font_size: Optional[Number] = None,
            id: Optional[str] = None,
            anchor: Optional[Tuple[Number, Number]] = None,
            clickable: Optional[bool] = None,
            collision_detection: Optional[bool] = None,
            direction: Optional[List[Number]] = None,
            distance: Optional[Number] = None,
            reset_time: Optional[Number] = None,
            speed: Optional[Number] = None,
            image: Optional[str] = None,
            time_span: Optional[Number] = None,
            rotate: Optional[Number] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        config = DictX({'width': 100, 'height': 100})
        config.update(without_none(self.__playground_config))
        if height is None:
            height = config.height / 20
        text_len = len(text)
        width = text_len * (height * config.height / config.width) / 4

        return self.add_sprite(
            id=id,
            form='rectangle',
            height=height,
            width=width,
            clickable=clickable,
            collision_detection=collision_detection,
            color=background_color,
            direction=direction,
            distance=distance,
            pos_x=pos_x,
            pos_y=pos_y,
            anchor=anchor,
            reset_time=reset_time,
            speed=speed,
            text=text,
            image=image,
            time_span=time_span,
            rotate=rotate,
            border_color=border_color,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            **delivery_opts
        )

    update_text = add_text

    def add_sprite(
            self,
            id: Optional[str] = None,
            clickable: Optional[bool] = None,
            collision_detection: Optional[bool] = None,
            color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
            direction: Optional[List[Number]] = None,
            distance: Optional[Number] = None,
            form: Optional[Union[SpriteForm, Literal['round', 'rectangle']]] = None,
            height: Optional[Number] = None,
            pos_x: Optional[Number] = None,
            pos_y: Optional[Number] = None,
            anchor: Optional[Tuple[Number, Number]] = None,
            reset_time: Optional[Number] = None,
            speed: Optional[Number] = None,
            text: Optional[str] = None,
            font_color: Optional[str] = None,
            font_size: Optional[Number] = None,
            image: Optional[str] = None,
            time_span: Optional[Number] = None,
            width: Optional[Number] = None,
            rotate: Optional[Number] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        '''
        Optional
        --------
        id : str
            unique id. When already present, this sprite will be updated.

        form : 'round' | 'rectangle'
            the form of the sprite

        width : Number
            the width of the sprite in playground units

        height : Number
            the height of the sprite in playground units

        pos_x : Number
            the x position in playground units

        pos_y : Number
            the y position in playground units

        anchor : Tuple[Number, Number]
            the anchor (center) of the sprite: range from 0 (left/bottom) to 1 (right/top)

        color : str
            the color of the sprite

        clickable : bool
            wheter an event is delivered when the sprite is clicked

        collision_detection : bool
            wheter to report collisions with other sprites or not. Collision-Detection can be costly,
            so use it with care.

        direction : [x: Number, y: Number]
            the direction of the sprite. In combination with a speed value, the sprite will be advanced
            for each display refresh in this direction.

        distance : Number
            the sprite will disappear after the given distance (in auto-movement mode) is reached.

        reset_time : bool
            wheter to reset the start time on an update. Resets the time_span or distance
            for auto-movement sprites.

        speed : Number
            makes a sprite auto-movable.

        text : str
            the text that is displayed on the sprite.

        image : str
            name of the image to be displayed. The image must be set when the playground is configured. No file ending expected.

        rotate : Number
            degrees to rotate the sprite clockwise

        time_span : Number
            the time a sprite lives

        z_index : int
            set a custom z_index for the div
        '''
        sprite = {
            'id': id if id is not None else f'sprite{randint(10000, 99999)}',
            'clickable': clickable,
            'collision_detection': collision_detection,
            'color': color,
            'border_color': border_color,
            'direction': direction,
            'distance': distance,
            'form': form,
            'height': height,
            'pos_x': pos_x,
            'pos_y': pos_y,
            'anchor': anchor,
            'reset_time': reset_time,
            'speed': speed,
            'text': text,
            'font_color': font_color,
            'font_size': font_size,
            'rotate': rotate,
            'image': image,
            'time_span': time_span,
            'width': width,
            'z_index': z_index
        }
        sprite = without_none(sprite)
        to_update = first(lambda s: s['id'] == sprite['id'], self.__sprites)
        if to_update is not None:
            to_update.update(sprite)
        else:
            self.__sprites.append(DictX(sprite))
        self.emit(
            SocketEvents.NEW_DATA,
            {
                'type': DataType.SPRITE,
                'sprite': sprite
            },
            **delivery_opts
        )
        return sprite['id']

    def clear_playground(self, **delivery_opts):
        self.__sprites = []
        self.emit(
            SocketEvents.NEW_DATA,
            {
                'type': DataType.CLEAR_PLAYGROUND
            }
        )
        self.sleep(0.2)

    def remove_sprite(self, sprite_id: str, **delivery_opts):
        to_remove = first(lambda s: s.id == sprite_id, self.__sprites)
        if to_remove is not None:
            self.__sprites.remove(to_remove)

        self.emit(
            SocketEvents.NEW_DATA,
            {
                'type': DataType.REMOVE_SPRITE,
                'id': sprite_id
            },
            **delivery_opts
        )

    remove_object = remove_sprite

    update_sprite = add_sprite

    def add_line(
            self,
            x1: Number,
            y1: Number,
            x2: Number,
            y2: Number,
            line_width: Optional[Number] = None,
            color: Optional[Union[Colors, str]] = None,
            id: Optional[str] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        '''Adds a line to the playground

        Parameters
        ----------

        x1 : Number
            start position x coordinate

        y1 : Number
            start position y coordinate

        x2 : Number
            end position x coordinate

        y2 : Number
            end position y coordinate

        Optional
        --------
        color : Colors, str
            color of the line

        line_width : Number
            width of the line stroke in playground size

        id : string
            the id of the line - can be used to update or remove the line later

        Returns
        -------
        str : the id of the added line
        '''
        line = {
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'line_width': line_width,
            'color': color,
            'z_index': z_index,
            'id': id if id is not None else f'line{randint(10000, 99999)}'
        }

        line = without_none(line)
        to_update = first(lambda s: s['id'] == line['id'], self.__lines)
        if to_update is not None:
            to_update.update(line)
        else:
            self.__lines.append(DictX(line))

        self.emit(
            SocketEvents.NEW_DATA,
            {
                'type': DataType.LINE,
                'line': line
            },
            **delivery_opts
        )
        return line['id']

    def update_line(
            self,
            id: str,
            x1: Optional[Number] = None,
            y1: Optional[Number] = None,
            x2: Optional[Number] = None,
            y2: Optional[Number] = None,
            line_width: Optional[Number] = None,
            color: Optional[Union[Colors, str]] = None,
            z_index: Optional[int] = None,
            **delivery_opts) -> str:
        '''Updates a line already added to the playground

        Optional
        --------
        x1 : Number
            start position x coordinate

        y1 : Number
            start position y coordinate

        x2 : Number
            end position x coordinate

        y2 : Number
            end position y coordinate

        color : Colors, str
            color of the line

        line_width : Number
            width of the line stroke in playground size

        id : string
            the id of the line - can be used to update or remove the line later

        Returns
        -------
        str : the id of the updated line
        '''
        return self.add_line(
            id=id,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            line_width=line_width,
            color=color,
            z_index=z_index,
            **delivery_opts
        )

    @contextmanager
    def add_lines(self, **delivery_opts):
        lines = []

        def line(
                x1: Number = None,
                y1: Number = None,
                x2: Number = None,
                y2: Number = None,
                line_width: Optional[Number] = None,
                color: Optional[Union[Colors, str]] = None,
                id: Optional[str] = None,
                z_index: Optional[int] = None) -> str:
            '''Adds or updates a line to the playground

            Parameters
            ----------

            x1 : Number
                start position x coordinate

            y1 : Number
                start position y coordinate

            x2 : Number
                end position x coordinate

            y2 : Number
                end position y coordinate

            Optional
            --------
            color : Colors, str
                color of the line

            line_width : Number
                width of the line stroke in playground size

            id : string
                the id of the line - can be used to update or remove the line later

            Returns
            -------
            str : the id of the added line
            '''
            l = {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'line_width': line_width,
                'color': color,
                'z_index': z_index,
                'id': id if id is not None else f'line{randint(10000, 99999)}'
            }
            lines.append(without_none(l))
            return l['id']

        try:
            yield line
        except:
            lines = []
            raise
        else:
            for l in lines:
                to_update = first(lambda ln: ln['id'] == l['id'], self.__lines)
                if to_update is not None:
                    to_update.update(l)
                else:
                    self.__lines.append(DictX(l))
            self.emit(
                SocketEvents.NEW_DATA,
                {
                    'type': DataType.LINES,
                    'lines': lines
                },
                **delivery_opts
            )
    update_lines = add_lines

    def remove_line(self, line_id: str, **delivery_opts):
        '''removes the line with the given id'''
        to_remove = first(lambda s: s.id == line_id, self.__lines)
        if to_remove is not None:
            self.__lines.remove(to_remove)

        self.emit(
            SocketEvents.NEW_DATA,
            {
                'type': DataType.REMOVE_LINE,
                'id': line_id
            },
            **delivery_opts
        )

    @property
    def get_grid(self) -> List[List[CssColorType]]:
        '''
        returns a copy of the last sent grid. Changes on the returned grid will not have an effect.
        '''
        return deepcopy(self.__get_grid)

    @property
    def __get_grid(self) -> List[List[CssColorType]]:
        '''
        returns the internal grid (no deep copy!)
        '''
        grid = self.__last_sent_grid['grid']
        is_2d = len(grid) > 0 and type(grid[0]) != str and hasattr(grid[0], "__getitem__")
        if is_2d:
            return grid
        return [grid]

    def get_grid_at(self, row: Optional[int] = None, column: Optional[int] = None, cell_number: Optional[int] = None) -> Optional[CssColorType]:
        grid = self.__get_grid
        if cell_number is not None:
            row = (cell_number - 1) // len(grid[0])
            column = (cell_number - 1) % len(grid[0])
        elif row is None or column is None:
            return None

        if len(grid) <= row:
            return None
        if len(grid[row]) <= column:
            return None
        return grid[row][column]

    def update_cell(self, row: Optional[int] = None, column: Optional[int] = None, color: Optional[CssColorType] = None, cell_number: Optional[int] = None, base_color: Optional[BaseColor] = None, **delivery_opts):
        '''
        sets the color of the current grid at the given row and column or at the given cell_number

        Optional
        ----------
        row : int
            row of the cell

        column : int
            column of the cell

        cell_number : int
            cells are enumerated from left to right, starting with "1" on cell top left

        color : CssColorType
            color to set

        base_color : CssColorType
            base color when numeric color values are set
        '''
        self.update_grid(row=row, column=column, color=color, cell_number=cell_number,
                         base_color=base_color, **delivery_opts)

    def set_grid_at(self, row: Optional[int] = None, column: Optional[int] = None, color: Optional[CssColorType] = None, cell_number: Optional[int] = None, base_color: Optional[BaseColor] = None, **delivery_opts):
        '''
        sets the color of the current grid at the given row and column or at the given cell_number

        Optional
        ----------
        row : int
            row of the cell

        column : int
            column of the cell

        cell_number : int
            cells are enumerated from left to right, starting with "1" on cell top left

        color : CssColorType
            color to set

        base_color : CssColorType
            base color when numeric color values are set
        '''

        self.update_grid(row=row, column=column, color=color, cell_number=cell_number,
                         base_color=base_color, **delivery_opts)

    def update_grid(self, row: Optional[int] = None, column: Optional[int] = None, color: Optional[CssColorType] = None, cell_number: Optional[int] = None, base_color: Optional[BaseColor] = None, enumerate: bool = None, **delivery_opts):
        '''
        sets the color of the current grid at the given row and column or at the given cell_number

        Optional
        ----------
        row : int
            row of the cell

        column : int
            column of the cell

        cell_number : int
            cells are enumerated from left to right, starting with "1" on cell top left

        color : CssColorType
            color to set

        base_color : CssColorType
            base color when numeric color values are set

        enumerate : bool
            wheter to enumerate grid cells or not
        '''

        grid_msg = {
            'type': 'grid_update',
            'row': row,
            'column': column,
            'number': cell_number,
            'color': color,
            'base_color': base_color,
            'enumerate': enumerate,
            'time_stamp': self.current_time_stamp
        }
        self.__set_local_grid_at(row=row, column=column, color=color, cell_number=cell_number)
        self.emit(
            SocketEvents.NEW_DATA,
            without_none(grid_msg),
            **delivery_opts
        )

    def set_image(self, image: Union[List[str], str], base_color: Union[BaseColor] = None, enumerate: bool = None, **delivery_opts):
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
        return self.set_grid(image, base_color=base_color, enumerate=enumerate, **delivery_opts)

    def reset_grid(self, **delivery_opts):
        self.set_grid([['white']], **delivery_opts)

    def setup_grid(self, rows: int, columns: int, color: Optional[CssColorType] = None, enumerate: Optional[bool] = None, base_color: Optional[BaseColor] = None, ** delivery_opts):
        grid = []
        colr = color if color is not None else 0
        for _ in range(rows):
            row = []
            for _ in range(columns):
                row.append(colr)
            grid.append(row)
        if base_color is None:
            base_color = 'white'
        self.set_grid(grid, enumerate=enumerate, base_color=base_color, **delivery_opts)

    def __set_local_grid_at(self, row: Optional[int] = None, column: Optional[int] = None, color: Optional[CssColorType] = None, cell_number: Optional[int] = None):
        if row is None and cell_number is None:
            return

        grid = self.get_grid

        rows = len(grid)
        if rows == 0:
            grid = [[]]

        col_count = len(grid[0]) if grid[0] is not None else 0
        if cell_number is not None:
            col_cnt = col_count
            if col_cnt == 0:
                col_cnt = 1
            cell_number = cell_number - 1
            row = cell_number // col_cnt
            column = cell_number % col_cnt

        while len(grid[0]) <= column:
            for col in grid:
                col.append(0)
        while len(grid) <= row:
            grid.append(list(repeat(0, len(grid[0]))))

        grid[row][column] = color
        self.__last_sent_grid.grid = grid

    def __set_local_grid(self, grid: ColorGrid):
        raw_grid = deepcopy(grid)
        if isinstance(raw_grid, str):
            raw_grid = lines_to_grid(image_to_lines(raw_grid))
        if isinstance(raw_grid, int):
            raw_grid = [[raw_grid]]
        if len(raw_grid) < 1:
            return
        if isinstance(raw_grid[0], str):
            raw_grid = lines_to_grid(cast(List[str], raw_grid))

        self.__last_sent_grid.grid = cast(List[List[CssColorType]], list(raw_grid))

    def set_grid(self, grid: ColorGrid, base_color: BaseColor = None, enumerate: bool = None, **delivery_opts):
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
            'enumerate': enumerate,
            'time_stamp': self.current_time_stamp
        }
        self.emit(
            SocketEvents.NEW_DATA,
            without_none(grid_msg),
            **delivery_opts
        )

    def set_color(self, color: CssColorType, **delivery_opts):
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
            SocketEvents.NEW_DATA,
            {
                'type': 'color',
                'color': color
            },
            **delivery_opts
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
        clbk = cast(Callable, self.__on_notify_subscribers)

        if arg_count == 0:
            return clbk()

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
        self.sleep(0.2)
        self.sio.disconnect()

    def join_room(self, device_id: str):
        self.emit(SocketEvents.JOIN_ROOM, DictX({'room': device_id}))

    def leave_room(self, device_id: str):
        self.emit(SocketEvents.LEAVE_ROOM, DictX({'room': device_id}))

    def start_recording(self):
        self.clean_data()
        self.__record_data = True

    def stop_recording(self):
        self.__record_data = False

    @property
    def is_recording(self):
        return self.__record_data

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

    def __update_current_data_frame(self, data: dict):
        if data['device_id'] not in self.__current_data_frame:
            self.__current_data_frame[data['device_id']] = default_data_frame()
        if data['type'] in ['key', 'acceleration', 'gyro']:
            self.__current_data_frame[data['device_id']][data['type']] = data
        elif data['type'] == DataType.POINTER:
            contex = data['context']
            tkey = f'{contex}_pointer'
            self.__current_data_frame[data['device_id']][tkey] = data

    def __update_latest_data(self, data: dict):
        self.__latest_data[data['type']] = data
        if data['type'] == DataType.POINTER:
            contex = data['context']
            tkey = f'{contex}_pointer'
            self.__latest_data[tkey] = data

    def __on_new_data(self, data: dict):
        data = DictX(data)
        if 'device_id' not in data:
            return

        if data['device_id'] not in self.data:
            self.data[data['device_id']] = DictX({})

        if data['type'] not in self.data[data['device_id']]:
            self.data[data['device_id']][data['type']] = []

        data_len = len(self.data[data['device_id']][data['type']])
        if not self.__record_data and (data_len >= data_threshold(data['type'])):
            self.data[data['device_id']][data['type']].pop(0)

        self.data[data['device_id']][data['type']].append(cast(ClientMsg, data))

        self.__update_current_data_frame(data)
        self.__update_latest_data(data)

        if self.__main_thread_blocked:
            self.__blocked_data_msgs.append(cast(DataMsg, data))
        else:
            self.__distribute_new_data_callback(cast(DataMsg, data))

    def __distribute_new_data_callback(self, data: DataMsg):
        if 'type' in data:
            if data['type'] in [DataType.ACCELERATION, DataType.GYRO]:
                self.__callback('on_sensor', data)

            if data['type'] == DataType.KEY:
                self.__callback('on_key', data)
                if data['key'] == 'F1':
                    self.__callback('on_f1', data)
                elif data['key'] == 'F2':
                    self.__callback('on_f2', data)
                elif data['key'] == 'F3':
                    self.__callback('on_f3', data)
                elif data['key'] == 'F4':
                    self.__callback('on_f4', data)
            elif data['type'] == DataType.ACCELERATION:
                self.__callback('on_acceleration', data)
            elif data['type'] == DataType.GYRO:
                self.__callback('on_gyro', data)
            elif data['type'] == DataType.POINTER:
                self.__callback('on_pointer', data)
            elif data['type'] == DataType.INPUT_RESPONSE:
                self.__responses.append(cast(InputResponseMsg, data))
            elif data['type'] == DataType.ALERT_CONFIRM:
                self.__alerts.append(cast(AlertConfirmMsg, data))
            elif data['type'] == DataType.SPRITE_OUT:
                sprite = self.get_sprite(data['id'])
                if sprite is not None:
                    data.update({
                        'sprite': deepcopy(sprite)
                    })
                self.__callback('on_sprite_out', data)
            elif data['type'] == DataType.SPRITE_REMOVED:
                sprite = self.get_sprite(data['id'])
                if sprite is not None:
                    data.update({'sprite': deepcopy(sprite)})
                    self.__sprites.remove(sprite)
                self.__callback('on_sprite_removed', data)
            elif data['type'] == DataType.SPRITE_COLLISION:
                if len(data['sprites']) == 2:
                    try:
                        s1 = self.get_sprite(data['sprites'][0]['id'])
                        s2 = self.get_sprite(data['sprites'][0]['id'])
                        if s1 is not None:
                            data['sprites'][0] = deepcopy(s1)
                        else:
                            data['sprites'][0] = DictX(data['sprites'][0])

                        if s2 is not None:
                            data['sprites'][1] = deepcopy(s2)
                        else:
                            data['sprites'][1] = DictX(data['sprites'][1])
                    except:
                        data['sprites'] = list(map(lambda s: DictX(s), data['sprites']))
                else:
                    data['sprites'] = list(map(lambda s: DictX(s), data['sprites']))

                self.__callback('on_sprite_collision', data)
                if data['overlap'] == 'in':
                    self.__callback('on_overlap_in', data)
                elif data['overlap'] == 'out':
                    self.__callback('on_overlap_out', data)

            elif data['type'] == DataType.BORDER_OVERLAP:
                original = self.get_sprite(data['id'])
                if original is not None:
                    data.update({'sprite': deepcopy(original)})
                self.__callback('on_border_overlap', data)
            elif data['type'] == DataType.SPRITE_CLICKED:
                self.__callback('on_sprite_clicked', data)
            elif data['type'] == DataType.PLAYGROUND_CONFIG:
                self.__playground_config = DictX(data['config'])

        if 'broadcast' in data and data['broadcast'] and self.on_broadcast_data is not None:
            self.__callback('on_broadcast_data', data)
        self.__callback('on_data', data)

    def __on_all_data(self, data: dict):
        if 'device_id' not in data:
            return
        xdata: dict[str, List[dict]] = data['all_data']
        for dtype in xdata:
            xdata[dtype] = list(map(lambda msg: DictX(msg), xdata[dtype]))

        data['all_data'] = DictX(xdata)
        self.data[data['device_id']] = data['all_data']
        if data['device_id'] == self.device_id:
            if DataType.SPRITE in data['all_data']:
                if self.__initial_all_data_received:
                    self.__sprites = list(map(lambda s: DictX(s), data['all_data'][DataType.SPRITE]))
                else:
                    for s in data['all_data'][DataType.SPRITE]:
                        if 'id' in s and self.get_sprite(s['id']) is None:
                            self.__sprites.append(DictX(s))

        self.__initial_all_data_received = True
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
