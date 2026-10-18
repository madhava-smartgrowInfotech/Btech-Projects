const BASE = import.meta.env.VITE_API_BASE || "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch (_) {
      /* keep statusText */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  health: () => request("/api/health"),
  status: () => request("/api/simulation/status"),
  gridState: () => request("/api/grid/state"),
  topology: () => request("/api/grid/topology"),
  scenarios: () => request("/api/scenarios"),
  start: (config, resume = false) => request(`/api/simulation/start?resume=${resume}`, { method: "POST", body: config }),
  stop: () => request("/api/simulation/stop", { method: "POST" }),
  reset: (config) => request("/api/simulation/reset", { method: "POST", body: config }),
  step: () => request("/api/simulation/step", { method: "POST" }),
  runScenario: (id, config) => request(`/api/scenarios/${id}/run`, { method: "POST", body: config }),
  agents: () => request("/api/agents"),
  agent: (id) => request(`/api/agents/${id}`),
  dryRun: (id, action) => request(`/api/agents/${id}/decision`, { method: "POST", body: action ? { action } : {} }),
  events: (type) => request(`/api/events${type ? `?type=${type}` : ""}`),
  safetyEvents: (status) => request(`/api/safety/events${status ? `?status=${status}` : ""}`),
  constraints: () => request("/api/safety/constraints"),
  metrics: () => request("/api/metrics"),
  runs: () => request("/api/runs"),
  runSteps: (id) => request(`/api/runs/${id}/steps`),
  experimentRun: (spec) => request("/api/experiments/run", { method: "POST", body: spec }),
  experiments: () => request("/api/experiments"),
  experiment: (id) => request(`/api/experiments/${id}`),
};
