# Websocket Payloads

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
        "volume": 100 // 0~100
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

### loadSong

```json
{
    "op": "loadSong",
    "d": {
        "guild_id": "guild id of audio player",
        "query": "something to search"
    }
}
```

### putSong

```json5
{
    "op": "putSong",
    "d": {
        "guild_id": "guild id of audio player",
        "song": {
            // Song Object
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

### changePause

```json
{
    "op": "changePause",
    "d": {
        "guild_id": "guild id of audio player"
    }
}
```

### repeat

```json
{
    "op": "repeat",
    "d": {
        "guild_id": "guild id of audio player",
        "repeat": false
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

### requestLyrics

```json
{
    "op": "requestLyrics",
    "d": {
        "guild_id": "guild id of audio player",
        "language": "en"
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