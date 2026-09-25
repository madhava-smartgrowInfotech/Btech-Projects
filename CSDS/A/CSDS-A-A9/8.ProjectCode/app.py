"""Entry point for the Certified Federated Unlearning Lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from certified_unlearning.engine import FederatedUnlearningEngine


def run_demo() -> None:
    """Run one deterministic, headless end-to-end scenario."""

    with TemporaryDirectory(prefix="unlearning_demo_") as temporary_directory:
        engine = FederatedUnlearningEngine(audit_path=Path(temporary_directory) / "audit.jsonl")
        training = engine.train()
        target = engine.active_client_ids[0]
        certificate = engine.unlearn(target)
        audit_valid, audit_detail = engine.audit.verify()
        output = {
            "training": {
                "active_clients": training.active_clients,
                "epsilon": round(training.epsilon, 6),
                "delta": training.delta,
                "perplexity": round(training.perplexity, 4),
                "next_character_accuracy": round(training.next_character_accuracy, 4),
            },
            "unlearning_certificate": certificate.to_dict(),
            "audit_valid": audit_valid,
            "audit_detail": audit_detail,
            "generated_sample": engine.generate("privacy", length=80),
        }
        print(json.dumps(output, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Certified federated machine-unlearning demonstrator")
    parser.add_argument("--demo", action="store_true", help="run a headless end-to-end demonstration")
    parser.add_argument("--desktop", action="store_true", help="run the Tkinter desktop interface")
    parser.add_argument("--host", default="127.0.0.1", help="localhost interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="local web port (default: 8000)")
    parser.add_argument("--open-browser", action="store_true", help="open the web interface in the default browser")
    args = parser.parse_args()
    if args.demo:
        run_demo()
    elif args.desktop:
        from certified_unlearning.gui import run_gui

        run_gui()
    else:
        from certified_unlearning.web import run_web

        run_web(host=args.host, port=args.port, open_browser=args.open_browser)


if __name__ == "__main__":
    main()
