from typing import List, Callable, TypeVar, Union
from time import time_ns
from datetime import datetime
import random
from .types import TimeStampedMsg, CssColorType, RgbColor
from pathlib import Path


def ClassProps(cls) -> List[str]:
    return [i for i in cls.__dict__.keys() if i[:2] != '__']


def ClassConsts(cls) -> List[str]:
    return list(map(lambda d: cls.__dict__[d], ClassProps(cls)))


def time_s() -> float:
    '''
    returns the current time in seconds since epoche
    '''
    return (time_ns() // 1000000) / 1000.0


def without_none(raw: dict) -> dict:
    '''
    removes all None values from the dict on level 1 (thus nested dicts are not supported). 
    '''
    return {k: v for k, v in raw.items() if v is not None}


def flatten(list_of_lists: List[List]) -> List:
    return [y for x in list_of_lists for y in x]


def to_datetime(data: Union[TimeStampedMsg, int, float]) -> datetime:
    '''
    extracts the datetime from a data package. if the field `time_stamp` is not present,
    the current datetime will be returned
    '''
    is_number = isinstance(data, int) or isinstance(data, float)

    if not is_number and 'time_stamp' not in data:
        return datetime.now()

    ts = data if (isinstance(data, int) or isinstance(data, float)) else data['time_stamp']
    # convert time_stamp from ms to seconds
    if ts > 1000000000000:
        ts = ts / 1000.0
    return datetime.fromtimestamp(ts)


def to_css_color(color: CssColorType, base_color: RgbColor = (255, 0, 0)) -> str:
    if isinstance(color, str):
        if len(color) > 1:
            return color
        elif len(color) == 1:
            color = int(color, 10)
        else:
            color = 0
    if isinstance(color, int):
        if base_color is None or len(base_color) < 3:
            base_color = (255, 0, 0)

        return f'rgba({base_color[0]},{base_color[1]},{base_color[2]},{color / 9})'

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


def first(filter_func: Callable[[T], bool], list_: List[T]) -> Union[T, None]:
    return next((item for item in list_ if try_or(lambda: filter_func(item), False)), None)


def image_to_lines(image: str):
    lines = image.splitlines(False)
    without_empty = list(filter(lambda l: len(l.strip()) > 0, lines))
    return list(map(lambda line: line.strip(), without_empty))


def lines_to_grid(lines: List[str]):
    return list(map(lambda line: [*line], lines))
