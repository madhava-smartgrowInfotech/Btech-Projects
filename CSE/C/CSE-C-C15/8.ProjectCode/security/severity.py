"""SentinelFlow explainable threat-severity engine (Low/Medium/High/Critical)."""


def assess_severity(prediction: str, confidence: float, features: dict,
                    distributed: dict, persistence: int = 0) -> dict:
    packet_rate = float(distributed.get("packet_rate", 0.0))
    risk = float(distributed.get("distributed_risk_score", 0.0))
    n_src = int(distributed.get("unique_sources", 0))
    n_dst = int(distributed.get("unique_destinations", 0))
    is_attack = (prediction == "Attack")

    score = 0.0
    factors = []

    if is_attack:
        score += 30
        factors.append("Random Forest classified the window as Attack (%.1f%% confidence)" % (confidence * 100))
    else:
        factors.append("Random Forest classified the window as Benign (%.1f%% confidence)" % (confidence * 100))
        score += 8 * confidence  # small residual for uncertain benign windows

    if confidence >= 0.9:
        score += 15
        factors.append("High model confidence (>= 90%)")
    elif confidence >= 0.75:
        score += 8
        factors.append("Moderate model confidence (>= 75%)")

    if packet_rate >= 3000:
        score += 20
        factors.append("Very high packet rate (%.0f pkt/s)" % packet_rate)
    elif packet_rate >= 1200:
        score += 12
        factors.append("Elevated packet rate (%.0f pkt/s)" % packet_rate)
    elif packet_rate >= 400:
        score += 5
        factors.append("Above-normal packet rate (%.0f pkt/s)" % packet_rate)

    if risk >= 0.7:
        score += 20
        factors.append("High distributed-traffic risk (%.2f): %s" % (risk, distributed.get("explanation", "")))
    elif risk >= 0.4:
        score += 10
        factors.append("Medium distributed-traffic risk (%.2f)" % risk)

    if n_src >= 25 or n_dst >= 12:
        score += 8
        factors.append("Wide traffic spread (%d sources, %d destinations)" % (n_src, n_dst))

    if persistence >= 3:
        score += 10
        factors.append("Persistent suspicious activity across %d consecutive windows" % persistence)
    elif persistence == 2:
        score += 5
        factors.append("Repeated suspicious activity across 2 consecutive windows")

    if not is_attack:
        score = min(score, 45)  # benign windows cannot exceed Medium

    if score >= 70:
        severity = "Critical"
        recommendation = "Quarantine top sources in SentinelFlow immediately and rate-limit the affected interface."
    elif score >= 50:
        severity = "High"
        recommendation = "Quarantine the most active suspicious sources and recommend rate limiting."
    elif score >= 28:
        severity = "Medium"
        recommendation = "Recommend rate limiting and keep the sources under heightened monitoring."
    else:
        severity = "Low"
        recommendation = "Continue routine monitoring; no action required."

    return {
        "severity": severity,
        "severity_score": round(score, 1),
        "factors": factors,
        "recommendation": recommendation,
    }
