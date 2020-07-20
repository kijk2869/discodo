from .. import getStat


def need_data(*keys):
    def decorator(func):
        async def wrapper(self, Data, **kwargs):
            if not Data:
                payload = {
                    'op': 'BAD_REQUEST',
                    'd': 'This event needs `d`.'
                }
                return await self.sendJson(payload)
            
            if keys:
                NeedKeys = [key for key in keys if not key in Data.keys()]
                if NeedKeys:
                    payload = {
                        'op': 'BAD_REQUEST',
                        'd': f'This event needs `{NeedKeys[0]}`.'
                    }
                    return await self.sendJson(payload)
            
            return await func(self, Data, **kwargs)
        return wrapper
    return decorator
            

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
    async def GET_STAT(self, Data):
        payload = {
            'op': 'STAT',
            'd': getStat()
        }

        if self.AudioManager:
            payload['d']['TotalPlayers'] = len(self.AudioManager.voiceClients)
        
        await self.sendJson(payload)

    @need_data('user_id')
    async def IDENTIFY(self, Data):
        if self.AudioManager:
            payload = {
                'op': 'ALREADY_IDENTIFIED',
                'd': 'This connection already identified.'
            }
        else:
            await self.initialize_manager(Data['user_id'])
            payload = {
                'op': 'IDENTIFIED',
                'd': 'AudioManager initialized.'
            }
        
        await self.sendJson(payload)

    @need_manager
    @need_data()
    async def DISCORD_EVENT(self, Data):
        self.AudioManager.discordDispatch(Data)

    @need_manager
    @need_data('guild_id', 'volume')
    async def setVolume(self, Data):
        if not Data['volume'] or not (isinstance(Data['volume'], int) or Data['volume'].isdigit()):
            payload = {
                'op': 'BAD_REQUEST',
                'd': '`Volume` must be intenger..'
            }
            return await self.sendJson(payload)
        
        value = int(Data['volume'])

        if value < 0 or value > 100:
            payload = {
                'op': 'BAD_REQUEST',
                'd': '`Volume` must be `0~100`..'
            }
            return await self.sendJson(payload)
        
        self.AudioManager.setVolume(Data['guild_id'], value / 100)
        
        payload = {
            'op': 'setVolume',
            'd': {
                'guild_id':Data['guild_id'],
                'volume': Data['volume']
            }
        }
        return await self.sendJson(payload)

    @need_manager
    @need_data('guild_id', 'crossfade')
    async def setCrossfade(self, Data):
        try:
            value = float(Data['crossfade'])
        except ValueError:
            payload = {
                'op': 'BAD_REQUEST',
                'd': '`crossfade` must be float..'
            }
            return await self.sendJson(payload)
        
        self.AudioManager.setCrossfade(Data['guild_id'], value)
        
        payload = {
            'op': 'setCrossfade',
            'd': {
                'guild_id':Data['guild_id'],
                'crossfade': Data['crossfade']
            }
        }
        return await self.sendJson(payload)

    @need_manager
    @need_data('guild_id', 'query')
    async def loadSong(self, Data):
        await self.AudioManager.loadSong(Data['guild_id'], Data['query'])