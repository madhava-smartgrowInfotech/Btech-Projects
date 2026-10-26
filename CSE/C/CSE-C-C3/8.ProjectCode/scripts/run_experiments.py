"""Runs every measurement behind the project documents and writes experiments/<name>/metrics.json.

    .venv\\Scripts\\python.exe scripts/run_experiments.py

Experiments
  buffer_population   - 4 buffer policies (+ the paper-literal rule) x vehicles 80..110, 25 % bad, 30 seeds
  buffer_badshare     - same policies x 25..50 % bad vehicles, population random in [80, 110], 30 seeds
  trust_ablation      - the same comparison with the Trust Score system switched off
  trust_dynamics      - trust score / fee multiplier of one driver against the overstay probability
  seeded_history      - Strategy Insights computed on the seeded 60-day demo history (synthetic data)
  engine_parity       - simulator against the real engine, decision for decision
  unit_tests          - pytest outcome
API latency and the concurrency probe are measured against a running server by scripts/measure_api.py.
"""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "experiments"

from scripts import parity  # noqa: E402
from scripts.parking_sim import SIM_ASSUMPTIONS, STRATEGIES, mean_std, run_config  # noqa: E402

SEEDS = list(range(30))


def save(name, obj):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print("wrote", d / "metrics.json")


def buffer_population():
    res = {"assumptions": SIM_ASSUMPTIONS, "bad_share": 0.25, "seeds": len(SEEDS), "by_population": {}}
    for n in (80, 90, 100, 110):
        res["by_population"][str(n)] = {s: run_config(n, 0.25, s, SEEDS) for s in STRATEGIES}
    save("buffer_population", res)
    return res


def buffer_badshare():
    res = {"assumptions": SIM_ASSUMPTIONS, "population": "uniform in [80, 110] per run", "seeds": len(SEEDS), "by_bad_share": {}}
    for bad in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50):
        res["by_bad_share"][str(bad)] = {s: run_config(0, bad, s, SEEDS, random_population=True) for s in STRATEGIES}
    save("buffer_badshare", res)
    return res


def trust_ablation():
    res = {"setting": "population random in [80, 110], 30 seeds", "by_bad_share": {}}
    for bad in (0.25, 0.50):
        res["by_bad_share"][str(bad)] = {
            "trust_on": {s: run_config(0, bad, s, SEEDS, trust_on=True, random_population=True) for s in STRATEGIES},
            "trust_off": {s: run_config(0, bad, s, SEEDS, trust_on=False, random_population=True) for s in STRATEGIES},
        }
    save("trust_ablation", res)
    return res


