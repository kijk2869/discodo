from http.client import responses


class DiscodoException(Exception):
    ...


class EncryptModeNotReceived(DiscodoException):
    ...


class NotPlaying(DiscodoException):
    ...


class VoiceClientNotFound(DiscodoException):
    ...


class NoSearchResults(DiscodoException):
    ...


class OpusLoadError(DiscodoException):
    ...


class HTTPException(DiscodoException):
    def __init__(self, status: int) -> None:
        super().__init__(f"{status} {responses.get(status, 'Unknown Status Code')}")


class Forbidden(DiscodoException):
    ...


class TooManyRequests(DiscodoException):
    ...


class NotSeekable(DiscodoException):
    ...


class NodeException(DiscodoException):
    def __init__(self, name, reason) -> None:
        self.name = name
        self.reason = reason

        super().__init__(f"{name}{': ' if reason else ''}{reason}")


class NodeNotConnected(DiscodoException):
    ...
