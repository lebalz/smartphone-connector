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
import sys


def noop(x):
    pass


DATA_MSG_THRESHOLD = 5
CHARTEABLE_DATA_MSG_THRESHOLD = 120  # around 2 seconds @ 16ms


def data_threshold(data_type: str) -> int:
    if data_type == DataType.ACCELERATION or data_type == DataType.GYRO:
        return CHARTEABLE_DATA_MSG_THRESHOLD
    return DATA_MSG_THRESHOLD


DEFAULT_PLAYGROUND_CONFIG = DictX({
        'width': 100,
        'height': 100,
        'shift_x': 0,
        'shift_y': 0
    })


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
    __playground_config: PlaygroundConfig = deepcopy(DEFAULT_PLAYGROUND_CONFIG)

    __sprites = []
    __lines = []
    __reportings: DictX

    # callback functions

    on_key: OnKeySignature = noop
    on_f1: OnF1Signature = noop
    on_f2: OnF2Signature = noop
    on_f3: OnF3Signature = noop
    on_f4: OnF4Signature = noop
    on_pointer: OnPointerSignature = noop
    on_acceleration: OnAccelerationSignature = noop
    on_gyro: OnGyroSignature = noop
    on_sensor: OnSensorSignature = noop
    on_data: OnDataSignature = noop
    on_broadcast_data: OnBroadcastDataSignature = noop
    on_all_data: OnAll_dataSignature = noop
    on_device: OnDeviceSignature = noop
    on_client_device: OnClientDeviceSignature = noop
    on_devices: OnDevicesSignature = noop
    on_error: OnErrorSignature = noop
    on_room_joined: OnRoomJoinedSignature = noop
    on_room_left: OnRoomLeftSignature = noop
    on_sprite_out: OnSpriteOutSignature = noop
    on_sprite_removed: OnSpriteRemovedSignature = noop
    on_sprite_collision: OnSpriteCollisionSignature = noop
    on_overlap_in: OnOverlapInSignature = noop
    on_overlap_out: OnOverlapOutSignature = noop
    on_border_overlap: OnBorderOverlapSignature = noop
    on_sprite_clicked: OnSpriteClickedSignature = noop
    on_auto_movement_pos: OnAutoMovementPosSignature = noop
    on_timer: OnTimerSignature = noop

    _on_key: List[OnKeySignature] = []
    _on_f1: List[OnF1Signature] = []
    _on_f2: List[OnF2Signature] = []
    _on_f3: List[OnF3Signature] = []
    _on_f4: List[OnF4Signature] = []
    _on_pointer: List[OnPointerSignature] = []
    _on_acceleration: List[OnAccelerationSignature] = []
    _on_gyro: List[OnGyroSignature] = []
    _on_sensor: List[OnSensorSignature] = []
    _on_data: List[OnDataSignature] = []
    _on_broadcast_data: List[OnBroadcastDataSignature] = []
    _on_all_data: List[OnAll_dataSignature] = []
    _on_device: List[OnDeviceSignature] = []
    _on_client_device: List[OnClientDeviceSignature] = []
    _on_devices: List[OnDevicesSignature] = []
    _on_error: List[OnErrorSignature] = []
    _on_room_joined: List[OnRoomJoinedSignature] = []
    _on_room_left: List[OnRoomLeftSignature] = []
    _on_sprite_out: List[OnSpriteOutSignature] = []
    _on_sprite_removed: List[OnSpriteRemovedSignature] = []
    _on_sprite_collision: List[OnSpriteCollisionSignature] = []
    _on_overlap_in: List[OnOverlapInSignature] = []
    _on_overlap_out: List[OnOverlapOutSignature] = []
    _on_border_overlap: List[OnBorderOverlapSignature] = []
    _on_sprite_clicked: List[OnSpriteClickedSignature] = []
    _on_auto_movement_pos: List[OnAutoMovementPosSignature] = []
    _on_timer: List[OnTimerSignature] = []

    @overload
    def on(self, event: Literal['key'], function: OnKeySignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['f1'], function: OnF1Signature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['f2'], function: OnF2Signature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['f3'], function: OnF3Signature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['f4'], function: OnF4Signature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['pointer'], function: OnPointerSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['acceleration', 'acc'], function: OnAccelerationSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['gyro'], function: OnGyroSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['sensor'], function: OnSensorSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['data'], function: OnDataSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['broadcast_data'], function: OnBroadcastDataSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['all_data'], function: OnAll_dataSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['device'], function: OnDeviceSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['client_device'], function: OnClientDeviceSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['devices'], function: OnDevicesSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['error'], function: OnErrorSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['room_joined'], function: OnRoomJoinedSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['room_left'], function: OnRoomLeftSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['sprite_out', 'object_out'], function: OnSpriteOutSignature, replace: bool = False): ...

    @overload
    def on(self, event: Literal['sprite_removed', 'object_removed'],
           function: OnSpriteRemovedSignature, replace: bool = False): ...

    @overload
    def on(self, event: Literal['sprite_collision', 'object_collision',
                                'collision'], function: OnSpriteCollisionSignature, replace: bool = False): ...

    @overload
    def on(self, event: Literal['overlap_in'], function: OnOverlapInSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['overlap_out'], function: OnOverlapOutSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['border_overlap'], function: OnBorderOverlapSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['auto_movement_pos'], function: OnAutoMovementPosSignature, replace: bool = False): ...
    @overload
    def on(self, event: Literal['timer'], function: OnTimerSignature, replace: bool = False): ...

    @overload
    def on(self, event: Literal['sprite_clicked', 'object_clicked'],
           function: OnSpriteClickedSignature, replace: bool = False): ...

    def on(self, event: Union[Event, EventAliases], function: CallbackSignature, replace: bool = False):
        funcs = []
        if event == 'key':
            funcs = self._on_key
        elif event == 'f1':
            funcs = self._on_f1
        elif event == 'f2':
            funcs = self._on_f2
        elif event == 'f3':
            funcs = self._on_f3
        elif event == 'f4':
            funcs = self._on_f4
        elif event == 'pointer':
            funcs = self._on_pointer
        elif event == 'acceleration' or event == 'acc':
            funcs = self._on_acceleration
        elif event == 'gyro':
            funcs = self._on_gyro
        elif event == 'sensor':
            funcs = self._on_sensor
        elif event == 'data':
            funcs = self._on_data
        elif event == 'broadcast_data':
            funcs = self._on_broadcast_data
        elif event == 'all_data':
            funcs = self._on_all_data
        elif event == 'device':
            funcs = self._on_device
        elif event == 'client_device':
            funcs = self._on_client_device
        elif event == 'devices':
            funcs = self._on_devices
        elif event == 'error':
            funcs = self._on_error
        elif event == 'room_joined':
            funcs = self._on_room_joined
        elif event == 'room_left':
            funcs = self._on_room_left
        elif event == 'sprite_out' or event == 'object_out':
            funcs = self._on_sprite_out
        elif event == 'sprite_removed' or event == 'object_removed':
            funcs = self._on_sprite_removed
        elif event == 'collision' or event == 'sprite_collision' or event == 'object_collision':
            funcs = self._on_sprite_collision
        elif event == 'overlap_in':
            funcs = self._on_overlap_in
        elif event == 'overlap_out':
            funcs = self._on_overlap_out
        elif event == 'border_overlap':
            funcs = self._on_border_overlap
        elif event == 'sprite_clicked' or event == 'object_clicked':
            funcs = self._on_sprite_clicked
        elif event == 'auto_movement_pos':
            funcs = self._on_auto_movement_pos
        elif event == 'timer':
            funcs = self._on_timer

        if replace:
            funcs.clear()
        funcs.append(function)

    def remove(self, event: Union[Event, EventAliases], function: Optional[CallbackSignature] = None):
        '''removes an assigned "on" callback functions. When no function is provided, all callbacks are removed
        '''
        funcs = []
        if event == 'key':
            funcs = self._on_key
        elif event == 'f1':
            funcs = self._on_f1
        elif event == 'f2':
            funcs = self._on_f2
        elif event == 'f3':
            funcs = self._on_f3
        elif event == 'f4':
            funcs = self._on_f4
        elif event == 'pointer':
            funcs = self._on_pointer
        elif event == 'acceleration' or event == 'acc':
            funcs = self._on_acceleration
        elif event == 'gyro':
            funcs = self._on_gyro
        elif event == 'sensor':
            funcs = self._on_sensor
        elif event == 'data':
            funcs = self._on_data
        elif event == 'broadcast_data':
            funcs = self._on_broadcast_data
        elif event == 'all_data':
            funcs = self._on_all_data
        elif event == 'device':
            funcs = self._on_device
        elif event == 'client_device':
            funcs = self._on_client_device
        elif event == 'devices':
            funcs = self._on_devices
        elif event == 'error':
            funcs = self._on_error
        elif event == 'room_joined':
            funcs = self._on_room_joined
        elif event == 'room_left':
            funcs = self._on_room_left
        elif event == 'sprite_out' or event == 'object_out':
            funcs = self._on_sprite_out
        elif event == 'sprite_removed' or event == 'object_removed':
            funcs = self._on_sprite_removed
        elif event == 'collision' or event == 'sprite_collision' or event == 'object_collision':
            funcs = self._on_sprite_collision
        elif event == 'overlap_in':
            funcs = self._on_overlap_in
        elif event == 'overlap_out':
            funcs = self._on_overlap_out
        elif event == 'border_overlap':
            funcs = self._on_border_overlap
        elif event == 'sprite_clicked' or event == 'object_clicked':
            funcs = self._on_sprite_clicked
        elif event == 'auto_movement_pos':
            funcs = self._on_auto_movement_pos
        elif event == 'timer':
            funcs = self._on_timer

        if function is None:
            funcs.clear()
        else:
            funcs.remove(function)

    __on_notify_subscribers: SubscriptionCallbackSignature = noop
    __subscription_job: CancleSubscription = None
    __async_subscription_jobs: List[ThreadJob] = []
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
        self.__reportings = DictX({})
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
        self.sio.on(SocketEvents.TIMER, self.__on_timer)
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

        if 'deliver_to' in delivery_opts:
            data['deliver_to'] = delivery_opts['deliver_to']

        if 'device_id' not in data:
            data['device_id'] = self.device_id

        if 'broadcast' in delivery_opts and delivery_opts['broadcast']:
            data['broadcast'] = True

        if 'unicast_to' in delivery_opts and type(delivery_opts['unicast_to']) == int:
            if 'broadcast' in data:
                del data['broadcast']
            data['unicast_to'] = delivery_opts['unicast_to']

        self.sio.emit(event, data)

    def send_to(self, to: str, data: DataMsg, **delivery_opts):
        '''
        Emits a new_data event to another device_id group
        Parameters
        ----------
        to : str
            the device_id of the receiver

        data : DataMsg
            the data to send, fields 'time_stamp' and 'device_id' are added when they are not present
        '''
        data['deliver_to'] = to
        self.emit(SocketEvents.NEW_DATA, data=data, **delivery_opts)

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

    def add_svg_to_playground(self, name: str, raw_svg: str, **delivery_opts):
        '''
        Parameters
        ----------
        name : str
            with this name the svg can be referred later

        raw_svg : str
            the svg content. This should contain a root element containing a viewBox and xmlns attributes

        Example
        -------
        A simple triangle
        ```svg
        <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <polygon points="0,0 100,0 50,100" style="fill:lime;stroke:purple;stroke-width:1"/>
        </svg>
        ```
        '''
        pkg = {'name': name, 'image': raw_svg, 'type': 'svg'}
        playground_config = {'images': [pkg]}
        if 'images' not in self.__playground_config:
            self.__playground_config['images'] = []
        self.__playground_config['images'].append(pkg)
        config = {
            'type': DataType.PLAYGROUND_CONFIG,
            'config': playground_config
        }
        self.emit(SocketEvents.NEW_DATA, config, **delivery_opts)

    def configure_playground(self,
                             width: Optional[Number] = None,
                             height: Optional[Number] = None,
                             origin_x: Optional[Number] = None,
                             origin_y: Optional[Number] = None,
                             shift_x: Optional[Number] = None,
                             shift_y: Optional[Number] = None,
                             color: Optional[Union[Colors, str]] = None,
                             images: Optional[Union[Path, str]] = None,
                             audio_tracks: Optional[Union[Path, str]] = None,
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
                rpath = Path(sys.argv[0]).parent.rglob(str(images))
                try:
                    while True:
                        new_p = next(rpath)
                        if new_p.is_dir():
                            images = new_p
                            break
                except:
                    pass

            if not images.is_dir():
                raise Exception(f'Image path {images} not found')
            for img in images.iterdir():
                if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    raw = img.read_bytes()
                    name = img.stem
                    file_type = img.suffix.lower()
                    raw_images.append({'name': name, 'image': raw, 'type': file_type[1:]})
                elif img.suffix.lower() in ['.svg']:
                    raw = img.read_text('utf-8')
                    name = img.stem
                    file_type = img.suffix.lower()
                    raw_images.append({'name': name, 'image': raw, 'type': file_type[1:]})
        raw_tracks = []
        if audio_tracks is not None:
            audio_tracks = Path(audio_tracks)
            if audio_tracks.is_absolute():
                pass
            else:
                rpath = Path(sys.argv[0]).parent.rglob(str(audio_tracks))
                try:
                    while True:
                        new_p = next(rpath)
                        if new_p.is_dir():
                            audio_tracks = new_p
                            break
                except:
                    pass

                if not audio_tracks.is_dir():
                    raise Exception(f'audio_tracks path {audio_tracks} not found')
                for track in audio_tracks.iterdir():
                    if track.suffix in ['.mp3', '.wav', '.ogg']:
                        raw = track.read_bytes()
                        name = track.stem
                        file_type = track.suffix
                        raw_tracks.append({'name': name, 'audio': raw, 'type': file_type[1:]})

        playground_config = without_none({
                'width': width,
                'height': height,
                'shift_x': shift_x if shift_x is not None else 0,
                'shift_y': shift_y if shift_y is not None else 0,
                'color': color,
                'image': image,
                'images': raw_images,
                'audio_tracks': raw_tracks
            })
        config = {
            'type': DataType.PLAYGROUND_CONFIG,
            'config': playground_config
        }
        if 'images' in self.__playground_config and len(raw_images) > 0:
            playground_config['images'] = [*raw_images, *self.__playground_config['images']]
        if 'audio_tracks' in self.__playground_config and len(raw_tracks) > 0:
            playground_config['audio_tracks'] = [*raw_tracks, *self.__playground_config['audio_tracks']]
        self.__playground_config.update(playground_config)
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
                border_width: Optional[int] = None,
                border_style: Optional[Literal['dotted', 'dashed', 'solid', 'double',
                                               'groove', 'ridge', 'inset', 'outset', 'none', 'hidden']] = None,
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
                movements: Optional[SpriteAutoMovement] = None,
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
                'border_style': border_style,
                'border_width': border_width,
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
                'movements': movements,
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

    @overload
    def apply_movement(id: str, direction: Tuple[Number, Number], time_span: Optional[Number]
                       = None, speed: Optional[Number] = 1, absolute=False, cancel_previous: Optional[bool] = True): ...

    @overload
    def apply_movement(id: str, direction: Tuple[Number, Number], distance: Optional[Number]
                       = None, speed: Optional[Number] = 1, absolute=False, cancel_previous: Optional[bool] = True): ...

    @overload
    def apply_movement(id: str, pos: Tuple[Number, Number], speed: Number,
                       movement='absolute', cancel_previous: Optional[bool] = True): ...

    @overload
    def apply_movement(id: str, pos: Tuple[Number, Number], time: Number,
                       movement='absolute', cancel_previous: Optional[bool] = True): ...

    def apply_movement(self, id: str,
                       direction: Tuple[Number, Number], time_span: Optional[Number] = None,
                       speed: Optional[Number] = 1, distance: Optional[Number] = None,
                       pos: Optional[Tuple[Number, Number]] = None, time: Optional[Number] = None,
                       movement=Optional[Literal['relative', 'absolute']], cancel_previous: Optional[bool] = True):
        '''
        Parameters
        ----------
        direction : [Number, Number]
            movement direction of the sprite

        time_span : Optional[Number]
            the time the sprite should be moved in the given Direction until the next movement takes place

        speed : Optional[Number], by default 1
            the speed of the sprite

        distance : Optional[Number]
            the distance the sprite should move

        cancel_previous : Optional[bool], by default True
            wheter previous movements should be canceled or not

        movement : 'absolute' | 'relative'
            wheter the movement is relative or absolute
        '''
        movement_msg = {}

        if time is not None and time_span is None:
            time_span = time
        if movement == 'absolute':
            if pos is None:
                logging.warn('No position provided for absolute movement, skipping...')
                return
            elif time_span is None and speed is None:
                logging.warn('No time or speed provided for absolute movement, skipping...')
                return
            else:
                movement_msg = without_none(
                    {'movement': 'absolute', 'to': pos, 'time': time_span, 'speed': speed}
                )
        else:
            if direction is None:
                logging.warn('No direction provided for relative movement, skipping...')
                return
            elif speed is None:
                logging.warn('No speed provided for relative movement, skipping...')
                return
            else:
                movement_msg = without_none(
                    {'movement': 'relative', 'direction': direction,
                        'time_span': time_span, 'speed': speed, 'distance': distance}
                )
        self.update_sprite(
            id=id,
            movements={
                'cancel_previous': cancel_previous,
                'movements': [movement_msg],
            }
        )

    @contextmanager
    def apply_movements(self, id: str, repeat: Optional[int] = None, cycle: Optional[bool] = None, cancel_previous: Optional[bool] = True):
        '''
        Parameters
        ----------
        repeat : Optional[int], by default 1
            how often the sequence should be repeated

        cycle : Optional[bool], by default False
            wheter to repeat the movements infinitely

        cancel_previous : Optional[bool], by default True
            wheter previous movements should be canceled or not
        '''
        movements = []

        @overload
        def movement(direction: Tuple[Number, Number], time_span: Optional[Number]
                     = None, speed: Optional[Number] = 1, absolute=False): ...

        @overload
        def movement(direction: Tuple[Number, Number], distance: Optional[Number]
                     = None, speed: Optional[Number] = 1, absolute=False): ...

        @overload
        def movement(pos: Tuple[Number, Number], speed: Number, movement='absolute'): ...

        @overload
        def movement(pos: Tuple[Number, Number], time: Number, movement='absolute'): ...

        def movement(direction: Tuple[Number, Number] = None, time_span: Optional[Number] = None, time: Optional[Number] = None, speed: Optional[Number] = 1, distance: Optional[Number] = None, movement: Optional[Literal['absolute', 'relative']] = 'relative', pos: Optional[Tuple[Number, Number]] = None):
            '''
            Parameters
            ----------
            direction : [Number, Number]
                movement direction of the sprite

            time_span : Optional[Number]
                the time the sprite should be moved in the given Direction until the next movement takes place

            speed : Optional[Number], by default 1 
                the speed of the sprite

            distance : Optional[Number]
                the distance the sprite should move
            '''
            if time is not None and time_span is None:
                time_span = time

            if movement == 'absolute':
                if pos is None:
                    logging.warn('No position provided for absolute movement, skipping...')
                elif time_span is None and speed is None:
                    logging.warn('No time or speed provided for absolute movement, skipping...')
                else:
                    movements.append(without_none(
                        {'movement': 'absolute', 'to': pos, 'time': time_span, 'speed': speed}
                    ))
            else:
                if direction is None:
                    logging.warn('No direction provided for relative movement, skipping...')
                elif speed is None:
                    logging.warn('No speed provided for relative movement, skipping...')
                else:
                    movements.append(without_none(
                        {'movement': 'relative', 'direction': direction,
                            'time_span': time_span, 'speed': speed, 'distance': distance}
                    ))
        try:
            yield movement
        except:
            movements = []
            raise
        else:
            self.update_sprite(
                id=id,
                movements=without_none({
                    'cycle': cycle,
                    'repeat': repeat,
                    'cancel_previous': cancel_previous,
                    'movements': movements
                })
            )

    @overload
    def move_to(self, id: str, pos: Tuple[Number, Number], speed: Number,
                via: Optional[Tuple[Number, Number]] = None): ...

    @overload
    def move_to(self, id: str, pos: Tuple[Number, Number], time: Number,
                via: Optional[Tuple[Number, Number]] = None): ...

    def move_to(self, id: str, pos: Tuple[Number, Number], speed: Optional[Number] = None, time: Optional[Number] = None, time_span: Optional[Number] = None, via: Optional[Tuple[Number, Number]] = None, cancel_previous: Optional[bool] = True):
        movements = []
        if time is None and time_span is not None:
            time = time_span
        if via is not None:
            movements.append(without_none({
                'movement': 'absolute',
                'to': via,
                'speed': speed,
                'time': time / 2 if time is not None else None
            }))

        movements.append(without_none({
            'movement': 'absolute',
            'to': pos,
            'speed': speed,
            'time': time / 2 if time is not None and via is not None else None
        }))
        self.update_sprite(
            id=id,
            movements={
                'movements': movements,
                'cancel_previous': cancel_previous
            }
        )

    def play_sound(self, name: str, id: Optional[str] = None, repeat: bool = False, volume: float = 0.8, **delivery_opts):
        '''
        volume : float
            0 -> no sound, 1 -> full volume
        '''
        self.emit(
            SocketEvents.NEW_DATA,
            without_none({
                'type': DataType.START_AUDIO,
                'name': name,
                'repeat': repeat,
                'volume': volume,
                'id': id
            }),
            **delivery_opts
        )

    def stop_sound(self, name: Optional[str] = None, id: Optional[str] = None, **delivery_opts):
        self.emit(
            SocketEvents.NEW_DATA,
            without_none({
                'type': DataType.STOP_AUDIO,
                'name': name,
                'id': id
            }),
            **delivery_opts
        )

    def add_circle(
            self,
            pos_x: Optional[Number] = None,
            pos_y: Optional[Number] = None,
            radius: Optional[Number] = None,
            color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
            border_width: Optional[int] = None,
            border_style: Optional[Literal['dotted', 'dashed', 'solid', 'double',
                                           'groove', 'ridge', 'inset', 'outset', 'none', 'hidden']] = None,
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
            movements: Optional[SpriteAutoMovement] = None,
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
            border_width=border_width,
            border_style=border_style,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            movements=movements,
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
            border_width: Optional[int] = None,
            border_style: Optional[Literal['dotted', 'dashed', 'solid', 'double',
                                           'groove', 'ridge', 'inset', 'outset', 'none', 'hidden']] = None,
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
            movements: Optional[SpriteAutoMovement] = None,
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
            border_width=border_width,
            border_style=border_style,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            movements=movements,
            **delivery_opts
        )
    update_ellipse = add_ellipse

    def add_square(
            self,
            pos_x: Number = None,
            pos_y: Number = None,
            size: Number = None,
            color: Optional[Union[Colors, str]] = None,
            border_color: Optional[Union[Colors, str]] = None,
        border_width: Optional[int] = None,
        border_style: Optional[Literal['dotted', 'dashed', 'solid', 'double',
                                       'groove', 'ridge', 'inset', 'outset', 'none', 'hidden']] = None,
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
            movements: Optional[SpriteAutoMovement] = None,
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
            border_width=border_width,
            border_style=border_style,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            movements=movements,
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
        border_width: Optional[int] = None,
        border_style: Optional[Literal['dotted', 'dashed', 'solid', 'double',
                                       'groove', 'ridge', 'inset', 'outset', 'none', 'hidden']] = None,
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
            movements: Optional[SpriteAutoMovement] = None,
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
            border_width=border_width,
            border_style=border_style,
            font_color=font_color,
            font_size=font_size,
            movements=movements,
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
            border_width: Optional[int] = None,
            border_style: Optional[Literal['dotted', 'dashed', 'solid', 'double',
                                           'groove', 'ridge', 'inset', 'outset', 'none', 'hidden']] = None,
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
            movements: Optional[SpriteAutoMovement] = None,
            **delivery_opts) -> str:
        config = DictX({'width': 100, 'height': 100})
        config.update(without_none(deepcopy(self.__playground_config)))
        if height is None:
            height = config.height / 20
        text = str(text)
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
            border_width=border_width,
            border_style=border_style,
            font_color=font_color,
            font_size=font_size,
            z_index=z_index,
            movements=movements,
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
        border_width: Optional[int] = None,
        border_style: Optional[Literal['dotted', 'dashed', 'solid', 'double',
                                       'groove', 'ridge', 'inset', 'outset', 'none', 'hidden']] = None,
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
            movements: Optional[SpriteAutoMovement] = None,
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
            'border_style': border_style,
            'border_width': border_width,
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
            'movements': movements,
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
        '''Cleans the playground and reconfigures the playground to
        the default playground config. Images and soundtracks have to be uploaded again
        '''
        self.__sprites = []
        self.__lines = []
        self.__playground_config = deepcopy(DEFAULT_PLAYGROUND_CONFIG)
        self.emit(
            SocketEvents.NEW_DATA,
            {
                'type': DataType.CLEAR_PLAYGROUND
            }
        )
        self.sleep(0.2)

    def clean_playground(self, **delivery_opts):
        '''Cleans the playground without reconfiguring the playground.
        Images and soundtracks can be reused and dont need to be uploaded again.
        '''
        self.__sprites = []
        self.__lines = []
        self.emit(
            SocketEvents.NEW_DATA,
            {
                'type': DataType.CLEAN_PLAYGROUND
            }
        )

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
    update_object = add_sprite

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

    def __distribute_dataframe(
        self,
        to: SubscriptionCallbackSignature = None,
        job: ThreadJob = None
    ):
        clbk = to if to is not None else self.__on_notify_subscribers
        if clbk is None:
            return

        arg_count = len(signature(clbk).parameters)
        clbk = cast(Callable, clbk)

        if arg_count == 0:
            return clbk()

        data: DataFrame = DataFrame({
            'key': self.latest_key(device_id=self.__device_id) or default('key'),
            'acceleration': self.latest_acceleration(device_id=self.__device_id) or default('acceleration'),
            'gyro': self.latest_gyro(device_id=self.__device_id) or default('gyro'),
            'color_pointer': self.latest_color_pointer(device_id=self.__device_id) or default('color_pointer'),
            'grid_pointer': self.latest_grid_pointer(device_id=self.__device_id) or default('grid_pointer'),
            'job': job
        })
        if arg_count == 1:
            clbk(data)
        elif arg_count == 2:
            clbk(data, self)

    def animate(self, callback: SubscriptionCallbackSignature = None, interval: float = 0.05, iteration_count: int = float('inf')) -> Union[ThreadJob, CancleSubscription]:
        return self.subscribe_async(callback=callback, interval=interval, iteration_count=iteration_count)

    def subscribe_async(self, callback: SubscriptionCallbackSignature = None, interval: float = 0.05, iteration_count: int = float('inf')) -> Union[ThreadJob, CancleSubscription]:
        return self.subscribe(callback=callback, interval=interval, blocking=False, iteration_count=iteration_count)

    def set_update_interval(self, interval: float):
        return self.subscribe(interval=interval, blocking=True)

    def set_timeout(self, callback: SubscriptionCallbackSignature = None, time: float = 0.05, repeat: int = 1, blocking=False) -> Union[None, Union[ThreadJob, CancleSubscription]]:
        return self.subscribe(callback=callback, interval=time, iteration_count=repeat, blocking=blocking)

    execute_in = set_timeout
    run_in = set_timeout
    schedule = set_timeout

    @ overload
    def subscribe(self, callback: SubscriptionCallbackSignature = None,
                  interval: float = 0.05, blocking=True, iteration_count: int = float('inf')) -> Union[ThreadJob, CancleSubscription]:
        ...

    @ overload
    def subscribe(self, callback: SubscriptionCallbackSignature = None, interval: float = 0.05, blocking=False, iteration_count: int = float('inf')) -> None:
        ...

    def subscribe(self, callback: SubscriptionCallbackSignature = None, interval: float = 0.05, blocking: bool = True, iteration_count: int = float('inf')) -> Union[None, Union[ThreadJob, CancleSubscription]]:
        '''
        blocked : bool wheter the main thread gets blocked or not.

        iteration_count : int
            how often the callback should be called (it is called at least once).
            Has only effect on async calls
        '''
        if blocking:
            self.__on_notify_subscribers = cast(Callable, callback)
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
            thread_job = ThreadJob(
                lambda job: self.__distribute_dataframe(to=callback, job=job),
                interval,
                iterations=iteration_count
            )
            self.__async_subscription_jobs.append(thread_job)
            thread_job.start()
            return thread_job

    def cancel_subscription(self):
        if self.__subscription_job is not None:
            self.__subscription_job.cancel()
            self.__subscription_job = None

    def cancel_async_subscriptions(self):
        for job in self.__async_subscription_jobs:
            job.cancel()
        self.__async_subscription_jobs.clear()

    def report(self, value: Union[int, str] = None, report_type: Literal['report_score'] = 'report_score', to: str = '__GAME_RUNNER__'):
        '''reports a value to a listener, e.g. to report a new highscore to the game runner.

        Example
        -------
        ```py
        score = 12
        device.report(score)
        ```
        '''
        if report_type in self.__reportings:
            if type(value) in [int, float] and type(self.__reportings[report_type]) in [int, float]:
                if value < self.__reportings[report_type]:
                    return
        self.__reportings[report_type] = value
        self.send({'type': report_type, 'score': value, 'deliver_to': to})

    stop_all_animations = cancel_async_subscriptions

    def wait(self):
        '''
        Wait until the connection with the server ends.

        Client applications can use this function to block the main thread during the life of the connection.
        '''
        self.sio.wait()

    def disconnect(self):
        if not self.sio.connected:
            return
        self.stop_sound()
        self.cancel_async_subscriptions()
        self.cancel_subscription()
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
        callbacks = getattr(self, f'_{name}')
        for clbk in [callback, *callbacks]:
            if clbk is None:
                continue
            try:
                arg_count = len(signature(clbk).parameters)
                if arg_count == 0:
                    clbk()
                elif arg_count == 1:
                    clbk(data)
                elif arg_count == 2:
                    clbk(data, self)
            except Exception as e:
                logging.warn(e)
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
                    obj = deepcopy(sprite)
                    data.update({
                        'sprite': obj,
                        'object': obj
                    })
                self.__callback('on_sprite_out', data)
            elif data['type'] == DataType.SPRITE_REMOVED:
                sprite = self.get_sprite(data['id'])
                if sprite is not None:
                    obj = deepcopy(sprite)
                    data.update({
                        'sprite': obj,
                        'object': obj
                    })
                    self.__sprites.remove(sprite)
                self.__callback('on_sprite_removed', data)
            elif data['type'] == DataType.AUTO_MOVEMENT_POS:
                sprite = self.get_sprite(data['id'])
                if sprite is not None:
                    sprite['pos_x'] = data['x']
                    sprite['pos_y'] = data['y']
                    obj = deepcopy(sprite)
                    data.update({
                        'sprite': obj,
                        'object': obj
                    })
                self.__callback('on_auto_movement_pos', data)
            elif data['type'] == DataType.SPRITE_COLLISION:
                if len(data['sprites']) == 2:
                    try:
                        s1 = self.get_sprite(data['sprites'][0]['id'])
                        s2 = self.get_sprite(data['sprites'][1]['id'])
                        # make sure the first sprite is a controlled sprite...
                        if 'collision_detection' in s1 and not s1['collision_detection']:
                            t = s2
                            s1 = s2
                            s2 = t
                        if s1 is not None:
                            raw = data['sprites'][0]
                            data['sprites'][0] = deepcopy(s1)
                            data['sprites'][0]['pos_x'] = raw['pos_x']
                            data['sprites'][0]['pos_y'] = raw['pos_y']
                            # update the position
                        else:
                            data['sprites'][0] = DictX(data['sprites'][0])

                        if s2 is not None:
                            raw = data['sprites'][1]
                            data['sprites'][1] = deepcopy(s2)
                            data['sprites'][1]['pos_x'] = raw['pos_x']
                            data['sprites'][1]['pos_y'] = raw['pos_y']
                        else:
                            data['sprites'][1] = DictX(data['sprites'][1])
                    except:
                        data['sprites'] = list(map(lambda s: DictX(s), data['sprites']))
                else:
                    data['sprites'] = list(map(lambda s: DictX(s), data['sprites']))
                # add alias
                data['objects'] = data['sprites']
                self.__callback('on_sprite_collision', data)
                if data['overlap'] == 'in':
                    self.__callback('on_overlap_in', data)
                elif data['overlap'] == 'out':
                    self.__callback('on_overlap_out', data)

            elif data['type'] == DataType.BORDER_OVERLAP:
                original = self.get_sprite(data['id'])
                if original is not None:
                    obj = deepcopy(original)
                    data.update({'sprite': obj, 'object': obj})
                self.__callback('on_border_overlap', data)
            elif data['type'] == DataType.SPRITE_CLICKED:
                data['object'] = data['sprite'] if 'sprite' in data else None
                self.__callback('on_sprite_clicked', data)
            elif data['type'] == DataType.PLAYGROUND_CONFIG:
                self.__playground_config = deepcopy(DEFAULT_PLAYGROUND_CONFIG)
                self.__playground_config.update(data['config'])

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

    def __on_timer(self, time_msg: dict):
        time_msg = DictX(time_msg)
        self.__callback('on_timer', time_msg)

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

'''
Callback Signatures

they have to be at the end, otherwise Connector is unknown...
'''
OnKeySignature = Union[Callable[[], None], Callable[[KeyMsg], None], Callable[[KeyMsg, Connector], None]]
OnF1Signature = Union[Callable[[], None], Callable[[KeyMsgF1], None], Callable[[KeyMsgF1, Connector], None]]
OnF2Signature = Union[Callable[[], None], Callable[[KeyMsgF2], None], Callable[[KeyMsgF2, Connector], None]]
OnF3Signature = Union[Callable[[], None], Callable[[KeyMsgF3], None], Callable[[KeyMsgF3, Connector], None]]
OnF4Signature = Union[Callable[[], None], Callable[[KeyMsgF4], None], Callable[[KeyMsgF4, Connector], None]]
OnPointerSignature = Union[Callable[[Union[ColorPointer, GridPointer]], None],
                           Callable[[Union[ColorPointer, GridPointer], Connector], None]]
OnAccelerationSignature = Union[Callable[[AccMsg], None], Callable[[AccMsg, Connector], None]]
OnGyroSignature = Union[Callable[[GyroMsg], None], Callable[[GyroMsg, Connector], None]]
OnSensorSignature = Union[Callable[[Union[GyroMsg, AccMsg]], None], Callable[[Union[GyroMsg, AccMsg], Connector], None]]
OnDataSignature = Union[Callable[[DataMsg], None], Callable[[DataMsg, Connector], None]]
OnBroadcastDataSignature = Union[Callable[[DataMsg], None], Callable[[DataMsg, Connector], None]]
OnAll_dataSignature = Union[Callable[[List[DataMsg]], None], Callable[[List[DataMsg], Connector], None]]
OnDeviceSignature = Union[Callable[[Device], None], Callable[[Device, Connector], None]]
OnClientDeviceSignature = Union[Callable[[Device], None], Callable[[Device, Connector], None]]
OnDevicesSignature = Union[Callable[[List[Device]], None], Callable[[List[Device], Connector], None]]
OnErrorSignature = Union[Callable[[ErrorMsg], None], Callable[[ErrorMsg, Connector], None]]
OnRoomJoinedSignature = Union[Callable[[DeviceJoinedMsg], None], Callable[[DeviceJoinedMsg, Connector], None]]
OnRoomLeftSignature = Union[Callable[[DeviceLeftMsg], None], Callable[[DeviceLeftMsg, Connector], None]]
OnSpriteOutSignature = Union[Callable[[SpriteOutMsg], None], Callable[[SpriteOutMsg, Connector], None]]
OnSpriteRemovedSignature = Union[Callable[[SpriteRemovedMsg], None], Callable[[SpriteRemovedMsg, Connector], None]]
OnSpriteCollisionSignature = Union[Callable[[SpriteCollisionMsg], None],
                                   Callable[[SpriteCollisionMsg, Connector], None]]
OnOverlapInSignature = Union[Callable[[SpriteCollisionMsg], None], Callable[[SpriteCollisionMsg, Connector], None]]
OnOverlapOutSignature = Union[Callable[[SpriteCollisionMsg], None], Callable[[SpriteCollisionMsg, Connector], None]]
OnBorderOverlapSignature = Union[Callable[[BorderOverlapMsg], None], Callable[[BorderOverlapMsg, Connector], None]]
OnSpriteClickedSignature = Union[Callable[[SpriteClickedMsg], None], Callable[[SpriteClickedMsg, Connector], None]]
OnAutoMovementPosSignature = Union[Callable[[AutoMovementPosMsg], None],
                                   Callable[[AutoMovementPosMsg, Connector], None]]
SubscriptionCallbackSignature = Union[Callable[[], None],
                                      Callable[[DataFrame], None], Callable[[DataFrame, Connector], None]]
OnTimerSignature = Union[Callable[[TimerMsg], None], Callable[[TimerMsg, Connector], None]]
Event = Literal['key', 'f1', 'f2', 'f3', 'f4', 'pointer', 'acceleration', 'gyro', 'sensor', 'data', 'broadcast_data', 'all_data', 'device', 'client_device',
                'devices', 'error', 'room_joined', 'room_left', 'sprite_out', 'sprite_removed', 'sprite_collision', 'overlap_in', 'overlap_out', 'border_overlap',
                'sprite_clicked', 'auto_movement_pos', 'timer']
EventAliases = Literal['acc', 'object_out', 'object_removed', 'object_collision', 'collision', 'object_clicked']
CallbackSignature = Union[
    OnKeySignature, OnF1Signature, OnF2Signature, OnF3Signature, OnF4Signature, OnPointerSignature, OnAccelerationSignature, OnGyroSignature, OnSensorSignature, OnDataSignature, OnBroadcastDataSignature, OnAll_dataSignature, OnDeviceSignature, OnClientDeviceSignature, OnDevicesSignature, OnErrorSignature, OnRoomJoinedSignature, OnRoomLeftSignature, OnSpriteOutSignature, OnSpriteRemovedSignature, OnSpriteCollisionSignature, OnOverlapInSignature, OnOverlapOutSignature, OnBorderOverlapSignature, OnSpriteClickedSignature, OnAutoMovementPosSignature
]
