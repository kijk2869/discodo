class DiscodoException(Exception):
    pass


class Forbidden(DiscodoException):
    pass


class TooManyRequests(DiscodoException):
    pass


class NoSearchResults(DiscodoException):
    pass


class NodeException(DiscodoException):
    def __init__(self, name, reason) -> None:
        self.name = name
        self.reason = reason

        super().__init__(f"{name}{': ' if reason else ''}{reason}")


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
