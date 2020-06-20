import asyncio

class VoiceClient:
    def __init__(self, guild_id, channel_id):
        self.loop = asyncio.get_event_loop()
        self.ws = None

        self.guild_id = guild_id
        self.channel_id = channel_id