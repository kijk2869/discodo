import logging

log = logging.getLogger("discodo.client")


class Node:
    def __init__(
        self,
        host: str,
        port: int,
        user_id: int = None,
        password: str = "hellodiscodo",
        region: str = None,
    ) -> None:
        self.host = host
        self.port = port
        self.password = password

        self.user_id = user_id
        self.region = region

        self.voiceClients = {}

    @property
    def URL(self) -> str:
        return f"ws://{self.host}:{self.port}"

    async def connect(self) -> None:
        pass