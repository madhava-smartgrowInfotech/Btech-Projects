#!/usr/bin/env bash
# One-shot launcher: install deps (first time), seed demo accounts, start the app.
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
python scripts/seed_demo.py || true
streamlit run app.py
