# API reference

The API runs at `http://localhost:8202`, and on the HTTPS tunnel address when `run.bat` starts one. Interactive documentation, where you can try every endpoint, is at **http://localhost:8202/docs**. Use the **Authorize** button with a demo account to try the protected ones.

- **JSON everywhere.** Times are ISO 8601 in UTC with a `Z` suffix.
- **Errors** have the form `{"detail": "message"}`. Validation errors (`422`) list each field.
- **People** authenticate with `Authorization: Bearer <token>` from `/api/auth/login`. Roles: `user` < `engineer` < `admin`.
- **Devices** (phones and ESP32 nodes) authenticate with `X-Device-Key: <key>`.
- The examples below are real responses from a running installation. Long lists are shortened (`... n more`), and keys and tokens are masked.

| Area | Endpoints |
|---|---|
| [Accounts and sign-in](#accounts-and-sign-in) | register, login, profile |
| [System](#system) | health, public stats, connection info |
| [Devices](#devices) | phones and nodes, keys |
| [Uploading readings](#uploading-readings) | phone batches, ESP32 batches, sync history |
| [Readings](#readings) | list, CSV export |
| [Coverage map](#coverage-map) | summary, zones, heat, points, nodes, live stream |
| [Phone probe](#phone-probe) | ping, speed test, carrier |
| [Better signal](#better-signal) | suggestion, offline spots, predicted grid |
| [Complaints](#complaints) | queue, report, lifecycle, notes, evidence, towers |
| [Analytics](#analytics) | summary, trends, worst areas, time of day, operators, funnel |
| [Model performance](#model-performance) | metrics, plots, field validation |
| [Administration](#administration) | users, settings, notifications, sample data |

## Accounts and sign-in

People sign in with email and password and send the returned token as `Authorization: Bearer <token>`.

### `POST /api/auth/register`

Create a field-user account (role `user`) and sign in.

**Auth:** none

Request body:

```json
{
  "name": "Field User",
  "email": "field.user@example.com",
  "password": "Str0ng-pass!"
}
```

Response `201`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 43200,
  "user": {
    "id": 7,
    "email": "field.user@example.com",
    "name": "Field User",
    "role": "user",
    "is_active": true,
    "notify_email": false,
    "is_demo": false,
    "created_at": "2026-09-22T13:33:28.275467Z",
    "last_login_at": null
  }
}
```

Errors: `409` when the email is already registered, `422` for a short password or invalid email.

### `POST /api/auth/login`

Sign in with email and password.

**Auth:** none

Request body:

```json
{
  "email": "user@signalscout.demo",
  "password": "Scout@2026"
}
```

Response `200`:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 43200,
  "user": {
    "id": 1,
    "email": "user@signalscout.demo",
    "name": "Demo Field User",
    "role": "user",
    "is_active": true,
    "notify_email": false,
    "is_demo": true,
    "created_at": "2026-09-22T12:04:00.022760Z",
    "last_login_at": "2026-09-22T13:33:30.520253Z"
  }
}
```

Errors: `401` for a wrong email or password, `403` for a disabled account.

### `POST /api/auth/token`

The same sign-in as a form (`username`, `password`), used by the **Authorize** button of the interactive docs at `/docs`.

**Auth:** none

Form fields: `username=<email>&password=<password>`. Response as for `/api/auth/login`.

### `GET /api/auth/me`

The signed-in account.

**Auth:** signed in

Response `200`:

```json
{
  "id": 1,
  "email": "user@signalscout.demo",
  "name": "Demo Field User",
  "role": "user",
  "is_active": true,
  "notify_email": false,
  "is_demo": true,
  "created_at": "2026-09-22T12:04:00.022760Z",
  "last_login_at": "2026-09-22T13:33:30.520253Z"
}
```

### `PATCH /api/auth/me`

Change your name, email notifications (`notify_email`) or password. Send only the fields to change; `new_password` needs `current_password`.

**Auth:** signed in

Request body:

```json
{
  "name": "Demo Field User"
}
```

Response `200`:

```json
{
  "id": 1,
  "email": "user@signalscout.demo",
  "name": "Demo Field User",
  "role": "user",
  "is_active": true,
  "notify_email": false,
  "is_demo": true,
  "created_at": "2026-09-22T12:04:00.022760Z",
  "last_login_at": "2026-09-22T13:33:30.520253Z"
}
```

## System

### `GET /api/health`

Status of the API, database and loaded models.

**Auth:** none

Response `200`:

```json
{
  "status": "ok",
  "app": "SignalScout",
  "version": "1.0.0",
  "time": "2026-09-22T13:33:41.156134Z",
  "database": "ok",
  "models": {
    "zone_classifier": true,
    "radio_estimate": true,
    "gp_signal": true
  },
  "model_versions": {
    "zone_classifier": "classifier_20260922_163745",
    "radio_estimate": "radio_estimate_20260922_164320",
    "gp_signal": "gp_20260922_164328"
  }
}
```

### `GET /api/public/stats`

Headline numbers for the landing page (aggregates only).

**Auth:** none

Response `200`:

```json
{
  "readings": 16704,
  "zones": 98,
  "complaints_registered": 14,
  "classifier_accuracy": 0.835,
  "classifier_model": "PyTorch MLP",
  "predictor_gain_vs_idw": 0.071
}
```

### `GET /api/system/connect`

Where phones and nodes can reach this installation: the HTTPS tunnel address (changes on every start) and the PC's LAN addresses.

**Auth:** signed in

Response `200`:

```json
{
  "tunnel_url": "https://example-words.trycloudflare.com",
  "tunnel_started_at": "2026-09-22T13:17:12.065898+00:00",
  "probe_url": "https://example-words.trycloudflare.com/probe",
  "tunnel_enabled": true,
  "lan_api_urls": [
    "http://192.168.1.20:8202"
  ],
  "lan_dashboard_urls": [
    "http://192.168.1.20:5202"
  ],
  "backend_port": 8202,
  "frontend_port": 5202
}
```

## Devices

Phones and ESP32 nodes upload with a device key in the `X-Device-Key` header. A key is returned once, when the device is created or its key is replaced.

### `GET /api/devices`

Devices with status, last seen and reading counts.

**Auth:** signed in (field users see their own; engineers and admins see all)

Response `200`:

```json
[
  {
    "id": 12,
    "owner_id": 1,
    "owner_name": "Demo Field User",
    "kind": "phone",
    "name": "Field phone",
    "api_key_prefix": "ssk_4bX...(shown once)",
    "hardware": "Chrome on Android",
    "firmware": null,
    "fixed_lat": null,
    "fixed_lon": null,
    "config": {},
    "is_active": true,
    "created_at": "2026-09-22T13:24:36.476238Z",
    "last_seen_at": "2026-09-22T13:24:42.656039Z",
    "last_sync_at": "2026-09-22T13:24:42.656039Z",
    "readings_count": 2,
    "online": false
  },
  "... 4 more"
]
```

### `POST /api/devices`

Add an ESP32 node (or a simulator). Give a fixed position if it has no GPS.

**Auth:** signed in

Request body:

```json
{
  "kind": "esp32",
  "name": "Market square node",
  "network_name": "Market square Wi-Fi",
  "fixed_lat": 18.5204,
  "fixed_lon": 73.8567
}
```

Response `201`:

```json
{
  "device": {
    "id": 13,
    "owner_id": 1,
    "owner_name": "Demo Field User",
    "kind": "esp32",
    "name": "Market square node",
    "api_key_prefix": "ssk_4bX...(shown once)",
    "hardware": null,
    "firmware": null,
    "fixed_lat": 18.5204,
    "fixed_lon": 73.8567,
    "config": {
      "network_name": "Market square Wi-Fi"
    },
    "is_active": true,
    "created_at": "2026-09-22T13:33:49.367213Z",
    "last_seen_at": null,
    "last_sync_at": null,
    "readings_count": 0,
    "online": false
  },
  "api_key": "ssk_4bX...(shown once)"
}
```

### `POST /api/devices/phone`

Register the phone this request comes from (the probe does this on first use).

**Auth:** signed in

Request body:

```json
{
  "name": "Field phone",
  "hardware": "Chrome on Android"
}
```

Response `201`:

```json
{
  "device": {
    "id": 14,
    "owner_id": 1,
    "owner_name": "Demo Field User",
    "kind": "phone",
    "name": "Field phone",
    "api_key_prefix": "ssk_4bX...(shown once)",
    "hardware": "Chrome on Android",
    "firmware": null,
    "fixed_lat": null,
    "fixed_lon": null,
    "config": {},
    "is_active": true,
    "created_at": "2026-09-22T13:33:51.427195Z",
    "last_seen_at": null,
    "last_sync_at": null,
    "readings_count": 0,
    "online": false
  },
  "api_key": "ssk_4bX...(shown once)"
}
```

### `PATCH /api/devices/{device_id}`

Rename a device, change its fixed position or network name, or disable it (`is_active`).

**Auth:** owner or admin

Request body:

```json
{
  "name": "Market square node 1"
}
```

Response `200`:

```json
{
  "id": 13,
  "owner_id": 1,
  "owner_name": "Demo Field User",
  "kind": "esp32",
  "name": "Market square node 1",
  "api_key_prefix": "ssk_4bX...(shown once)",
  "hardware": null,
  "firmware": null,
  "fixed_lat": 18.5204,
  "fixed_lon": 73.8567,
  "config": {
    "network_name": "Market square Wi-Fi"
  },
  "is_active": true,
  "created_at": "2026-09-22T13:33:49.367213Z",
  "last_seen_at": null,
  "last_sync_at": null,
  "readings_count": 0,
  "online": false
}
```

### `POST /api/devices/{device_id}/rotate-key`

Replace the device key. The old key stops working immediately.

**Auth:** owner or admin

Response `200`:

```json
{
  "device": {
    "id": 13,
    "owner_id": 1,
    "owner_name": "Demo Field User",
    "kind": "esp32",
    "name": "Market square node 1",
    "api_key_prefix": "ssk_4bX...(shown once)",
    "hardware": null,
    "firmware": null,
    "fixed_lat": 18.5204,
    "fixed_lon": 73.8567,
    "config": {
      "network_name": "Market square Wi-Fi"
    },
    "is_active": true,
    "created_at": "2026-09-22T13:33:49.367213Z",
    "last_seen_at": null,
    "last_sync_at": null,
    "readings_count": 0,
    "online": false
  },
  "api_key": "ssk_4bX...(shown once)"
}
```

## Uploading readings

### `POST /api/ingest/readings`

Upload up to 500 readings from a phone (or a replay). Idempotent: a `client_uuid` already stored is reported as `duplicate`. The operator is found from the request's IP address unless the reading names one.

**Auth:** device key

Request body:

```json
{
  "readings": [
    {
      "client_uuid": "docs-1790084035-0",
      "ts": "2026-09-22T13:31:26.039860+00:00",
      "lat": 18.5207,
      "lon": 73.8563,
      "accuracy_m": 9,
      "connection_type": "cellular",
      "effective_type": "4g",
      "latency_ms": 62,
      "jitter_ms": 8,
      "packet_loss": 0,
      "probes_sent": 3,
      "probes_ok": 3,
      "dl_mbps": 18.4,
      "ul_mbps": 6.1
    }
  ]
}
```

Response `200`:

```json
{
  "received": 2,
  "accepted": 2,
  "duplicates": 0,
  "rejected": 0,
  "operator": "Jio",
  "link": "cellular",
  "results": [
    {
      "client_uuid": "docs-1790084035-0",
      "status": "accepted",
      "zone_label": "Strong",
      "zone_confidence": 1.0,
      "label_method": "service-bands",
      "radio_estimate": "Strong",
      "radio_estimate_conf": 0.487,
      "reasons": [
        "Latency and speed within the Strong band"
      ],
      "error": null
    },
    "... 1 more"
  ]
}
```

Reading fields (all optional except `client_uuid`, `ts`, `lat`, `lon`): `accuracy_m`, `operator`, `network_type`, `connection_type`, `in_service`, `connected`, radio metrics `rsrp`, `rsrq`, `sinr`, `rssi`, `cqi`, `cell_id`, `tac`, `pci`, `earfcn`, service metrics `latency_ms`, `jitter_ms`, `packet_loss`, `probes_sent`, `probes_ok`, `dl_mbps`, `ul_mbps`, browser hints `effective_type`, `downlink_est`, `rtt_est`. Values outside physical ranges are rejected per reading.

### `POST /api/ingest/node`

Upload buffered readings from an ESP32 node in the compact firmware format. Without `lat`/`lon` the node's fixed position is used.

**Auth:** device key (ESP32 node or simulator)

Request body:

```json
{
  "firmware": "signalscout-node-1.0.0",
  "uptime_s": 3600,
  "network_name": "Market square Wi-Fi",
  "readings": [
    {
      "seq": 100001,
      "ts": "2026-09-22T13:33:06.039860+00:00",
      "connected": true,
      "wifi_rssi": -71.0,
      "ble_rssi": -80.0,
      "latency_ms": 48.2,
      "packet_loss": 0.0
    },
    {
      "seq": 100002,
      "ts": "2026-09-22T13:33:16.039860+00:00",
      "connected": false,
      "wifi_rssi": -84.0
    }
  ]
}
```

Response `200`:

```json
{
  "received": 2,
  "accepted": 2,
  "duplicates": 0,
  "rejected": 0,
  "operator": "Market square Wi-Fi",
  "link": "wifi",
  "results": [
    {
      "client_uuid": "node-13-100001-1790064186",
      "status": "accepted",
      "zone_label": "Weak",
      "zone_confidence": null,
      "label_method": "wifi-ranges",
      "radio_estimate": null,
      "radio_estimate_conf": null,
      "reasons": [
        "Wi-Fi RSSI -71 dBm is below -67 dBm"
      ],
      "error": null
    },
    {
      "client_uuid": "node-13-100002-1790064196",
      "status": "accepted",
      "zone_label": "Dead",
      "zone_confidence": null,
      "label_method": "wifi-ranges",
      "radio_estimate": null,
      "radio_estimate_conf": null,
      "reasons": [
        "Node is not connected to Wi-Fi"
      ],
      "error": null
    }
  ]
}
```

### `GET /api/devices/{device_id}/sync`

Upload history of a device.

**Auth:** owner or admin

Response `200`:

```json
[
  {
    "id": 1112,
    "ts": "2026-09-22T13:33:57.592400Z",
    "received": 2,
    "accepted": 2,
    "duplicates": 0,
    "rejected": 0,
    "oldest_reading": "2026-09-22T13:31:26.039860Z"
  }
]
```

## Readings

### `GET /api/readings`

Readings, newest first.

**Auth:** signed in (field users see their own phone readings)

| Parameter | Meaning |
|---|---|
| `operator` | only this operator |
| `source` | `phone`, `esp32`, `simulator`, `sample_dataset` (comma list) |
| `label` | Strong / Weak / Dead |
| `device_id` | one device |
| `days` | last N days |
| `limit, offset` | paging (limit up to 1000) |

Response `200`:

```json
[
  {
    "id": 16713,
    "client_uuid": "node-3-830328-1790064235",
    "device_id": 3,
    "source": "simulator",
    "ts": "2026-09-22T13:33:55.111085Z",
    "lat": 12.9724,
    "lon": 77.5988,
    "accuracy_m": 5.0,
    "h3_cell": "8960145b49bffff",
    "operator": "Bus stand Wi-Fi",
    "link": "wifi",
    "network_type": null,
    "connected": true,
    "in_service": true,
    "rsrp": null,
    "rsrq": null,
    "sinr": null,
    "rssi": null,
    "latency_ms": 116.7,
    "jitter_ms": null,
    "packet_loss": 0.082,
    "dl_mbps": null,
    "ul_mbps": null,
    "wifi_rssi": -62.1,
    "zone_label": "Strong",
    "zone_confidence": null,
    "label_method": "wifi-ranges",
    "radio_estimate": null,
    "radio_estimate_conf": null,
    "reasons": [
      "Wi-Fi RSSI -62.1 dBm is at or above -67 dBm"
    ]
  }
]
```

### `GET /api/readings/export.csv`

The same readings as CSV (same filters).

**Auth:** signed in

Response `200`:

```
id,ts,source,device_id,lat,lon,accuracy_m,h3_cell,operator,link,network_type,connected,in_service,rsrp,rsrq,sinr,rssi,cqi,latency_ms,jitter_ms,packet_loss,dl_mbps,ul_mbps,wifi_rssi,ble_rssi,zone_label,zone_confidence,label_method,radio_estimate,radio_estimate_conf,model_version
4,2026-07-31T17:07:08Z,sample_dataset,4,51.893487,-8.499558,5.0,89182a3a0dbffff,Operator A,cellular,LTE,True,True,-101.0,-13.0,7.0,-84.0,8.0,,,,0.0,0.0,,,Weak,1.0,model,,,classifier_20260922_163745
5,2026-07-31T17:07:09Z,sample_dataset,4,51.893483,-8.499488,5.0,89182a3a0dbffff,Operator A,cellular,LTE,True,True,-101.0,-13.0,7.0,-82.0,6.0,,,,0.0,0.0,,,Weak,1.0,model,,,classifier_20260922_163745
```

## Coverage map

Common filters for every coverage endpoint: `operator`, `days`, `hours` (e.g. `18-23`), `sources` (comma list) and `include_wifi` (default false).

### `GET /api/coverage/summary`

Operators and sources with reading counts, the data bounds and the latest reading time.

**Auth:** signed in

Response `200`:

```json
{
  "operators": [
    {
      "name": "Operator A",
      "readings": 8805
    },
    {
      "name": "Operator B",
      "readings": 6796
    },
    "... 6 more"
  ],
  "sources": [
    {
      "name": "esp32",
      "readings": 2
    },
    {
      "name": "phone",
      "readings": 61
    },
    "... 2 more"
  ],
  "first_ts": "2026-07-31T17:07:08Z",
  "last_ts": "2026-09-22T13:34:10.150785Z",
  "bounds": [
    [
      12.97127,
      -8.59402
    ],
    [
      51.93568,
      77.59994
    ]
  ],
  "total": 16714,
  "sample_data": {
    "state": "idle",
    "readings": 0
  }
}
```

### `GET /api/coverage/hex`

H3 zones as GeoJSON with class counts, the zone label and medians.

**Auth:** signed in

| Parameter | Meaning |
|---|---|
| `resolution` | H3 resolution 6-11 (default 9) |

Response `200`:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -8.43544,
              51.91913
            ],
            "... 6 more"
          ]
        ]
      },
      "properties": {
        "cell": "89182a0482fffff",
        "n": 181,
        "strong": 59,
        "weak": 111,
        "dead": 11,
        "label": "Weak",
        "bad_share": 0.674,
        "confidence": 1.0,
        "median_rsrp": -102.0,
        "median_latency": null,
        "median_dl": 19.73,
        "median_wifi_rssi": null,
        "last_ts": "2026-08-10T12:07:27Z",
        "sources": [
          "sample_dataset"
        ],
        "operators": {
          "Operator A": {
            "n": 181,
            "label": "Weak"
          }
        },
        "center": [
          51.91737,
          -8.43471
        ]
      }
    },
    "... 36 more"
  ],
  "resolution": 9,
  "readings": 8805
}
```

### `GET /api/coverage/heat`

Weighted points for the problem heat layer (Dead 1.0, Weak 0.5).

**Auth:** signed in

Response `200`:

```json
{
  "points": [
    [
      51.874,
      -8.5194,
      0.4889
    ],
    [
      51.8914,
      -8.5124,
      0.55
    ],
    "... 207 more"
  ],
  "mode": "problems"
}
```

### `GET /api/coverage/points`

Most recent individual readings for the live layer.

**Auth:** signed in

Response `200`:

```json
[
  {
    "id": 16720,
    "ts": "2026-09-22T13:34:10.150785Z",
    "lat": 12.9724,
    "lon": 77.5988,
    "label": "Strong",
    "confidence": null,
    "operator": "Bus stand Wi-Fi",
    "source": "simulator",
    "rsrp": null,
    "latency_ms": 76.4,
    "dl_mbps": null,
    "wifi_rssi": -65.8,
    "mine": false
  },
  {
    "id": 16719,
    "ts": "2026-09-22T13:34:10.143114Z",
    "lat": 12.976,
    "lon": 77.5959,
    "label": "Dead",
    "confidence": null,
    "operator": "Health centre Wi-Fi",
    "source": "simulator",
    "rsrp": null,
    "latency_ms": 169.9,
    "dl_mbps": null,
    "wifi_rssi": -85.4,
    "mine": false
  }
]
```

### `GET /api/coverage/nodes`

Sensor nodes with their position and latest state.

**Auth:** signed in

Response `200`:

```json
[
  {
    "id": 1,
    "name": "Market square node",
    "kind": "simulator",
    "lat": 12.9763,
    "lon": 77.5999,
    "online": true,
    "network_name": "Market square Wi-Fi",
    "last_seen_at": "2026-09-22T13:34:10.137119Z",
    "label": "Strong",
    "wifi_rssi": -56.6,
    "latency_ms": 52.2
  },
  "... 3 more"
]
```

### `GET /api/coverage/stream`

Server-Sent Events: `readings` (new readings, as in `/points`) and `complaint` (status changes). A comment line is sent every 15 s to keep the connection open.

**Auth:** signed in (token in `?access_token=` because browsers cannot set headers on EventSource)

Response:

```
event: complaint
data: {"id": 43, "ref_code": "SS-2026-000043", "status": "registered", "event": "registered", "operator": "Airtel", ...}

event: readings
data: [{"id": 16475, "ts": "2026-09-22T13:20:04Z", "lat": 12.9716, "lon": 77.5946, "label": "Strong", ...}]
```

## Phone probe

### `GET /api/probe/ping`

Tiny, never-cached response used to time round trips.

**Auth:** none

Response `200`:

```json
{
  "t": 1790084061442
}
```

### `GET /api/probe/download`

Random bytes for the download test.

**Auth:** device key

| Parameter | Meaning |
|---|---|
| `bytes` | 10,000 to 5,000,000 (default 250,000) |

Response: `application/octet-stream` of the requested size, not cached.

### `POST /api/probe/upload`

Accepts up to 2 MB of bytes for the upload test and reports what arrived.

**Auth:** device key

Response:

```json
{
  "bytes": 250000,
  "server_ms": 41.7
}
```

### `GET /api/probe/whoami`

The operator and link detected from this phone's address, plus the probe settings to use.

**Auth:** device key

Response `200`:

```json
{
  "device": {
    "id": 14,
    "name": "Field phone"
  },
  "carrier": {
    "operator": "Jio",
    "network_name": "Reliance Jio Infocomm Limited",
    "asn": 55836,
    "kind": "mixed",
    "ip": "49.36.x.x"
  },
  "config": {
    "interval_s": 10,
    "speedtest_interval_s": 60,
    "speedtest_max_bytes": 1000000,
    "weak_rtt_ms": 400.0,
    "weak_dl_mbps": 2.0
  }
}
```

Behind the tunnel the phone's public address arrives in `CF-Connecting-IP`; the API trusts forwarding headers only from this PC.

## Better signal

### `GET /api/suggest`

Nearest spot predicted Strong with at least 80% probability (Gaussian Process on readings of the same operator within 1.5 km).

**Auth:** signed in

| Parameter | Meaning |
|---|---|
| `lat, lon` | where the person is |
| `operator` | operator to predict for (default: the most common one nearby) |

Response `200`:

```json
{
  "found": true,
  "status": "already_strong",
  "message": "You are already in a strong area (predicted -85 dBm).",
  "target": "rsrp",
  "method": "gaussian-process",
  "lat": 51.8975,
  "lon": -8.473,
  "distance_m": 0.0,
  "bearing_deg": null,
  "direction": null,
  "predicted": -85.436,
  "predicted_sd": 6.503,
  "probability": 0.987,
  "here_predicted": -85.436,
  "here_probability": 0.987,
  "supporting_readings": 2481,
  "unit": "dBm",
  "operator": "Operator A",
  "model_version": "gp_20260922_164328"
}
```

`status` is `found`, `already_strong`, `none_nearby` or `too_few_readings`; `message` is ready to show.

### `GET /api/suggest/area`

Predicted strong spots around a point, which the phone saves for offline use.

**Auth:** signed in

| Parameter | Meaning |
|---|---|
| `radius_m` | up to 5,000 (default 2,500) |

Response `200`:

```json
{
  "center": [
    51.8975,
    -8.473
  ],
  "operator": "Operator A",
  "target": "rsrp",
  "spots": [
    {
      "lat": 51.8948,
      "lon": -8.4852,
      "value": -90.911,
      "p_strong": 0.82,
      "target": "rsrp"
    },
    {
      "lat": 51.8953,
      "lon": -8.4914,
      "value": -96.026,
      "p_strong": 0.803,
      "target": "rsrp"
    },
    "... 210 more"
  ]
}
```

### `GET /api/coverage/predicted`

Predicted coverage grid (value and probability of Strong) around a point, for the map's prediction layer.

**Auth:** signed in

Response `200`:

```json
{
  "cells": [
    {
      "lat": 51.8925,
      "lon": -8.473,
      "value": -102.191,
      "sd": 10.759,
      "p_strong": 0.419
    },
    {
      "lat": 51.8925,
      "lon": -8.4724,
      "value": -103.019,
      "sd": 10.471,
      "p_strong": 0.387
    },
    "... 605 more"
  ],
  "target": "rsrp",
  "operator": "Operator A",
  "strong_threshold": -100.0,
  "step_m": 40,
  "unit": "dBm"
}
```

## Complaints

Statuses: `detected`, `registered`, `acknowledged`, `in_progress`, `resolved`, `verified`, `dismissed`.

### `GET /api/complaints`

Complaints, most recently updated first, with counts per status.

**Auth:** signed in (field users: complaints they reported or from zones they measured; engineers: all)

| Parameter | Meaning |
|---|---|
| `status` | comma list of statuses |
| `operator` | one operator |
| `source` | e.g. `sample_dataset` |
| `q` | search in reference, zone and operator |
| `mine` | only complaints I reported |
| `assigned_to_me` | only complaints assigned to me |
| `limit, offset` | paging (limit up to 500) |

Response `200`:

```json
{
  "items": [
    {
      "id": 45,
      "ref_code": "SS-2026-000045",
      "h3_cell": "8960145b49bffff",
      "operator": "Bus stand Wi-Fi",
      "lat": 12.9721,
      "lon": 77.5975,
      "status": "registered",
      "severity": "dead",
      "origin": "auto",
      "source": "simulator",
      "reporter_user_id": null,
      "assigned_to_id": null,
      "assigned_to_name": null,
      "reporter_name": null,
      "summary": "Complaint SS-2026-000045: poor Bus stand Wi-Fi coverage in zone 8960145b49bffff (around 12.97206, 77.59751). 9 readings from 1 device(s) between 2026-09-22 1...",
      "reopen_count": 0,
      "detected_at": "2026-09-22T13:17:06.077547Z",
      "registered_at": "2026-09-22T13:19:06.561002Z",
      "acknowledged_at": null,
      "in_progress_at": null,
      "resolved_at": null,
      "verified_at": null,
      "dismissed_at": null,
      "updated_at": "2026-09-22T13:34:25.216751Z",
      "readings": 9,
      "bad_share": 1.0,
      "verification": null
    }
  ],
  "total": 49,
  "counts": {
    "detected": 5,
    "registered": 10,
    "acknowledged": 3,
    "in_progress": 0,
    "resolved": 0,
    "verified": 1,
    "dismissed": 30
  }
}
```

### `POST /api/complaints`

Report a problem at a place. It is registered at once, with the evidence from that zone attached. A report for a zone with an open complaint is added to it as a note.

**Auth:** signed in

Request body:

```json
{
  "lat": 18.484,
  "lon": 73.8566,
  "note": "Calls drop every evening near the bus stand"
}
```

Response `201`:

```json
{
  "id": 50,
  "ref_code": "SS-2026-000050",
  "h3_cell": "89608852a8fffff",
  "operator": "Unknown",
  "lat": 18.4837,
  "lon": 73.8569,
  "status": "registered",
  "severity": "weak",
  "origin": "user",
  "source": "phone",
  "reporter_user_id": 1,
  "assigned_to_id": null,
  "assigned_to_name": null,
  "reporter_name": "Demo Field User",
  "summary": "Complaint SS-2026-000050: user report for Unknown in zone 89608852a8fffff. User note: Calls drop every evening near the bus stand",
  "reopen_count": 0,
  "detected_at": "2026-09-22T13:34:33.868836Z",
  "registered_at": "2026-09-22T13:34:33.868836Z",
  "acknowledged_at": null,
  "in_progress_at": null,
  "resolved_at": null,
  "verified_at": null,
  "dismissed_at": null,
  "updated_at": "2026-09-22T13:34:33.869834Z",
  "readings": 0,
  "bad_share": null,
  "verification": null,
  "evidence": {
    "readings": 0,
    "classes": {
      "Strong": 0,
      "Weak": 0,
      "Dead": 0
    },
    "zone": {
      "h3_cell": "89608852a8fffff",
      "center": [
        18.48375,
        73.85688
      ],
      "operator": "Unknown"
    }
  },
  "suggestion": null,
  "boundary": [
    [
      18.48349,
      73.85863
    ],
    "... 5 more"
  ],
  "events": [
    {
      "id": 107,
      "ts": "2026-09-22T13:34:33.870916Z",
      "kind": "status",
      "from_status": null,
      "to_status": "detected",
      "actor_label": "Demo Field User",
      "note": "Reported by Demo Field User: Calls drop every evening near the bus stand"
    },
    "... 1 more"
  ]
}
```

### `GET /api/complaints/{complaint_id}`

One complaint with evidence, zone outline, suggestion and timeline.

**Auth:** signed in (visibility as for the list)

Response `200`:

```json
{
  "id": 43,
  "ref_code": "SS-2026-000043",
  "h3_cell": "8960145b4d7ffff",
  "operator": "Airtel",
  "lat": 12.9753,
  "lon": 77.5982,
  "status": "verified",
  "severity": "dead",
  "origin": "auto",
  "source": "phone",
  "reporter_user_id": 1,
  "assigned_to_id": 2,
  "assigned_to_name": "Demo Engineer",
  "reporter_name": "Demo Field User",
  "summary": "Complaint SS-2026-000043: poor Airtel coverage in zone 8960145b4d7ffff (around 12.97527, 77.59817). 28 readings from 1 device(s) between 2026-09-22 13:07 and...",
  "reopen_count": 0,
  "detected_at": "2026-09-22T13:07:18.120000Z",
  "registered_at": "2026-09-22T13:09:33.503000Z",
  "acknowledged_at": "2026-09-22T13:09:48.563710Z",
  "in_progress_at": "2026-09-22T13:09:50.062976Z",
  "resolved_at": "2026-09-22T13:09:51.527811Z",
  "verified_at": "2026-09-22T13:10:06.093179Z",
  "dismissed_at": null,
  "updated_at": "2026-09-22T13:10:06.094179Z",
  "readings": 28,
  "bad_share": 1.0,
  "verification": {
    "state": "verified",
    "readings": 3,
    "strong_share": 1.0,
    "bad_share": 0.0,
    "needed": 3,
    "checked_at": "2026-09-22T13:10:06.093179Z"
  },
  "evidence": {
    "zone": {
      "h3_cell": "8960145b4d7ffff",
      "resolution": 9,
      "center": [
        12.97527,
        77.59817
      ],
      "area_km2": 0.109,
      "operator": "Airtel"
    },
    "window": {
      "first": "2026-09-22T13:07:18.120000Z",
      "last": "2026-09-22T13:09:33.503000Z",
      "minutes": 2.3
    },
    "readings": 28,
    "classes": {
      "Strong": 0,
      "Weak": 0,
      "Dead": 28
    },
    "bad_share": 1.0,
    "dead_share": 1.0,
    "devices": 1,
    "sources": {
      "phone": 28
    },
    "methods": {
      "service-bands": 28
    },
    "model_versions": [],
    "mean_confidence": 1.0,
    "service": {
      "readings": 28,
      "no_connectivity_share": 1.0,
      "latency_median_ms": null,
      "latency_p90_ms": null,
      "jitter_median_ms": null,
      "packet_loss_mean": 1.0,
      "download_median_mbps": null,
      "upload_median_mbps": null,
      "asns": [
        45609
      ],
      "radio_estimate": {}
    },
    "top_reasons": [
      {
        "reason": "Phone reported no connection",
        "count": 28
      }
    ],
    "series": [
      {
        "ts": "2026-09-22T13:07:18.120000Z",
        "label": "Dead",
        "rsrp": null,
        "latency_ms": null,
        "dl_mbps": null,
        "wifi_rssi": null
      },
      "... 27 more"
    ],
    "samples": [
      {
        "ts": "2026-09-22T13:07:18.120000Z",
        "lat": 12.9752,
        "lon": 77.5983,
        "label": "Dead",
        "confidence": 1.0,
        "rsrp": null,
        "rsrq": null,
        "sinr": null,
        "latency_ms": null,
        "dl_mbps": null,
        "wifi_rssi": null,
        "cell_id": null,
        "source": "phone"
      },
      "... 27 more"
    ],
    "nearest_strong_spot": {
      "found": true,
      "status": "found",
      "message": "Too few readings to model the area; the nearest measured strong spot is 535 m SW.",
      "lat": 12.9716,
      "lon": 77.595,
      "distance_m": 535.0,
      "direction": "SW",
      "predicted": 2.602,
      "predicted_mbps": 399.94,
      "probability": null,
      "target": "log_dl"
    }
  },
  "suggestion": {
    "found": true,
    "status": "found",
    "message": "Too few readings to model the area; the nearest measured strong spot is 535 m SW.",
    "lat": 12.9716,
    "lon": 77.595,
    "distance_m": 535.0,
    "direction": "SW",
    "predicted": 2.602,
    "predicted_mbps": 399.94,
    "probability": null,
    "target": "log_dl"
  },
  "boundary": [
    [
      12.9749,
      77.59997
    ],
    "... 5 more"
  ],
  "events": [
    {
      "id": 80,
      "ts": "2026-09-22T13:09:39.012917Z",
      "kind": "status",
      "from_status": null,
      "to_status": "detected",
      "actor_label": "System",
      "note": "28 of 28 readings Weak or Dead within 10 minutes"
    },
    "... 5 more"
  ]
}
```

### `POST /api/complaints/{complaint_id}/transition`

Move a complaint along its lifecycle. Allowed moves: registered → acknowledged / in_progress / dismissed; acknowledged → in_progress / dismissed; in_progress → resolved; resolved → verified (confirm by hand) / registered (reopen). Dismissing needs a note.

**Auth:** engineer

Request body:

```json
{
  "to": "acknowledged",
  "note": "Checking the sector antenna"
}
```

Response `200`:

```json
{
  "...": "the updated complaint, as GET /api/complaints/{id}"
}
```

Errors: `409` for a move that is not allowed from the current status.

### `POST /api/complaints/{complaint_id}/assign`

Assign to an engineer (`user_id`), or unassign with `null`.

**Auth:** engineer

Request body:

```json
{
  "user_id": 3
}
```

Response `200`:

```json
{
  "...": "the updated complaint"
}
```

### `POST /api/complaints/{complaint_id}/notes`

Add a note to the timeline.

**Auth:** signed in (anyone who can see it)

Request body:

```json
{
  "note": "Still no signal at 8 pm today"
}
```

Response `200`:

```json
{
  "...": "the updated complaint"
}
```

### `GET /api/complaints/{complaint_id}/evidence.json`

Download the evidence bundle (attachment).

**Auth:** signed in

Response `200`:

```json
{
  "ref_code": "SS-2026-000050",
  "status": "acknowledged",
  "operator": "Unknown",
  "zone": "89608852a8fffff",
  "summary": "Complaint SS-2026-000050: user report for Unknown in zone 89608852a8fffff. User note: Calls drop every evening near the bus stand",
  "evidence": {
    "readings": 0,
    "classes": {
      "Strong": 0,
      "Weak": 0,
      "Dead": 0
    },
    "zone": {
      "h3_cell": "89608852a8fffff",
      "center": [
        18.48375,
        73.85688
      ],
      "operator": "Unknown"
    }
  },
  "exported_at": "2026-09-22T13:34:48.345124Z"
}
```

### `GET /api/complaints/{complaint_id}/evidence.csv`

Download the readings behind the complaint as CSV.

**Auth:** signed in

Response `200`:

```
ts,source,lat,lon,accuracy_m,zone_label,zone_confidence,label_method,rsrp,rsrq,sinr,rssi,cell_id,latency_ms,jitter_ms,packet_loss,dl_mbps,ul_mbps,wifi_rssi,connected
```

### `GET /api/complaints/{complaint_id}/towers`

Known cell towers within 1 km (OpenCelliD). Returns `enabled: false` without an OpenCelliD key.

**Auth:** signed in

Response `200`:

```json
{
  "enabled": false,
  "towers": []
}
```

With a key: `{"enabled": true, "towers": [{"radio": "LTE", "mcc": 404, "mnc": 45, "area": 11, "cell": 502, "lat": 18.52, "lon": 73.85, "range_m": 900, "distance_m": 220, "serving": false}]}`.

### `GET /api/complaints/meta/engineers`

Engineers a complaint can be assigned to.

**Auth:** engineer

Response `200`:

```json
[
  {
    "id": 3,
    "name": "Demo Admin"
  },
  {
    "id": 2,
    "name": "Demo Engineer"
  }
]
```

## Analytics

Common parameters: `operator`, `days`, `include_sample` (default true) and `tz_offset_min` (the viewer's offset from UTC, for day and hour grouping).

### `GET /api/analytics/summary`

Key figures for the dashboard. Field users also get `mine` (their readings and complaints).

**Auth:** signed in

Response `200`:

```json
{
  "readings_total": 16720,
  "readings_24h": 1119,
  "zones_monitored": 98,
  "zones_bad": 49,
  "zones_dead": 6,
  "bad_zone_share": 0.5,
  "complaints_open": 19,
  "complaints_needing_action": 10,
  "complaints_registered_7d": 15,
  "complaints_verified": 1,
  "median_hours_to_resolve": 0.01,
  "median_hours_to_verify": 0.0,
  "devices_online": 5,
  "mine": null
}
```

### `GET /api/analytics/trends`

Per day: readings by class, and complaints registered and resolved.

**Auth:** signed in

Response `200`:

```json
{
  "days": [
    {
      "day": "2026-09-15",
      "readings": 671,
      "strong": 374,
      "weak": 257,
      "dead": 40,
      "weak_share": 0.383,
      "dead_share": 0.06,
      "registered": 0,
      "resolved": 0
    },
    {
      "day": "2026-09-16",
      "readings": 1278,
      "strong": 838,
      "weak": 379,
      "dead": 61,
      "weak_share": 0.297,
      "dead_share": 0.048,
      "registered": 0,
      "resolved": 0
    },
    "... 3 more"
  ]
}
```

### `GET /api/analytics/worst-areas`

Zones with the highest share of Weak/Dead readings (`min_readings`, default 20), with any open complaint.

**Auth:** signed in

Response `200`:

```json
[
  {
    "cell": "89182a3a427ffff",
    "operator": "Operator A",
    "readings": 67,
    "bad_share": 1.0,
    "dead_share": 0.955,
    "lat": 51.8943,
    "lon": -8.4717,
    "median_rsrp": -109.0,
    "median_latency": null,
    "last": "2026-07-31T17:55:56Z",
    "sources": [
      "sample_dataset"
    ],
    "complaint": null
  },
  {
    "cell": "89182a3a6afffff",
    "operator": "Operator A",
    "readings": 133,
    "bad_share": 1.0,
    "dead_share": 0.82,
    "lat": 51.8945,
    "lon": -8.5045,
    "median_rsrp": -111.0,
    "median_latency": null,
    "last": "2026-08-03T13:50:09Z",
    "sources": [
      "sample_dataset"
    ],
    "complaint": null
  }
]
```

### `GET /api/analytics/time-of-day`

Share of Weak/Dead readings by weekday (0 = Monday) and hour.

**Auth:** signed in

Response `200`:

```json
{
  "cells": [
    {
      "weekday": 0,
      "hour": 4,
      "bad_share": 0.453,
      "readings": 424
    },
    {
      "weekday": 0,
      "hour": 5,
      "bad_share": 0.28,
      "readings": 1009
    },
    "... 22 more"
  ]
}
```

### `GET /api/analytics/operators`

Operator comparison: class shares, medians, complaints and resolution time.

**Auth:** signed in

Response `200`:

```json
[
  {
    "operator": "Operator A",
    "readings": 8805,
    "zones": 37,
    "strong_share": 0.412,
    "weak_share": 0.42,
    "dead_share": 0.169,
    "median_rsrp": -95.0,
    "median_latency": null,
    "median_dl": 13.46,
    "complaints_total": 22,
    "complaints_open": 4,
    "median_hours_to_resolve": null,
    "sources": [
      "sample_dataset"
    ]
  },
  "... 7 more"
]
```

### `GET /api/analytics/complaint-funnel`

How many complaints reached each stage, and the median hours between stages.

**Auth:** signed in

Response `200`:

```json
{
  "stages": [
    {
      "stage": "detected",
      "reached": 50
    },
    {
      "stage": "registered",
      "reached": 15
    },
    {
      "stage": "acknowledged",
      "reached": 5
    },
    {
      "stage": "in_progress",
      "reached": 1
    },
    {
      "stage": "resolved",
      "reached": 1
    },
    {
      "stage": "verified",
      "reached": 1
    }
  ],
  "gaps": [
    {
      "from": "detected",
      "to": "registered",
      "median_hours": 0.13
    },
    {
      "from": "registered",
      "to": "acknowledged",
      "median_hours": 0.0
    },
    {
      "from": "acknowledged",
      "to": "in_progress",
      "median_hours": 0.0
    },
    {
      "from": "in_progress",
      "to": "resolved",
      "median_hours": 0.0
    },
    {
      "from": "resolved",
      "to": "verified",
      "median_hours": 0.0
    }
  ],
  "dismissed": 30,
  "reopened": 0
}
```

## Model performance

### `GET /api/ml/models`

Every trained model with its evaluation from `experiments/` (full metrics as in docs/05).

**Auth:** signed in

Response `200`:

```json
{
  "models": {
    "zone_classifier": {
      "title": "Zone classifier",
      "run": "classifier_20260922_163745",
      "created_at": "2026-09-22T11:13:15+00:00",
      "...": "metrics, splits, baselines, plots"
    },
    "radio_estimate": {
      "title": "Radio-condition estimate (phone speed tests)",
      "run": "radio_estimate_20260922_164320",
      "created_at": "2026-09-22T11:13:25+00:00",
      "...": "metrics, splits, baselines, plots"
    },
    "gp_signal": {
      "title": "Better-signal predictor (Gaussian Process)",
      "run": "gp_20260922_164328",
      "created_at": "2026-09-22T11:13:45+00:00",
      "...": "metrics, splits, baselines, plots"
    }
  },
  "loaded": {
    "zone_classifier": {
      "loaded": true,
      "version": "classifier_20260922_163745",
      "name": "PyTorch MLP"
    },
    "radio_estimate": {
      "loaded": true,
      "version": "radio_estimate_20260922_164320",
      "name": "XGBoost (speed tests)"
    },
    "gp_signal": {
      "loaded": true,
      "version": "gp_20260922_164328",
      "name": null
    }
  }
}
```

### `GET /api/ml/models/{run}/artifacts/{filename}`

A plot (`.png`), `metrics.json` or `train.log` from a training run, e.g. `/api/ml/models/gp_20260922_164328/artifacts/rmse_comparison.png`.

**Auth:** signed in

### `GET /api/ml/field-validation`

How the models behave on this installation's own readings.

**Auth:** signed in

Response `200`:

```json
{
  "radio": {
    "readings": 0,
    "note": "No field readings with radio metrics yet (phone-browser probes measure service quality, not radio)."
  },
  "probe": {
    "readings": 50,
    "with_speed_test": 6,
    "agreement": 1.0,
    "matrix": [
      [
        6,
        0,
        0
      ],
      [
        0,
        0,
        0
      ],
      "... 1 more"
    ],
    "measured_classes": {
      "Strong": 22,
      "Dead": 28
    }
  },
  "gp": {
    "cells": 1,
    "needed": 30,
    "note": "Collect speed tests in at least 30 different 10 m cells to validate the predictor on your own data."
  }
}
```

## Administration

All endpoints in this section need the `admin` role.

### `GET /api/admin/users`

All accounts.

**Auth:** admin

Response `200`:

```json
[
  {
    "id": 7,
    "email": "field.user.1790084006@example.com",
    "name": "Field User",
    "role": "user",
    "is_active": true,
    "notify_email": false,
    "is_demo": false,
    "created_at": "2026-09-22T13:33:28.275467Z",
    "last_login_at": null
  },
  "... 6 more"
]
```

### `PATCH /api/admin/users/{user_id}`

Change a user's role (`user`, `engineer`, `admin`) or disable the account (`is_active`). Admins cannot demote or disable themselves.

**Auth:** admin

Request body:

```json
{
  "role": "engineer"
}
```

Response:

```json
{
  "...": "the updated user"
}
```

### `GET /api/admin/settings`

Detection thresholds, notification switches and channel status.

**Auth:** admin

Response `200`:

```json
{
  "settings": [
    {
      "key": "detect_min_readings",
      "value": 4,
      "default": 8,
      "type": "int",
      "min": 2,
      "max": 200,
      "description": "Readings needed in the window before a zone is judged"
    },
    {
      "key": "detect_window_min",
      "value": 10,
      "default": 30,
      "type": "int",
      "min": 1,
      "max": 1440,
      "description": "Sliding window length (minutes)"
    },
    {
      "key": "detect_bad_share",
      "value": 0.7,
      "default": 0.7,
      "type": "float",
      "min": 0.3,
      "max": 1.0,
      "description": "Share of Weak/Dead readings that makes a zone bad"
    },
    "... 10 more"
  ],
  "channels": {
    "telegram": {
      "token": true,
      "chat_id": null,
      "ready": false
    },
    "email": {
      "configured": true,
      "from": "desk@example.com",
      "desk_email": "desk@example.com",
      "ready": false
    },
    "gemini": {
      "configured": false,
      "model": "gemini-3.8-flash"
    },
    "opencellid": {
      "configured": false
    }
  },
  "sample_data": {
    "state": "idle",
    "readings": 0
  },
  "demo_preset": {
    "detect_min_readings": 4,
    "detect_window_min": 10,
    "detect_bad_share": 0.7,
    "detect_persist_min": 2,
    "verify_min_readings": 3,
    "verify_strong_share": 0.7,
    "verify_reopen_share": 0.5
  }
}
```

### `PUT /api/admin/settings`

Change settings; send only the keys to change. Values are checked against their ranges (`422` otherwise).

**Auth:** admin

Request body:

```json
{
  "detect_persist_min": 10,
  "notify_email": true
}
```

Response `200`:

```json
{
  "...": "as GET /api/admin/settings"
}
```

### `POST /api/admin/settings/preset/{name}`

Apply the `demo` (fast) or `standard` detection thresholds.

**Auth:** admin

Response:

```json
{
  "...": "as GET /api/admin/settings"
}
```

### `POST /api/admin/notifications/test`

Send a real test message on every configured channel.

**Auth:** admin

Response:

```json
[
  {
    "channel": "telegram",
    "ok": true,
    "detail": "Sent"
  },
  {
    "channel": "email",
    "ok": true,
    "detail": "Sent to desk@example.com"
  }
]
```

### `POST /api/admin/telegram/link`

Use the chat that most recently messaged the bot for desk notifications.

**Auth:** admin

Response:

```json
{
  "ok": true,
  "detail": "Linked to Desk group",
  "chat_id": "123456789"
}
```

When nobody has messaged the bot yet: `{"ok": false, "detail": "No messages found. Open your bot in Telegram, tap Start and send any message, then try again."}`.

### `GET /api/admin/notifications`

The 50 most recent notifications and their delivery state (`pending`, `sent`, `failed`).

**Auth:** admin

Response `200`:

```json
[]
```

### `POST /api/admin/sample-data`

Load the sample data again (runs in the background).

**Auth:** admin

Response:

```json
{
  "state": "loading"
}
```

### `DELETE /api/admin/sample-data`

Remove the replayed public-dataset readings, their zones and complaints.

**Auth:** admin

Response:

```json
{
  "readings": 15601,
  "complaints": 38
}
```

### `DELETE /api/devices/{device_id}`

Remove a device. Its readings stay, so the map and complaints keep their evidence.

**Auth:** owner or admin
