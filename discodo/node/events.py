def need_manager(func):
    def wrapper(self, *args, **kwargs):
        if not self.AudioManager:
            payload = {
                'op': 'not_identified',
                'd': 'Identify first.'
            }

            return self.sendJson(payload)
        return func(self, *args, **kwargs)
    return wrapper


class WebsocketEvents:
    async def IDENTIFY(self, Data):
        if self.AudioManager:
            payload = {
                'op': 'ALREADY_IDENTIFIED',
                'd': 'This connection already identified.'
            }
        elif not 'user_id' in Data:
            payload = {
                'op': 'BAD_REQUEST',
                'd': 'Identify needs `user_id`.'
            }
        else:
            await self.initialize_manager(Data['user_id'])
            payload = {
                'op': 'IDENTIFIED',
                'd': 'AudioManager initialized.'
            }

        await self.sendJson(payload)

    @need_manager
    async def DISCORD_EVENT(self, Data):
        self.AudioManager.discordDispatch(Data)
