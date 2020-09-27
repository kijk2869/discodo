from .node import Node

try:
    import discord
except ModuleNotFoundError:
    pass
else:
    from .DPYClient import DPYClient
