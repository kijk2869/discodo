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