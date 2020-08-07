import os
from logging import getLogger

log = getLogger("discodo.VoiceClient")


class IPAddress:
    def __init__(self, IP):
        self.IP = IP
        self.penalty = 0

        self.MAX_PENALTY = int(os.getenv("MAX_PENALTY", "5"))

    def __str__(self):
        return self.IP

    def givePenalty(self):
        log.debug(f"penalty is given to {self}")
        self.penalty += 1

    @property
    def blocked(self):
        return self.penalty >= self.MAX_PENALTY


class IPRotator:
    def __init__(self):
        self.Mode = os.getenv("ROTATE_MODE", "ROTATE")
        self.IPAddresses = []

    def add(self, IP: str):
        if IP in [_IP.__str__() for _IP in self.IPAddresses]:
            raise ValueError("already exists")

        log.debug(f"add {IP} to address list")
        _IP = IPAddress(IP)
        self.IPAddresses.append(_IP)

        return _IP

    @property
    def usableAddresses(self):
        return [Address for Address in self.IPAddresses if not Address.blocked]

    def get(self):
        IP = self._get()

        log.debug(f"IP {IP} selected.")

        return IP

    def _get(self):
        if self.Mode == "ROTATE":
            SelectedIP = self.usableAddresses[0]
            SelectedIndex = self.IPAddresses.index(SelectedIP)

            self.IPAddresses = (
                self.IPAddresses[SelectedIndex:] + self.IPAddresses[:SelectedIndex]
            )

            return SelectedIP
        elif self.Mode == "SEQUENCE":
            return self.usableAddresses[0]
        else:
            raise ValueError("Mode does not found")
