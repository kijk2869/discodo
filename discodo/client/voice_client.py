import asyncio
from discodo.utils.eventDispatcher import EventDispatcher

from ..utils import EventDispatcher


class VoiceClient:
    def __init__(self, Node, guild_id: int) -> None:
        self.Node = Node
        self.loop = Node.loop
        self.guild_id = guild_id

        self.event = EventDispatcher()

    def __del__(self):
        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc == self:
            self.Node.voiceClients.pop(self.guild_id)

    async def send(self, Operation: str, Data: dict = {}):
        Data["guild_id"] = self.guild_id

        return await self.Node.send(Operation, Data)