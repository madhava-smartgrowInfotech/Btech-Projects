"""SentinelFlow distributed-traffic (carpet-bombing aware) risk analysis.

Transparent rule layer around the Random Forest prediction. Produces a
0..1 distributed_risk_score from measurable quantities: source
diversity, destination diversity, aggregate packet rate, and deviation
from a rolling baseline. Never replaces the ML prediction.
"""

import math


def compute_distributed_risk(features: dict, context: dict, baseline: dict | None = None) -> dict:
    packet_rate = float(features.get("received_packets_per_second", 0.0)) + float(
        features.get("sent_packets_per_second", 0.0))
    byte_rate = float(features.get("received_bytes_per_second", 0.0)) + float(
        features.get("sent_bytes_per_second", 0.0))
    n_src = int(context.get("unique_sources", 0) or 0)
    n_dst = int(context.get("unique_destinations", 0) or 0)

    # Component 1: source diversity (many distinct sources).
    src_component = min(n_src / 30.0, 1.0)
    # Component 2: destination diversity (carpet-bombing signal).
    dst_component = min(n_dst / 15.0, 1.0)
    # Component 3: absolute packet-rate pressure.
    rate_component = min(packet_rate / 1500.0, 1.0)
    # Component 4: deviation from rolling baseline.
    if baseline and baseline.get("packet_rate", 0) > 1:
        deviation = packet_rate / max(baseline["packet_rate"], 1.0)
        baseline_component = min(max(deviation - 1.0, 0.0) / 4.0, 1.0)
    else:
        baseline_component = 0.0 if packet_rate < 300 else 0.4

    score = round(
        0.30 * src_component
        + 0.30 * dst_component
        + 0.25 * rate_component
        + 0.15 * baseline_component,
        4,
    )
    if score >= 0.7:
        level = "High"
    elif score >= 0.4:
        level = "Medium"
    else:
        level = "Low"

    spread = "concentrated"
    if n_dst >= 8 and n_src >= 8:
        spread = "distributed across many sources and destinations"
    elif n_dst >= 8:
        spread = "spread across many destinations (possible carpet-bombing pattern)"
    elif n_src >= 12:
        spread = "spread across many sources (possible distributed flood)"

    explanation = (
        "Observed %d unique sources and %d unique destinations at %.0f packets/sec "
        "(%.0f bytes/sec); traffic is %s." % (n_src, n_dst, packet_rate, byte_rate, spread)
    )
    return {
        "distributed_risk_score": score,
        "distributed_risk_level": level,
        "packet_rate": round(packet_rate, 2),
        "byte_rate": round(byte_rate, 2),
        "unique_sources": n_src,
        "unique_destinations": n_dst,
        "components": {
            "source_diversity": round(src_component, 3),
            "destination_diversity": round(dst_component, 3),
            "packet_rate_pressure": round(rate_component, 3),
            "baseline_deviation": round(baseline_component, 3),
        },
        "explanation": explanation,
    }
