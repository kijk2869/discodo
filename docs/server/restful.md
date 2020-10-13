# Restful API

## Routes

### GET /stat

Check the resource status of the server.

If you want to check size of players, use `GET_STAT` websocket payload.

#### Response

```json
{
    "UsedMemory": 0,
    "TotalMemory": 0,
    "ProcessLoad": 0,
    "TotalLoad": 0,
    "Cores": 0,
    "Threads": 0,
    "NetworkInbound": 0,
    "NetworkOutbound": 0
}
```

#### Response

```json
{
    "_type": "AudioData",
    "id": "...",
    "title": "...",
    "webpage_url": "...",
    "thumbnail": "...",
    "url": "...",
    "duration": 0,
    "is_live": true,
    "uploader": "...",
    "description": "...",
}
```

### GET /planner

Get the information of the Route Planner

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|

#### Response

```json
{
    "ipBlocks": [
        {
            "version": 4,
            "broadcast_address": "0.0.0.0",
            "size": 1
        }
    ],
    "failedAddresses": [
        {
            "address": "0.0.0.0",
            "status": 429,
            "failed_at": 0
        }
    ]
}
```

### POST /planner/unmark

Unmark an address on planner's failed list.

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|

#### Parameters

|Key|Type|Description|
|---|----|-----------|
|address|string|address to unmark|

#### Response

```json
{"status": 200}
```

### POST /planner/unmark/all

Unmark all address on planner's failed list.

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|

#### Response

```json
{"status": 200}
```

### GET /getSong

Get the information of the video searched on Youtube

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|

#### Parameters

|Key|Type|Description|
|---|----|-----------|
|query|string|query to search on youtube|

#### Response

```json5
{
    "source": {
        // Source Object
    }
}
```

### POST /putSong

Put source object to queue

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json5
{
    "source": {
        // Source Object
    }
}
```

#### Response

```json
{
    "index": 0
}
```

### POST /loadSource

Load query from youtube and put source object to queue

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json
{
    "query": "Something"
}
```

#### Response

```json5
{
    "source": {
        // Source Object
    }
}
```

### POST /setVolume

Set volume of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json5
{
    "volume": 1.0 // 0.0 ~ 2.0
}
```

#### Response

Empty `204`

### POST /setCrossfade

Set crossfade of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json
{
    "crossfade": 10.0
}
```

#### Response

Empty `204`

### POST /setGapless

Set gapless of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json
{
    "gapless": false
}
```

#### Response

Empty `204`

### POST /setAutoplay

Set autoplay of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json
{
    "autoplay": true
}
```

#### Response

Empty `204`

### POST /setFilter

Set filter of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json5
{
    "filter": {
        // libavfilter object
    }
}
```

#### Response

Empty `204`

### POST /seek

Seek source to offset of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json
{
    "offset": 10.0
}
```

#### Response

Empty `204`

### POST /skip

Skip source of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Data

```json
{
    "offset": 1
}
```

#### Response

Empty `204`

### POST /pause

Pause source of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Response

Empty `204`

### POST /resume

Resume source of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Response

Empty `204`

### POST /shuffle

Shuffle the queue of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Response

```json5
{
    "entries": [
        {
            // Source Object
        }
    ]
}
```

### POST /remove

Remove source object from the queue of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Response

```json5
{
    "removed": 1,
    "entries": [
        {
            // Source Object
        }
    ]
}
```

### GET /state

Get state of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Response

```json
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

### GET /queue

Get state of Guild ID

#### Headers

|Key|Type|Description|
|---|----|-----------|
|Authorization|string|Password for discodo server|
|User-ID|integer|Discord User ID|
|Guild-ID|integer|Discord Guild ID|

#### Response

```json5
{
    "entries": [
        {
            // Source Object
        }
    ]
}
```