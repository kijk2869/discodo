import asyncio
import json
import logging
import os
import secrets
import sys

import aiohttp
from websockets import ConnectionClosed

from .. import __dirname
from ..errors import NodeNotConnected, VoiceClientNotFound
from ..utils import EventDispatcher, tcp
from .gateway import NodeConnection
from .models import ensureQueueObjectType
from .voice_client import VoiceClient

log = logging.getLogger("discodo.client.node")

LocalNodeProc = None


def getLocalNode():
    return LocalNodeProc


async def launchLocalNode(**options):
    global LocalNodeProc

    if LocalNodeProc and LocalNodeProc.returncode is not None:
        raise ValueError("LocalNode already launched.")

    options["HOST"] = "127.0.0.1"
    options["PORT"] = tcp.getFreePort()
    options["PASSWORD"] = secrets.token_hex()

    log.info(
        f"trying to spawn local node process on {options['HOST']}:{options['PORT']}"
    )

    os.environ["PYTHONPATH"] = os.path.dirname(__dirname)

    LocalNodeProc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "discodo", "--config-json", json.dumps(options)
    )

    LocalNodeProc.HOST = options["HOST"]
    LocalNodeProc.PORT = options["PORT"]
    LocalNodeProc.PASSWORD = options["PASSWORD"]

    if LocalNodeProc.returncode:
        log.debug(
            f"while launching local node process, returned {LocalNodeProc.returncode}"
        )

        raise SystemError("Cannot launch discodo subprocess.")

    loop = asyncio.get_event_loop()

    for _ in range(30):
        try:
            transport, _ = await loop.create_connection(
                asyncio.Protocol, host=LocalNodeProc.HOST, port=LocalNodeProc.PORT
            )
            transport.close()
        except (OSError, ConnectionRefusedError):
            await asyncio.sleep(1)
            continue

        return LocalNodeProc

    LocalNodeProc.kill()

    raise SystemError("Testing local node connection timed out.")


