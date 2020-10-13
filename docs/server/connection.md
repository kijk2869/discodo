# Websocket Connection

## Connecting to Discodo

### Connecting

#### Websockets Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|

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
        "user_id": "my bot id"
    }
}
```

### Resumed

If the same user id is connected before VC_TIMEOUT, it will be resumed.

#### Example RESUMED Payload

```json5
{
    "op": "RESUMED",
    "d": {
        "voice_clients": [
            [0, 0] // guild_id, voicechannel_id(can be null)
        ]
    }
}
```

If the client recieve RESUMED payload, must reconnect to the voice channel.

### Disconnections

If the connection is closed, Server will clean up manager and sources.
