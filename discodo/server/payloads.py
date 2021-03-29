import asyncio
import functools
import uuid

from ..errors import NotPlaying
from ..source import SubtitleSource
from ..utils import getStatus


def need_manager(func):
    @functools.wraps(func)
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
    @staticmethod
    async def GET_STATUS(self, _):
        payload = {"op": "STATUS", "d": getStatus()}

        await self.sendJson(payload)

    @staticmethod
    async def HEARTBEAT(self, data):
        await self.sendJson({"op": "HEARTBEAT_ACK", "d": data})

    @staticmethod
    async def IDENTIFY(self, data):
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
            await self.initializeManager(data["user_id"], data.get("shard_id"))
            payload = {"op": "IDENTIFIED", "d": "ClientManager initialized."}

        await self.sendJson(payload)

    @staticmethod
    @need_manager
    async def DISCORD_EVENT(self, data):
        self.ClientManager.discordDispatch(data)

    @staticmethod
    @need_manager
    async def getState(self, data):
        VoiceClient = self.ClientManager.getVC(data["guild_id"])

        payload = {
            "op": "getState",
            "d": {
                "id": VoiceClient.id,
                "guild_id": VoiceClient.guild_id,
                "channel_id": VoiceClient.channel_id,
                "state": VoiceClient.state,
                "current": VoiceClient.current,
                "duration": VoiceClient.current.duration
                if VoiceClient.current
                else None,
                "position": VoiceClient.current.position
                if VoiceClient.current
                else None,
                "remain": VoiceClient.current.remain if VoiceClient.current else None,
                "remainQueue": len(VoiceClient.Queue),
                "options": {
                    "autoplay": VoiceClient.autoplay,
                    "volume": VoiceClient.volume,
                    "crossfade": VoiceClient.crossfade,
                    "filter": VoiceClient.filter,
                },
                "context": VoiceClient.Context,
            },
        }

        return await self.sendJson(payload)

    @staticmethod
    @need_manager
    async def getQueue(self, data):
        VoiceClient = self.ClientManager.getVC(data["guild_id"])

        payload = {
            "op": "getQueue",
            "d": {
                "guild_id": VoiceClient.guild_id,
                "entries": VoiceClient.Queue,
            },
        }

        return await self.sendJson(payload)

    @staticmethod
    @need_manager
    async def VC_DESTROY(self, data):
        self.ClientManager.delVC(data["guild_id"])

    @staticmethod
    @need_manager
    async def requestSubtitle(self, data):
        vc = self.ClientManager.getVC(data["guild_id"])

        if not vc.current:
            raise NotPlaying

        if "url" in data:
            url = data["url"]
        else:
            if not data["lang"] in vc.current.subtitles:
                payload = {
                    "op": "requestSubtitle",
                    "d": {
                        "guild_id": data["guild_id"],
                        "NoSubtitle": f"There is no subtitle in {data['lang']}",
                    },
                }
                return await self.sendJson(payload)

            url = vc.current.subtitles[data["lang"]]

        current = vc.current
        _identify_token = str(uuid.uuid4())

        if url.endswith(".smi"):
            Subtitle = await SubtitleSource.smi.load(url)
        else:
            Subtitle = await SubtitleSource.srv1.load(url)

        payload = {
            "op": "requestSubtitle",
            "d": {
                "guild_id": data["guild_id"],
                "identify": _identify_token,
                "url": url,
            },
        }
        await self.sendJson(payload)

        try:
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
                            "guild_id": data["guild_id"],
                            "identify": _identify_token,
                            "previous": Previous,
                            "current": Now,
                            "next": Next,
                        },
                    }
                    await self.sendJson(payload)

                await asyncio.sleep(0.1)
        finally:
            payload = {
                "op": "subtitleDone",
                "d": {
                    "guild_id": data["guild_id"],
                    "identify": _identify_token,
                },
            }
            return await self.sendJson(payload)
