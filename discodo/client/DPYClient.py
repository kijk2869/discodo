import asyncio
import contextlib
import itertools

import discord
import discord.ext

from ..errors import NodeNotConnected, VoiceClientNotFound
from ..utils.eventDispatcher import EventDispatcher
from .node import Node as OriginNode
from .node import Nodes, launchLocalNode


class NodeClient(OriginNode):
    async def onResumed(self, Data):
        await super().onResumed(Data)

        for guild_id, vc_data in Data["voice_clients"].items():
            guild = self.client.client.get_guild(int(guild_id))
            if "channel" in vc_data and vc_data["channel"]:
                channel = guild.get_channel(int(vc_data["channel"]))
                self.loop.create_task(self.client.connect(channel, self))
            else:
                self.loop.create_task(self.client.disconnect(guild))

    async def close(self) -> None:
        for guildId in self.voiceClients:
            self.loop.create_task(
                self.client.disconnect(self.client.client.get_guild(guildId))
            )


class DPYClient:
    r"""Represents a client connection that connects to Discodo.
    This class will interact with Discodo nodes.

    :param discord.Client class: The client of the bot with discord.py

    :var list Nodes: The list of :py:class:`discodo.Node` that is registered.
    :var EventDispatcher dispatcher: The event dispatcher that the client dispatches events.
    :var asyncio.AbstractEventLoop loop: The event loop that the client uses for operation."""

    def __init__(self, client):
        self.client = client
        self.loop = client.loop or asyncio.get_event_loop()

        self.dispatcher = EventDispatcher()

        self.GuildReservationMap = {}

        self.Nodes = Nodes()
        self.__registerEvent()

    def __repr__(self) -> str:
        return f"<DPYClient Nodes={self.Nodes} voiceClients={len(self.voiceClients)}>"

    @property
    def event(self):
        r"""A decorator that registers an event to listen to.

        :param str event: The event name to listen to."""

        return self.dispatcher.event

    def __registerEvent(self):
        if hasattr(self.client, "on_socket_response"):
            originFunc = self.client.on_socket_response
        else:
            originFunc = None

        @self.client.event
        async def on_socket_response(*args, **kwargs):
            self.loop.create_task(self.discordDispatch(*args, **kwargs))

            if originFunc:
                return await originFunc()

        if isinstance(self.client, discord.ext.commands.Bot):
            originContextFunc = discord.ext.commands.Context.voice_client.fget

            @discord.ext.commands.Context.voice_client.getter
            def voice_client(ctx):
                if ctx.bot == self.client:
                    return self.getVC(ctx.guild, safe=True)

                return originContextFunc(ctx)

            discord.ext.commands.Context.voice_client = voice_client

    async def discordDispatch(self, payload) -> None:
        if payload["t"] in ["VOICE_STATE_UPDATE", "VOICE_SERVER_UPDATE"]:
            VC = self.getVC(payload["d"]["guild_id"], safe=True)
            SelectNodes = [
                self.GuildReservationMap.get(
                    int(payload["d"]["guild_id"]),
                    (VC.Node if VC else self.getBestNode()),
                )
            ]
        else:
            SelectNodes = self.Nodes

        NodesTask = [
            Node.discordDispatch(payload)
            for Node in SelectNodes
            if Node and Node.is_connected
        ]
        if NodesTask:
            await asyncio.wait(
                NodesTask,
                return_when="ALL_COMPLETED",
            )

    def registerNode(
        self,
        host=None,
        port=None,
        password="hellodiscodo",
        region=None,
        launchOptions=None,
    ):
        r"""Creates a websocket connection of the node and register it on the client.

        If the value ``host`` or ``port`` is ``None``, it will launch local node process.

        :param Optional[str] host: The host of the node to connect to.
        :param Optional[int] port: The port of the node to connect to.
        :param Optional[str] password: The password of the node to connect to, defaults to ``hellodiscodo``.
        :param Optional[str] region: The region of the node to connect to. This is like a annotation. It is not involved in the actual connection.
        :param Optional[dict] launchOptions: The options to use when launching a local node

        :return: The scheduled task to connect with the node
        :rtype: asyncio.Task"""

        if launchOptions is None:
            launchOptions = {}

        async def connectNode(self, host, port, password, region, launchOptions):
            await self.client.wait_until_ready()

            if not host or not port:
                LocalNodeProc = await launchLocalNode(**launchOptions)

                host = LocalNodeProc.HOST
                port = LocalNodeProc.PORT
                password = LocalNodeProc.PASSWORD

            user_id = self.client.user.id
            shard_id = (
                self.client.shard_id
                if isinstance(self.client, discord.Client)
                else None
            )

            Node = NodeClient(self, host, port, user_id, shard_id, password, region)
            await Node.connect()

            self.Nodes.append(Node)
            Node.dispatcher.on("VC_DESTROYED", self._onVCDestroyed)
            Node.dispatcher.onAny(self._onAnyNodeEvent)

        return self.loop.create_task(
            connectNode(self, host, port, password, region, launchOptions)
        )

    async def _onVCDestroyed(self, data):
        guild = self.client.get_guild(int(data["guild_id"]))
        ws = self.getWebsocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def _onAnyNodeEvent(self, event, data):
        if not isinstance(data, dict) or not "guild_id" in data:
            return

        guild = self.client.get_guild(int(data["guild_id"]))
        vc = self.getVC(guild, safe=True)

        if not vc:
            return

        self.dispatcher.dispatch(event, vc, data)

    def getBestNode(self, exceptNode=None):
        r"""Get the node with the fewest connected players.

        :param Optional[discodo.Node] exceptNode: The host to except from the list.

        :rtype: discodo.Node"""

        SortedWithPerformance = sorted(
            [Node for Node in self.Nodes if Node.is_connected],
            key=lambda Node: len(Node.voiceClients),
        )

        if exceptNode and exceptNode in SortedWithPerformance:
            SortedWithPerformance.remove(exceptNode)

        return SortedWithPerformance[0] if SortedWithPerformance else None

    @property
    def voiceClients(self):
        r"""A property that returns all voice clients from all of connected nodes.

        :rtype: dict"""

        return dict(
            list(
                itertools.chain.from_iterable(
                    [
                        Node.voiceClients.items()
                        for Node in self.Nodes
                        if Node.is_connected
                    ]
                )
            )
        )

    def getVC(self, guild, safe=False):
        r"""Get a voice client from the guild.

        :param guild: Guild or guild ID from which to get the voice client.
        :type guild: int or discord.Guild
        :param bool safe: Whether to raise an exception when the voice client cannot be found, defaults to ``False``.

        :raises discodo.VoiceClientNotFound: The voice client was not found and the ``safe`` value is ``False``.

        :rtype: discodo.VoiceClient"""

        if isinstance(guild, discord.Guild):
            guild = guild.id

        if int(guild) not in self.voiceClients and not safe:
            raise VoiceClientNotFound

        return self.voiceClients.get(int(guild))

    def getWebsocket(self, id):
        r"""Get a websocket object of the shard from discord.py

        :param int id: The shard id to get a object.

        :rtype: discord.gateway.DiscordWebSocket"""

        if isinstance(self.client, discord.AutoShardedClient):
            return self.client.shards[id].ws
        elif not self.client.shard_id or self.client.shard_id == id:
            return self.client.ws

    async def connect(
        self, channel: discord.VoiceChannel, node: NodeClient = None
    ) -> None:
        r"""Connect to the voice channel.

        :param discord.VoiceChannel channel: The channel to connect to.
        :param Optional[discodo.Node] node: The node to connect with, defaults to ``getBestNode()``

        :raise ValueError: The ``channel`` value has no ``guild`` property.
        :raise discodo.NodeNotConnected: There is no discodo node that is connected.
        :raise asyncio.TimeoutError: The connection is not established in 10 seconds.

        :rtype: discodo.VoiceClient"""

        if not hasattr(channel, "guild"):
            raise ValueError

        if not node:
            if not self.getBestNode():
                raise NodeNotConnected

            node = self.getBestNode()

        self.GuildReservationMap[channel.guild.id] = node

        VC = self.getVC(channel.guild, safe=True)

        if VC and VC.Node != node:
            await VC.destroy()

        Task = (
            self.loop.create_task(
                self.dispatcher.wait_for(
                    "VC_CREATED",
                    lambda _, Data: int(Data["guild_id"]) == channel.guild.id,
                    timeout=10.0,
                )
            )
            if not VC or VC.Node != node
            else None
        )

        await self.getWebsocket(channel.guild.shard_id).voice_state(
            channel.guild.id, channel.id
        )

        if Task:
            VC, _ = await Task

        if self.GuildReservationMap.get(channel.guild.id) == node:
            del self.GuildReservationMap[channel.guild.id]

        return VC

    async def disconnect(self, guild: discord.Guild) -> None:
        r"""Disconnect from the voice channel.

        .. note::
            This coroutine doesn't destroy the voice client. Recommand to use :meth:`destroy`

        :param discord.Guild guild: The guild to disconnect from."""

        ws = self.getWebsocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def destroy(self, guild: discord.Guild) -> None:
        r"""Destroy the voice client and disconnect from the voice channel

        :param discord.Guild guild: The guild to destroy the voice client.

        :raises discodo.VoiceClientNotFound: The voice client was not found."""

        if not guild.id in self.voiceClients:
            raise VoiceClientNotFound

        vc = self.getVC(guild.id)
        ws = self.getWebsocket(guild.shard_id)

        await ws.voice_state(guild.id, None)
        await vc.destroy()
