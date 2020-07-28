import asyncio
import discord
from itertools import chain
from .node.client import Node as OriginNode
from .exceptions import VoiceClientNotFound

class NodeClient(OriginNode):
    def __init__(self, DPYClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.DPYClient = DPYClient

    async def destroy(self, *args, **kwargs):
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
        if hasattr(self.client, 'on_socket_response'):
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
            VC = self.getVC(payload['d']['guild_id'])
            SelectNodes = [VC.Node] if VC else [await self.getBestNode()]
        else:
            SelectNodes = self.Nodes
        
        await asyncio.wait(
            [Node.discordDispatch(payload) for Node in SelectNodes],
            return_when='ALL_COMPLETED'
        )

    def register_node(self, *args, **kwargs):
        Node = NodeClient(self, *args, **kwargs)

        self.Nodes.append(Node)

        Node.event.on('VC_DESTROYED', self._vc_destroyed)

        return self

    async def _vc_destroyed(self, Data):
        guild = self.client.get_guild(int(Data['guild_id']))
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def getBestNode(self):
        SortedWithPerformance = sorted(
            self.Nodes, key=lambda Node: len(Node.voiceClients), reverse=True)

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

    def getVC(self, guildID:int):
        return self.voiceClients.get(int(guildID))

    def __get_websocket(self, id):
        if isinstance(self.client, discord.AutoShardedClient):
            return self.client.shards[id].ws
        elif not self.client.shard_id or self.client.shard_id == id:
            return self.client.ws

    async def connect(self, channel):
        if not hasattr(channel, 'guild'):
            raise ValueError

        ws = self.__get_websocket(channel.guild.shard_id)

        await ws.voice_state(channel.guild.id, channel.id)

    async def disconnect(self, guild):
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def destroy(self, guild):
        if not guild.id in self.voiceClients:
            raise VoiceClientNotFound

        vc = self.getVC(guild.id)
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)
        await vc.destroy()
