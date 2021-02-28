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
    def __init__(self, status: int, data=None) -> None:
        if not data:
            data = {}

        self.status = data.get("status", status)
        self.description = data.get(
            "description", responses.get(status, "Unknown Status Code")
        )
        self.message = data.get("message", "")

        super().__init__(f"{self.status} {self.description}: {self.message}")


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
