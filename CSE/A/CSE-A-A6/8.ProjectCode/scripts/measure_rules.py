"""Characterise the explainable rule engine (core.RiskEngine) on SCRIPTED measurement streams.

These streams are generated, not recorded from people: they show how the rules behave (how long a closure must last
before a warning, what blink patterns can false-alarm, what the parameters trade off). They are not evidence of
accuracy on real riders and say nothing about alcohol. Every stream, seed and parameter is in this file.

Run:  .venv\\Scripts\\python.exe scripts\\measure_rules.py      -> experiments/rule_engine/{metrics.json,*.png}
"""
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import Observation, RiskEngine, Settings, WARNING, NORMAL, UNKNOWN  # noqa: E402

OUT = ROOT / 'experiments' / 'rule_engine'
OPEN, CLOSED = 0.30, 0.12


def stream(rng, seconds, fps, blink_per_min=17, blink_dur=(0.1, 0.4), noise=0.012, closures=(), roll=0.0,
           slow_blink_p=0.0, slow_dur=(0.8, 1.3)):
    """Yield (t, ear, roll). `closures` = [(start_s, duration_s)] of deliberate eye closures."""
    n = int(seconds * fps)
    t = np.arange(n) / fps
    ear = rng.normal(OPEN, noise, n)
    blinks = int(seconds * blink_per_min / 60)
    for start in rng.uniform(1, seconds - 2, blinks):
        d = rng.uniform(*slow_dur) if rng.random() < slow_blink_p else rng.uniform(*blink_dur)
        ear[(t >= start) & (t < start + d)] = rng.normal(CLOSED, 0.01)
    for s, d in closures:
        ear[(t >= s) & (t < s + d)] = rng.normal(CLOSED, 0.01)
    return t, np.clip(ear, 0.02, 0.6), np.full(n, roll)


def run(settings, t, ear, roll):
    engine = RiskEngine(settings)
    out = []
    for a, b, c in zip(t, ear, roll):
        out.append(engine.update(Observation(float(a), float(b), float(c), 'Good')))
    return out


def first_warning(decisions, t, after=0.0):
    for d, ti in zip(decisions, t):
        if ti >= after and d.state == WARNING:
            return ti
    return None


def exp_latency():
    """Warning latency vs closure duration at several frame rates (closure begins at t = 6 s)."""
    rows = []
    for fps in (10, 15, 30):
        for dur in (0.5, 1.0, 1.5, 2.0, 2.4, 2.6, 3.0, 4.0, 6.0):
            lat, fired = [], 0
            for seed in range(30):
                rng = np.random.default_rng(seed)
                t, ear, roll = stream(rng, 16, fps, blink_per_min=0, closures=[(6.0, dur)])
                d = run(Settings(), t, ear, roll)
                w = first_warning(d, t, 6.0)
                if w is not None:
                    fired += 1
                    lat.append(w - 6.0)
            rows.append({'fps': fps, 'closure_s': dur, 'runs': 30, 'warned': fired,
                         'latency_mean_s': float(np.mean(lat)) if lat else None,
                         'latency_min_s': float(np.min(lat)) if lat else None,
                         'latency_max_s': float(np.max(lat)) if lat else None})
    return rows


def exp_false_alarm(sessions=300, seconds=180, fps=15):
    """Normal-looking blink streams: how often does the default rule set warn?"""
    cases = {
        'normal blinks 17/min (0.1-0.4 s)': dict(blink_per_min=17, blink_dur=(0.1, 0.4)),
        'frequent blinks 35/min (0.1-0.4 s)': dict(blink_per_min=35, blink_dur=(0.1, 0.4)),
        'noisy EAR (sd 0.04), blinks 17/min': dict(blink_per_min=17, noise=0.04),
        '5% slow blinks (0.8-1.3 s), 17/min': dict(blink_per_min=17, slow_blink_p=0.05),
        '20% slow blinks (0.8-1.3 s), 17/min': dict(blink_per_min=17, slow_blink_p=0.20),
    }
    rows = []
    for name, kw in cases.items():
        warned_sessions, warning_frames, total_frames, alerts = 0, 0, 0, 0
        for seed in range(sessions):
            rng = np.random.default_rng(1000 + seed)
            t, ear, roll = stream(rng, seconds, fps, **kw)
            d = run(Settings(), t, ear, roll)
            states = [x.state for x in d]
            warned_sessions += any(s == WARNING for s in states)
            warning_frames += sum(s == WARNING for s in states)
            total_frames += len(states)
            alerts += sum(x.alert for x in d)
        hours = sessions * seconds / 3600
        rows.append({'case': name, 'sessions': sessions, 'session_s': seconds, 'fps': fps,
                     'sessions_with_warning': warned_sessions,
                     'session_false_warning_rate': warned_sessions / sessions,
                     'alerts_per_hour': alerts / hours, 'warning_time_fraction': warning_frames / total_frames})
    return rows


