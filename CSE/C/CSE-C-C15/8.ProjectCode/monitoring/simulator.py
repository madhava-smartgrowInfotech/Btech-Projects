"""SentinelFlow safe traffic simulator (Simulation Mode).

Generates realistic packet-level windows in software (no network I/O,
no attack traffic emitted) and feeds them through the exact same
aggregation + inference pipeline as live capture.
"""

import random
import threading
import time


class TrafficSimulator:
    def __init__(self, on_window=None, seed=7):
        self.on_window = on_window
        self._thread = None
        self._stop = threading.Event()
        self.running = False
        self.window_seconds = 10
        self.attack_probability = 0.35
        self._rng = random.Random(seed)
        self.windows_completed = 0

    def start(self, window_seconds: int = 10):
        if self.running:
            raise RuntimeError("Simulator already running.")
        self.window_seconds = max(int(window_seconds), 2)
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.running = True

    def stop(self):
        self._stop.set()
        self.running = False

    def _loop(self):
        from monitoring.interface_manager import local_ip_set
        from monitoring.traffic_aggregator import aggregate_packets

        local_ips = local_ip_set()
        local_host = "192.168.1.20"
        while not self._stop.is_set():
            is_attack = self._rng.random() < self.attack_probability
            packets = self._make_window(is_attack)
            features, context = aggregate_packets(packets, self.window_seconds, local_ips | {local_host})
            context["simulated_attack_intended"] = bool(is_attack)
            self.windows_completed += 1
            if self.on_window and not self._stop.is_set():
                try:
                    self.on_window(features, context, "simulation", "simulation")
                except Exception as exc:
                    print("SentinelFlow simulator callback failed: %s" % exc)
            # Wait for the window period (interruptible).
            deadline = time.time() + self.window_seconds
            while time.time() < deadline and not self._stop.is_set():
                time.sleep(0.2)

    def _make_window(self, is_attack: bool) -> list:
        r = self._rng
        packets = []
        if not is_attack:
            n = r.randint(60, 600)
            for _ in range(n):
                if r.random() < 0.55:
                    src, dst = "192.168.1.20", r.choice(["93.184.216.34", "142.250.72.14", "192.168.1.1"])
                else:
                    src, dst = r.choice(["93.184.216.34", "142.250.72.14"]), "192.168.1.20"
                proto = r.choices(["TCP", "UDP", "ICMP", "other"], weights=[62, 28, 4, 6])[0]
                packets.append({"src": src, "dst": dst, "proto": proto,
                                "length": int(r.gauss(700, 350)) if proto == "TCP" else int(r.uniform(60, 1200))})
        else:
            style = r.choice(["flood", "carpet", "slow"])
            if style == "flood":
                n = r.randint(2500, 9000)
                attacker_pool = ["10.66.%d.%d" % (r.randint(0, 40), r.randint(2, 254)) for _ in range(r.randint(8, 40))]
                for _ in range(n):
                    packets.append({"src": r.choice(attacker_pool), "dst": "192.168.1.20",
                                    "proto": r.choices(["TCP", "UDP", "ICMP"], weights=[55, 35, 10])[0],
                                    "length": int(r.uniform(60, 320))})
            elif style == "carpet":
                n = r.randint(1800, 6000)
                attacker_pool = ["172.16.%d.%d" % (r.randint(0, 60), r.randint(2, 254)) for _ in range(r.randint(10, 45))]
                victim_pool = ["192.168.1.%d" % i for i in r.sample(range(2, 60), r.randint(6, 20))]
                for _ in range(n):
                    packets.append({"src": r.choice(attacker_pool), "dst": r.choice(victim_pool),
                                    "proto": r.choices(["TCP", "UDP"], weights=[50, 50])[0],
                                    "length": int(r.uniform(60, 520))})
            else:
                n = r.randint(300, 1200)
                for _ in range(n):
                    packets.append({"src": "10.99.%d.%d" % (r.randint(0, 20), r.randint(2, 254)),
                                    "dst": "192.168.1.20", "proto": "TCP",
                                    "length": int(r.uniform(200, 1400))})
        # Clamp lengths to sane Ethernet bounds.
        for p in packets:
            p["length"] = max(40, min(1500, int(p["length"])))
        return packets
