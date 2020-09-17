from .voice_connector import VoiceConnector
from .player import Player


class VoiceClient(VoiceConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)