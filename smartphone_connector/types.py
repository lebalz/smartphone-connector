from __future__ import annotations
from typing import Final, overload, Union, Literal, Optional, Tuple, List, TypedDict
from dataclasses import dataclass
from .dictx import DictX

SocketEvents = Literal[
    'device',
    'devices',
    'all_data',
    'new_data',
    'new_data',
    'clear_data',
    'new_device',
    'get_all_data',
    'get_devices',
    'join_room',
    'leave_room',
    'room_left',
    'room_joined',
    'error_msg',
    'information_msg',
    'set_new_device_nr'
]


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
    INPUT_RESPONSE: Final[str] = 'input_response'
    UNKNOWN: Final[str] = 'unknown'
    ALLDATA: Final[str] = 'all_data'
    ALERT_CONFIRM: Final[str] = 'alert_confirm'
    REMOVE_SPRITE: Final[str] = 'remove_sprite'
    SPRITE: Final[str] = 'sprite'
    SPRITES: Final[str] = 'sprites'
    SPRITE_COLLISION: Final[str] = 'sprite_collision'
    SPRITE_OUT: Final[str] = 'sprite_out'
    PLAYGROUND_CONFIG: Final[str] = 'playground_config'
    CLEAR_PLAYGROUND: Final[str] = 'clear_playground'
    BORDER_OVERLAP: Final[str] = 'border_overlap'


DataTypes = Literal[
    DataType.KEY,
    DataType.GRID,
    DataType.GRIDUPDATE,
    DataType.COLOR,
    DataType.ACCELERATION,
    DataType.GYRO,
    DataType.POINTER,
    DataType.NOTIFICATION,
    DataType.INPUT_PROMPT,
    DataType.INPUT_RESPONSE,
    DataType.UNKNOWN,
    DataType.ALLDATA,
    DataType.ALERT_CONFIRM,
    DataType.REMOVE_SPRITE,
    DataType.SPRITE,
    DataType.SPRITES,
    DataType.SPRITE_COLLISION,
    DataType.SPRITE_OUT,
    DataType.PLAYGROUND_CONFIG,
    DataType.CLEAR_PLAYGROUND,
    DataType.BORDER_OVERLAP
]


InputType = Literal[
    'text',
    'number',
    'datetime',
    'date',
    'time',
    'select',
    'datetime-local'
]

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
    type: DataTypes


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


class PlaygroundConfigMsg(PlaygroundConfig):
    time_stamp: float
    device_id: str
    device_nr: int


class Sprite(DataMsg):
    type: Literal['sprite']
    id: str
    pos_x: int
    pos_y: int
    width: int
    height: int
    form: Literal['round', 'rectangle']
    color: CssColorType
    movement: Literal['controlled', 'uncontrolled']


class SpriteMsg(Sprite):
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
    movement: Literal['controlled', 'uncontrolled']


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
    movement: Literal['controlled', 'uncontrolled']
    x: float
    y: float
    id: str


class BorderOverlapMsg(BorderOverlap):
    time_stamp: float
    device_id: str
    device_nr: int


class SpriteOut(DataMsg):
    type: Literal['sprite_out']
    sprite_id: str
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