def exp_sweep(runs=60):
    """closure_seconds x persistence_seconds: detection of a 3 s closure vs alerts/hour on blink streams."""
    rows = []
    for closure in (1.0, 1.5, 2.0, 3.0):
        for persist in (0.5, 1.0, 2.0):
            s = Settings(closure_seconds=closure, persistence_seconds=persist)
            hit = 0
            for seed in range(runs):
                rng = np.random.default_rng(seed)
                t, ear, roll = stream(rng, 14, 15, blink_per_min=0, closures=[(6.0, 3.0)])
                hit += first_warning(run(s, t, ear, roll), t, 6.0) is not None
            alerts, secs = 0, 0
            for seed in range(runs):
                rng = np.random.default_rng(5000 + seed)
                t, ear, roll = stream(rng, 180, 15, blink_per_min=17, slow_blink_p=0.10)
                alerts += sum(x.alert for x in run(s, t, ear, roll))
                secs += 180
            rows.append({'closure_seconds': closure, 'persistence_seconds': persist,
                         'detect_3s_closure_rate': hit / runs,
                         'alerts_per_hour_with_10pct_slow_blinks': alerts / (secs / 3600)})
    return rows


def exp_other_rules():
    out = {}
    # closed-fraction rule: repeated 0.9 s closures every 1.5 s (60 % closed), never one long closure
    rng = np.random.default_rng(1)
    t = np.arange(0, 30, 1 / 15)
    ear = rng.normal(OPEN, 0.012, len(t))
    for s in np.arange(5, 30, 1.5):
        ear[(t >= s) & (t < s + 0.9)] = CLOSED
    d = run(Settings(), t, ear, np.zeros(len(t)))
    w = first_warning(d, t, 5.0)
    out['closed_fraction_rule'] = {'pattern': '0.9 s closures every 1.5 s from t=5 s (60 % closed)',
                                   'first_warning_after_onset_s': None if w is None else w - 5.0,
                                   'reason_at_warning': next((x.reason for x in d if x.state == WARNING), None)}
    # head tilt rule: roll 30 deg with EAR just under threshold
    t = np.arange(0, 14, 1 / 15)
    ear = np.where(t >= 6, 0.19, 0.30)
    roll = np.where(t >= 6, 30.0, 0.0)
    d = run(Settings(), t, ear, roll)
    w = first_warning(d, t, 6.0)
    out['tilt_rule'] = {'pattern': 'roll 30 deg with EAR 0.19 from t=6 s',
                        'first_warning_after_onset_s': None if w is None else w - 6.0}
    # tilt alone must not warn
    d = run(Settings(), t, np.full(len(t), 0.30), np.where(t >= 6, 30.0, 0.0))
    out['tilt_alone_warns'] = any(x.state == WARNING for x in d)
    # warm-up and recovery
    t = np.arange(0, 6, 1 / 15)
    d = run(Settings(), t, np.full(len(t), OPEN), np.zeros(len(t)))
    out['warmup_first_normal_s'] = next(float(ti) for x, ti in zip(d, t) if x.state == NORMAL)
    e = RiskEngine(Settings())
    last = None
    for ti in np.arange(0, 3, 1 / 15):
        last = e.update(Observation(float(ti), OPEN, 0, 'Good'))
    e.update(Observation(3.0, 0, 0, 'No face'))
    after = [e.update(Observation(3.0 + (i + 1) / 15, OPEN, 0, 'Good')).state for i in range(45)]
    out['recovery_after_signal_loss_first_normal_s'] = next((i + 1) / 15 for i, s in enumerate(after) if s == NORMAL)
    return out


def exp_cost():
    e = RiskEngine(Settings())
    n = 200000
    start = time.perf_counter()
    for i in range(n):
        e.update(Observation(i / 15, OPEN if (i // 20) % 5 else CLOSED, 1.0, 'Good'))
    per = (time.perf_counter() - start) / n * 1e6
    return {'updates': n, 'microseconds_per_update': per}


def charts(latency, sweep):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    for fps, c in ((10, '#e76f51'), (15, '#2a9d8f'), (30, '#264653')):
        xs = [r['closure_s'] for r in latency if r['fps'] == fps]
        ys = [100 * r['warned'] / r['runs'] for r in latency if r['fps'] == fps]
        ax.plot(xs, ys, marker='o', ms=3, label=f'{fps} frames/s', color=c)
    ax.axvline(2.5, color='grey', ls=':')
    ax.set(xlabel='Duration of continuous eye closure (s)', ylabel='Runs that warned (%)',
           title='Scripted closures: warning vs closure length (defaults)')
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / 'closure_vs_warning.png'); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.8), dpi=150)
    for persist, c in ((0.5, '#e76f51'), (1.0, '#2a9d8f'), (2.0, '#264653')):
        rows = [r for r in sweep if r['persistence_seconds'] == persist]
        ax.plot([r['closure_seconds'] for r in rows], [r['alerts_per_hour_with_10pct_slow_blinks'] for r in rows],
                marker='o', ms=3, label=f'persistence {persist} s', color=c)
    ax.set(xlabel='closure_seconds setting', ylabel='Alerts per hour (scripted blink streams)',
           title='Parameter trade-off: sensitivity to slow blinks')
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / 'parameter_tradeoff.png'); plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    latency, false_alarm, sweep = exp_latency(), exp_false_alarm(), exp_sweep()
    result = {'note': 'Scripted streams (seeded generators in scripts/measure_rules.py), not recordings of people.',
              'defaults': {k: v for k, v in Settings().__dict__.items()},
              'closure_latency': latency, 'false_alarm_on_blink_streams': false_alarm,
              'parameter_sweep': sweep, 'other_rules': exp_other_rules(), 'engine_cost': exp_cost()}
    (OUT / 'metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    charts(latency, sweep)
    print(json.dumps({k: v for k, v in result.items() if k not in ('closure_latency', 'parameter_sweep')}, indent=1))
    print(json.dumps(latency[:9], indent=0))


if __name__ == '__main__':
    main()
