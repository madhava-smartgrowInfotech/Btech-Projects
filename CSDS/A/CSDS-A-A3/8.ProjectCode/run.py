#!/usr/bin/env python3
"""PhishGuard command-line entry point.

    python run.py train              train + compare RF / XGBoost / LR
    python run.py check <url>...     classify one or more URLs
    python run.py report <url> phishing|safe [--reporter NAME] [--note TEXT]
    python run.py sync               pull public phishing feeds into threat intel
    python run.py retrain            retrain with community-confirmed URLs
    python run.py serve [--port N]   start the web interface
    python run.py download           fetch the full 420k-row dataset
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from phishguard import config  # noqa: E402
from phishguard.data import build_matrices, dataset_summary, download_full_dataset, load_dataset  # noqa: E402
from phishguard.threat_intel import ThreatIntel  # noqa: E402


def cmd_train(args):
    from phishguard.train import train_all
    print(f"Loading dataset {args.dataset} ...")
    df = load_dataset(args.dataset, max_rows=args.max_rows)
    print(json.dumps(dataset_summary(df), indent=2))
    print("Extracting features ...")
    X_tr, X_te, y_tr, y_te = build_matrices(df)
    print(f"Training on {len(y_tr)} rows, testing on {len(y_te)} rows")
    summary = train_all(X_tr, y_tr, X_te, y_te)
    print("\nModel comparison")
    print(f"{'model':<22}{'accuracy':>10}{'precision':>11}{'recall':>9}{'f1':>9}{'roc_auc':>9}")
    for name, m in summary["models"].items():
        print(f"{name:<22}{m['accuracy']:>10.4f}{m['precision']:>11.4f}{m['recall']:>9.4f}"
              f"{m['f1']:>9.4f}{m['roc_auc']:>9.4f}")


def cmd_check(args):
    from phishguard.detector import Detector
    det = Detector(ThreatIntel())
    for url in args.urls:
        r = det.check(url)
        print(f"\n{r['normalized_url']}")
        print(f"  verdict     : {r['verdict'].upper()}   (probability "
              f"{r['probability'] if r['probability'] is not None else '-'}, by {r['decided_by']})")
        print(f"  reason      : {r['reason']}")
        for f in r["red_flags"]:
            print(f"  red flag    : {f}")
        if args.json:
            print(json.dumps(r, indent=2))


def cmd_report(args):
    ti = ThreatIntel()
    entry = ti.report(args.url, args.verdict, args.reporter, args.note)
    print(f"{entry['url_norm']}: status={entry['status']} "
          f"(phishing {entry['phishing_votes']} / safe {entry['safe_votes']})")


def cmd_sync(args):
    ti = ThreatIntel()
    print(json.dumps(ti.sync_feeds(limit_per_feed=args.limit), indent=2))
    print(json.dumps(ti.stats(), indent=2))


def cmd_retrain(args):
    from phishguard.retrain import retrain
    summary = retrain(ThreatIntel(), max_rows=args.max_rows)
    print(json.dumps({k: v for k, v in summary.items() if k != "models"}, indent=2))


def cmd_serve(args):
    from phishguard.webapp import create_app
    app = create_app()
    print(f"PhishGuard web interface -> http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


def cmd_download(args):
    print("saved to", download_full_dataset())


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train"); t.add_argument("--dataset", default=str(config.DATASET_CSV))
    t.add_argument("--max-rows", type=int, default=None); t.set_defaults(fn=cmd_train)

    c = sub.add_parser("check"); c.add_argument("urls", nargs="+"); c.add_argument("--json", action="store_true")
    c.set_defaults(fn=cmd_check)

    r = sub.add_parser("report"); r.add_argument("url"); r.add_argument("verdict", choices=["phishing", "safe"])
    r.add_argument("--reporter", default="anonymous"); r.add_argument("--note", default="")
    r.set_defaults(fn=cmd_report)

    s = sub.add_parser("sync"); s.add_argument("--limit", type=int, default=500); s.set_defaults(fn=cmd_sync)

    rt = sub.add_parser("retrain"); rt.add_argument("--max-rows", type=int, default=None)
    rt.set_defaults(fn=cmd_retrain)

    sv = sub.add_parser("serve"); sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=5000); sv.add_argument("--debug", action="store_true")
    sv.set_defaults(fn=cmd_serve)

    sub.add_parser("download").set_defaults(fn=cmd_download)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
