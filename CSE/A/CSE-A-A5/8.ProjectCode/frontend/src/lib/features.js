// Scoring form schema. Option lists and defaults mirror cipherguard/ids/features.py and the IDSRecord model in cipherguard/api/main.py.

const opts = (list) => list.map((v) => [v, v])

export const PROTO = opts(['tcp', 'udp', 'icmp', 'arp', 'ospf', 'igmp'])
export const SERVICE = opts(['-', 'http', 'ftp', 'smtp', 'ssh', 'dns', 'ftp-data', 'pop3', 'dhcp', 'ssl', 'snmp', 'radius', 'irc'])
export const STATE = opts(['FIN', 'INT', 'CON', 'REQ', 'RST', 'ECO', 'ACC', 'CLO', 'PAR', 'URN', 'no', '-'])

// kind: 'int' | 'float' (ints are sent as whole numbers - the API model rejects fractions for them)
export const MAIN_FIELDS = [
  { key: 'dur', label: 'Duration (s)', kind: 'float', def: '0.5' },
  { key: 'sbytes', label: 'Src bytes', kind: 'int', def: '1200' },
  { key: 'dbytes', label: 'Dst bytes', kind: 'int', def: '800' },
  { key: 'rate', label: 'Rate', kind: 'float', def: '15000' },
  { key: 'spkts', label: 'Src packets', kind: 'int', def: '8' },
  { key: 'dpkts', label: 'Dst packets', kind: 'int', def: '6' },
  { key: 'sload', label: 'Src load', kind: 'float', def: '80000' },
  { key: 'dload', label: 'Dst load', kind: 'float', def: '60000' },
  { key: 'ct_srv_src', label: 'ct_srv_src', kind: 'int', def: '2' },
  { key: 'ct_dst_ltm', label: 'ct_dst_ltm', kind: 'int', def: '2' },
  { key: 'ct_src_ltm', label: 'ct_src_ltm', kind: 'int', def: '2' },
  { key: 'ct_srv_dst', label: 'ct_srv_dst', kind: 'int', def: '2' },
]

export const ADVANCED_FIELDS = [
  { key: 'sttl', label: 'sttl', kind: 'int', def: '62' },
  { key: 'dttl', label: 'dttl', kind: 'int', def: '62' },
  { key: 'sloss', label: 'sloss', kind: 'int', def: '0' },
  { key: 'dloss', label: 'dloss', kind: 'int', def: '0' },
  { key: 'sinpkt', label: 'sinpkt', kind: 'float', def: '50' },
  { key: 'dinpkt', label: 'dinpkt', kind: 'float', def: '50' },
  { key: 'sjit', label: 'sjit', kind: 'float', def: '5' },
  { key: 'djit', label: 'djit', kind: 'float', def: '5' },
  { key: 'swin', label: 'swin', kind: 'int', def: '255' },
  { key: 'dwin', label: 'dwin', kind: 'int', def: '255' },
  { key: 'stcpb', label: 'stcpb', kind: 'int', def: '1000000' },
  { key: 'dtcpb', label: 'dtcpb', kind: 'int', def: '1000000' },
  { key: 'tcprtt', label: 'tcprtt', kind: 'float', def: '0.02' },
  { key: 'synack', label: 'synack', kind: 'float', def: '0.01' },
  { key: 'ackdat', label: 'ackdat', kind: 'float', def: '0.01' },
  { key: 'smean', label: 'smean', kind: 'int', def: '100' },
  { key: 'dmean', label: 'dmean', kind: 'int', def: '100' },
  { key: 'trans_depth', label: 'trans_depth', kind: 'int', def: '1' },
  { key: 'response_body_len', label: 'response_body_len', kind: 'int', def: '200' },
  { key: 'ct_state_ttl', label: 'ct_state_ttl', kind: 'int', def: '2' },
  { key: 'ct_src_dport_ltm', label: 'ct_src_dport_ltm', kind: 'int', def: '2' },
  { key: 'ct_dst_sport_ltm', label: 'ct_dst_sport_ltm', kind: 'int', def: '2' },
  { key: 'ct_dst_src_ltm', label: 'ct_dst_src_ltm', kind: 'int', def: '2' },
  { key: 'is_ftp_login', label: 'is_ftp_login', kind: 'int', def: '0' },
  { key: 'ct_ftp_cmd', label: 'ct_ftp_cmd', kind: 'int', def: '0' },
  { key: 'ct_flw_http_mthd', label: 'ct_flw_http_mthd', kind: 'int', def: '1' },
  { key: 'is_sm_ips_ports', label: 'is_sm_ips_ports', kind: 'int', def: '0' },
]

export const ALL_FIELDS = [...MAIN_FIELDS, ...ADVANCED_FIELDS]

export function initialForm() {
  return {
    proto: 'tcp', service: 'http', state: 'CON',
    ...Object.fromEntries(ALL_FIELDS.map((f) => [f.key, f.def])),
  }
}

// Presets used by "Simulate normal / attack" (same values the original dashboard used).
export const PRESETS = {
  normal: { proto: 'tcp', service: 'http', state: 'CON', dur: '0.3', sbytes: '900', dbytes: '700', rate: '12000', spkts: '7', dpkts: '5', ct_srv_src: '1', ct_dst_ltm: '1' },
  attack: { proto: 'tcp', service: 'ftp', state: 'RST', dur: '3.5', sbytes: '85000', dbytes: '1200', rate: '95000', spkts: '35', dpkts: '4', ct_srv_src: '12', ct_dst_ltm: '15' },
}

// -> { record } or { errors: { key: message } }
export function buildRecord(form) {
  const errors = {}
  const record = { proto: form.proto, service: form.service, state: form.state }
  for (const f of ALL_FIELDS) {
    const raw = String(form[f.key] ?? '').trim()
    const v = Number(raw)
    if (raw === '' || !Number.isFinite(v)) errors[f.key] = 'Enter a number'
    else if (v < 0) errors[f.key] = 'Must be 0 or more'
    else if (f.kind === 'int' && !Number.isInteger(v)) errors[f.key] = 'Whole number'
    else record[f.key] = v
  }
  return Object.keys(errors).length ? { errors } : { record }
}