class Node:
    r"""Represents a discodo node connection.

    :var discodo.DPYClient client: The client which the node is binded.
    :var Optional ws: The websocket gateway the client is currently connected to.
    :var EventDispatcher dispatcher: The event dispatcher that the client dispatches events.
    :var asyncio.AbstractEventLoop loop: The event loop that the client uses for operation.
    :var str host: The host of the node to connect to.
    :var int port: The port of the node to connect to.
    :var str password:  The password of the node to connect to.
    :var int user_id: This bot's ID
    :var Optional[int] shard_id: This bot's shard ID, could be ``None``
    :var Optional[str] region: Region set when registering a node
    :var dict voiceClients: A dictionary consisting of pairs of guild IDs and voice clients."""

    def __init__(
        self,
        client,
        host,
        port,
        user_id,
        shard_id=None,
        password="hellodiscodo",
        region=None,
    ):
        self.client = client

        self.ws = None
        self.session = aiohttp.ClientSession()

        self.dispatcher = EventDispatcher()
        self.dispatcher.onAny(self.onAnyEvent)

        self.loop = asyncio.get_event_loop()

        self.host = host
        self.port = port
        self.password = password

        self.user_id = user_id
        self.shard_id = shard_id
        self.region = region

        self._polling = None
        self.voiceClients = {}
        self.connected = asyncio.Event()

    def __del__(self):
        self.loop.call_soon_threadsafe(
            lambda: self.loop.create_task(self.session.close())
        )

    def __repr__(self) -> str:
        return (
            f"<Node connected={self.is_connected} host={self.host} port={self.port}"
            + f" region={self.region} voiceClients={len(self.voiceClients)}>"
        )

    @property
    def URL(self) -> str:
        r"""Represents the restful api url of the node.

        :rtype: str"""

        return f"http://{self.host}:{self.port}"

    @property
    def WS_URL(self) -> str:
        r"""Represents the websocket url of the node.

        :rtype: str"""

        return f"ws://{self.host}:{self.port}/ws"

    @property
    def is_connected(self) -> bool:
        r"""Represents whether the node is connected.

        :rtype: bool"""

        return self.connected.is_set() and self.ws and self.ws.is_connected

    async def connect(self):
        r"""Connect to the node.

        :raises ValueError: The node is already connected."""

        if self.connected.is_set():
            raise ValueError("Node already connected")

        if self.ws and self.ws.is_connected:
            await self.ws.close()

        self.ws = await NodeConnection.connect(self)
        self.voiceClients = {}
        self.connected.set()

        if not self._polling or self._polling.done():
            self._polling = self.loop.create_task(self.pollingWS())

        await self.send(
            "IDENTIFY", {"user_id": self.user_id, "shard_id": self.shard_id}
        )

    async def close(self):
        """ some action to do after disconnected from node """

        ...

    async def destroy(self):
        r"""Destroy the node and remove from the client."""

        if self._polling and not self._polling.done():
            self._polling.cancel()

        if self.ws and not self.ws.closed:
            await self.ws.close()
        self.ws = None

        self.connected.clear()
        self.voiceClients = {}

        if self in self.client.Nodes:
            self.client.Nodes.remove(self)

    async def pollingWS(self) -> None:
        while True:
            try:
                Operation, Data = await self.ws.poll()
            except (asyncio.TimeoutError, ConnectionClosed):
                self.connected.clear()

                if self.ws:
                    await self.ws.close()
                self.ws = None

                await self.close()
                self.voiceClients = {}

                return

            if Data and isinstance(Data, dict) and "guild_id" in Data:
                VC = self.getVC(Data["guild_id"], safe=True)
                if VC:
                    Data = ensureQueueObjectType(VC, Data)

                    VC.dispatcher.dispatch(Operation, Data)

            self.dispatcher.dispatch(Operation, Data)

    async def send(self, op, data=None):
        """Send websocket payload to the node

        :param str op: Operation name of the payload
        :param Optional[dict] data: Operation data to send with

        :raises discodo.NodeNotConnected: The node is not connnected."""

        if not self.ws:
            raise NodeNotConnected

        return await self.ws.sendJson({"op": op, "d": data})

    async def onResumed(self, Data):
        for voice_client in self.voiceClients:
            voice_client.__del__()

        for guild_id, vc_data in Data["voice_clients"].items():
            self.voiceClients[int(guild_id)] = VoiceClient(
                self, vc_data["id"], guild_id
            )

    async def onAnyEvent(self, Operation, Data):
        if Operation == "RESUMED":
            await self.onResumed(Data)
        if Operation == "VC_CREATED":
            guild_id = int(Data["guild_id"])
            self.voiceClients[guild_id] = VoiceClient(self, Data["id"], guild_id)
        if Operation == "VC_DESTROYED":
            guild_id = int(Data["guild_id"])
            if guild_id in self.voiceClients:
                self.voiceClients[guild_id].__del__()

    def getVC(self, guildID, safe=False):
        r"""Get a voice client from the guild.

        :param int guildID: guild ID from which to get the voice client.
        :param bool safe: Whether to raise an exception when the voice client cannot be found, defaults to ``False``.

        :raises discodo.VoiceClientNotFound: The voice client was not found and the ``safe`` value is ``False``.

        :rtype: discodo.VoiceClient"""

        if not int(guildID) in self.voiceClients and not safe:
            raise VoiceClientNotFound

        return self.voiceClients.get(int(guildID))

    async def discordDispatch(self, payload):
        r"""Dispatch the discord payload to the node.

        .. note::
            If you are using :py:class:`discodo.DPYClient`, you don't have to use this.

        :param dict payload: The event data from the discord."""

        if not payload["t"] in [
            "READY",
            "RESUME",
            "VOICE_STATE_UPDATE",
            "VOICE_SERVER_UPDATE",
        ]:
            return

        return await self.send("DISCORD_EVENT", payload)

    async def getStatus(self):
        r"""Get status like cpu usage from the node with websocket.

        :rtype: dict"""

        await self.send("GET_STATUS")

        return await self.dispatcher.wait_for("STATUS", timeout=10.0)


class Nodes(list):
    r"""Represents a discodo node connection list.

    You can also use it like :py:class:`list`."""

    async def connect(self):
        """Try to connect to all registered nodes.

        :rtype: list"""

        task_list: list = list(map(lambda Node: Node.connect(), self))

        if not task_list:
            return []

        Done, _ = await asyncio.wait(task_list, return_when="ALL_COMPLETED")

        return list(map(lambda task: task.result(), Done))

    async def getStatus(self):
        """Try to get status from all registered nodes.

        :rtype: list"""

        def get_task(Item):
            if Item.is_connected:
                return Item.getStatus()

        task_list: list = list(filter(None, map(get_task, self)))

        if not task_list:
            return []

        Done, _ = await asyncio.wait(task_list, return_when="ALL_COMPLETED")

        return list(map(lambda task: task.result(), Done))
