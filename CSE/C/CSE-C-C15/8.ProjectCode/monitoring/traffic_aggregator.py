"""SentinelFlow traffic aggregation: packets -> common ML feature schema.

Orientation rule (documented):
  received_* = inbound to this host (packet dst is a local address,
               or neither endpoint is local -> counted as received
               because the sensor observes it arriving on the wire).
  sent_*     = outbound from this host (packet src is local and dst
               is not local).
"""

from collections import Counter


def aggregate_packets(packets: list, window_seconds: float, local_ips: set) -> tuple:
    """Aggregate packet summaries into (features, context).

    packets: list of dicts {src, dst, proto, length}
    Returns (feature_dict, context_dict) using the 10-feature schema.
    """
    window_seconds = max(float(window_seconds), 1e-6)
    received_packets = 0
    received_bytes = 0
    sent_packets = 0
    sent_bytes = 0
    srcs = []
    dsts = []
    protos = []
    per_src = Counter()
    per_dst = Counter()

    for pkt in packets:
        try:
            src = str(pkt.get("src", "unknown"))
            dst = str(pkt.get("dst", "unknown"))
            length = max(int(pkt.get("length", 0)), 0)
            proto = str(pkt.get("proto", "other"))
        except Exception:
            continue
        srcs.append(src)
        dsts.append(dst)
        protos.append(proto)
        per_src[src] += 1
        per_dst[dst] += 1
        src_local = src in local_ips
        dst_local = dst in local_ips
        if src_local and not dst_local:
            sent_packets += 1
            sent_bytes += length
        else:
            # dst local, both local (loopback), or external transit
            received_packets += 1
            received_bytes += length

    features = {
        "received_packets": float(received_packets),
        "received_bytes": float(received_bytes),
        "received_packets_per_second": float(received_packets / window_seconds),
        "received_bytes_per_second": float(received_bytes / window_seconds),
        "average_received_packet_size": float(received_bytes / received_packets) if received_packets else 0.0,
        "sent_packets": float(sent_packets),
        "sent_bytes": float(sent_bytes),
        "sent_packets_per_second": float(sent_packets / window_seconds),
        "sent_bytes_per_second": float(sent_bytes / window_seconds),
        "average_sent_packet_size": float(sent_bytes / sent_packets) if sent_packets else 0.0,
    }

    total = max(len(srcs), 1)
    proto_counts = Counter(protos)
    context = {
        "packet_count": len(packets),
        "unique_sources": len(set(srcs)),
        "unique_destinations": len(set(dsts)),
        "packets_per_source": float(len(packets) / max(len(set(srcs)), 1)),
        "packets_per_destination": float(len(packets) / max(len(set(dsts)), 1)),
        "protocol_distribution": {k: int(v) for k, v in proto_counts.items()},
        "tcp_share": float(proto_counts.get("TCP", 0) / total),
        "udp_share": float(proto_counts.get("UDP", 0) / total),
        "icmp_share": float(proto_counts.get("ICMP", 0) / total),
        "top_sources": [{"ip": ip, "packets": int(c)} for ip, c in per_src.most_common(5)],
        "top_destinations": [{"ip": ip, "packets": int(c)} for ip, c in per_dst.most_common(5)],
        "window_seconds": float(window_seconds),
    }
    return features, context
