import enum


class WebsocketCloseCode(enum.Enum):
    HEARTBEAT_TIMEOUT = 1000
    CLOUDFLARE = 1001
    ABNORMAL = 1006
    NORMAL = 4000
    UNKNOWN_OP_CODE = 4001
    NOT_AUTHENTICATED = 4003
    AUTHENTICATION_FAILED = 4004
    ALREADY_AUTHENTICATED = 4005
    SESSION_NO_LONGER_VALID = 4006
    SESSION_TIMEOUT = 4009
    SERVER_NOT_FOUND = 4011
    UNKNOWN_PROTOCOL = 4012
    DISCONNECTED = 4014
    VOICE_SERVER_CRASHED = 4015
    UNKNOWN_ENCRYPTION_MODE = 4016

    WARN_CODES = [1006, 4001, 4003, 4004, 4005, 4006, 4009, 4011, 4012, 4016]
    RESUME_CODES = [1000, 1001, 1006, 4001, 4015]

    @classmethod
    def __missing__(cls, _):
        return cls.NORMAL

    @property
    def warn(self) -> bool:
        return self.value in self.WARN_CODES.value

    @property
    def resume(self) -> bool:
        return self.value in self.RESUME_CODES.value
