import asyncio
import logging
from itertools import chain
from typing import Union

import discord

from ..errors import NodeNotConnected, VoiceClientNotFound
from ..utils import EventDispatcher
from .node import Node as OriginNode
from .node import Nodes
from .voice_client import VoiceClient

log = logging.getLogger("discodo.client")


class NodeClient(OriginNode):
    def __init__(self, client, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.client = client

    async def _resumed(self, Data: dict) -> None:
        await super()._resumed(Data)

        for guild_id, vc_data in Data["voice_clients"].items():
            guild = self.client.client.get_guild(int(guild_id))
            if "channel" in vc_data:
                channel = guild.get_channel(vc_data["channel"])
                self.loop.create_task(self.client.connect(channel))
            else:
                self.loop.create_task(self.client.disconnect(guild))

    async def close(self) -> None:
        for guildId in self.voiceClients:
            self.loop.create_task(
                self.client.disconnect(self.client.client.get_guild(guildId))
            )

        return super().close()

    async def destroy(self, *args, **kwargs) -> None:
        log.infmo(f"destroying Node {self.URL}")
        await super().destroy(*args, **kwargs)

        if self in self.client.Nodes:
            self.client.Nodes.remove(self)


class DPYClient:
    def __init__(self, client) -> None:
        self.client = client
        self.loop = client.loop or asyncio.get_event_loop()

        self.dispatcher = EventDispatcher()
        self.event = self.dispatcher.event

        self.Nodes = Nodes()
        self.__register_event()

    def __repr__(self) -> str:
        return f"<DPYClient Nodes={self.Nodes} voiceClients={len(self.voiceClients)}>"

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

    async def discord_socket_response(self, payload: dict) -> None:
        if payload["t"] in ["VOICE_STATE_UPDATE", "VOICE_SERVER_UPDATE"]:
            VC = self.getVC(payload["d"]["guild_id"], safe=True)
            SelectNodes = [VC.Node] if VC else [self.getBestNode()]
        else:
            SelectNodes = self.Nodes

        NodesTask = [
            Node.discordDispatch(payload) for Node in SelectNodes if Node.is_connected
        ]
        if NodesTask:
            await asyncio.wait(
                NodesTask,
                return_when="ALL_COMPLETED",
            )

    def register_node(self, *args, **kwargs) -> None:
        return self.loop.create_task(self._register_event(*args, **kwargs))

    async def _register_event(self, *args, **kwargs) -> None:
        await self.client.wait_until_ready()
        kwargs["user_id"] = self.client.user.id

        Node = NodeClient(self, *args, **kwargs)
        await Node.connect()

        log.info(f"registering Node {Node.host}:{Node.port}")

        self.Nodes.append(Node)

        Node.dispatcher.on("VC_DESTROYED", self._vc_destroyed)
        Node.dispatcher.onAny(self._node_event)

        return self

    async def _vc_destroyed(self, Data: dict) -> None:
        guild = self.client.get_guild(int(Data["guild_id"]))
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def _node_event(self, Event: str, Data: dict) -> None:
        if not isinstance(Data, dict) or not "guild_id" in Data:
            return

        guild = self.client.get_guild(int(Data["guild_id"]))
        vc = self.getVC(guild)

        self.dispatcher.dispatch(Event, vc, Data)

    def getBestNode(self):
        SortedWithPerformance = sorted(
            [Node for Node in self.Nodes if Node.is_connected],
            key=lambda Node: len(Node.voiceClients),
        )

        return SortedWithPerformance[0] if SortedWithPerformance else None

    @property
    def voiceClients(self):
        return dict(
            list(
                chain.from_iterable(
                    [
                        Node.voiceClients.items()
                        for Node in self.Nodes
                        if Node.is_connected
                    ]
                )
            )
        )

    def getVC(
        self, guild: Union[discord.Guild, int], safe: bool = False
    ) -> VoiceClient:
        if isinstance(guild, discord.Guild):
            guild = guild.id

        if int(guild) not in self.voiceClients and not safe:
            raise VoiceClientNotFound

        return self.voiceClients.get(int(guild))

    def __get_websocket(self, id: int):
        if isinstance(self.client, discord.AutoShardedClient):
            return self.client.shards[id].ws
        elif not self.client.shard_id or self.client.shard_id == id:
            return self.client.ws

    async def connect(self, channel: discord.VoiceChannel) -> None:
        log.info(f"connecting to {channel.id} of {channel.guild.id}")
        if not hasattr(channel, "guild"):
            raise ValueError

        if not self.getBestNode():
            raise NodeNotConnected

        ws = self.__get_websocket(channel.guild.shard_id)

        await ws.voice_state(channel.guild.id, channel.id)

        VC, _ = await self.dispatcher.wait_for(
            "VC_CREATED",
            lambda _, Data: int(Data["guild_id"]) == channel.guild.id,
            timeout=10.0,
        )

        return VC

    async def disconnect(self, guild: discord.Guild) -> None:
        log.info(f"disconnecting voice of {guild.id} without destroying")
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def destroy(self, guild: discord.Guild) -> None:
        log.info(f"destroying voice client of {guild.id}")
        if not guild.id in self.voiceClients:
            raise VoiceClientNotFound

        vc = self.getVC(guild.id)
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)
        await vc.destroy()
