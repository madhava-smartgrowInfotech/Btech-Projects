"""Chapter 7: System testing. Every number comes from facts.py / docs/REPORT_FACTS.md."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n

T = F.TESTS

TEST_FILES = [
    ["`test_safety.py`", "22", "Shield outcomes and the audit trail: approval, projection that keeps the original request, battery limits, line overload, under- and over-voltage, "
     "limits read from configuration, a failed power flow blocks the action, a pre-existing violation does not block a relieving action, schema rejection, "
     "a 1,000 kW export, unknown agent or target, determinism, import isolation, hash-chain tamper evidence"],
    ["`test_agents.py`", "12", "Structured context, reproducible mock provider, labelled fallback after a failure, malformed output, time-out or unconfigured API provider, "
     "schema validation of API output, the EV agent defers when the vehicle is away, an unsafe proposal never equals the executed action, explanations without chain-of-thought"],
    ["`test_simulation.py`", "11", "Seven scenarios, seeded profiles, zero violations caused with the shield, violations caused without it in congestion, "
     "unsafe scenario intervenes and logs the original request, reproducible runs, tamper detection on a real run, dry run without side effects, conflict detection, a real experiment"],
    ["`test_grid.py`", "6", "Network structure, power-flow convergence and balance, a trial leaves committed state untouched, battery state-of-charge integration, line overload, topology"],
    ["`test_api.py`", "4", "Health, grid state, topology; scenario run and safety events with a valid chain; step, reset and dry run (unknown field gives 422); WebSocket event stream"],
]


def blocks():
    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Testing Strategy"),
        P("SafeGrid-AI has two kinds of risk: ordinary software risk (a wrong response shape, a screen that fails on a narrow window) and a risk specific to the project, "
          "that a proposal which should have been stopped reaches the grid or that the audit record cannot be trusted. The strategy has four layers, and the second carries the most weight."),
        N("**Unit tests** (pytest) check each backend module in isolation, above all the shield, with hand-built nodes and limits so that the expected outcome can be written down in advance.",
          "**Scenario tests** run the whole engine through the seven scenarios and assert the property the project exists to deliver: executed actions never create or worsen a violation.",
          "**Integration and smoke tests** exercise the HTTP and WebSocket interface of a running server (`scripts/smoke_test.py`, 20 checks).",
          "**Browser walk-through** drives every screen of the React console in Chromium with Playwright at three widths and in both themes, watching the console for errors."),
        P(f"The measured outcome (2026-10-18) is **{T['passed']} of {T['total']} test functions passing, {T['failed']} failing and {T['hung']} hanging**. "
          "The failures and the hang are described in Section 7.2: they are defects of the test code, not of the shield, but they are defects. "
          "The environments were Python 3.11.9 (pytest 9.1.1, pandapower 3.5.6, FastAPI 0.143.3, pydantic 2.14.1) and Chromium driven by Playwright 1.44.0."),
        H2("7.2 Unit Testing"),
        P(f"The backend has {T['total']} test functions in five files (table below). The suite takes about {T['seconds']} seconds with the hanging WebSocket test excluded, mostly in power-flow calculations."),
        TAB("Backend test files and what they cover", ["File", "Tests", "Coverage"], TEST_FILES, widths=[1.3, 0.5, 4.5], size=9.5, align=["l", "c", "l"]),
        H3("Design of the shield tests"),
        P("The shield tests build a single node with chosen load, solar output and battery state, a configuration with chosen limits and a stand-in power-flow function; each test states one expectation. "
          "A 9 kW export on a node whose export limit is 5 kW must be projected, report `NODE_EXPORT_LIMIT` and give a safe power of 5.0 kW within 0.001 kW. "
          "A 1,000 kW export must be stopped with the original value kept in the decision record. An export request on a node that can only import must be rejected, because no scaling turns an import into an export. "
          "Two further tests protect the interpretation of the results: `test_preexisting_violation_does_not_block_a_relieving_action` (a grid already outside its limits does not stop an action that improves it) "
          "and `test_shield_is_deterministic` (the same request twice gives identical decisions apart from the time stamp)."),
        H3("Failing and hanging tests"),
        P("Two tests fail and one hangs. They are reported here exactly as measured."),
        B("**`test_grid.py::test_power_flow_converges_and_balances`** fails: the external-grid power is **10.995 kW** where the test expects 10.0 kW within 0.5 kW. "
          "The power flow converges; the cause of the difference was not investigated, and the tolerance was probably chosen for an older pandapower release.",
          "**`test_grid.py::test_trial_does_not_change_committed_state`** fails: the second trial gives **-3.12314 kW** where the test expects -3.123 kW within 1e-6. "
          "The values differ by about 0.00014 kW; a related property (a dry run does not change engine state) is covered by a passing test in `test_simulation.py`.",
          "**`test_api.py::test_websocket_receives_events`** hangs under the installed Starlette test client and was excluded with `--deselect`. The WebSocket endpoint itself works: the dashboard receives live events from it."),
        P("The backend was not edited for this documentation task, so these defects remain (see Chapters 8 and 9). The numeric tests need wider tolerances or a value computed in the same test; "
          "the hanging test needs an asynchronous test client."),
        H2("7.3 Integration Testing"),
        P("`scripts/smoke_test.py` uses only the Python standard library and talks to a running backend (and the frontend proxy when Vite is up). All twenty checks passed (**20 of 20**):"),
        N("health, seven scenarios, topology; reset to the unsafe-action scenario at step 0 and three consecutive steps;",
          "grid state with converged power-flow totals; three agents, each with a latest decision, history and explanation;",
          "a dry run of an absurd 1,000 kW export is not approved and nothing is applied; metrics; a valid safety-log chain;",
          "constraints (0.95 pu lower limit, node limits); a scenario run to completion with no violation caused by executed actions; event log, stored runs, a 404 for an unknown agent, and the frontend proxy."),
        P("The script is end-to-end, not a mock: it starts from a reset engine, so it also shows that reset, step, metrics and persistence cooperate."),
        H2("7.4 Functional and System Testing"),
        H3("Scenario runs"),
        P("Each of the seven scenarios was run to completion through `POST /api/scenarios/{id}/run`. The `normal` scenario (32 steps, 96 proposals) completed in 10.68 s with 10 shield interventions, "
          "and `unsafe_ai_action` (12 steps, 36 proposals) in 2.12 s with 12 interventions. In the second, the injected faults appear in the log where the scenario places them: "
          "a 1,000 kW export in steps 1-3, a 900 kW import in steps 2-4, a 50 kW EV discharge in step 3, a 100 kW curtailment request in step 5 and a malformed output in step 6, "
          "which became a labelled `fallback` decision (reason `LLMOutputError`) and was still passed through the shield."),
        H3("Strategy comparison"),
        P(f"The comparison experiment (Chapter 8) is itself a functional test of the whole stack: {F.N_RUNS} complete simulations through the engine that serves the dashboard, "
          "with a valid hash chain in every shielded run (21 of 21)."),
        H3("Browser walk-through"),
        P("Every screen was walked in Chromium through the real API: sign-in with a wrong password and with the demo account; run controls; dashboard; grid view; agent monitor; the safety shield with a dry run, an event dialog and the status filter; power flow; scenarios with a run and a comparison; explainability; sign-out and the route guard. "
          "The walk was repeated at **360, 768 and 1440 px** in **light and dark** themes: no console errors, no failed requests, no 4xx or 5xx responses, no unhandled rejections and no horizontal scrolling. "
          "At narrow widths the sidebar becomes a drawer, Escape closes drawers and dialogs, the skip link receives focus first, and the theme survives a reload; reduced-motion users get a static picture instead of the three-dimensional landing scene. "
          "`npm run build` passes, with the landing page, sign-in page and each console page as separate chunks."),
        H2("7.5 Security Testing"),
        P("The system is a single-user research prototype with no account system behind the API, so this section tests what the design claims, which is narrower than a security review: that a model cannot reach the grid except through a validated, logged path."),
        B("**Closed schema.** `EnergyAction` forbids extra fields, allows seven action types, caps power at 1,000,000 kW, rejects negative and non-finite values and restricts reason codes to `[A-Z0-9_]{1,48}`. "
          "`test_malformed_actions_fail_schema_validation` tries seven bad variants (negative power, `NaN`, the action `shutdown_grid`, confidence 1.7, zero duration, the reason code `drop table; --`, an extra field `run_code`); every one is refused, and the HTTP interface returns 422 for an extra field.",
          "**Independence of the shield.** `test_shield_does_not_import_llm_or_agents` imports the shield in a fresh interpreter and fails if any `app.llm`, `app.agents`, `app.simulation` or `app.grid` module is loaded as a side effect.",
          "**No chain-of-thought.** `test_explanation_is_structured_and_has_no_chain_of_thought` requires the decision, reason codes, context, factors and safety result, and none of the keys `chain_of_thought`, `reasoning`, `thoughts` or `scratchpad`. "
          "Free-text rationales are not reliable descriptions of why a model acted " + n(17) + ", so decisions are explained from structured inputs and factors.",
          "**Tamper evidence.** `test_event_chain_is_tamper_evident` forges the second of three linked events (`approved` to `rejected`) and requires `verify_chain` to fail; `test_safety_chain_detects_tampering` repeats this on a real run. "
          "The chain uses SHA-256 " + n(20) + ".",
          "**Database and model output.** Every SQL statement uses bound parameters; provider output is parsed as data into the schema, with no `eval`, shell call or SQL built from it."),
        P("Not tested, and not claimed: authentication of the API (there is none), transport security, denial of service, and a real hosted model under adversarial prompts. "
          "The demo sign-in (`operator@safegrid.ai`) is a browser-side gate, not a security boundary."),
        H2("7.6 Validation and Edge Cases"),
        P("Edge cases are concentrated where the shield and the engine make decisions. The table lists the ones covered by automated tests and the behaviour each must show."),
        TAB("Edge cases and expected behaviour", ["Case", "Expected behaviour", "Test"],
            [["Charge request on a full battery", "Rejected with a state-of-charge code", "`test_charge_on_full_battery_is_rejected_with_soc_limit`"],
             ["Discharge beyond stored energy", "Projected to what is stored", "`test_discharge_beyond_stored_energy_is_projected`"],
             ["EV away from home", "Battery unavailable; the EV agent defers", "`test_battery_unavailable_when_ev_away`, `test_storage_agent_defers_when_ev_away`"],
             ["Curtailment larger than generation", "Projected to the available generation (3.0 kW in the test)", "`test_curtail_more_than_generated_is_projected`"],
             ["Power flow does not converge", "The action is blocked", "`test_power_flow_failure_blocks_action`"],
             ["Limits changed in configuration", "Voltage limits follow the configuration, nothing is hard-coded", "`test_voltage_limits_come_from_configuration`"],
             ["Duration other than the 15-minute step", "Aligned to the step and recorded as a correction", "`test_idle_always_approved_and_duration_is_aligned`"],
             ["Provider fails, times out or is unconfigured", "Labelled fallback decision, still shielded", "`test_llm_failure_uses_labelled_fallback` and three related tests"],
             ["Same seed twice", "Identical totals", "`test_runs_are_reproducible`"],
             ["Dry run", "Nothing in the grid state changes", "`test_step_by_step_and_dry_run_does_not_mutate`"]],
            widths=[1.9, 2.3, 2.3], size=9.5),
        P("The projection loop is also an edge-case guard: the exact rounded action is re-verified up to four times (scale factor times 0.999 each time), so a result that is safe only by a rounding accident is never executed; results below 0.05 kW are rejected."),
        H2("7.7 Performance Testing"),
        P("Latency was measured against a live `uvicorn` server on the same machine as the client (" + F.MACHINE + "), scenario `unsafe_ai_action`, seed 42, 12 to 50 repetitions per call. "
          "Network time is negligible, so the numbers describe computation."),
        TAB("Live API latency (milliseconds)", ["Call", "Runs", "Median", "95th percentile"],
            [[c, str(k), F.f1(m), F.f1(p)] for c, k, m, p in F.API_LAT], widths=[3.6, 0.6, 0.9, 1.3], size=9.5, align=["l", "c", "r", "r"]),
        FIG(F.fig("fig_api_latency.png"), "Median and 95th-percentile latency of the live API calls", 5.8),
        P("Read-only calls cost a few milliseconds; the expensive calls run trial power flows. "
          "A dry run of the agent's own proposal costs a median of 62.8 ms, a rejected absurd export 36.6 ms (structural checks stop it before any power flow), "
          "a projected request 230.0 ms (bisection evaluates many trial power flows) and a full simulation step 440.7 ms."),
        P(f"The batch experiment agrees: the mean step time with the shield is **{F.f1(F.mean('safegrid_shielded', 'avg_step_time_ms'))} ms** against **{F.f1(F.mean('agents_unshielded', 'avg_step_time_ms'))} ms** without it "
          f"(rule baseline {F.f1(F.mean('baseline_rule', 'avg_step_time_ms'))} ms). The shield roughly triples the compute time of a step, the price of validating every action with a real AC power flow; "
          "at a 15-minute control interval this is negligible. "
          "The decision latency of the mock provider (0.1-0.2 ms) does not represent a real language model, whose latency was not measured."),
        H2("7.8 User Acceptance Testing"),
        P("**No user acceptance testing was carried out.** No operator, instructor or outside user used the system, so statements about usability or trust are not supported by data; "
          "only the developers' browser walk-through (Section 7.4) exists. A proper test would give power-systems students or network operators a task script "
          "(start a scenario, find the first intervention, explain it, validate a custom action), a comprehension check on the explanation view, a trust and workload questionnaire, "
          "and a comparison of the dashboard with and without the explanation lane."),
        H2("7.9 Testing Limitations"),
        B("Two grid tests fail and one API test hangs (Section 7.2); the suite is therefore not green.",
          "The scenario tests assert the central safety property on the same simulated model that the shield uses to judge actions, so they show consistency of the shield with its model, not agreement with a real network.",
          "Agent tests use the deterministic mock provider; the real-model provider is exercised only through its output validation and its unconfigured path, because no API key was configured.",
          "Performance figures come from one desktop machine with other work running, and latency numbers shift between runs.",
          "There is no load test with concurrent users, no long-duration soak test and no test of the three-dimensional landing page beyond the browser walk-through.",
          "No user study was conducted."),
    ]
    return out
