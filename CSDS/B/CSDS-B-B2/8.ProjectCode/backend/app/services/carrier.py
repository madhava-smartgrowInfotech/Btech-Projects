"""Which mobile operator (and which kind of link) a phone-probe request came from, from its public IP.

Uses the iptoasn.com IP-to-ASN table (public domain, data/asn/ip2asn-v4.tsv.gz) - fully offline.
Some networks carry both mobile and home-broadband traffic under one ASN (Jio, BSNL); for those the
browser's own connection hint (navigator.connection.type) decides between cellular and Wi-Fi.
"""
from __future__ import annotations

import bisect
import gzip
import ipaddress
import logging
import re
import socket
import struct
import threading
from dataclasses import dataclass

from ..core.config import settings

log = logging.getLogger("signalscout.carrier")

# ASN -> (operator name, network kind). kind: mobile | broadband | mixed
KNOWN_ASNS: dict[int, tuple[str, str]] = {
    55836: ("Jio", "mixed"), 64049: ("Jio", "mixed"),
    45609: ("Airtel", "mobile"), 24560: ("Airtel", "broadband"), 9498: ("Airtel", "broadband"),
    38266: ("Vi", "mobile"), 45271: ("Vi", "mobile"), 55410: ("Vi", "mobile"), 55644: ("Vi", "mobile"),
    9829: ("BSNL", "mixed"), 17488: ("MTNL", "mixed"),
}


@dataclass
class CarrierInfo:
    ip: str | None
    asn: int | None
    operator: str | None       # short operator name when it is a known mobile network
    network_name: str | None   # the ASN's registered name
    kind: str                  # mobile / broadband / mixed / local / unknown

    @property
    def display_name(self) -> str | None:
        """Readable network name: 'PEL-AS-IN Pioneer Elabs Ltd.' -> 'Pioneer Elabs Ltd.'."""
        if self.kind == "local":
            return "Local network"
        if not self.network_name:
            return None
        head, _, rest = self.network_name.partition(" ")
        return rest.strip() if rest and re.fullmatch(r"[A-Z0-9-]+", head) else self.network_name

    def link_for(self, browser_type: str | None) -> str:
        """cellular / wifi / unknown, combining the ASN kind with the browser's hint."""
        hint = (browser_type or "").lower()
        if hint == "cellular":
            return "cellular"
        if hint in ("wifi", "ethernet"):
            return "wifi"
        if self.kind == "mobile":
            return "cellular"
        if self.kind in ("broadband", "local"):
            return "wifi"
        return "unknown"


class _AsnTable:
    def __init__(self):
        self._starts: list[int] = []
        self._rows: list[tuple[int, int, str, str]] = []   # (end, asn, country, name)
        self._loaded = False
        self._lock = threading.Lock()

    def _load(self) -> None:
        path = settings.data_dir / "asn" / "ip2asn-v4.tsv.gz"
        if not path.exists():
            log.warning("ASN table missing - operator detection disabled", extra={"fields": {"path": str(path)}})
            self._loaded = True
            return
        starts, rows = [], []
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 5 or parts[2] == "0":
                    continue
                starts.append(_ip_to_int(parts[0]))
                rows.append((_ip_to_int(parts[1]), int(parts[2]), parts[3], parts[4]))
        self._starts, self._rows, self._loaded = starts, rows, True
        log.info("ASN table loaded", extra={"fields": {"ranges": len(rows)}})

    def lookup(self, ip: str) -> tuple[int, str, str] | None:
        if not self._loaded:
            with self._lock:
                if not self._loaded:
                    self._load()
        try:
            n = _ip_to_int(ip)
        except OSError:
            return None
        i = bisect.bisect_right(self._starts, n) - 1
        if i >= 0 and n <= self._rows[i][0]:
            _, asn, country, name = self._rows[i]
            return asn, country, name
        return None


_table = _AsnTable()


def _ip_to_int(ip: str) -> int:
    return struct.unpack("!I", socket.inet_aton(ip))[0]


def preload_in_background() -> None:
    """Load the ASN table at start-up so the first phone request is not slowed down."""
    threading.Thread(target=lambda: _table.lookup("1.1.1.1"), name="asn-preload", daemon=True).start()


def client_ip(headers: dict, peer: str | None) -> str | None:
    """The phone's public IP: Cloudflare puts it in CF-Connecting-IP; otherwise the socket peer."""
    for key in ("cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        value = headers.get(key)
        if value:
            return value.split(",")[0].strip()
    return peer


def lookup(ip: str | None) -> CarrierInfo:
    if not ip:
        return CarrierInfo(None, None, None, None, "unknown")
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return CarrierInfo(ip, None, None, None, "unknown")
    if addr.is_private or addr.is_loopback or addr.is_link_local:
        return CarrierInfo(ip, None, None, "Local network", "local")
    if addr.version != 4:
        return CarrierInfo(ip, None, None, None, "unknown")
    hit = _table.lookup(ip)
    if not hit:
        return CarrierInfo(ip, None, None, None, "unknown")
    asn, _country, name = hit
    known = KNOWN_ASNS.get(asn)
    if known:
        return CarrierInfo(ip, asn, known[0], name, known[1])
    return CarrierInfo(ip, asn, None, name, "broadband")
