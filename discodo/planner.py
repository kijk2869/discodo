import os
from socket import AddressFamily

MAX_PENALTY = int(os.getenv("MAX_PENALTY", "5"))

class IPAddress:
    def __init__(self, IP):
        self.IP = IP
        self.penalty = 0
    
    def __str__(self):
        return self.IP if not self.blocked else None
    
    def givePenalty(self):
        self.penalty += 1
    
    @property
    def blocked(self):
        return self.penalty >= MAX_PENALTY

class IPRotator:
    def __init__(self):
        self.Mode = 'ROTATE'
        self.IPAddresses = []
    
    def add(self, IP: str):
        if IP in [_IP.__str__() for _IP in self.IPAddresses]:
            raise ValueError('already exists')

        _IP = IPAddress(IP)
        self.IPAddresses.append(_IP)

        return _IP

    @property
    def usableAddresses(self):
        return [Address for Address in self.IPAddresses if not Address.blocked]
    
    @property
    def get(self):
        if self.Mode == 'ROTATE':
            SelectedIP = self.usableAddresses[0]
            SelectedIndex = self.IPAddresses.index(SelectedIP)

            self.IPAddresses = self.IPAddresses[SelectedIndex:] + self.IPAddresses[:SelectedIndex]
            
            return SelectedIP
        elif self.Mode == 'SEQUENCE':
            return self.usableAddresses[0]
        else:
            raise ValueError('Mode does not found')