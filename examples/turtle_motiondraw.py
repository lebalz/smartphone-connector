from turtle import *
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector, DataFrame
from smartphone_connector.types import KeyMsg
from examples.server_adress import SERVER_ADRESS


device = Connector(SERVER_ADRESS, 'FooBar')
Screen().tracer(1, 0)


def on_interval(data: DataFrame):
    if data.acceleration.x < -2:
        right(5)
    elif data.acceleration.x > 2:
        left(5)
    forward(5)


device.subscribe(on_interval, interval=0.01)
