from __future__ import annotations
from typing import overload, Union, Literal, Optional, Tuple, List, TypedDict
from dataclasses import dataclass
from .dictx import DictX
from enum import Enum

Number = Union[float, int]


class InputType(str, Enum):
    TEXT = 'text'
    NUMBER = 'number'
    DATETIME = 'datetime'
    DATE = 'date'
    TIME = 'time'
    SELECT = 'select'


class SocketEvents(str, Enum):
    ALL_DATA = "all_data"
    CLEAR_DATA = "clear_data"
    DATA_STORE = "data_store"
    DEVICE = "device"
    DEVICES = "devices"
    ERROR_MSG = "error_msg"
    GET_ALL_DATA = "get_all_data"
    GET_DEVICES = "get_devices"
    INFORMATION_MSG = "information_msg"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    NEW_DATA = "new_data"
    NEW_DEVICE = "new_device"
    REMOVE_ALL = "remove_all"
    ROOM_JOINED = "room_joined"
    ROOM_LEFT = "room_left"
    SET_NEW_DEVICE_NR = "set_new_device_nr"


class DataType(str, Enum):
    ACCELERATION = "acceleration"
    ALERT_CONFIRM = "alert_confirm"
    ALL_DATA = "all_data"
    BORDER_OVERLAP = "border_overlap"
    CLEAR_PLAYGROUND = "clear_playground"
    COLOR = "color"
    GRID = "grid"
    GRID_UPDATE = "grid_update"
    GYRO = "gyro"
    INPUT_PROMPT = "input_prompt"
    INPUT_RESPONSE = "input_response"
    KEY = "key"
    NOTIFICATION = "notification"
    PLAYGROUND_CONFIG = "playground_config"
    POINTER = "pointer"
    REMOVE_SPRITE = "remove_sprite"
    SPRITE = "sprite"
    SPRITES = "sprites"
    SPRITE_CLICKED = "sprite_clicked"
    SPRITE_COLLISION = "sprite_collision"
    SPRITE_OUT = "sprite_out"
    UNKNOWN = "unknown"


class ClientDataMsgInputType(str, Enum):
    DATE = "date"
    DATETIME_LOCAL = "datetime-local"
    NUMBER = "number"
    SELECT = "select"
    TEXT = "text"
    TIME = "time"


R = int
G = int
B = int
A = float

RgbColor = Union[Tuple[R, G, B], List[int]]
CssColorType = Union[int, str, RgbColor, Tuple[R, G, B, A], List[float], List[Union[int, float]]]
BaseColor = Union[str, RgbColor]


@dataclass
class DeliveryOptions:
    broadcast: bool = False
    unicast_to: Optional[int] = None
    device_id: Optional[str] = None


@dataclass
class TimeStampedMsg(DictX):
    time_stamp: Optional[Union[float, int]]


class BaseMsg(TimeStampedMsg):
    device_id: Optional[str]
    device_nr: Optional[int]


class DataMsg(BaseMsg):
    type: DataType


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


class Key(DataMsg):
    type: Literal['key']
    key: Literal['up', 'right', 'down', 'left', 'home', 'F1', 'F2', 'F3', 'F4']


class KeyMsg(Key):
    time_stamp: float
    device_id: str
    device_nr: int


@overload
def default(type: Literal['key']) -> KeyMsg: ...
@overload
def default(type: Literal['acceleration']) -> AccMsg: ...
@overload
def default(type: Literal['gyro']) -> GyroMsg: ...
@overload
def default(type: Literal['grid_pointer']) -> GridPointer: ...
@overload
def default(type: Literal['color_pointer']) -> ColorPointer: ...
@overload
def default(type: Literal['notification']) -> Notification: ...


def default(type: str) -> DictX:
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


class PointerData(DataMsg):
    type: Literal['pointer']
    context: Literal['color', 'grid']


class PointerDataMsg(PointerData):
    time_stamp: float
    device_id: str
    device_nr: int


class ColorPointer(PointerDataMsg):
    context: Literal['color']
    x: int
    y: int
    width: int
    height: int
    displayed_at: float


class GridPointer(PointerDataMsg):
    context: Literal['grid']
    row: int
    column: int
    color: str
    displayed_at: float


class Acc(BaseMsg):
    type: Literal['acceleration']
    x: float
    y: float
    z: float
    interval: float


class AccMsg(Acc):
    time_stamp: float
    device_id: str
    device_nr: int


class Gyro(BaseMsg):
    type: Literal['gyro']
    alpha: float
    beta: float
    gamma: float
    absolute: bool


