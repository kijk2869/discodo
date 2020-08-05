class DiscodoException(Exception):
    """Base exception class for Discodo
    """

    pass


class VoiceClientNotFound(DiscodoException):
    pass


class NoSearchResults(DiscodoException):
    pass


class AudioSourceNotPlaying(DiscodoException):
    pass


class NodeNotConnected(DiscodoException):
    pass


class NotSeekable(DiscodoException):
    pass


class NeedUpdate(DiscodoException):
    pass
