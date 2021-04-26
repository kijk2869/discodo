from . import models
from .node import Node, Nodes
from .voice_client import VoiceClient

try:
    import discord
except ModuleNotFoundError:
    pass
else:
    from .DPYClient import DPYClient
