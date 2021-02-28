Installation
============

Prerequisites
-------------

Discodo works with **Python 3.7 or higher.**

Ealier versions of Python may not be worked.

Dependencies
------------

On Linux environments, below dependencies are required:

- ``python3-dev``
- ``libopus-dev``
- ``libnacl-dev``

PyAV depends upon several libraries from FFmpeg:

- ``libavcodec-dev``
- ``libavdevice-dev``
- ``libavfilter-dev``
- ``libavformat-dev``
- ``libavutil-dev``
- ``libswresample-dev``
- ``libswscale-dev``
- ``pkg-config``

Mac OS X
^^^^^^^^

.. code-block:: console

    $ brew install opus pkg-config ffmpeg

Ubuntu
^^^^^^

.. code-block:: console

    $ sudo apt update

    # Our general dependencies
    $ sudo apt install --no-install-recommends -y python3-dev libopus-dev libnacl-dev

    # PyAV dependencies
    $ sudo apt install --no-install-recommends -y \
        pkg-config libavformat-dev libavcodec-dev libavdevice-dev \
        libavutil-dev libswscale-dev libavresample-dev libavfilter-dev

Installing
----------

PyPI
^^^^

.. code-block:: console

    $ python3 -m pip install -U discodo

Docker
^^^^^^

.. code-block:: console

    $ docker pull kijk2869/discodo:release-2.3.13

Execution
---------

You can see additional options with the ``--help`` flag.

.. code-block:: console

    $ python3 -m discodo [-h] [--version] [--config CONFIG] [--config-json CONFIG_JSON] [--host HOST] [--port PORT]
               [--auth AUTH] [--ws-interval WS_INTERVAL] [--ws-timeout WS_TIMEOUT] [--ip IP] [--exclude-ip EXCLUDE_IP]
               [--default-volume DEFAULT_VOLUME] [--default-crossfade DEFAULT_CROSSFADE]
               [--default-autoplay DEFAULT_AUTOPLAY] [--bufferlimit BUFFERLIMIT] [--preload PRELOAD]
               [--timeout TIMEOUT] [--enabled-resolver ENABLED_RESOLVER] [--spotify-id SPOTIFY_ID]
               [--spotify-secret SPOTIFY_SECRET] [--verbose]

Options
-------

.. code-block:: console

    optional arguments:
    -h, --help            show this help message and exit
    --version             Config json file path (default: None)
    --config CONFIG       Config json file path (default: None)
    --config-json CONFIG_JSON
                            Config json string (default: None)

    Webserver Option:
    --host HOST, -H HOST  the hostname to listen on (default: 0.0.0.0)
    --port PORT, -P PORT  the port of the webserver (default: 8000)
    --auth AUTH, -A AUTH  the password of the webserver (default: hellodiscodo)
    --ws-interval WS_INTERVAL
                            heartbeat interval between discodo server and client (default: 15)
    --ws-timeout WS_TIMEOUT
                            seconds to close connection there is no respond from client (default: 60)

    Network Option:
    --ip IP               Client-side IP blocks to use
    --exclude-ip EXCLUDE_IP
                            Client-side IP addresses not to use

    Player Option:
    --default-volume DEFAULT_VOLUME
                            player's default volume (default: 100)
    --default-crossfade DEFAULT_CROSSFADE
                            player's default crossfade seconds (default: 10.0)
    --default-autoplay DEFAULT_AUTOPLAY
                            player's default auto related play state (default: True)
    --bufferlimit BUFFERLIMIT
                            seconds of audio will be loaded in buffer (default: 5)
    --preload PRELOAD     seconds to load next song before this song ends (default: 10)
    --timeout TIMEOUT     seconds to cleanup player when connection of discord terminated (default: 300)

    Extra Extractor Option:
    --enabled-resolver ENABLED_RESOLVER
                            Extra resolvers to enable (Support melon and spotify)
    --spotify-id SPOTIFY_ID
                            Spotify API id (default: None)
    --spotify-secret SPOTIFY_SECRET
                            Spotify API secret (default: None)

    Logging Option:
    --verbose, -v         Print various debugging information

Config file
^^^^^^^^^^^

.. code-block:: json

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
        "ENABLED_EXT_RESOLVER": [
            "melon",
            "vibe"
        ],
        "SPOTIFY_ID": null,
        "SPOTIFY_SECRET": null
    }
