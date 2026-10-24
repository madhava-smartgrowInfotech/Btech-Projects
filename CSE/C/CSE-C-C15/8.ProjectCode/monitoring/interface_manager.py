"""SentinelFlow interface discovery (Scapy + psutil)."""

import socket

import psutil


def list_interfaces() -> list:
    """Return available capture interfaces with addresses and status."""
    results = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
    except Exception as exc:
        return [{"name": "error", "display": "psutil unavailable: %s" % exc, "ips": [], "up": False}]

    try:
        from scapy.interfaces import get_if_list  # type: ignore

        scapy_ifaces = list(get_if_list())
    except Exception:
        scapy_ifaces = []

    names = sorted(set(list(addrs.keys()) + scapy_ifaces))
    for name in names:
        ips = []
        try:
            for addr in addrs.get(name, []):
                if addr.family in (socket.AF_INET, socket.AF_INET6) and addr.address:
                    ips.append(addr.address)
        except Exception:
            ips = []  # keep the interface listed even when its addresses cannot be read
        up = True
        try:
            if name in stats:
                up = bool(stats[name].isup)
        except Exception:
            up = True  # assume reachable when the OS status query fails
        results.append({
            "name": name,
            "display": "%s (%s)" % (name, ", ".join(ips[:2]) if ips else "no address"),
            "ips": ips,
            "up": up,
        })
    if not results:
        results.append({"name": "default", "display": "default (any interface)", "ips": [], "up": True})
    return results


def local_ip_set() -> set:
    ips = set()
    try:
        for _, addr_list in psutil.net_if_addrs().items():
            for addr in addr_list:
                if addr.family == socket.AF_INET and addr.address:
                    ips.add(addr.address)
    except Exception:
        ips = set()  # unreadable adapters are ignored; loopback is added below
    ips.add("127.0.0.1")
    return ips
