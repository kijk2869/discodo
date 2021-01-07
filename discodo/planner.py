"""
Thx for @Sannoob
"""

import collections
import ipaddress
import random
import time
from typing import Dict, Union


class RoutePlanner:
    def __init__(self, ipBlocks: list, excludeIps: list = []) -> None:
        self.failedAddress: Dict[
            Union[ipaddress.IPv4Address, ipaddress.IPv6Address],
            Dict[str, Union[str, float]],
        ] = {}
        self.usedCount: Dict[
            Union[ipaddress.IPv4Address, ipaddress.IPv6Address], int
        ] = collections.defaultdict(int)

        self.ipBlocks = [ipaddress.ip_network(ipBlock) for ipBlock in ipBlocks]
        self.excludeIps = [ipaddress.ip_address(excludeIp) for excludeIp in excludeIps]

    def mark_failed_address(
        self,
        address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address],
        status: int = 429,
    ) -> None:
        self.failedAddress[address] = {"status": status, "failed_at": time.time()}

    def unmark_failed_address(
        self, address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]
    ) -> None:
        del self.failedAddress[address]

    @staticmethod
    def __get_random(
        ipBlock: Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
    ) -> str:
        cidr: int = ipBlock.prefixlen

        host_bits: int = (128 if ipBlock.version == 6 else 32) - cidr

        start: int = (int(ipBlock.broadcast_address) >> host_bits) << host_bits
        end: int = start | ((1 << host_bits) - 1)

        return ipaddress.ip_address(random.randrange(start, end))

    def get(self) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
        sortedIpBlocks = sorted(
            self.ipBlocks, key=lambda ipBlock: self.usedCount.get(ipBlock, 0)
        )
        randomResult = self.__get_random(sortedIpBlocks[0])
        self.usedCount[sortedIpBlocks[0]] += 1

        if len(self.failedAddress) >= sum(
            [ipBlock.num_addresses for ipBlock in self.ipBlocks]
        ):
            raise ValueError("No Ips available")

        if randomResult in self.excludeIps or randomResult in self.failedAddress:
            return self.get()

        return randomResult
