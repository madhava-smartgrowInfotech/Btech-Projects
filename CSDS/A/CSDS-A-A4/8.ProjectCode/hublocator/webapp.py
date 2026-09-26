"""Web interface (Flask). Templates live in this file as Python strings.

Pages
    /            dashboard - data, forecast quality, latest results
    /forecast    Random Forest demand forecast (metrics, importances, next-month forecast)
    /optimize    plan hubs: choose month/parameters, run the matheuristic (or exact MIP), see the map
    /compare     proposed vs traditional methods (+ scalability benchmark)
    /rolling     month-by-month re-optimisation vs a static plan
JSON API
    GET  /api/forecast            POST /api/optimize {n_hubs, capacity_factor, period, ...}
    GET  /api/compare             GET  /api/rolling
"""
from __future__ import annotations

import threading

import numpy as np
from flask import Flask, jsonify, redirect, render_template, request, url_for
from jinja2 import DictLoader

from . import config
from .baselines import load_comparison, run_comparison
from .data import dataset_summary, load_dataset
from .forecast import forecast_for_period, forecast_next_period, load_forecast_metrics, load_forecaster, train_forecaster
from .matheuristic import solve_matheuristic
from .model import HAS_PULP, Instance, evaluate_solution, solve_exact
from .rolling import load_rolling, load_scalability, rolling_reoptimisation, scalability_benchmark
from .viz import bar_chart, line_chart, network_map

