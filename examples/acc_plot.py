import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from smartphone_connector import Connector
from smartphone_connector.api_types import AccMsg
import matplotlib.pyplot as plt
phone = Connector('https://io.lebalz.ch', 'FooBar')

MAX_SAMPLES = 300

x = []
y = []

plt.show()


def on_acc(data: AccMsg):
    if len(x) > MAX_SAMPLES:
        x.pop(0)
        y.pop(0)

    x.append(data.time_stamp)
    y.append([data.x, data.y, data.z])


def on_intervall():
    plt.clf()
    plt.plot(x, y)
    plt.pause(0.005)


phone.on_acceleration = on_acc
phone.subscribe(on_intervall, interval=0.0)
