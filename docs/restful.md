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
    "description": "...",
    "duration": 0,
    "id": "...",
    "is_live": null,
    "playlist": null,
    "thumbnail": "...",
    "title": "...",
    "uploader": "...",
    "webpage_url": "...
}
```