BASE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}HubLocator{% endblock %}</title>
{% if refresh %}<meta http-equiv="refresh" content="6">{% endif %}
<style>
:root{--ink:#1b2330;--ink2:#55606f;--line:#dde2e8;--bg:#f2f4f7;--panel:#fff;--blue:#1f5f8b;--blue-bg:#e4eef6;--orange:#c8552b;--green:#2c8c5a;--green-bg:#e1f2e8;--red:#b23a3a;--red-bg:#f7e2e2;--amber:#a2711a;--amber-bg:#f8efd8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.55 "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
header{background:var(--ink);color:#fff}.nav{max-width:1120px;margin:0 auto;padding:13px 20px;display:flex;gap:24px;align-items:center;flex-wrap:wrap}
.brand{color:#fff;text-decoration:none;font-weight:700;font-size:19px}.brand small{display:block;font-weight:400;font-size:12px;opacity:.7}
.nav a.l{color:#c5cfdc;text-decoration:none}.nav a.l.on,.nav a.l:hover{color:#fff;border-bottom:2px solid #fff}
main{max-width:1120px;margin:0 auto;padding:26px 20px 60px}h1{font-size:28px;margin:0 0 6px}h2{font-size:19px;margin:24px 0 10px}
.lead{color:var(--ink2);margin:0 0 20px;max-width:78ch}.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}.stat{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 15px}
.stat b{display:block;font-size:24px}.stat span{color:var(--ink2);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14.5px}th,td{text-align:left;padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12.5px;color:var(--ink2);font-weight:600}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.best td{background:var(--blue-bg);font-weight:600}.tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
.tag.ok{background:var(--green-bg);color:var(--green)}.tag.warn{background:var(--amber-bg);color:var(--amber)}.tag.bad{background:var(--red-bg);color:var(--red)}.tag.info{background:var(--blue-bg);color:var(--blue)}
label{display:block;font-size:13px;font-weight:600;margin:10px 0 4px}input,select{font:inherit;padding:9px 11px;border:1.5px solid var(--line);border-radius:7px;width:100%;background:#fff}
input:focus,select:focus{outline:2px solid var(--blue);outline-offset:1px}.form{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:0 14px}
button,.btn{font:inherit;font-weight:600;padding:10px 18px;border-radius:7px;border:0;cursor:pointer;background:var(--ink);color:#fff;text-decoration:none;display:inline-block}
.btn.sec,button.sec{background:#fff;color:var(--ink);border:1.5px solid var(--line)}.flash{padding:11px 15px;border-radius:8px;margin-bottom:14px;background:var(--blue-bg);color:var(--blue)}
.muted{color:var(--ink2);font-size:13.5px}code{font-family:Consolas,Menlo,monospace;font-size:13.5px;background:#eef1f5;padding:1px 5px;border-radius:4px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:800px){.two{grid-template-columns:1fr}}
.bar{height:8px;background:var(--blue);border-radius:4px}.scroll{overflow-x:auto}svg{max-width:100%;height:auto;display:block}
</style></head><body><header><div class="nav">
<a class="brand" href="{{ url_for('index') }}">HubLocator<small>RF demand forecasting + matheuristic hub location</small></a>
<a class="l {{ 'on' if page=='index' }}" href="{{ url_for('index') }}">Dashboard</a>
<a class="l {{ 'on' if page=='forecast' }}" href="{{ url_for('forecast') }}">Forecast</a>
<a class="l {{ 'on' if page=='optimize' }}" href="{{ url_for('optimize') }}">Plan hubs</a>
<a class="l {{ 'on' if page=='compare' }}" href="{{ url_for('compare') }}">Compare methods</a>
<a class="l {{ 'on' if page=='rolling' }}" href="{{ url_for('rolling') }}">Re-optimise</a>
</div></header><main>{% if msg %}<div class="flash">{{ msg }}</div>{% endif %}{% block body %}{% endblock %}</main>
<footer style="max-width:1120px;margin:0 auto;padding:0 20px 30px;color:var(--ink2);font-size:13px">Batch A4 · CSE (Data Science) · predict-then-optimise framework · solver: {{ 'CBC via PuLP' if has_pulp else 'greedy fallback (install pulp)' }}</footer></body></html>"""

INDEX = r"""{% extends "base.html" %}{% block body %}
<h1>E-commerce hub location, driven by demand forecasts</h1>
<p class="lead">Historical order data from {{ ds.regions }} regions over {{ ds.periods }} months feeds a Random Forest that forecasts next-month regional demand. The forecast becomes the demand input of a capacitated hub-location model that a matheuristic solves in seconds.</p>
<div class="grid">
<div class="stat"><b>{{ ds.regions }}</b><span>demand regions (cities + districts)</span></div>
<div class="stat"><b>{{ ds.periods }}</b><span>months of history ({{ ds.first_period }} to {{ ds.last_period }})</span></div>
<div class="stat"><b>{{ '{:,}'.format(ds.total_orders) }}</b><span>orders in the dataset</span></div>
<div class="stat"><b>{{ fm.random_forest.mape if fm else '-' }}%</b><span>Random Forest forecast MAPE (held-out months)</span></div>
</div>
<div class="panel"><h2 style="margin-top:0">Monthly order volume across the network</h2>{{ chart|safe }}</div>
<div class="two">
<div class="panel"><h2 style="margin-top:0">Pipeline status</h2><table>
<tr><td>1. Historical data</td><td><span class="tag ok">ready</span> <span class="muted">data/demand_history.csv</span></td></tr>
<tr><td>2. Random Forest forecaster</td><td>{% if fm %}<span class="tag ok">trained</span> <span class="muted">{{ fm.trained_at[:16]|replace('T',' ') }}</span>{% else %}<span class="tag warn">not trained</span>{% endif %}</td></tr>
<tr><td>3-4. Hub location matheuristic</td><td><span class="tag ok">available</span> <span class="muted">{{ 'exact sub-problems via CBC' if has_pulp else 'greedy allocation fallback' }}</span></td></tr>
<tr><td>5. Rolling re-optimisation</td><td>{% if ro %}<span class="tag ok">{{ ro.periods|length }} months evaluated</span>{% else %}<span class="tag warn">not run</span>{% endif %}</td></tr>
<tr><td>6. Method comparison</td><td>{% if cmp %}<span class="tag ok">{{ cmp.methods|length }} methods</span>{% else %}<span class="tag warn">not run</span>{% endif %}</td></tr>
</table></div>
<div class="panel"><h2 style="margin-top:0">Largest markets (avg monthly orders)</h2><table>{% for k,v in ds.top_regions.items() %}<tr><td>{{ names[k] }}</td><td class="n">{{ '{:,}'.format(v) }}</td></tr>{% endfor %}</table></div>
</div>
{% if cmp %}<div class="panel"><h2 style="margin-top:0">Latest comparison ({{ cmp.methods.proposed.hub_cities|join(', ') }})</h2>
<table><thead><tr><th>Method</th><th class="n">Operating cost</th><th class="n">vs proposed</th><th class="n">Avg delivery</th><th class="n">Fulfilment</th><th class="n">Reliability</th></tr></thead><tbody>
{% for k,m in cmp.methods.items() %}<tr class="{{ 'best' if k=='proposed' }}"><td>{{ m.label }}</td><td class="n">{{ '{:,.0f}'.format(m.total_cost) }}</td><td class="n">{{ '%+.2f'|format(m.cost_vs_proposed_pct) }}%</td><td class="n">{{ m.avg_delivery_hours }} h</td><td class="n">{{ '%.1f'|format(m.fulfilment_rate*100) }}%</td><td class="n">{{ '%.1f'|format(m.reliability_sla*100) }}%</td></tr>{% endfor %}
</tbody></table></div>{% endif %}
{% endblock %}"""

FORECAST = r"""{% extends "base.html" %}{% block body %}
<h1>Random Forest demand forecast</h1>
<p class="lead">Each region's next-month orders are predicted from lags, rolling averages, seasonality (festival months), promotions and region attributes. The last {{ fm.test_rows // ds.regions if fm else 6 }} months are held out for evaluation; two naive forecasters show what the model adds.</p>
{% if not fm %}<div class="panel">Not trained yet. <form method="post" action="{{ url_for('train') }}" style="display:inline"><button>Train forecaster</button></form></div>{% else %}
<div class="panel"><table><thead><tr><th>Forecaster</th><th class="n">MAE</th><th class="n">RMSE</th><th class="n">MAPE</th><th class="n">R²</th></tr></thead><tbody>
<tr class="best"><td>Random Forest (proposed)</td><td class="n">{{ '{:,.0f}'.format(fm.random_forest.mae) }}</td><td class="n">{{ '{:,.0f}'.format(fm.random_forest.rmse) }}</td><td class="n">{{ fm.random_forest.mape }}%</td><td class="n">{{ fm.random_forest.r2 }}</td></tr>
<tr><td>Last month's value</td><td class="n">{{ '{:,.0f}'.format(fm.baseline_last_value.mae) }}</td><td class="n">{{ '{:,.0f}'.format(fm.baseline_last_value.rmse) }}</td><td class="n">{{ fm.baseline_last_value.mape }}%</td><td class="n">{{ fm.baseline_last_value.r2 }}</td></tr>
<tr><td>3-month moving average</td><td class="n">{{ '{:,.0f}'.format(fm.baseline_moving_avg_3.mae) }}</td><td class="n">{{ '{:,.0f}'.format(fm.baseline_moving_avg_3.rmse) }}</td><td class="n">{{ fm.baseline_moving_avg_3.mape }}%</td><td class="n">{{ fm.baseline_moving_avg_3.r2 }}</td></tr>
</tbody></table><p class="muted" style="margin:10px 0 0">Trained on {{ fm.train_periods }} ({{ fm.train_rows }} rows), tested on {{ fm.test_periods }} ({{ fm.test_rows }} rows), {{ fm.train_seconds }}s. <form method="post" action="{{ url_for('train') }}" style="display:inline"><button class="sec" style="padding:4px 10px">Retrain</button></form></p></div>
<div class="two">
<div class="panel"><h2 style="margin-top:0">Feature importance</h2><table>{% for f in fm.feature_importance[:10] %}<tr><td><code>{{ f.feature }}</code></td><td style="width:45%"><div class="bar" style="width:{{ (f.importance / fm.feature_importance[0].importance*100)|round }}%"></div></td><td class="n">{{ f.importance }}</td></tr>{% endfor %}</table></div>
<div class="panel"><h2 style="margin-top:0">Forecast for {{ nxt.period }} (next month)</h2><p class="muted">Network total: <strong>{{ '{:,}'.format(nxt.total) }}</strong> orders. This vector is the demand input to the hub model.</p>
<div class="scroll" style="max-height:340px;overflow-y:auto"><table><thead><tr><th>Region</th><th class="n">Forecast</th></tr></thead><tbody>{% for r in nxt.rows %}<tr><td>{{ r.city }}</td><td class="n">{{ '{:,}'.format(r.forecast) }}</td></tr>{% endfor %}</tbody></table></div></div>
</div>
<div class="panel"><h2 style="margin-top:0">Back-test: {{ fm.last_period }} actual vs predicted</h2>{{ chart|safe }}
<details><summary>Per-region table</summary><div class="scroll"><table><thead><tr><th>Region</th><th class="n">Actual</th><th class="n">Predicted</th><th class="n">Error</th></tr></thead><tbody>{% for r in fm.last_period_detail %}<tr><td>{{ names[r.region_id] }}</td><td class="n">{{ '{:,}'.format(r.actual) }}</td><td class="n">{{ '{:,}'.format(r.predicted) }}</td><td class="n">{{ r.error_pct }}%</td></tr>{% endfor %}</tbody></table></div></details></div>
{% endif %}{% endblock %}"""

OPTIMIZE = r"""{% extends "base.html" %}{% block body %}
<h1>Plan hub locations</h1>
<p class="lead">Choose the planning month and network parameters. Demand comes from the Random Forest forecast (for a past month, only data before it is used, so the result can be scored against what really happened).</p>
<div class="panel"><form method="post" action="{{ url_for('optimize') }}"><div class="form">
<div><label>Planning month</label><select name="period">{% for p in periods %}<option value="{{ p }}" {{ 'selected' if p==f.period }}>{{ p }}{{ ' (next month)' if loop.first }}</option>{% endfor %}</select></div>
<div><label>Max hubs (p)</label><input type="number" name="n_hubs" min="1" max="20" value="{{ f.n_hubs }}"></div>
<div><label>Capacity factor</label><input type="number" step="0.05" min="1" name="capacity_factor" value="{{ f.capacity_factor }}"></div>
<div><label>Transport rate (₹/order/km)</label><input type="number" step="0.001" name="transport_rate" value="{{ f.transport_rate }}"></div>
<div><label>Fixed hub cost (₹/month)</label><input type="number" step="10000" name="fixed_cost_per_hub" value="{{ f.fixed_cost_per_hub|int }}"></div>
<div><label>Time penalty (₹/order/hour)</label><input type="number" step="0.5" name="time_penalty" value="{{ f.time_penalty }}"></div>
<div><label>Delivery SLA (hours)</label><input type="number" step="1" name="sla_hours" value="{{ f.sla_hours|int }}"></div>
<div><label>SLA constraint</label><select name="sla_hard"><option value="0" {{ 'selected' if not f.sla_hard }}>soft (penalised)</option><option value="1" {{ 'selected' if f.sla_hard }}>hard (forbid late assignments)</option></select></div>
<div><label>Method</label><select name="method"><option value="matheuristic" {{ 'selected' if f.method=='matheuristic' }}>Matheuristic (proposed)</option><option value="exact" {{ 'selected' if f.method=='exact' }}>Exact MIP (traditional)</option></select></div>
<div><label>Time limit (s)</label><input type="number" name="time_limit" min="2" max="300" value="{{ f.time_limit|int }}"></div>
</div><p style="margin:14px 0 0"><button>Optimise</button></p></form></div>
{% if res %}
<div class="grid">
<div class="stat"><b>{{ res.kpi.n_hubs }}</b><span>hubs opened: {{ res.kpi.hub_cities|join(', ') }}</span></div>
<div class="stat"><b>₹{{ '{:,.0f}'.format(res.kpi.total_cost) }}</b><span>monthly operating cost ({{ '{:.2f}'.format(res.kpi.cost_per_order) }} per order)</span></div>
<div class="stat"><b>{{ res.kpi.avg_delivery_hours }} h</b><span>avg delivery time (max {{ res.kpi.max_delivery_hours }} h)</span></div>
<div class="stat"><b>{{ '%.1f'|format(res.kpi.fulfilment_rate*100) }}%</b><span>fulfilment rate{{ ' on realised demand' if res.realized else ' on forecast' }}</span></div>
<div class="stat"><b>{{ '%.1f'|format(res.kpi.reliability_sla*100) }}%</b><span>orders delivered within SLA</span></div>
<div class="stat"><b>{{ res.sol.seconds }} s</b><span>{{ res.sol.status }}{% if res.sol.subproblems_solved %} · {{ res.sol.subproblems_solved }} sub-MIPs · kernel {{ res.sol.kernel_status }}{% endif %}</span></div>
</div>
<div class="panel"><h2 style="margin-top:0">Network map — squares are hubs, circles are regions sized by demand</h2>{{ res.map|safe }}</div>
<div class="two">
<div class="panel"><h2 style="margin-top:0">Hub utilisation{{ ' (realised demand)' if res.realized }}</h2><table><thead><tr><th>Hub</th><th class="n">Load / capacity</th><th></th></tr></thead><tbody>
{% for h,u in res.kpi.utilisation.items() %}<tr><td>{{ names_idx[h|int] }}</td><td class="n">{{ '%.0f'|format(u*100) }}%</td><td><span class="tag {{ 'bad' if u>1 else ('warn' if u>0.9 else 'ok') }}">{{ 'overloaded' if u>1 else ('tight' if u>0.9 else 'ok') }}</span></td></tr>{% endfor %}
</tbody></table><p class="muted">Cost split: fixed ₹{{ '{:,.0f}'.format(res.kpi.fixed_cost) }} · transport ₹{{ '{:,.0f}'.format(res.kpi.transport_cost) }} · time ₹{{ '{:,.0f}'.format(res.kpi.time_cost) }}</p></div>
<div class="panel"><h2 style="margin-top:0">Search log</h2><table><thead><tr><th>Phase</th><th class="n">Objective</th><th class="n">t (s)</th></tr></thead><tbody>
{% for l in res.sol.log or [] %}<tr><td>{{ l.phase }}</td><td class="n">{{ '{:,.0f}'.format(l.objective) }}</td><td class="n">{{ l.t }}</td></tr>{% else %}<tr><td colspan="3" class="muted">Exact MIP: {{ res.sol.status }}</td></tr>{% endfor %}</tbody></table></div>
</div>
<div class="panel"><details><summary>Region allocation ({{ res.kpi.assignment|length }} regions)</summary><div class="scroll"><table><thead><tr><th>Region</th><th>Served by</th><th class="n">Demand</th><th class="n">Distance</th><th class="n">Delivery</th></tr></thead><tbody>
{% for a in res.kpi.assignment %}<tr><td>{{ a.region }}</td><td>{{ a.hub }}</td><td class="n">{{ '{:,}'.format(a.demand) }}</td><td class="n">{{ a.distance_km }} km</td><td class="n">{{ a.hours }} h</td></tr>{% endfor %}</tbody></table></div></details></div>
{% endif %}{% endblock %}"""

COMPARE = r"""{% extends "base.html" %}{% block body %}
<h1>Proposed vs traditional hub location methods</h1>
<p class="lead">All methods plan on the same month and are scored on the demand that actually occurred. Traditional approaches are the full exact MIP (time-limited), a greedy heuristic, k-means clustering, a managerial "largest markets" rule and a fixed historical-average demand plan.</p>
<div class="panel"><form method="post" action="{{ url_for('compare') }}" style="display:flex;gap:12px;align-items:end;flex-wrap:wrap">
<div><label>Evaluation month</label><select name="period">{% for p in periods %}<option value="{{ p }}" {{ 'selected' if p==sel }}>{{ p }}</option>{% endfor %}</select></div>
<div><label>Exact MIP time limit (s)</label><input type="number" name="exact_limit" value="30" min="5" max="300"></div>
<div><button {{ 'disabled' if running }}>{{ 'Running…' if running else 'Run comparison' }}</button></div>
<div><button name="scal" value="1" class="sec" {{ 'disabled' if running }}>Run scalability benchmark</button></div>
</form>{% if running %}<p class="muted">A job is running in the background — this page refreshes automatically.</p>{% endif %}</div>
{% if cmp %}
<div class="panel"><p class="muted">Planned on forecast total {{ '{:,}'.format(cmp.forecast_total_demand) }} orders; realised {{ '{:,}'.format(cmp.realized_total_demand) }}. p = {{ cmp.params.n_hubs }}, capacity factor {{ cmp.params.capacity_factor }}, SLA {{ cmp.params.sla_hours|int }} h.</p>
<div class="scroll"><table><thead><tr><th>Method</th><th>Hubs</th><th class="n">Operating cost (₹)</th><th class="n">vs proposed</th><th class="n">Avg delivery</th><th class="n">Fulfilment</th><th class="n">Reliability (SLA)</th><th class="n">Overloaded hubs</th><th class="n">Solve time</th></tr></thead><tbody>
{% for k,m in cmp.methods.items() %}<tr class="{{ 'best' if k=='proposed' }}"><td>{{ m.label }}</td><td class="muted">{{ m.hub_cities|join(', ') }}</td><td class="n">{{ '{:,.0f}'.format(m.total_cost) }}</td><td class="n">{{ '%+.2f'|format(m.cost_vs_proposed_pct) }}%</td><td class="n">{{ m.avg_delivery_hours }} h</td><td class="n">{{ '%.1f'|format(m.fulfilment_rate*100) }}%</td><td class="n">{{ '%.1f'|format(m.reliability_sla*100) }}%</td><td class="n">{{ m.overloaded_hubs }}</td><td class="n">{{ m.seconds }} s</td></tr>{% endfor %}
</tbody></table></div></div>
<div class="two"><div class="panel"><h2 style="margin-top:0">Operating cost</h2>{{ chart_cost|safe }}</div><div class="panel"><h2 style="margin-top:0">Fulfilment rate</h2>{{ chart_fulfil|safe }}</div></div>
{% endif %}
{% if scal %}<div class="panel"><h2 style="margin-top:0">Scalability: exact MIP vs matheuristic</h2><p class="muted">The network is inflated by splitting every region into nearby demand points. The exact MIP is stopped at its time limit; the matheuristic keeps a small gap while staying fast.</p>
<table><thead><tr><th class="n">Demand points</th><th class="n">Binary variables</th><th class="n">Matheuristic time</th><th class="n">Exact MIP time</th><th>Exact status</th><th class="n">Matheuristic gap</th></tr></thead><tbody>
{% for s in scal %}<tr><td class="n">{{ s.nodes }}</td><td class="n">{{ '{:,}'.format(s.binary_vars) }}</td><td class="n">{{ s.matheuristic_seconds }} s</td><td class="n">{{ s.exact_seconds }} s</td><td>{{ s.exact_status }}</td><td class="n">{{ s.matheuristic_gap_pct if s.matheuristic_gap_pct is defined else '-' }}%</td></tr>{% endfor %}
</tbody></table></div>{% endif %}
{% endblock %}"""

ROLLING = r"""{% extends "base.html" %}{% block body %}
<h1>Re-optimising as demand changes</h1>
<p class="lead">Each month the forecaster is re-run with the data available at that time and the matheuristic re-plans the network; the result is scored against realised demand. A static plan, fixed once on the historical average (the traditional assumption), is scored on the same months.</p>
<div class="panel"><form method="post" action="{{ url_for('rolling') }}" style="display:flex;gap:12px;align-items:end;flex-wrap:wrap">
<div><label>Months to simulate</label><input type="number" name="n_months" value="6" min="2" max="12"></div>
<div><button {{ 'disabled' if running }}>{{ 'Running…' if running else 'Run rolling horizon' }}</button></div></form>
{% if running %}<p class="muted">Running in the background — this page refreshes automatically.</p>{% endif %}</div>
{% if ro %}
<div class="grid">
<div class="stat"><b>{{ '%.1f'|format(ro.adaptive_avg.fulfilment_rate*100) }}%</b><span>avg fulfilment — adaptive (vs {{ '%.1f'|format(ro.static_avg.fulfilment_rate*100) }}% static)</span></div>
<div class="stat"><b>{{ '%.1f'|format(ro.adaptive_avg.reliability_sla*100) }}%</b><span>avg SLA reliability — adaptive (vs {{ '%.1f'|format(ro.static_avg.reliability_sla*100) }}% static)</span></div>
<div class="stat"><b>{{ '%+.1f'|format((ro.adaptive_avg.total_cost - ro.static_avg.total_cost)/ro.static_avg.total_cost*100) }}%</b><span>avg operating cost vs static plan</span></div>
<div class="stat"><b>{{ ro.hub_changes }}</b><span>hub openings across the horizon (static hubs: {{ ro.static_hubs|join(', ') }})</span></div>
</div>
<div class="two"><div class="panel"><h2 style="margin-top:0">Fulfilment rate by month</h2>{{ chart_f|safe }}</div><div class="panel"><h2 style="margin-top:0">Realised demand vs forecast</h2>{{ chart_d|safe }}</div></div>
<div class="panel"><div class="scroll"><table><thead><tr><th>Month</th><th class="n">Forecast</th><th class="n">Realised</th><th class="n">Error</th><th>Hubs</th><th>Changes</th><th class="n">Adaptive cost</th><th class="n">Adaptive fulfil</th><th class="n">Static cost</th><th class="n">Static fulfil</th></tr></thead><tbody>
{% for t in ro.timeline %}<tr><td>{{ t.period }}</td><td class="n">{{ '{:,}'.format(t.forecast_total) }}</td><td class="n">{{ '{:,}'.format(t.realized_total) }}</td><td class="n">{{ t.forecast_error_pct }}%</td><td class="muted">{{ t.hub_cities|join(', ') }}</td><td>{% for c in t.opened %}<span class="tag ok">+{{ c }}</span> {% endfor %}{% for c in t.closed %}<span class="tag bad">−{{ c }}</span> {% endfor %}</td><td class="n">{{ '{:,.0f}'.format(t.adaptive.total_cost) }}</td><td class="n">{{ '%.1f'|format(t.adaptive.fulfilment_rate*100) }}%</td><td class="n">{{ '{:,.0f}'.format(t.static.total_cost) }}</td><td class="n">{{ '%.1f'|format(t.static.fulfilment_rate*100) }}%</td></tr>{% endfor %}
</tbody></table></div></div>
{% endif %}{% endblock %}"""


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_loader = DictLoader({"base.html": BASE, "index.html": INDEX, "forecast.html": FORECAST,
                                   "optimize.html": OPTIMIZE, "compare.html": COMPARE, "rolling.html": ROLLING})
    regions, demand = load_dataset()
    names = dict(zip(regions.region_id, regions.city))
    names_idx = regions.city.tolist()
    jobs = {"compare": False, "rolling": False}
    periods_hist = sorted(demand.period.unique())
    next_period = str(np.datetime64(periods_hist[-1] + "-01", "M") + 1)

    def ctx(page, **kw):
        return dict(page=page, has_pulp=HAS_PULP, names=names, names_idx=names_idx, **kw)

    def demand_vectors(period: str):
        """(forecast, realized or None, hist_avg) for a planning period."""
        if period == next_period:
            fc = forecast_next_period(regions, demand)
            real = None
            hist = demand.groupby("region_id")["orders"].mean()
        else:
            fc = forecast_for_period(regions, demand, period)
            real = demand[demand.period == period].set_index("region_id").loc[regions.region_id, "orders"].to_numpy(float)
            hist = demand[demand.period < period].groupby("region_id")["orders"].mean()
        fc = fc.set_index("region_id").loc[regions.region_id, "forecast"].to_numpy(float)
        return fc, real, hist.loc[regions.region_id].to_numpy(float)

    # ---------------------------------------------------------------- pages
    @app.route("/")
    def index():
        ds = dataset_summary(regions, demand)
        chart = line_chart(list(ds["monthly_total"]), {"orders": list(ds["monthly_total"].values())})
        return render_template("index.html", **ctx("index", ds=ds, fm=load_forecast_metrics(), chart=chart,
                                                    cmp=load_comparison(), ro=load_rolling(), msg=request.args.get("msg")))

    @app.route("/forecast")
    def forecast():
        fm = load_forecast_metrics()
        chart, nxt = "", None
        if fm:
            det = fm["last_period_detail"]
            chart = line_chart([names[r["region_id"]] for r in det], {"actual": [r["actual"] for r in det],
                                                                        "predicted": [r["predicted"] for r in det]})
            f = forecast_next_period(regions, demand)
            nxt = {"period": f.period[0], "total": int(f.forecast.sum()),
                   "rows": f.sort_values("forecast", ascending=False).to_dict("records")}
        return render_template("forecast.html", **ctx("forecast", fm=fm, chart=chart, nxt=nxt,
                                                       ds=dataset_summary(regions, demand), msg=request.args.get("msg")))

    @app.post("/train")
    def train():
        train_forecaster(regions, demand, verbose=False)
        return redirect(url_for("forecast", msg="Forecaster retrained."))

    @app.route("/optimize", methods=["GET", "POST"])
    def optimize():
        f = {**{k: v for k, v in config.DEFAULTS.items()}, "period": next_period, "method": "matheuristic"}
        res = None
        if request.method == "POST":
            for k in ("n_hubs", "capacity_factor", "transport_rate", "fixed_cost_per_hub", "time_penalty",
                      "sla_hours", "time_limit"):
                f[k] = float(request.form.get(k, f[k]))
            f["n_hubs"], f["time_limit"] = int(f["n_hubs"]), int(f["time_limit"])
            f["sla_hard"] = request.form.get("sla_hard") == "1"
            f["period"], f["method"] = request.form.get("period", next_period), request.form.get("method", "matheuristic")
            res = _plan(f)
        periods = [next_period] + periods_hist[::-1][:18]
        return render_template("optimize.html", **ctx("optimize", f=f, res=res, periods=periods))

    def _plan(f: dict) -> dict:
        fc, real, _ = demand_vectors(f["period"])
        params = {k: f[k] for k in config.DEFAULTS}
        inst = Instance.from_forecast(regions, fc, **params)
        sol = solve_exact(inst, time_limit=f["time_limit"]) if (f["method"] == "exact" and HAS_PULP) else solve_matheuristic(inst)
        if sol.get("assign") is None:
            return {"error": "No feasible solution (try more hubs, a larger capacity factor or a soft SLA)."}
        kpi = evaluate_solution(inst, sol["hubs"], sol["assign"], real)
        sol_public = {k: v for k, v in sol.items() if k != "assign"}
        sol_public["hubs"] = [int(h) for h in sol["hubs"]]
        return {"sol": sol_public, "kpi": kpi, "realized": real is not None,
                "map": network_map(regions, sol["hubs"], sol["assign"], real if real is not None else fc)}

    @app.route("/compare", methods=["GET", "POST"])
    def compare():
        sel = request.form.get("period") or (periods_hist[-3] if len(periods_hist) > 3 else periods_hist[-1])
        if request.method == "POST" and not jobs["compare"]:
            limit = float(request.form.get("exact_limit", 30))

            def job():
                try:
                    if request_form.get("scal"):
                        fc, _, _ = demand_vectors(sel)
                        scalability_benchmark(regions, fc, factors=(1, 2, 3), exact_time_limit=limit, verbose=False)
                    else:
                        fc, real, hist = demand_vectors(sel)
                        run_comparison(regions, fc, real, hist, exact_time_limit=limit, verbose=False)
                finally:
                    jobs["compare"] = False
            request_form = dict(request.form)
            jobs["compare"] = True
            threading.Thread(target=job, daemon=True).start()
            return redirect(url_for("compare"))
        cmp = load_comparison()
        cc = cf = ""
        if cmp:
            labels = [m["label"].replace(" (proposed)", "") for m in cmp["methods"].values()]
            cc = bar_chart(labels, [m["total_cost"] for m in cmp["methods"].values()], highlight=0)
            cf = bar_chart(labels, [m["fulfilment_rate"] * 100 for m in cmp["methods"].values()], fmt=lambda v: f"{v:.1f}%", highlight=0)
        return render_template("compare.html", **ctx("compare", cmp=cmp, scal=load_scalability(), periods=periods_hist[::-1][:18],
                                                      sel=sel, running=jobs["compare"], refresh=jobs["compare"], chart_cost=cc, chart_fulfil=cf))

    @app.route("/rolling", methods=["GET", "POST"])
    def rolling():
        if request.method == "POST" and not jobs["rolling"]:
            n = int(request.form.get("n_months", 6))

            def job():
                try:
                    rolling_reoptimisation(regions, demand, n_months=n, verbose=False)
                finally:
                    jobs["rolling"] = False
            jobs["rolling"] = True
            threading.Thread(target=job, daemon=True).start()
            return redirect(url_for("rolling"))
        ro = load_rolling()
        cf = cd = ""
        if ro:
            t = ro["timeline"]
            labels = [x["period"] for x in t]
            cf = line_chart(labels, {"adaptive": [x["adaptive"]["fulfilment_rate"] * 100 for x in t],
                                     "static": [x["static"]["fulfilment_rate"] * 100 for x in t]}, y_label="%")
            cd = line_chart(labels, {"realised": [x["realized_total"] for x in t], "forecast": [x["forecast_total"] for x in t]})
        return render_template("rolling.html", **ctx("rolling", ro=ro, running=jobs["rolling"], refresh=jobs["rolling"],
                                                      chart_f=cf, chart_d=cd))

    # ---------------------------------------------------------------- API
    @app.get("/api/forecast")
    def api_forecast():
        f = forecast_next_period(regions, demand)
        return jsonify({"period": f.period[0], "total": int(f.forecast.sum()), "regions": f.to_dict("records"),
                        "metrics": load_forecast_metrics().get("random_forest")})

    @app.post("/api/optimize")
    def api_optimize():
        body = request.get_json(silent=True) or {}
        f = {**config.DEFAULTS, "period": next_period, "method": "matheuristic", **body}
        try:
            res = _plan(f)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": str(exc)}), 400
        res.pop("map", None)
        return jsonify(res)

    @app.get("/api/compare")
    def api_compare():
        return jsonify(load_comparison())

    @app.get("/api/rolling")
    def api_rolling():
        return jsonify(load_rolling())

    return app
