import asyncio
import uuid

from discodo.source import SubtitleSource

from ..errors import NotConnected, NotPlaying
from ..extractor import search
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


class WebsocketPayloads:
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
    async def getContext(self, _: dict) -> None:
        payload = {
            "op": "getContext",
            "d": {"context": self.ClientManager.Context},
        }

        await self.sendJson(payload)

    @need_manager
    async def setContext(self, Data: dict) -> None:
        self.ClientManager.Context.update(Data["context"])

        payload = {
            "op": "setContext",
            "d": {"context": self.ClientManager.Context},
        }

        await self.sendJson(payload)

    @need_manager
    async def getVCContext(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        payload = {
            "op": "getVCContext",
            "d": {"context": VoiceClient.Context},
        }

        await self.sendJson(payload)

    @need_manager
    async def setVCContext(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.Context.update(Data["context"])

        payload = {
            "op": "setVCContext",
            "d": {"context": VoiceClient.Context},
        }

        await self.sendJson(payload)

    @need_manager
    async def getSource(self, Data: dict) -> None:
        payload = {
            "op": "getSource",
            "d": {
                "source": await AudioData.create(Data["query"]),
            },
        }

        await self.sendJson(payload)

    @need_manager
    async def searchSources(self, Data: dict) -> None:
        payload = {
            "op": "searchSources",
            "d": {
                "sources": filter(
                    lambda Source: AudioData(Source), await search(Data["query"])
                ),
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

        await VoiceClient.loadSource(Data["query"])

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
    async def setAutoplay(self, Data: dict) -> None:
        VoiceClient = self.ClientManager.getVC(Data["guild_id"])
        if not VoiceClient:
            raise NotConnected

        VoiceClient.autoplay = Data["autoplay"]

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
            "d": {"guild_id": Data["guild_id"], "remain": len(VoiceClient.Queue)},
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

        removed = VoiceClient.Queue[Data["index"] - 1]
        del VoiceClient.Queue[Data["index"] - 1]

        payload = {
            "op": "remove",
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
            "op": "getState",
            "d": {
                "id": VoiceClient.id,
                "guild_id": VoiceClient.guild_id,
                "channel_id": VoiceClient.channel_id,
                "state": VoiceClient.state,
                "current": VoiceClient.current,
                "duration": VoiceClient.current.duration,
                "position": VoiceClient.current.position,
                "remain": VoiceClient.current.remain,
                "remainQueue": len(VoiceClient.Queue),
                "options": {
                    "autoplay": VoiceClient.autoplay,
                    "volume": VoiceClient.volume,
                    "crossfade": VoiceClient.crossfade,
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
            "op": "getQueue",
            "d": {
                "guild_id": Data["guild_id"],
                "entries": VoiceClient.Queue,
            },
        }

        return await self.sendJson(payload)

    @need_manager
    async def VC_DESTROY(self, Data: dict) -> None:
        self.ClientManager.delVC(Data["guild_id"])

    @need_manager
    async def requestSubtitle(self, Data: dict) -> None:
        vc = self.ClientManager.getVC(Data["guild_id"])

        if not vc.current:
            raise NotPlaying

        if "url" in Data:
            url = Data["url"]
        else:
            if not Data["lang"] in vc.current.subtitles:
                payload = {
                    "op": "requestSubtitle",
                    "d": {
                        "guild_id": Data["guild_id"],
                        "NoSubtitle": f"There is no subtitle in {Data['lang']}",
                    },
                }
                return await self.sendJson(payload)

            url = vc.current.subtitles[Data["lang"]]

        current = vc.current
        _identify_token = str(uuid.uuid4())

        if url.endswith(".smi"):
            Subtitle = await SubtitleSource.smi.load(url)
        else:
            Subtitle = await SubtitleSource.srv1.load(url)

        payload = {
            "op": "requestSubtitle",
            "d": {
                "guild_id": Data["guild_id"],
                "identify": _identify_token,
                "url": url,
            },
        }
        await self.sendJson(payload)

        Previous = Now = Next = ""
        Elements = list(Subtitle.TextElements.values())
        while not Subtitle.is_done and not current.stopped:
            Element = Subtitle.seek(current.position)

            if Element and Element["markdown"] and Element["markdown"] != Now:
                if not Element["markdown"].startswith(Now) and not Element[
                    "markdown"
                ].endswith(Now):
                    Previous = Now
                Now = Element["markdown"]

                NextElements = [
                    NextElement["markdown"]
                    for NextElement in Elements[Elements.index(Element) + 1 :]
                    if NextElement["markdown"] != Now
                    if not NextElement["markdown"].startswith(Now)
                    and not NextElement["markdown"].endswith(Now)
                ]

                Next = NextElements[0] if NextElements else None

                payload = {
                    "op": "Subtitle",
                    "d": {
                        "guild_id": Data["guild_id"],
                        "identify": _identify_token,
                        "previous": Previous,
                        "current": Now,
                        "next": Next,
                    },
                }
                await self.sendJson(payload)

            await asyncio.sleep(0.1)

        payload = {
            "op": "subtitleDone",
            "d": {
                "guild_id": Data["guild_id"],
                "identify": _identify_token,
                "language": Data["language"],
            },
        }
        return await self.sendJson(payload)