def trust_dynamics():
    """One driver, 100 sessions, probability p of overstaying; trust rules exactly as engine.record_checkout_trust."""
    from scripts.parking_sim import suspended, trust_update
    from app.engine import fee_multiplier
    out = {}
    for p in (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0):
        finals, mults, first_susp, avg_hist = [], [], [], []
        for seed in range(200):
            rnd = random.Random(seed)
            st = {"trust": 3.0, "streak": 0, "warnings": 0, "last_warning": None, "suspended_until": -1.0, "now": 0.0}
            first = None
            for k in range(100):
                st["now"] = k * 24 * 60.0
                if suspended(st, st["now"]):
                    first = k if first is None else first
                    continue                         # a refused request records no outcome
                trust_update(st, rnd.random() >= p)
            finals.append(st["trust"])
            mults.append(fee_multiplier(st["trust"]))
            first_susp.append(first)
        m_t, s_t = mean_std(finals)
        m_f, _ = mean_std(mults)
        hit = [f for f in first_susp if f is not None]
        out[str(p)] = {"mean_final_trust": round(m_t, 3), "std_final_trust": round(s_t, 3),
                       "mean_fee_multiplier": round(m_f, 3),
                       "share_ever_suspended": round(len(hit) / len(first_susp), 3),
                       "median_first_suspension_session": (sorted(hit)[len(hit) // 2] if hit else None)}
    save("trust_dynamics", {"sessions": 100, "drivers_per_setting": 200, "note": "one session per day; a suspended driver books nothing, so the 14-day lockout shows up as time without sessions", "by_overstay_probability": out})
    return out


SEED_CHILD = '''
import json, sys
sys.path.insert(0, r"{root}")
from app.database import Base, SessionLocal, engine
from app.seed import seed_if_empty
from app.models import ParkingLocation, Payment, Reservation, User
from scripts.compute_buffer_strategy_metrics import compute_all
Base.metadata.create_all(bind=engine)
db = SessionLocal()
seed_if_empty(db)
states = ("completed", "failed", "declined", "reserved", "active", "cancelled")
meta = {{"users": db.query(User).count(), "locations": db.query(ParkingLocation).count(),
        "reservations": db.query(Reservation).count(), "payments": db.query(Payment).count(),
        "status_counts": {{s: db.query(Reservation).filter(Reservation.status == s).count() for s in states}}}}
meta["insights_60d"] = compute_all(db, window_days=60)
print(json.dumps(meta, default=str))
'''


def seeded_history():
    """Fresh database seeded by app/seed.py, in a child process so the throw-away DB is the one the app binds to."""
    tmp = tempfile.mkdtemp(prefix="parksure_seed_")
    env = dict(os.environ, PARKSURE_DB="sqlite:///" + (Path(tmp) / "seed.db").as_posix())
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    p = subprocess.run([str(py if py.exists() else sys.executable), "-c", SEED_CHILD.format(root=str(ROOT))],
                       capture_output=True, text=True, env=env, cwd=tmp)
    if p.returncode:
        raise RuntimeError(p.stderr)
    meta = json.loads(p.stdout.strip().splitlines()[-1])
    save("seeded_history", meta)
    return meta


def engine_microbench():
    """Cost of the individual engine decisions on an in-memory database (no HTTP, no bcrypt)."""
    import statistics
    from datetime import datetime, timedelta, timezone
    from app.engine import forecast_free, haversine_km, nearest_alternate
    from app.models import ParkingLocation, Reservation, User
    s = parity._session()
    u = User(name="U", email="u@x.io", password_hash="x")
    s.add(u)
    t0 = datetime(2030, 1, 1, tzinfo=timezone.utc)
    locs = [ParkingLocation(name=f"L{i}", address="", latitude=12.9 + 0.01 * i, longitude=77.5, capacity=50, buffer_size=1, price_per_hour=3) for i in range(50)]
    s.add_all(locs)
    s.commit()
    rnd = random.Random(5)
    for lc in locs:
        for _ in range(100):
            a = t0 + timedelta(minutes=rnd.uniform(0, 7 * 24 * 60))
            s.add(Reservation(user_id=u.id, location_id=lc.id, start_time=a, end_time=a + timedelta(hours=rnd.uniform(1, 3)), status="reserved"))
    s.commit()

    def timeit(fn, n):
        xs = []
        for _ in range(n):
            a = time.perf_counter()
            fn()
            xs.append((time.perf_counter() - a) * 1000)
        return {"n": n, "mean_ms": round(statistics.mean(xs), 4), "p95_ms": round(sorted(xs)[int(0.95 * (n - 1))], 4)}

    st, en = t0 + timedelta(days=3), t0 + timedelta(days=3, hours=2)
    res = {"database": "in-memory SQLite, 50 locations x 100 stored bookings = 5,000 reservations",
           "forecast_free (admission, 100 bookings at the location)": timeit(lambda: forecast_free(s, locs[0], st, en), 300),
           "nearest_alternate over 49 other locations": timeit(lambda: nearest_alternate(s, locs[0], st, en), 100),
           "haversine_km (one pair)": timeit(lambda: haversine_km(12.9, 77.5, 12.95, 77.6), 20000)}
    save("engine_microbench", res)
    return res


def engine_parity():
    r = parity.all_parity()
    save("engine_parity", r)
    return r


def unit_tests():
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    t0 = time.time()
    p = subprocess.run([str(py if py.exists() else sys.executable), "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True)
    tail = p.stdout.strip().splitlines()[-1]
    passed = int(re.search(r"(\d+) passed", tail).group(1)) if "passed" in tail else 0
    failed = int(re.search(r"(\d+) failed", tail).group(1)) if "failed" in tail else 0
    res = {"summary_line": tail, "passed": passed, "failed": failed, "seconds": round(time.time() - t0, 1),
           "files": {"tests/test_engine.py": 0, "tests/test_api.py": 0, "tests/test_sim_parity.py": 0}}
    for f in res["files"]:
        q = subprocess.run([sys.executable if False else str(py), "-m", "pytest", f, "--collect-only", "-q", "-p", "no:cacheprovider"],
                           cwd=ROOT, capture_output=True, text=True)
        res["files"][f] = sum(1 for ln in q.stdout.splitlines() if "::" in ln)
    save("unit_tests", res)
    return res


if __name__ == "__main__":
    only = set(sys.argv[1:])
    steps = {"buffer_population": buffer_population, "buffer_badshare": buffer_badshare, "trust_ablation": trust_ablation,
             "trust_dynamics": trust_dynamics, "seeded_history": seeded_history, "engine_parity": engine_parity,
             "engine_microbench": engine_microbench, "unit_tests": unit_tests}
    for name, fn in steps.items():
        if not only or name in only:
            t = time.time()
            fn()
            print(f"  {name}: {time.time() - t:.1f}s")
