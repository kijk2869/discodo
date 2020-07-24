from ...utils import EventEmitter


class VoiceClient:
    def __init__(self, Node, guild_id):
        self.Node = Node
        self.guild_id = guild_id

        self.emitter = EventEmitter()

    def __del__(self):
        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc is self:
            self.Node.voiceClients.pop(self.guild_id)

    async def send(self, Operation, Data={}):
        Data["guild_id"] = self.guild_id

        return await self.Node.send(Operation, Data)

    async def loadSong(self, Query):
        await self.send("loadSong", {"query": Query})

        return await self.emitter.wait_for("loadSong", timeout=10.0)

    async def skip(self, offset=1):
        await self.send("skip", {"offset": offset})

        return await self.emitter.wait_for("skip", timeout=10.0)

    async def seek(self, offset):
        await self.send("seek", {"offset": offset})

        return await self.emitter.wait_for("seek", timeout=10.0)

    async def setVolume(self, volume):
        await self.send("setVolume", {"volume": volume})

        return await self.emitter.wait_for("setVolume", timeout=10.0)

    async def setCrossfade(self, crossfade):
        await self.send("setCrossfade", {"crossfade": crossfade})

        return await self.emitter.wait_for("setCrossfade", timeout=10.0)

    async def setAutoplay(self, autoplay):
        await self.send("setAutoplay", {"autoplay": autoplay})

        return await self.emitter.wait_for("setAutoplay", timeout=10.0)

    async def setFilter(self, filter):
        await self.send("setFilter", {"filter": filter})

        return await self.emitter.wait_for("setFilter", timeout=10.0)

    async def getQueue(self):
        await self.send("getQueue")

        return await self.emitter.wait_for("Queue", timeout=10.0)

    async def getCurrent(self):
        await self.send("getCurrent")

        return await self.emitter.wait_for("Current", timeout=10.0)

    async def shuffle(self):
        await self.send("shuffle")

        return await self.emitter.wait_for("shuffle", timeout=10.0)

    async def remove(self, index):
        await self.send("remove", {"index": index})

        return await self.emitter.wait_for("remove", timeout=10.0)

    async def destroy(self):
        await self.send("VC_DESTROY")

        return await self.emitter.wait_for("VC_DESTROYED", timeout=10.0)
