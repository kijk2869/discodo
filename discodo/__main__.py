import argparse
import asyncio
import json
import logging
import os
import sys

import psutil
from rich.logging import RichHandler

from . import __version__
from .config import Config
from .errors import OpusLoadError
from .natives import opus

log = logging.getLogger("discodo")


if not opus.isLoaded() and not opus.loadDefaultOpus():
    raise OpusLoadError(
        "Cannot load libopus, please check your python architecture."
        if sys.platform == "win32"
        else "Cannot load libopus, please install `libopus-dev` if you are using linux."
    )

accessHandler = RichHandler(rich_tracebacks=True)
accessHandler.setFormatter(
    logging.Formatter("%(name)s :\t%(request)s %(message)s %(status)d %(byte)d")
)

genericHandler = RichHandler(rich_tracebacks=True)
genericHandler.setFormatter(logging.Formatter("%(name)s :\t%(message)s"))


def setLoggingLevel(level) -> None:
    for logger in [log, logging.getLogger("libav")]:
        logger.setLevel(level)
        logger.addHandler(genericHandler)


logging.getLogger("sanic").setLevel(logging.INFO)

logging.getLogger("sanic.root").addHandler(genericHandler)

errorLogger = logging.getLogger("sanic.error")
errorLogger.propagate = True
errorLogger.addHandler(genericHandler)

accessLogger = logging.getLogger("sanic.access")
accessLogger.propagate = True
accessLogger.addHandler(accessHandler)

parser = argparse.ArgumentParser("discodo")


def is_valid_file(parser, args):
    if not os.path.exists(args):
        parser.error(f"The file {args} does not exist!")

    with open(args, "r") as fp:
        return json.load(fp)


def is_valid_json(parser, args):
    try:
        return json.loads(args)
    except Exception as e:
        parser.error(f"The json {args} is not valid!")


parser.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s {__version__}",
    help="Config json file path (default: None)",
)

parser.add_argument(
    "--config",
    type=lambda args: is_valid_file(parser, args),
    default={},
    help="Config json file path (default: None)",
)

parser.add_argument(
    "--config-json",
    type=lambda args: is_valid_json(parser, args),
    default={},
    help="Config json string (default: None)",
)

webGroup = parser.add_argument_group("Webserver Option")

webGroup.add_argument(
    "--host",
    "-H",
    type=str,
    default="0.0.0.0",
    help="the hostname to listen on (default: 0.0.0.0)",
)
webGroup.add_argument(
    "--port",
    "-P",
    type=int,
    default=8000,
    help="the port of the webserver (default: 8000)",
)
webGroup.add_argument(
    "--auth",
    "-A",
    type=str,
    default="hellodiscodo",
    help="the password of the webserver (default: hellodiscodo)",
)
webGroup.add_argument(
    "--ws-interval",
    type=int,
    default=15,
    help="heartbeat interval between discodo server and client (default: 15)",
)
webGroup.add_argument(
    "--ws-timeout",
    type=int,
    default=60,
    help="seconds to close connection there is no respond from client (default: 60)",
)

networkGroup = parser.add_argument_group("Network Option")
networkGroup.add_argument(
    "--ip",
    type=str,
    action="append",
    default=[],
    help="Client-side IP blocks to use",
)
networkGroup.add_argument(
    "--exclude-ip",
    type=str,
    action="append",
    default=[],
    help="Client-side IP addresses not to use",
)

playerGroup = parser.add_argument_group("Player Option")

playerGroup.add_argument(
    "--default-volume",
    type=float,
    default=1.0,
    help="player's default volume (default: 1.0)",
)
playerGroup.add_argument(
    "--default-crossfade",
    type=float,
    default=10.0,
    help="player's default crossfade seconds (default: 10.0)",
)
playerGroup.add_argument(
    "--default-autoplay",
    type=bool,
    default=True,
    help="player's default auto related play state (default: True)",
)
playerGroup.add_argument(
    "--bufferlimit",
    type=int,
    default=5,
    help="seconds of audio will be loaded in buffer (default: 5)",
)
playerGroup.add_argument(
    "--preload",
    type=int,
    default=10,
    help="seconds to load next song before this song ends (default: 10)",
)
playerGroup.add_argument(
    "--timeout",
    type=int,
    default=300,
    help="seconds to cleanup player when connection of discord terminated (default: 300)",
)

extExtractorParser = parser.add_argument_group("Extra Extractor Option")

extExtractorParser.add_argument(
    "--enabled-resolver",
    action="append",
    default=[],
    help="Extra resolvers to enable (Support melon and spotify)",
)
extExtractorParser.add_argument(
    "--spotify-id",
    type=str,
    default=None,
    help="Spotify API id (default: None)",
)
extExtractorParser.add_argument(
    "--spotify-secret",
    type=str,
    default=None,
    help="Spotify API secret (default: None)",
)

logParser = parser.add_argument_group("Logging Option")

logParser.add_argument(
    "--verbose", "-v", action="store_true", help="Print various debugging information"
)


def main():
    args = parser.parse_args()

    if not args.config and not args.config_json:
        verbose = args.verbose

        Config.HOST = args.host
        Config.PORT = args.port
        Config.PASSWORD = args.auth
        Config.HANDSHAKE_INTERVAL = args.ws_interval
        Config.HANDSHAKE_TIMEOUT = args.ws_timeout
        Config.IPBLOCKS = args.ip
        Config.EXCLUDEIPS = args.exclude_ip
        Config.DEFAULT_AUTOPLAY = args.default_autoplay
        Config.DEFAULT_VOLUME = args.default_volume
        Config.DEFAULT_CROSSFADE = args.default_crossfade
        Config.BUFFERLIMIT = args.bufferlimit
        Config.VCTIMEOUT = args.timeout
        Config.ENABLED_EXT_RESOLVER = args.enabled_resolver
        Config.SPOTIFY_ID = args.spotify_id
        Config.SPOTIFY_SECRET = args.spotify_secret
    else:
        verbose = (args.config or args.config_json).pop("verbose", False)

        Config.from_dict(args.config or args.config_json)

    if verbose:
        setLoggingLevel(logging.DEBUG)
    else:
        setLoggingLevel(logging.INFO)

    if hasattr(psutil, "HIGH_PRIORITY_CLASS"):
        psutil.Process(os.getpid()).nice(psutil.HIGH_PRIORITY_CLASS)

    try:
        import uvloop
    except ModuleNotFoundError:
        loop = asyncio.get_event_loop()
    else:
        loop = uvloop.new_event_loop()

        log.debug(f"uvloop {uvloop.__version__} detected, will use {loop}")

    asyncio.set_event_loop(loop)

    if log.level == logging.DEBUG:
        loop.set_debug(True)
    else:
        loop.set_debug(False)

    from .server import server

    loop.create_task(
        server.create_server(
            host=Config.HOST, port=Config.PORT, return_asyncio_server=True
        )
    )
    loop.run_forever()


if __name__ == "__main__":
    main()
