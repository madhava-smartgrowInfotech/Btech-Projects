const blank = (v) => v === null || v === undefined || Number.isNaN(v)

export const num = (v, d = 2) => (blank(v) ? '-' : Number(v).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d }))
export const int = (v) => (blank(v) ? '-' : Math.round(Number(v)).toLocaleString())
export const kw = (v, d = 2) => (blank(v) ? '-' : `${num(v, d)} kW`)
export const pct = (v, d = 0) => (blank(v) ? '-' : `${(Number(v) * 100).toFixed(d)}%`)
export const pctPoints = (v, d = 0) => (blank(v) ? '-' : `${Number(v).toFixed(d)}%`)
export const pu = (v) => (blank(v) ? '-' : Number(v).toFixed(3))
export const titleize = (s = '') => String(s).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
export const humanize = (s = '') => String(s).replace(/_/g, ' ')

export function timeOf(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? String(iso) : d.toLocaleTimeString()
}

export const ACTION_LABEL = {
  charge_battery: 'Charge battery',
  discharge_battery: 'Discharge battery',
  import_power: 'Import power',
  export_power: 'Export power',
  curtail_generation: 'Curtail generation',
  shift_load: 'Shift load',
  idle: 'Idle',
}

export const SOURCE_LABEL = {
  llm: 'LLM',
  mock: 'Mock LLM',
  fallback: 'Fallback policy',
  baseline: 'Baseline controller',
  injected: 'Injected fault',
  operator: 'Operator',
}

export const SOURCE_TONE = { llm: 'info', mock: 'info', fallback: 'warn', baseline: 'neutral', injected: 'danger', operator: 'neutral' }

export const SHIELD = {
  approved: { label: 'Approved', tone: 'safe' },
  projected: { label: 'Projected', tone: 'warn' },
  rejected: { label: 'Rejected', tone: 'danger' },
}

export const PROVIDERS = [
  { value: 'mock', label: 'Mock LLM' },
  { value: 'api', label: 'Real LLM (API)' },
  { value: 'failing', label: 'Failing LLM (fallback test)' },
  { value: 'baseline', label: 'Baseline (no LLM)' },
]

export const CHECK_LABEL = {
  STRUCTURE: 'Structure',
  POWER_LIMITS: 'Power limits',
  POWER_BALANCE: 'Power balance',
  BATTERY: 'Battery',
  NODE_LIMITS: 'Node limits',
  POWER_FLOW: 'Power flow',
  VOLTAGE: 'Voltage',
  LINE_LOADING: 'Line loading',
  TRANSFORMER: 'Transformer',
  GRID_LIMITS: 'Grid limits',
}

export const ROLE_LABEL = {
  residential_prosumer: 'Residential prosumer',
  ev_storage: 'EV / storage node',
  renewable_prosumer: 'Renewable prosumer',
}

export const CONSTRAINT_LABEL = {
  v_min: ['Minimum voltage', 'pu'],
  v_max: ['Maximum voltage', 'pu'],
  line_max_loading_pct: ['Line loading limit', '%'],
  trafo_max_loading_pct: ['Transformer loading limit', '%'],
  max_grid_import_kw: ['Grid import limit', 'kW'],
  max_grid_export_kw: ['Grid export limit', 'kW'],
  min_action_kw: ['Smallest useful action', 'kW'],
  implausible_factor: ['Implausible-request factor', 'x node rating'],
  balance_tol_kw: ['Power balance tolerance', 'kW'],
  attribution_tol: ['Violation attribution tolerance', ''],
}

export const NODE_IDS = ['node_1', 'node_2', 'node_3']

export const isFinished = (status) => !!status && status.step >= status.total_steps
