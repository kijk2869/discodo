import argparse
import asyncio
import logging
import os
import sys

import colorlog

from .node import server
from .updater import check_version

log = logging.getLogger("discodo")


class loggingFilter(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


stdoutHandler = logging.StreamHandler(sys.stdout)
stderrHandler = logging.StreamHandler(sys.stderr)
stdoutHandler.addFilter(loggingFilter(logging.WARNING))


def setLoggingLevel(level):
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


def addLoggingHandler(logger):
    logger.addHandler(stdoutHandler)
    logger.addHandler(stderrHandler)


parser = argparse.ArgumentParser("discodo")

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

genParser = parser.add_argument_group("General Option")

genParser.add_argument(
    "--update", "-U", action="store_true", help="Auto update when there is new version."
)

logParser = parser.add_argument_group("Logging Option")

logParser.add_argument(
    "--verbose", "-v", action="store_true", help="Print various debugging information"
)

args = parser.parse_args()

if args.verbose:
    setLoggingLevel(logging.DEBUG)
else:
    setLoggingLevel(logging.INFO)

os.environ["VCTIMEOUT"] = str(args.timeout)
os.environ["DEFAULTVOLUME"] = str(round(args.default_volume / 100, 3))
os.environ["DEFAULTCROSSFADE"] = str(args.default_crossfade)
os.environ["DEFAULAUTOPLAY"] = "1" if args.default_autoplay else "0"
os.environ["PRELOAD_TIME"] = str(args.preload)
os.environ["WSINTERVAL"] = str(args.ws_interval)
os.environ["WSTIMEOUT"] = str(args.ws_timeout)
os.environ["AUDIOBUFFERLIMIT"] = str(args.bufferlimit)
os.environ["PASSWORD"] = str(args.auth)
os.environ["AUTO_UPDATE"] = "1" if args.update else "0"

check_version()

loop = asyncio.get_event_loop()
loop.create_task(
    server.create_server(host=args.host, port=args.port, return_asyncio_server=True)
)
loop.run_forever()
