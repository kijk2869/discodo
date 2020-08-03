# Websocket Connection

## Payloads

#### Payload Structure

|Key|Type|Description|
|---|----|-----------|
|op|string|the event name for this payload|
|d|mixed (Mostly JSON)|the event data for this payload|

### Sending Payloads

#### Example Payload Dispatch

```json
{
    "op": "the event name",
    "d": {}
}
```

## Connecting to Discodo

### Connecting

#### Websockets Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discoo server|

If you missed headers or mismatched, the client recieves FORBIDDEN payload.

#### Example FORBIDDEN

```json
{
    "op": "FORBIDDEN",
    "d": "why the connection forbidden"
}
```

When connected, the client recieves HELLO payload with the connection's heartbeat interval.

#### Example HELLO

```json
{
    "op": "HELLO",
    "d": {
        "heartbeat_interval": 15.0
    }
}
```

### Heartbeating

Recieveing HELLO payload, the client should begin sending HEARTBEAT payloads every `heartbeat_interval` seconds, until the connection closed.

#### Exmaple HEARTBEAT Payload

```json5
{
    "op": "HEARTBEAT",
    "d": 1596417937 // timestamp
}
```

Event Data (`d`) can be None, Server will echo them.

#### Example HEARTBEAT_ACK

```json5
{
    "op": "HEARTBEAT_ACK",
    "d": 1596417937 // timestamp
}
```

### Identifying

The client must send IDENTIFY payload to configure the audio manager.

#### Example IDENTIFY Payload

```json
{
    "op": "IDENTIFY",
    "d": {
        "user_id": "my bot id",
        "session_id": "my bot session id to discord"
    }
}
```

`user_id` and `session_id` can be `None`.

In this case, Server will fetch them from `READY` and `RESUME` payloads of discord.

### Disconnections

If the connection is closed, Server will clean up manager and sources.