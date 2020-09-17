import asyncio


class ClientManager:
    def __init__(self, **kwargs) -> None:
        self.loop = asyncio.get_event_loop()

        self.id = kwargs.get("user_id")
        self.session_id = kwargs.get("session_id")

        self.voiceClients = {}