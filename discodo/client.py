import asyncio
from .event import DiscordEvent


class Client:
    def __init__(self, *args, **kwargs):
        self.bot_id = kwargs.get('bot_id')
        self.session_id = kwargs.get('session_id')

        self.voiceClients = {}

        self.discordEvent = DiscordEvent(self)

    async def discordDispatch(self, data):
        Event, Data = data['t'], data['d']

        return await self.discordEvent.dispatch(Event, Data)
