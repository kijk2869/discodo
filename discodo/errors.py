class DiscodoException(Exception):
    pass


class Forbidden(DiscodoException):
    pass


class TooManyRequests(DiscodoException):
    pass


class NoSearchResults(DiscodoException):
    pass


class WebsocketConnectionClosed(DiscodoException):
    def __init__(self, socket, code=None) -> None:
        self.code = code or socket.close_code

        super().__init__(f"Websocket connection closed with {self.code}")


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
