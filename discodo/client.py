import asyncio

class Client:
    def __init__(self, *args, **kwargs):
        self.bot_id = kwargs.get('bot_id')
        self.session_id = kwargs.get('session_id')