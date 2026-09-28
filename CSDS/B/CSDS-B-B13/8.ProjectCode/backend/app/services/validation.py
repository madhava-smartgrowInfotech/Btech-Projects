"""F8 - validate scan findings against a target's known-vulnerability list."""


def validate(known_vulns: list[dict], findings: list[dict]) -> dict:
    known_keys = {k["key"] for k in known_vulns}
    found_keys = {f["vuln_key"] for f in findings
                  if f.get("vuln_key") and f["severity"] != "info"}

    detected = sorted(known_keys & found_keys)
    missed = sorted(known_keys - found_keys)
    false_positives = sorted(found_keys - known_keys)

    total = len(known_keys)
    detection_rate = round(100 * len(detected) / total, 1) if total else 0.0

    key_to_name = {k["key"]: k.get("name", k["key"]) for k in known_vulns}
    return {
        "total_known": total,
        "detected_count": len(detected),
        "missed_count": len(missed),
        "false_positive_count": len(false_positives),
        "detection_rate": detection_rate,
        "detected": [{"key": k, "name": key_to_name.get(k, k)} for k in detected],
        "missed": [{"key": k, "name": key_to_name.get(k, k)} for k in missed],
        "false_positives": list(false_positives),
    }
