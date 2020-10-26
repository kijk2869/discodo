# Introduction

## Requirement

Discodo works with **Python 3.7 or higher**.

Ealier versions of Python may not be worked.

## Installing

You can get this library from [**PyPI**](https://pypi.org/project/discodo/):

```sh
python3 -m pip install --upgrade discodo
```

On Linux environments, more dependencies are required:

- python3-dev
- libopus-dev
- libnacl-dev

## Execution

You can see additional options with the `--help` flag.

```sh
python3 -m discodo [-h] [--config CONFIG] [--host HOST] [--port PORT] [--auth AUTH] [--ws-interval WS_INTERVAL]
               [--ws-timeout WS_TIMEOUT] [--ip IP] [--exclude-ip EXCLUDE_IP] [--default-volume DEFAULT_VOLUME]
               [--default-crossfade DEFAULT_CROSSFADE] [--default-gapless DEFAULT_GAPLESS]
               [--default-autoplay DEFAULT_AUTOPLAY] [--bufferlimit BUFFERLIMIT] [--preload PRELOAD]
               [--timeout TIMEOUT] [--verbose]
```

## Options

```
optional arguments:
  -h, --help            show this help message and exit
  --version             show this library's version and exit
  --config CONFIG       Config json file path (default: None)

Webserver Option:
  --host HOST, -H HOST  the hostname to listen on (default: 0.0.0.0)
  --port PORT, -P PORT  the port of the webserver (default: 8000)
  --auth AUTH, -A AUTH  the password of the webserver (default: hellodiscodo)
  --ws-interval WS_INTERVAL
                        heartbeat interval between discodo server and client (default: 15)
  --ws-timeout WS_TIMEOUT
                        seconds to close connection there is no respond from client (default: 60)

Network Option:
  --ip IP               Client-side IP addresses to use
  --exclude-ip EXCLUDE_IP
                        Client-side IP addresses not to use

Player Option:
  --default-volume DEFAULT_VOLUME
                        player's default volume (default: 100)
  --default-crossfade DEFAULT_CROSSFADE
                        player's default crossfade seconds (default: 10.0)
  --default-gapless DEFAULT_GAPLESS
                        player's default gapless state (default: False)
  --default-autoplay DEFAULT_AUTOPLAY
                        player's default auto related play state (default: True)
  --bufferlimit BUFFERLIMIT
                        seconds of audio will be loaded in buffer (default: 5)
  --preload PRELOAD     seconds to load next song before this song ends (default: 10)
  --timeout TIMEOUT     seconds to cleanup player when connection of discord terminated (default: 300)

Logging Option:
  --verbose, -v         Print various debugging information
```

### Config file

Must pass `json` file to `--config` flag.

```json
{
    "HOST": "0.0.0.0",
    "PORT": 8000,
    "PASSWORD": "hellodiscodo",
    "HANDSHAKE_INTERVAL": 15,
    "HANDSHAKE_TIMEOUT": 60,
    "IPBLOCKS": [],
    "EXCLUDEIPS": [],
    "DEFAULT_AUTOPLAY": true,
    "DEFAULT_VOLUME": 1,
    "DEFAULT_CROSSFADE": 10,
    "DEFAULT_GAPLESS": false,
    "BUFFERLIMIT": 5,
    "PRELOAD_TIME": 10,
    "VCTIMEOUT": 300,
    "ENABLED_EXT_EXTRACTOR": [
        "melon",
        "spotify"
    ],
    "SPOTIFY_ID": null,
    "SPOTIFY_SECRET": null
}
```