class GyroMsg(Gyro):
    time_stamp: float
    device_id: str
    device_nr: int


class DataFrame(DictX):
    key: KeyMsg
    acceleration: AccMsg
    gyro: GyroMsg
    color_pointer: ColorPointer
    grid_pointer: GridPointer


class ErrorMsg(BaseMsg):
    type: SocketEvents
    msg: str
    err: Union[str, dict]


class InformationMsg(TimeStampedMsg):
    message: str
    action: DataMsg
    should_retry: Optional[bool]


class InputResponse(DataMsg):
    type: Literal['input_response']
    response: str
    displayed_at: float


class InputResponseMsg(InputResponse):
    time_stamp: float
    device_id: str
    device_nr: int


class AlertConfirm(DataMsg):
    type: Literal['alert_confirm']
    displayed_at: float


class AlertConfirmMsg(AlertConfirm):
    time_stamp: float
    device_id: str
    device_nr: int


ColorGrid = Union[CssColorType, List[str], List[CssColorType], List[List[CssColorType]]]


class Grid(DataMsg):
    type: Literal['grid']
    grid: ColorGrid
    base_color: RgbColor


class GridMsg(Grid):
    time_stamp: float
    device_id: str
    device_nr: int


class Notification(DataMsg):
    type: Literal['notification']
    message: str
    alter: Optional[bool]
    time: Optional[Union[int, float]]


class PlaygroundConfig(DataMsg):
    type: Literal['playground_config']
    width: Optional[int]
    height: Optional[int]
    shift_x: Optional[int]
    shift_y: Optional[int]
    color: Optional[str]


class PlaygroundConfigMsg(PlaygroundConfig):
    time_stamp: float
    device_id: str
    device_nr: int


class SpriteForm(str, Enum):
    RECTANGLE = "rectangle"
    ROUND = "round"


class Sprite(DataMsg):
    id: str
    clickable: Optional[bool] = None
    collision_detection: Optional[bool] = None
    color: Optional[str] = None
    direction: Optional[List[float]] = None
    distance: Optional[float] = None
    form: Optional[SpriteForm] = None
    height: Optional[float] = None
    pos_x: Optional[float] = None
    pos_y: Optional[float] = None
    reset_time: Optional[bool] = None
    speed: Optional[float] = None
    text: Optional[str] = None
    time_span: Optional[float] = None
    width: Optional[float] = None


class SpriteMsg(Sprite):
    type: Literal['sprite']
    time_stamp: float
    device_id: str
    device_nr: int


class UpdateSprite(DataMsg):
    type: Literal['sprite']
    pos_x: int
    pos_y: int
    width: int
    height: int
    form: Literal['round', 'rectangle']
    color: CssColorType


class UpdateSpriteMsg(UpdateSprite):
    time_stamp: float
    device_id: str
    device_nr: int


class SpriteBase:
    id: str
    collision_detection: bool


class SpriteCollision(DataMsg):
    type: Literal['sprite_collision']
    sprites: Tuple[SpriteBase, SpriteBase]
    time_stamp: float
    overlap: Literal['in', 'out']


class SpriteCollisionMsg(SpriteCollision):
    time_stamp: float
    device_id: str
    device_nr: int


class BorderOverlap(DataMsg):
    type: Literal['border_overlap']
    border: Literal['left', 'right', 'top', 'bottom']
    collision_detection: bool
    x: float
    y: float
    id: str


class BorderOverlapMsg(BorderOverlap):
    time_stamp: float
    device_id: str
    device_nr: int


class SpriteOut(DataMsg):
    type: Literal['sprite_out']
    id: str
    time_stamp: float


class SpriteOutMsg(SpriteOut):
    time_stamp: float
    device_id: str
    device_nr: int


class Unknown(DictX):
    type: Literal['unknown']


class UnknownMsg(Unknown):
    time_stamp: float
    device_id: str
    device_nr: int


ClientMsg = Union[
    KeyMsg,
    GridMsg,
    AccMsg,
    GyroMsg,
    PointerDataMsg,
    InputResponseMsg,
    AlertConfirmMsg,
    SpriteMsg,
    UpdateSpriteMsg,
    PlaygroundConfigMsg,
    SpriteOutMsg,
    SpriteCollisionMsg,
    UnknownMsg
]

ClientData = Union[
    Key,
    Grid,
    Acc,
    Gyro,
    PointerData,
    InputResponse,
    AlertConfirm,
    Sprite,
    UpdateSprite,
    PlaygroundConfig,
    SpriteOut,
    SpriteCollision,
    Unknown,
    Notification
]
