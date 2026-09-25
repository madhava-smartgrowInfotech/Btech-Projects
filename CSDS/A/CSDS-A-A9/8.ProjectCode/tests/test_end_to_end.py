from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer

from certified_unlearning.audit import AuditLedger
from certified_unlearning.engine import FederatedUnlearningEngine
from certified_unlearning.web import ApplicationState, make_handler


class FederatedUnlearningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.audit_path = Path(self.temporary_directory.name) / "audit.jsonl"
        self.engine = FederatedUnlearningEngine(audit_path=self.audit_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_complete_training_and_unlearning_workflow(self) -> None:
        training = self.engine.train()
        self.assertEqual(training.active_clients, 5)
        self.assertGreater(training.epsilon, 0)
        self.assertGreater(training.perplexity, 0)

        certificate = self.engine.unlearn("client_finance")
        self.assertEqual(certificate.status, "CERTIFIED")
        self.assertEqual(certificate.clients_before, 5)
        self.assertEqual(certificate.clients_after, 4)
        self.assertLessEqual(certificate.reference_retrain_l2, 1e-10)
        self.assertNotEqual(certificate.model_hash_before, certificate.model_hash_after)
        self.assertTrue(certificate.audit_record_hash)
        self.assertTrue(self.engine.audit.verify()[0])

    def test_unlearning_is_not_repeatable_for_same_client(self) -> None:
        self.engine.train()
        self.engine.unlearn("client_health")
        with self.assertRaises(ValueError):
            self.engine.unlearn("client_health")

    def test_audit_detects_tampering(self) -> None:
        self.engine.train()
        records = self.engine.audit.read_all()
        records[0]["epsilon"] = 999
        self.audit_path.write_text(json.dumps(records[0]) + "\n", encoding="utf-8")
        valid, detail = AuditLedger(self.audit_path).verify()
        self.assertFalse(valid)
        self.assertIn("failed", detail.lower())

    def test_certificate_export_is_machine_readable(self) -> None:
        self.engine.train()
        certificate = self.engine.unlearn("client_education")
        export_path = Path(self.temporary_directory.name) / "certificate.json"
        self.engine.export_certificate(certificate, export_path)
        payload = json.loads(export_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["certificate_id"], certificate.certificate_id)
        self.assertIn("Verified", payload["audit_verification"])

    def test_localhost_health_and_state_endpoints(self) -> None:
        application = ApplicationState(self.audit_path)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(application))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            root = f"http://127.0.0.1:{server.server_address[1]}"
            with urllib.request.urlopen(f"{root}/api/health", timeout=3) as response:
                health = json.loads(response.read())
            self.assertEqual(health["status"], "ok")
            with urllib.request.urlopen(f"{root}/api/state", timeout=3) as response:
                state = json.loads(response.read())
            self.assertFalse(state["trained"])
            self.assertEqual(len(state["contributions"]), 5)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
