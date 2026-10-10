#!/usr/bin/env python3
"""Allow only the NAS's current trusted IPv4 interface addresses in Narou's UI.

Uses Linux virtual /sys interface names and SIOCGIFADDR; no disk logs, network
requests, extra Python modules, or writes when values are already present.
Preserves custom allow-list entries. Designed for QTS/Linux only.
"""
import fcntl
import ipaddress
from pathlib import Path
import socket
import struct
import subprocess
import sys

SIOCGIFADDR = 0x8915
TRUSTED = tuple(ipaddress.ip_network(n) for n in
                ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10"))
SETTING_KEYS = ("server-add-accepted-hosts", "server-ws-add-accepted-domains")


def trusted_ipv4(value):
    try:
        address = ipaddress.IPv4Address(value)
        return any(address in network for network in TRUSTED)
    except ipaddress.AddressValueError:
        return False


def current_interface_addresses(directory=Path("/sys/class/net")):
    addresses = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for interface in directory.iterdir():
            name = interface.name
            if not name.isascii() or not 1 <= len(name) <= 15:
                continue
            try:
                packed = struct.pack("256s", name.encode("ascii"))
                result = fcntl.ioctl(sock.fileno(), SIOCGIFADDR, packed)
                address = socket.inet_ntoa(result[20:24])
            except (OSError, UnicodeEncodeError, struct.error):
                continue
            if trusted_ipv4(address) and address not in addresses:
                addresses.append(address)
    return addresses


def merged_allowlist(existing, addresses):
    entries = [s.strip() for s in existing.split(",") if s.strip()]
    for addr in addresses:
        if trusted_ipv4(addr) and addr not in entries:
            entries.append(addr)
    return ",".join(entries)


def configure(binary, addresses, runner=subprocess.run):
    if not addresses:
        raise RuntimeError("No trusted QNAP LAN or Tailscale address detected")
    for name in SETTING_KEYS:
        current = runner([binary, "setting", name], check=True,
                         capture_output=True, text=True).stdout.strip()
        desired = merged_allowlist(current, addresses)
        if desired != current:
            runner([binary, "setting", name + "=" + desired], check=True,
                   capture_output=True, text=True)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: configure_hosts.py /path/to/narou_rs")
    try:
        configure(sys.argv[1], current_interface_addresses())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"QnapNarou host configuration failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
