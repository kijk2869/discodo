class DiscodoException(Exception):
    pass


class Forbidden(DiscodoException):
    pass


class TooManyRequests(DiscodoException):
    pass


class NoSearchResults(DiscodoException):
    pass


class VoiceClientNotFound(DiscodoException):
    pass


class NotConnected(DiscodoException):
    pass


class NotSeekable(DiscodoException):
    pass


class NotPlaying(DiscodoException):
    pass


class NodeNotConnected(DiscodoException):
    pass
