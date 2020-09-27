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
    "d": "ClientManager initialized."
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

```json5
{
    "op": "setVolume",
    "d": {
        "guild_id": "guild id of audio player",
        "volume": 1.0 // 0.0 ~ 2.0
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

### setGapless

```json
{
    "op": "setGapless",
    "d": {
        "guild_id": "guild id of audio player",
        "gapless": true
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

```json5
{
    "op": "getSource",
    "d": {
        "guild_id": "guild id of audio player",
        "source": {
            // Source object
        }
    }
}
```

### loadSource

```json5
{
    "op": "loadSource",
    "d": {
        "guild_id": "guild id of audio player",
        "source": {
            // Source object
        }
    }
}
```

### putSource

```json5
{
    "op": "putSong",
    "d": {
        "guild_id": "guild id of audio player",
        "source": {
            // Source object
        }
    }
}
```

### REQUIRE_NEXT_SOURCE

**If `autoplay` is on, related song will be added after this event.**

```json5
{
    "op": "REQUIRE_NEXT_SOURCE",
    "d": {
        "guild_id": "guild id of audio player",
        "current": {
            // Sourcec object
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
            // source objects
        ]
    }
}
```

### State

```json5
{
    "op": "getState",
    "d": {
        "id": "...",
        "guild_id": "...",
        "channel_id": "...",
        "state": "...",
        "current": {},
        "duration": 0.0,
        "position": 0.0,
        "remain": 0.0,
        "options": {
            "autoplay": true,
            "volume": 1.0,
            "crossfade": 10.0,
            "gapless": false,
            "filter": {}
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

### shuffle

```json5
{
    "op": "shuffle",
    "d": {
        "guild_id": "guild id of audio player",
        "entries": [
            // Source objects
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
            // Source object
        },
        "entries": [
            // Source objects
        ]
    }
}
```

### requestSubtitle

```json
{
    "op": "requestSubtitle",
    "d": {
        "guild_id": "guild id of audio player",
        "identify": "58b8b68f-e938-4699-b4ad-ffa262bf903d",
        "url": "..."
    }
}
```

### Subtitle

```json
{
    "op": "Subtitle",
    "d": {
        "guild_id": "guild id of audio player",
        "identify": "58b8b68f-e938-4699-b4ad-ffa262bf903d",
        "previous": "Previous Lyrics",
        "current": "Current Lyrics",
        "next": "Next Lyrics"
    }
}
```

### subtitleDone

```json
{
    "op": "subtitleDone",
    "d": {
        "guild_id": "guild id of audio player",
        "identify": "58b8b68f-e938-4699-b4ad-ffa262bf903d",
        "url": "..."
    }
}
```