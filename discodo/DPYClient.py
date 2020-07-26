import asyncio
import discord
from itertools import chain
from .node.client import Node as NodeClient
from .exceptions import VoiceClientNotFound


class DPYClient:
    def __init__(self, client):
        self.client = client

        self.Nodes = []

    def register_node(self, *args, **kwargs):
        Node = NodeClient(*args, **kwargs)

        self.Nodes.append(Node)

        Node.event.on('VC_DESTROYED', self._node_destroyed)

        return self

    async def _node_destroyed(self, Data):
        guild = self.client.get_guild(int(Data['guild_id']))
        ws = self.__get_websocket(guild.shard_id)

        await ws.voice_state(guild.id, None)

    async def getBestNode(self):
        async def getWithNodeData(self, Node):
            Data = await Node.getStat()
            Data['Node'] = Node

            return Data

        Futures, _ = await asyncio.wait(
            [getWithNodeData(Node) for Node in self.Nodes],
            return_when='ALL_COMPLETED'
        )

        Stats = [Future.result() for Future in Futures if Future.result()]
        SortedWithPerformance = sorted(
            Stats, key=lambda x: x['TotalPlayers'], reverse=True)

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
                    ]
                )
            )
        }

    def getVC(self, guildID):
        return self.voiceClients.get(guildID)

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
