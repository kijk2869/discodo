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
