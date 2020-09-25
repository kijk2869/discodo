from ..errors import NotConnected
from ..source import AudioData
from ..status import getStatus


def need_manager(func):
    def wrapper(self, *args, **kwargs):
        if not self.ClientManager:
            payload = {
                "op": func.__name__,
                "d": {"traceback": {"NOT_IDENTIFIED": "Identify first."}},
            }

            return self.sendJson(payload)
        return func(self, *args, **kwargs)

    return wrapper


class WebsocketEvents:
    async def GET_STATUS(self, Data: None) -> None:
        payload = {"op": "STATUS", "d": getStatus()}

        await self.sendJson(payload)

    async def HEARTBEAT(self, Data: int) -> None:
        payload = {"op": "HEARTBEAT_ACK", "d": Data}

        await self.sendJson(payload)

    async def IDENTIFY(self, Data: dict) -> None:
        if self.ClientManager:
            payload = {
                "op": "IDENTIFY",
                "d": {
                    "traceback": {
                        "ALREADY_IDENTIFIED": "This connection already identified."
                    }
                },
            }
        else:
            await self.initialize_manager(Data["user_id"])
            payload = {"op": "IDENTIFIED", "d": "ClientManager initialized."}

        await self.sendJson(payload)

    @need_manager
    async def DISCORD_EVENT(self, Data: dict) -> None:
        self.ClientManager.discordDispatch(Data)

    @need_manager
    async def getSource(self, Data: dict) -> None:
        payload = {
            "op": "getSource",
            "d": {
                "index": await AudioData.create(Data["query"]),
            },
        }

        await self.sendJson(payload)

    @need_manager
    async def putSource(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        payload = {
            "op": "putSource",
            "d": {
                "guild_id": Data["guild_id"],
                "index": VoiceClient.putSource(Data["source"]),
            },
        }

        await self.sendJson(payload)

    @need_manager
    async def loadSource(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        payload = {
            "op": "loadSource",
            "d": {
                "guild_id": Data["guild_id"],
                "source": await VoiceClient.loadSource(Data["query"]),
            },
        }

        await self.sendJson(payload)

    @need_manager
    async def setVolume(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.volume = Data["volume"]

        payload = {
            "op": "setVolume",
            "d": {"guild_id": Data["guild_id"], "volume": VoiceClient.volume},
        }

        await self.sendJson(payload)

    @need_manager
    async def setCrossfade(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.crossfade = Data["crossfade"]

        payload = {
            "op": "setCrossfade",
            "d": {"guild_id": Data["guild_id"], "crossfade": VoiceClient.crossfade},
        }

        await self.sendJson(payload)

    @need_manager
    async def setGapless(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.gapless = Data["gapless"]

        payload = {
            "op": "setGapless",
            "d": {"guild_id": Data["guild_id"], "gapless": VoiceClient.gapless},
        }

        await self.sendJson(payload)

    @need_manager
    async def setAutoplay(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.gapless = Data["autoplay"]

        payload = {
            "op": "setAutoplay",
            "d": {"guild_id": Data["guild_id"], "autoplay": VoiceClient.autoplay},
        }

        await self.sendJson(payload)

    @need_manager
    async def setFilter(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.filter = Data["filter"]

        payload = {
            "op": "setFilter",
            "d": {"guild_id": Data["guild_id"], "filter": VoiceClient.filter},
        }

        await self.sendJson(payload)

    @need_manager
    async def seek(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        await VoiceClient.seek(Data["offset"])

        payload = {
            "op": "seek",
            "d": {"guild_id": Data["guild_id"], "offset": Data["offset"]},
        }

        await self.sendJson(payload)

    @need_manager
    async def skip(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.skip(Data["offset"])

        payload = {
            "op": "skip",
            "d": {"guild_id": Data["guild_id"], "remain": len(Data.Queue)},
        }

        await self.sendJson(payload)

    @need_manager
    async def pause(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.pause()

        payload = {
            "op": "pause",
            "d": {"guild_id": Data["guild_id"], "state": VoiceClient.state},
        }

        await self.sendJson(payload)

    @need_manager
    async def resume(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.resume()

        payload = {
            "op": "resume",
            "d": {"guild_id": Data["guild_id"], "state": VoiceClient.state},
        }

        await self.sendJson(payload)

    @need_manager
    async def shuffle(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.shuffle()

        payload = {
            "op": "shuffle",
            "d": {"guild_id": Data["guild_id"], "entries": VoiceClient.Queue},
        }

        await self.sendJson(payload)

    @need_manager
    async def remove(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        removed = VoiceClient.Queue[Data["index"]]
        del VoiceClient.Queue[Data["index"]]

        payload = {
            "op": "shuffle",
            "d": {
                "guild_id": Data["guild_id"],
                "removed": removed,
                "entries": VoiceClient.Queue,
            },
        }

        await self.sendJson(payload)

    @need_manager
    async def getState(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        payload = {
            "op": "State",
            "d": {
                "id": VoiceClient.id,
                "guild_id": VoiceClient.guild_id,
                "channel_id": VoiceClient.channel_id,
                "state": VoiceClient.state,
                "current": VoiceClient.current,
                "duration": VoiceClient.current.duration,
                "position": VoiceClient.current.position,
                "remain": VoiceClient.current.remain,
                "options": {
                    "autoplay": VoiceClient.autoplay,
                    "volume": VoiceClient.volume,
                    "crossfade": VoiceClient.crossfade,
                    "gapless": VoiceClient.gapless,
                    "filter": VoiceClient.filter,
                },
            },
        }

        return await self.sendJson(payload)

    @need_manager
    async def getQueue(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        payload = {
            "op": "Queue",
            "d": {
                "guild_id": Data["guild_id"],
                "entries": VoiceClient.Queue,
            },
        }

        return await self.sendJson(payload)