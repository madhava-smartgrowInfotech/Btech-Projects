"""Shared pytest fixtures: every test runs against a scratch SQLite file, never data/sentinelflow.db."""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.db import Database  # noqa: E402


@pytest.fixture()
def db(tmp_path):
    return Database(str(tmp_path / "test.db"))


@pytest.fixture()
def flask_app(tmp_path):
    import app as app_module

    scratch = Database(str(tmp_path / "api.db"))
    old_db, old_mit_db = app_module.db, app_module.mitigation.db
    app_module.db = scratch
    app_module.mitigation.db = scratch
    app_module.mitigation.active.clear()
    app_module.mitigation.quarantine_seconds = 40
    app_module.monitor.window_seconds = 10
    app_module.baseline_rates.clear()
    app_module.consecutive_suspicious = 0
    app_module.latest_detection = None
    app_module.app.config["TESTING"] = True
    yield app_module
    app_module.simulator.stop()
    app_module.monitor.stop()
    app_module.db, app_module.mitigation.db = old_db, old_mit_db
    app_module.mitigation.active.clear()


@pytest.fixture()
def client(flask_app):
    return flask_app.app.test_client()


def attack_features():
    """A window that looks like a volumetric flood (many packets, small payloads, one-way)."""
    return {
        "received_packets": 60000.0, "received_bytes": 6.0e6, "received_packets_per_second": 6000.0,
        "received_bytes_per_second": 6.0e5, "average_received_packet_size": 100.0,
        "sent_packets": 0.0, "sent_bytes": 0.0, "sent_packets_per_second": 0.0,
        "sent_bytes_per_second": 0.0, "average_sent_packet_size": 0.0,
    }


def benign_features():
    return {
        "received_packets": 1500.0, "received_bytes": 1.0e6, "received_packets_per_second": 150.0,
        "received_bytes_per_second": 1.0e5, "average_received_packet_size": 666.0,
        "sent_packets": 1500.0, "sent_bytes": 1.0e6, "sent_packets_per_second": 150.0,
        "sent_bytes_per_second": 1.0e5, "average_sent_packet_size": 666.0,
    }


def attack_context(n_src=40, n_dst=14):
    return {
        "packet_count": 60000, "unique_sources": n_src, "unique_destinations": n_dst,
        "top_sources": [{"ip": "10.66.1.%d" % i, "packets": 5000 - i} for i in range(1, 6)],
        "top_destinations": [{"ip": "192.168.1.20", "packets": 40000}],
        "protocol_distribution": {"TCP": 30000, "UDP": 30000}, "window_seconds": 10.0,
    }
