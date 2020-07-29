import asyncio
from itertools import chain
from logging import getLogger

import discord

from .exceptions import VoiceClientNotFound
from .node.client import Node as OriginNode

log = getLogger("discodo.DPYClient")


class NodeClient(OriginNode):
    def __init__(self, DPYClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.DPYClient = DPYClient

    async def destroy(self, *args, **kwargs):
        log.infmo(f"destroying Node {self.URL}")
        await super().destroy(*args, **kwargs)

        if self in self.DPYClient.Nodes:
            self.DPYClient.Nodes.remove(self)


class DPYClient:
    def __init__(self, client):
        self.client = client
        self.loop = client.loop or asyncio.get_event_loop()

        self.Nodes = []
        self.__register_event()

    def __register_event(self):
        if hasattr(self.client, "on_socket_response"):
            originFunc = self.client.on_socket_response
        else:
            originFunc = None

        @self.client.event
        async def on_socket_response(*args, **kwargs):
            self.loop.create_task(self.discord_socket_response(*args, **kwargs))

            if originFunc:
                return await originFunc()

    async def discord_socket_response(self, payload):
        if payload["t"] == "VOICE_SERVER_UPDATE":
            VC = self.getVC(payload["d"]["guild_id"])
            SelectNodes = [VC.Node] if VC else [self.getBestNode()]
        else:
            SelectNodes = self.Nodes

        if SelectNodes:
            await asyncio.wait(
                [Node.discordDispatch(payload) for Node in SelectNodes],
                return_when="ALL_COMPLETED",
            )

    def register_node(self, *args, **kwargs):
        return self.loop.create_task(self._register_event(*args, **kwargs))

    async def _register_event(self, *args, **kwargs):
        await self.client.wait_until_ready()

        kwargs["user_id"] = self.client.user.id
        Node = NodeClient(self, *args, **kwargs)
        log.info(f"registering Node {Node.URL}")

        self.Nodes.append(Node)

        Node.emitter.on("VC_DESTROYED", self._vc_destroyed)

        return self

    async def _vc_destroyed(self, Data):
        guild = self.client.get_guild(int(Data["guild_id"]))
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    def getBestNode(self):
        SortedWithPerformance = sorted(
            [Node for Node in self.Nodes if Node.connected.is_set()],
            key=lambda Node: len(Node.voiceClients),
        )

        return SortedWithPerformance[0]

    @property
    def voiceClients(self):
        return {
            ID: Value
            for ID, Value in list(
                chain.from_iterable(
                    [
                        Node.voiceClients.items()
                        for Node in self.Nodes
                        if Node.connected.is_set()
                    ]
                )
            )
        }

    def getVC(self, guild):
        if isinstance(guild, discord.Guild):
            guild = guild.id

        return self.voiceClients.get(int(guild))

    def __get_websocket(self, id):
        if isinstance(self.client, discord.AutoShardedClient):
            return self.client.shards[id].ws
        elif not self.client.shard_id or self.client.shard_id == id:
            return self.client.ws

    async def connect(self, channel):
        log.info(f"connecting to {channel.id} of {channel.guild.id}")
        if not hasattr(channel, "guild"):
            raise ValueError

        ws = self.__get_websocket(channel.guild.shard_id)

        await ws.voice_state(channel.guild.id, channel.id)

    async def disconnect(self, guild):
        log.info(f"disconnecting voice of {guild.id} without destroying")
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def destroy(self, guild):
        log.info(f"destroying voice client of {guild.id}")
        if not guild.id in self.voiceClients:
            raise VoiceClientNotFound

        vc = self.getVC(guild.id)
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)
        await vc.destroy()
