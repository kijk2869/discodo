from http.client import responses


class DiscodoException(Exception):
    """The basic exception class of discodo"""

    ...


class EncryptModeNotReceived(DiscodoException):
    """Exception that is thrown when trying to send packet before receveing encrypt mode.

    It's only raise in :py:class:`DiscordVoiceClient`"""

    ...


class NotPlaying(DiscodoException):
    """Exception that is thrown when trying to operate something while not playing."""

    ...


class VoiceClientNotFound(DiscodoException):
    """Exception that is thrown when there is no voice client."""

    ...


class NoSearchResults(DiscodoException):
    """Exception that is thrown when there is no search results."""

    ...


class OpusLoadError(DiscodoException):
    """Exception that is thrown when loading libopus failed."""

    ...


class HTTPException(DiscodoException):
    """Exception that is thrown when HTTP operation failed.

    :var int status: HTTP status code
    :var str description: Description of the HTTP status code
    :var str message: Server message with this request"""

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
    """Exception that is thrown when HTTP status code is 403."""

    ...


class TooManyRequests(DiscodoException):
    """Exception that is thrown when HTTP status code is 429."""

    ...


class NotSeekable(DiscodoException):
    """Exception that is thrown when trying to seek the source which is not seekable."""

    ...


class NodeException(DiscodoException):
    """Exception that is thrown when discodo node returns some exception."""

    def __init__(self, name, reason) -> None:
        self.name = name
        self.reason = reason

        super().__init__(f"{name}{': ' if reason else ''}{reason}")


class NodeNotConnected(DiscodoException):
    """Exception that is thrown when there is no discodo node that is connected."""

    ...
