# Websocket Events

### HEARTBEAT_ACK

```json5
{
    "op": "HEARTBEAT_ACK",
    "d": 1596417937 // timestamp
}
```

### STAT

```json
{
    "UsedMemory": 0,
    "TotalMemory": 0,
    "ProcessLoad": 0,
    "TotalLoad": 0,
    "Cores": 0,
    "Threads": 0,
    "NetworkInbound": 0,
    "NetworkOutbound": 0,
    "TotalPlayer": 0
}
```

### IDENTIFIED

```json
{
    "op": "IDENTIFIED",
    "d": "AudioManager initialized."
}
```

## Audio Player

May send after connect to voice channel.

### VC_CREATED

```json
{
    "op": "VC_CREATED",
    "d": {
        "guild_id": "guild id of audio player" 
    }
}
```

### VC_DESTROYED

```json
{
    "op": "VC_DESTROYED",
    "d": {
        "guild_id": "guild id of audio player" 
    }
}
```

### setVolume

```json
{
    "op": "setVolume",
    "d": {
        "guild_id": "guild id of audio player",
        "volume": 100
    }
}
```

### setCrossfade

```json
{
    "op": "setCrossfade",
    "d": {
        "guild_id": "guild id of audio player",
        "crossfade": 10.0
    }
}
```

### setAutoplay

```json
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

```json5
{
    "op": "loadSong",
    "d": {
        "guild_id": "guild id of audio player",
        "song": {
            // Song object
        }
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
            // Song object
        }
    }
}
```

### NeedNextSong

**If `autoplay` is on, related song will be added after this event.**

```json5
{
    "op": "NeedNextSong",
    "d": {
        "guild_id": "guild id of audio player",
        "current": {
            // Song object
        }
    }
}
```

### skip

```json
{
    "op": "skip",
    "d": {
        "guild_id": "guild id of audio player",
        "remain": 0
    }
}
```

### seek

```json
{
    "op": "seek",
    "d": {
        "guild_id": "guild id of audio player",
        "offset": 0
    }
}
```

### Queue

```json5
{
    "op": "Queue",
    "d": {
        "guild_id": "guild id of audio player",
        "entries": [
            // Song objects
        ]
    }
}
```

### State

```json5
{
    "op": "Queue",
    "d": {
        "guild_id": "guild id of audio player",
        "state": "playing",
        "current": {
            // Current Song Object
        },
        "position": {
            "duration": 10,
            "remain": 50
        },
        "options": {
            "autoplay": true,
            "volume": 100,
            "crossfade": 10.0,
            "filter": {
                // libavfilter object
            }
        }
    }
}
```

### pause

```json
{
    "op": "pause",
    "d": {
        "guild_id": "guild id of audio player",
        "state": "paused"
    }
}
```

### resume

```json
{
    "op": "pause",
    "d": {
        "guild_id": "guild id of audio player",
        "state": "playing"
    }
}
```

### changePause

```json5
{
    "op": "pause",
    "d": {
        "guild_id": "guild id of audio player",
        "state": "playing" // or paused
    }
}
```

### repeat

```json
{
    "op": "repeat",
    "d": {
        "guild_id": "guild id of audio player",
        "repeat": true
    }
}
```

### shuffle

```json5
{
    "op": "shuffle",
    "d": {
        "guild_id": "guild id of audio player",
        "entries": [
            // Song objects
        ]
    }
}
```

### remove

```json5
{
    "op": "remove",
    "d": {
        "guild_id": "guild id of audio player",
        "removed": {
            // Song object
        },
        "entries": [
            // Song objects
        ]
    }
}
```

### requestLyrics

```json
{
    "op": "requestLyrics",
    "d": {
        "guild_id": "guild id of audio player",
        "identify": "58b8b68f-e938-4699-b4ad-ffa262bf903d",
        "language": "en"
    }
}
```

### Lyrics

```json
{
    "op": "Lyrics",
    "d": {
        "guild_id": "guild id of audio player",
        "identify": "58b8b68f-e938-4699-b4ad-ffa262bf903d",
        "previous": "Previous Lyrics",
        "current": "Current Lyrics",
        "next": "Next Lyrics"
    }
}
```

### lyricsDone

```json
{
    "op": "lyricsDone",
    "d": {
        "guild_id": "guild id of audio player",
        "identify": "58b8b68f-e938-4699-b4ad-ffa262bf903d",
        "language": "en"
    }
}
```