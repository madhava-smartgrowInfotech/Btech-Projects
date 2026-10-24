"""SentinelFlow shared feature schema.

Single source of truth for the 10 ML features. Both training
(CICIDS2017 preprocessing) and inference (Scapy live windows) must
produce exactly these features in this order.
"""

FEATURE_COLUMNS = [
    "received_packets",
    "received_bytes",
    "received_packets_per_second",
    "received_bytes_per_second",
    "average_received_packet_size",
    "sent_packets",
    "sent_bytes",
    "sent_packets_per_second",
    "sent_bytes_per_second",
    "average_sent_packet_size",
]

# Mapping documentation: CICIDS2017 flow orientation ->
# common schema orientation.
#   sent_*     <- forward direction (initiator -> responder):
#                   Fwd Packets, Total Length of Fwd Packets
#   received_* <- backward direction (responder -> initiator):
#                   Bwd Packets, Total Length of Bwd Packets
#   rates      <- counts / flow duration in seconds
#   averages   <- bytes / packets (0 when packet count is 0)
#
# Live capture orientation (documented in traffic_aggregator):
#   received_* <- packets whose destination is a local interface
#                 address (inbound to this host). Packets matching no
#                 local address are counted as received since the
#                 sensor observes them arriving on the wire.
#   sent_*     <- packets whose source is a local interface address
#                 (outbound from this host).


def validate_feature_dict(features: dict) -> list:
    """Validate a feature dict and return ordered value list.

    Raises ValueError when a required feature is missing or invalid.
    """
    missing = [c for c in FEATURE_COLUMNS if c not in features]
    if missing:
        raise ValueError("Missing features for prediction: %s" % ", ".join(missing))
    ordered = []
    for col in FEATURE_COLUMNS:
        try:
            value = float(features[col])
        except (TypeError, ValueError):
            raise ValueError("Invalid (non-numeric) value for feature '%s': %r" % (col, features[col]))
        if value != value or value in (float("inf"), float("-inf")):  # NaN / inf guard
            raise ValueError("Invalid (NaN/inf) value for feature '%s'" % col)
        if value < 0:
            raise ValueError("Negative value for feature '%s'" % col)
        ordered.append(value)
    return ordered


def empty_feature_dict() -> dict:
    return {c: 0.0 for c in FEATURE_COLUMNS}
