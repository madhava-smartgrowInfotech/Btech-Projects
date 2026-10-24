"""SentinelFlow adaptive mitigation: application-level denylist/rate-control.

Safe by design: quarantine decisions live inside SentinelFlow and expire
automatically (default ~40 s). No OS firewall is touched unless an
explicit opt-in routine is called (disabled by default).
"""

import threading
import time


def _local_ips_safe() -> set:
    try:
        from monitoring.interface_manager import local_ip_set

        return set(local_ip_set())
    except Exception as exc:
        print("SentinelFlow: local address lookup unavailable (%s); protecting loopback only." % exc)
        return set()


class MitigationManager:
    def __init__(self, db, quarantine_seconds: int = 40):
        self.db = db
        self.quarantine_seconds = int(quarantine_seconds)
        self._lock = threading.Lock()
        self.active: dict = {}  # ip -> record

    def set_duration(self, seconds: int):
        self.quarantine_seconds = max(int(seconds), 5)

    def decide(self, severity: str, context: dict, reason: str) -> list:
        """Apply policy for one window. Returns list of actions taken."""
        actions = []
        self.expire_due()
        protected = {"unknown", "127.0.0.1", "::1", "192.168.1.20"} | _local_ips_safe()
        if severity in ("High", "Critical"):
            targets = [t["ip"] for t in (context.get("top_sources") or [])[:3]
                       if t["ip"] not in protected]
            duration = self.quarantine_seconds * (2 if severity == "Critical" else 1)
            for ip in targets:
                if self.quarantine(ip, reason + " [%s]" % severity, duration):
                    actions.append({"action": "quarantine", "target": ip, "duration": duration})
            if not targets:
                actions.append({"action": "rate_limit_recommended", "target": "interface", "duration": 0})
        elif severity == "Medium":
            actions.append({"action": "rate_limit_recommended", "target": "interface", "duration": 0})
        else:
            actions.append({"action": "monitor", "target": "interface", "duration": 0})
        return actions

    def quarantine(self, ip: str, reason: str, duration: int | None = None) -> bool:
        duration = int(duration or self.quarantine_seconds)
        now = time.time()
        with self._lock:
            existing = self.active.get(ip)
            if existing and existing["expires_at"] > now:
                return False
            record = {
                "ip": ip,
                "reason": reason,
                "quarantined_at": now,
                "expires_at": now + duration,
                "duration": duration,
                "status": "active",
            }
            self.active[ip] = record
        try:
            self.db.add_mitigation(ip, reason, duration, "active")
        except Exception as exc:
            print("SentinelFlow mitigation history write failed: %s" % exc)
        return True

    def expire_due(self) -> list:
        now = time.time()
        expired = []
        with self._lock:
            for ip, rec in list(self.active.items()):
                if rec["expires_at"] <= now:
                    rec["status"] = "recovered"
                    expired.append(rec)
                    del self.active[ip]
        for rec in expired:
            try:
                self.db.mark_mitigation_recovered(rec["ip"], rec["reason"])
            except Exception as exc:
                print("SentinelFlow recovery history update failed: %s" % exc)
        return expired

    def get_active(self) -> list:
        self.expire_due()
        now = time.time()
        out = []
        with self._lock:
            for rec in self.active.values():
                remaining = max(int(rec["expires_at"] - now), 0)
                out.append({
                    "ip": rec["ip"],
                    "reason": rec["reason"],
                    "quarantined_at": rec["quarantined_at"],
                    "expires_at": rec["expires_at"],
                    "remaining_seconds": remaining,
                    "duration": rec["duration"],
                    "status": "active",
                })
        return out

    # Optional OS firewall integration: disabled by default, explicit only.
    def apply_os_firewall_block(self, ip: str) -> dict:
        return {
            "applied": False,
            "message": ("OS-level firewall integration is disabled by default. "
                        "No system firewall rule was changed for %s. "
                        "SentinelFlow application-level quarantine remains the active mechanism." % ip),
        }
