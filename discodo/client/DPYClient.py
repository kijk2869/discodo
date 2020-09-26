import logging
import asyncio
from .node import Node as OriginNode
from ..utils import EventDispatcher

log = logging.getLogger("discodo.client")


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

        self.dispatcher = EventDispatcher()
        self.event = self.dispatcher.event
