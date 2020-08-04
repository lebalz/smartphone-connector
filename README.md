# Smartphone Connector

This simple package exposes methods to interact with smartphones connected to a [socket.io server](https://github.com/lebalz/socketio_server) instance.

## Socket Server

This package talks with a socket.io server, which defines the following interface:

### Events

- `device`
  ```py
  {
    'deviceId': str,
    'isController': bool,
    'deviceNr': int,
    'socketId': str
  }
  ```
- `devices``
  ```
  [
    {
        'deviceId': str,
        'isController': bool,
        'deviceNr': int,
        'socketId': str
    },
    ...
  ]
  ```
- `all_data`
  ```
  [
    {
        'deviceId': str,
        'timeStamp': int, # time (ms) since client loaded page,
        ...
    },
    ...
  ]
  ```
- `new_data`
  ```
  {
    'deviceId': str,
    'timeStamp': int, # time (ms) since client loaded page,
    ...
  }
  ```

### Actions (for emitting)

- `emit('clear_data', { 'deviceId': str })`
- `emit('new_device', { 'deviceId': str })`
- `emit('get_all_data', { 'deviceId': str })`
- `emit('get_devices', { 'deviceId': str })`
- `emit('new_data', { 'deviceId': str, timeStamp: int, ... })`
- `emit('new_data', { 'deviceNr': int, timeStamp: int, ... })`

A simple socket io server implementing this interface can be seen on [github.com/lebalz/socketio_server](https://github.com/lebalz/socketio_server). A running server is currently (August 2020) deployed under [io.lebalz.ch](https://io.lebalz.ch).


## Example

```py
from smartphone_connecter
connector = Connector('https://io.lebalz.ch', 'FooBar')

# draw a 3x3 checker board
connector.set_grid([
    ['black','white','black'],
    ['white','black','white'],
    ['black','white','black']
], broadcast=True)
```
results on all devices in the following screen.

When `broadcast` is set to `False` (default), only the `FooBar` devices display the checker board.

![checker board](checker_demo.png)


### Package and upload to pip
@see [this tutorial](https://packaging.python.org/tutorials/packaging-projects/)

```sh
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
```