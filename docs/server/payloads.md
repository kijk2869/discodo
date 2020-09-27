# Websocket Payloads

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

### Exception while execute payload

#### Example Payload Exception

```json
{
    "op": "the event name",
    "d": {
        "traceback": "Python Traceback"
    }
}
```

### HEARTBEAT

```json5
{
    "op": "HEARTBEAT",
    "d": 1596417937 // timestamp
}
```

### GET_STAT

```json5
{
    "op": "GET_STAT"
}
```

### IDENTIFY

```json
{
    "op": "IDENTIFY",
    "d": {
        "user_id": "my bot id",
        "session_id": "my bot session id to discord"
    }
}
```

### DISCORD_EVENT

```json5
{
    "op": "DISCORD_EVENT",
    "d": {
        // Discord Socket Event Payloads
    }
}
```
**Just need `READY`, `RESUME`, `VOICE_STATE_UPDATE`, `VOICE_SERVER_UPDATE` payloads**

## Audio Player

Can use after connect to voice channel.

### setVolume

```json5
{
    "op": "setVolume",
    "d": {
        "guild_id": "guild id of audio player",
        "volume": 1 // 0.0~2.0
    }
}
```

### setCrossfade

```json5
{
    "op": "setCrossfade",
    "d": {
        "guild_id": "guild id of audio player",
        "crossfade": 10 // seconds
    }
}
```

### setAutoplay

```json5
{
    "op": "setAutoplay",
    "d": {
        "guild_id": "guild id of audio player",
        "autoplay": true
    }
}
```

### setGapless

```json5
{
    "op": "setGapless",
    "d": {
        "guild_id": "guild id of audio player",
        "gapless": true // Can;t use with crossfade
    }
}
```

### setFilter

```json5
{
    "op": "setFilter",
    "d": {
        "guild_id": "guild id of audio player",
        "filter": {
            // libavfilter object
        }
    }
}
```

### getSource

```json
{
    "op": "getSource",
    "d": {
        "guild_id": "guild id of audio player",
        "query": "something to search"
    }
}
```

### loadSource

```json
{
    "op": "loadSource",
    "d": {
        "guild_id": "guild id of audio player",
        "query": "something to search"
    }
}
```

### putSong

```json5
{
    "op": "putSource",
    "d": {
        "guild_id": "guild id of audio player",
        "source": {
            // Source Object
        }
    }
}
```

### skip

```json5
{
    "op": "skip",
    "d": {
        "guild_id": "guild id of audio player",
        "offset": 1 // number to skip song.
    }
}
```

### seek

```json5
{
    "op": "seek",
    "d": {
        "guild_id": "guild id of audio player",
        "offset": 10 // seconds
    }
}
```

### getQueue

```json
{
    "op": "getQueue",
    "d": {
        "guild_id": "guild id of audio player"
    }
}
```

### getState

```json
{
    "op": "getState",
    "d": {
        "guild_id": "guild id of audio player"
    }
}
```

### pause

```json
{
    "op": "pause",
    "d": {
        "guild_id": "guild id of audio player"
    }
}
```

### resume

```json
{
    "op": "resume",
    "d": {
        "guild_id": "guild id of audio player"
    }
}
```

### shuffle

```json
{
    "op": "shuffle",
    "d": {
        "guild_id": "guild id of audio player"
    }
}
```

### remove

```json5
{
    "op": "remove",
    "d": {
        "guild_id": "guild id of audio player",
        "index": 1 // song number to remove
    }
}
```

### requestSubtitle

Either `lang` or `url` is requested.

Discodo supports `smi` and `srv1` type.

```json5
{
    "op": "requestSubtitle",
    "d": {
        "guild_id": "guild id of audio player",
        "lang": "en",
        "url": "..."
    }
}
```

### VC_DESTROY

```json
{
    "op": "VC_DESTROY",
    "d": {
        "guild_id": "guild id of audio player"
    }
}
```