class DiscordEvent:
    def __init__(self):
        pass
    
    def parseReady(self):
        raise NotImplementedError

    def parseResume(self):
        raise NotImplementedError

    def parseVoiceStateUpdate(self):
        raise NotImplementedError

    def parseVoiceServerUpdate(self):
        raise NotImplementedError