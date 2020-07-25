import asyncio
from .node.client import Node as NodeClient

class DPYClient:
    def __init__(self, client):
        self.client = client
    
        self.Nodes = []

    def register_node(self, *args, **kwargs):
        Node = NodeClient(*args, **kwargs)

        self.Nodes.append(Node)

        return self
    
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
        SortedWithPerformance = sorted(Stats, key=lambda x: x['TotalPlayers'], reverse=True)

        return SortedWithPerformance[0]