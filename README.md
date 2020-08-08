# Smartphone Connector

This simple package exposes methods to interact with smartphones connected to a [socket.io server](https://github.com/lebalz/socketio_server) instance.

## Socket Server

This package talks with a socket.io server, which defines the following events and actions.

A simple socket io server implementing this interface can be seen on [github.com/lebalz/socketio_server](https://github.com/lebalz/socketio_server). A running server is currently (August 2020) deployed under [io.lebalz.ch](https://io.lebalz.ch).

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
- `devices`
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
        'timeStamp': int, # time (seconds) since client loaded page,
        ...
    },
    ...
  ]
  ```
- `new_data`
  ```
  {
    'deviceId': str,
    'deviceNr': int,
    'timeStamp': int, # time (seconds) since client loaded page,
    'type': 'key' | 'acceleration' | 'gyro' | 'pointer' | 'notification'
    ...
  }
  ```
- `room_joined`
  ```
  {
    'deviceId': str,
    'isController': bool,
    'deviceNr': int,
    'socketId': str
  }
  ```
- `room_left`
  ```
  {
    'deviceId': str,
    'isController': bool,
    'deviceNr': int,
    'socketId': str
  }
  ```
- `error_msg`
  ```
  {
    'msg': str,
    'err': dict | str
  }
  ```

### Actions (for emitting)

- `emit('clear_data', { 'deviceId': str })`
- `emit('new_device', { 'deviceId': str })`
- `emit('get_all_data', { 'deviceId': str })`
- `emit('get_devices', { 'deviceId': str })`
- `emit('new_data', { 'deviceId': str, timeStamp: int, ... })`
- `emit('new_data', { 'deviceNr': int, timeStamp: int, ... })`
- `emit('join_room', { 'room': str })`
- `emit('leave_room', { 'room': str })`

### Callbacks (when fired when event is received)

when a function is assigned to one of the following props, this function will be called with the received data as its first argument

- `on_key`
- `on_pointer`
- `on_acceleration`
- `on_gyro`
- `on_sensor`
- `on_data`
- `on_broadcast_data`
- `on_all_data`
- `on_device`
- `on_devices`
- `on_error`
- `on_room_joined`
- `on_room_left`
- `on_client_device` - when a webbrowser client with the same `device_id` connects (the client device is passed) or disconnects (`None` is passed)

e.g.

```py
connector = Connector('https://io.lebalz.ch')
connector.on_key = lambda data: print('on key', data)
```

will print each received key

## Helpers

To convert the timestamps (seconds since epoch) to a python `timestamp` object, the function `to_datetime` may be used.

## Class ´Controller`

### Attributes

- `data` data dictionary. key: `device_id`, value: List containing all data messages
- `devices` all devices
- `device` the connected device (self)
- `server_url` the connected server. (readonly)
- `device_id` the device_id connected to. (readonly)
- `sio` the raw socket io client
- `room_members` list of devices and scripts connected to this room
- `joined_rooms` all rooms which this client gets events from
- `device_count` the count of all devices and scripts currently connected to the server
- `client_count` the count of client devices connected over a webbrowser to the server (e.g. Smartphones)
- `room_member_count` count of other clients/scripts connected to this room. All these clients will receive the events of this room too.
- `client_device` the first found device connected over a webbrowser with the same `device_id`
- `client_devices` all devices connected over a webbrowser to the server

## Methods

- `emit(event, data={}, broadcast=False, unicast_to=None)`
  - `event`: name of the emitted event
  - `data`: whatever data you want to send
  - `broadcast`: when set to true, the event is broadcasted to all currently connected devices. Defaults to `False`
  - `unicast_to`: the message is sent exclusively to the device with the specified number. Has precedence over the `boradcast` option.
- `broadcast(data: {type: str})` broadcast's a `new_data` event. The data must contain two fields: `type` and a field equivalent to the `types` value.
  e.g.

  ```py
  connector.broadcast({'type': 'grid', 'grid': ['red']})
  connector.broadcast({'type': 'color', 'color': 'red'})
  ```
- `unicast_to(data: {'type': str}, device_nr: int)` unicast's a `new_data` event to the specified device. The data must contain two fields: `type` and a field equivalent to the `types` value.
  e.g.

  ```py
  connector.unicast({'type': 'grid', 'grid': ['red']}, 2)
  connector.unicast({'type': 'color', 'color': 'red'}, 1)
  ```
- `clear_data()` clears all data on the server related to this `device_id``
- `all_broadcast_data(data_type: str = None) -> List[DataMsg]` returns all broadcasted data of the given type. When no type is provided, all broadcasted data is returned.
- `latest_broadcast_data(data_type: str = None) -> DataMsg | None` returns the latest received data of the given type. None is returned when no data is present.
- `all_data(data_type: str = None, device_id: str = None) -> List[DataMsg]` returns all data with the given type and from the given device_id.
- `latest_data(data_type: str = None, device_id: str = None) -> DataMsg | None` returns the latest data (last received) with the given type and from the given device_id.
- `set_grid(grid, device_id: str = None, device_nr: int = None, broadcast: bool = False)` sends a `new_data` event with the given grid. the grid can be either a `1D` or `2D` array containing css colors.
- `set_color(color: str, device_id: str = None, device_nr: int = None, broadcast: bool = False)` sets the color of the color panel
- `disconnect()`
- `join_room(deviceId: str)` joins the room of another device. This means that all events from this other device will be streamed to this client too.
- `leave_room(deviceId: str)` leaves the room of this device. This means no events from this device are received.

## Example

```py
from smartphone_connecter import Connector
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
rm -rf build/ dist/ smartphone_connector.egg-info/
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
```
