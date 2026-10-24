"""SentinelFlow live packet capture engine (Scapy sniff, rolling windows)."""

import threading
import time


class MonitorEngine:
    """Background rolling-window capture engine.

    on_window(features, context, source, interface) is invoked after
    every completed window.
    """

    def __init__(self, on_window=None):
        self.on_window = on_window
        self._thread = None
        self._stop = threading.Event()
        self.running = False
        self.source = "stopped"  # stopped | live | simulation
        self.interface = ""
        self.window_seconds = 10
        self.last_error = ""
        self.windows_completed = 0

    def start_live(self, interface: str, window_seconds: int = 10):
        if self.running:
            raise RuntimeError("Monitor already running. Stop it first.")
        self.interface = interface
        self.window_seconds = max(int(window_seconds), 2)
        self._stop.clear()
        self._thread = threading.Thread(target=self._live_loop, daemon=True)
        self._thread.start()
        self.running = True
        self.source = "live"

    def stop(self):
        self._stop.set()
        self.running = False
        self.source = "stopped"

    # -- internal -----------------------------------------------------
    def _live_loop(self):
        from monitoring.interface_manager import local_ip_set
        from monitoring.traffic_aggregator import aggregate_packets

        try:
            from scapy.all import sniff  # type: ignore
        except Exception as exc:
            self.last_error = "Scapy is unavailable: %s" % exc
            self.running = False
            self.source = "stopped"
            return

        local_ips = local_ip_set()
        while not self._stop.is_set():
            packets = []
            error = ""

            def _cb(pkt):
                try:
                    src = pkt["IP"].src if pkt.haslayer("IP") else (
                        pkt["IPv6"].src if pkt.haslayer("IPv6") else "unknown")
                    dst = pkt["IP"].dst if pkt.haslayer("IP") else (
                        pkt["IPv6"].dst if pkt.haslayer("IPv6") else "unknown")
                    if pkt.haslayer("TCP"):
                        proto = "TCP"
                    elif pkt.haslayer("UDP"):
                        proto = "UDP"
                    elif pkt.haslayer("ICMP") or pkt.haslayer("ICMPv6Unknown"):
                        proto = "ICMP"
                    else:
                        proto = "other"
                    try:
                        length = int(len(pkt))
                    except Exception:
                        length = 64
                    packets.append({"src": src, "dst": dst, "proto": proto, "length": length})
                except Exception:
                    return None  # skip this malformed packet; the window continues

            try:
                sniff(iface=self.interface if self.interface not in ("", "default") else None,
                      prn=_cb, timeout=self.window_seconds, store=False)
            except PermissionError as exc:
                error = ("Packet capture permission denied: %s. "
                         "Run as Administrator/root, install Npcap on Windows, "
                         "or use Simulation Mode." % exc)
            except Exception as exc:
                msg = str(exc).lower()
                if "no such device" in msg or "no interface" in msg or "unknown" in msg:
                    error = "Invalid network interface '%s': %s" % (self.interface, exc)
                elif "npcap" in msg or "winpcap" in msg:
                    error = ("Packet capture driver unavailable: %s. "
                             "Install Npcap (https://npcap.com) or use Simulation Mode." % exc)
                else:
                    error = "Capture failed on '%s': %s" % (self.interface, exc)
            if self._stop.is_set():
                break
            if error:
                self.last_error = error
                # Back off briefly, then surface one empty-window callback so
                # the UI can display the failure instead of hanging silently.
                time.sleep(2)
                if self.on_window and not self._stop.is_set():
                    try:
                        self.on_window({}, {"error": error, "packet_count": 0},
                                       "live-error", self.interface)
                    except Exception as exc:
                        self.last_error = "Detection callback failed: %s" % exc
                # Stop after a hard failure to avoid hot-looping; user can
                # restart or switch to Simulation Mode.
                self.running = False
                self.source = "stopped"
                return
            try:
                features, context = aggregate_packets(packets, self.window_seconds, local_ips)
                self.windows_completed += 1
                if self.on_window:
                    self.on_window(features, context, "live", self.interface)
            except Exception as exc:
                self.last_error = "Aggregation failed: %s" % exc
