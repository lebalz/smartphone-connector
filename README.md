# Smartphone Connector

This simple package exposes methods to interact with smartphones connected to a [socket.io server](https://github.com/lebalz/socketio_server) instance.

## Examples

[All examples and scripts on GitHub](https://github.com/lebalz/smartphone-connector/blob/master/examples/)

### Draw 3x3 checker board

```py
from smartphone_connector import Connector
phone = Connector('https://io.lebalz.ch', 'FooBar')

# draw a 3x3 checker board
phone.set_grid([
    ['black','white','black'],
    ['white','black','white'],
    ['black','white','black']
], broadcast=True)

# print the letter A
phone.set_grid([
  [9,9,9,9],
  [9,0,0,9],
  [9,9,9,9],
  [9,0,0,9],
  [9,0,0,9],
])
```

results on all devices in the following screen.

When `broadcast` is set to `False` (default), only the `FooBar` devices display the checker board.

![checker board](checker_demo.png)

### Stream & display gyroscope data

```py
from smartphone_connector import Connector, GyroMsg
import matplotlib.pyplot as plt
phone = Connector('https://io.lebalz.ch', 'FooBar')
MAX_SAMPLES = 300

y = []
x = []
plt.show()


def on_gyro(data: GyroMsg):
    if len(x) > MAX_SAMPLES:
        x.pop(0)
        y.pop(0)

    x.append(data.time_stamp)
    y.append([data.alpha, data.beta, data.gamma])


def on_intervall():
    plt.clf()
    plt.plot(x, y)
    plt.pause(0.01)


phone.on_gyro = on_gyro
phone.subscribe(on_intervall, interval=0)
```

Displays gyroscope data from the smartphone on a Matplotlib-Plot.
![Gyroscope-Plot](assets/gyroscope.png)

## Package and upload to pip

@see [this tutorial](https://packaging.python.org/tutorials/packaging-projects/)

```sh
rm -rf build/ dist/ smartphone_connector.egg-info/ && \
python3 setup.py sdist bdist_wheel && \
python3 -m twine upload dist/*
```

## Changelog

- 0.0.106: add possibility to control movement distances
- 0.0.105: control repeats of movement sequences
- 0.0.104: add methods to apply movements to objects:
  ```py
  # single movement
  device.apply_movement(id='circle', direction=[1, 1], time_span=1, speed=3)
  # movement sequence
  with device.apply_movements(id='circle') as movement:
      movement(direction=[1, 0], time_span=1, speed=2)
      movement(direction=[-1, 0], time_span=1, speed=2)
  ```
  - adding example [playground_flappy.py](examples/playground_flappy.py)
- 0.0.103: change function annotation of `set_timeout(callback, time, repeat=1)` instead of `set_timeout(callback, interval, iteration_count=inf)`
- 0.0.102: add alias methods for `subscribe_async`: `set_timeout`, `schedule`, `execute_in`
- 0.0.101: introduce `move_to(id: str, pos: [x, y], via: [x, y])` method to make jumps easyier. Event `auto_movement_pos` is triggered when an auto movement within a sequence finished.
- 0.0.100: support image formats `.gif`, `.bmp`, `.webp`
- 0.0.99: introduce method `add_svg_to_playground(name: str, raw_svg: str)` to upload plain svg source text
- 0.0.98 fix iteration count
- 0.0.97: introduce sound - provide a `audio_tracks` source directory in `configure_playground` and start/stop sounds with `play_sound(name: str, id: Optional[str])` / `stop_sound(name: Optional[str], id: Optional[str])`
- 0.0.96 register multiple callback functions with `on(event, clbk)`
- 0.0.95 support `border_style` and `border_width` for sprites
