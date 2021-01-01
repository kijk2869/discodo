import argparse
import asyncio
import json
import logging
import os
import sys

import colorlog
import psutil

from . import __version__
from .config import Config
from .natives import opus

log = logging.getLogger("discodo")


if not opus.isLoaded() and not opus.loadDefaultOpus():
    raise ValueError(
        "Cannot load libopus, please install `libopus-dev` if you are using linux."
    )


class loggingFilter(logging.Filter):
    def __init__(self, level) -> None:
        self.level = level

    def filter(self, record) -> bool:
        return record.levelno < self.level


stdoutHandler = logging.StreamHandler(sys.stdout)
stderrHandler = logging.StreamHandler(sys.stderr)
stdoutHandler.addFilter(loggingFilter(logging.WARNING))


def setLoggingLevel(level) -> None:
    for logger in [log, logging.getLogger("libav")]:
        addLoggingHandler(logger)
        logger.setLevel(logging.DEBUG)
        stdoutHandler.setLevel(level)
        stderrHandler.setLevel(max(level, logging.WARNING))


ColoredFormatter = colorlog.ColoredFormatter(
    "[%(asctime)s] [%(filename)s] [%(name)s:%(bold)s%(module)s%(reset)s] %(log_color)s[%(levelname)s]%(reset)s: %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        "DEBUG": "green",
        "INFO": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
    secondary_log_colors={},
    style="%",
)
stdoutHandler.setFormatter(ColoredFormatter)
stderrHandler.setFormatter(ColoredFormatter)


def addLoggingHandler(logger) -> None:
    logger.addHandler(stdoutHandler)
    logger.addHandler(stderrHandler)


parser = argparse.ArgumentParser("discodo")


def is_valid_file(parser, args):
    if not os.path.exists(args):
        parser.error(f"The file {args} does not exist!")

    with open(args, "r") as fp:
        return json.load(fp)


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
    type=int,
    default=100,
    help="player's default volume (default: 100)",
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

args = parser.parse_args()

if not args.config:
    verbose = args.verbose

    Config.HOST = args.host
    Config.PORT = args.port
    Config.PASSWORD = args.auth
    Config.HANDSHAKE_INTERVAL = args.ws_interval
    Config.HANDSHAKE_TIMEOUT = args.ws_timeout
    Config.IPBLOCKS = args.ip
    Config.EXCLUDEIPS = args.exclude_ip
    Config.DEFAULT_AUTOPLAY = args.default_autoplay
    Config.DEFAULT_VOLUME = round(args.default_volume / 100, 3)
    Config.DEFAULT_CROSSFADE = args.default_crossfade
    Config.BUFFERLIMIT = args.bufferlimit
    Config.VCTIMEOUT = args.timeout
    Config.ENABLED_EXT_RESOLVER = args.enabled_resolver
    Config.SPOTIFY_ID = args.spotify_id
    Config.SPOTIFY_SECRET = args.spotify_secret
else:
    verbose = args.config.pop("verbose", False)

    Config.from_dict(args.config)

if verbose:
    setLoggingLevel(logging.DEBUG)
else:
    setLoggingLevel(logging.INFO)

if __name__ == "__main__":
    if hasattr(psutil, "HIGH_PRIORITY_CLASS"):
        psutil.Process(os.getpid()).nice(psutil.HIGH_PRIORITY_CLASS)

    loop = asyncio.get_event_loop()

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
