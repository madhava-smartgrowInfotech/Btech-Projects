# Field readings

Readings measured with this installation's own devices: the phone field probe and ESP32 nodes. The public-dataset sample and the simulator are not included. The files are created by a script, so they always follow the same anonymisation rules.

| File | Contents |
|---|---|
| `field_readings.csv.gz` | One row per reading. The columns are listed in `summary.json`. |
| `summary.json` | Counts by source, operator and class; date range; number of zones. |

## Creating or updating the sample

1. Collect readings.
   - **Phone:** open the field probe on the phone with mobile data on and Wi-Fi off. Walk or ride through the area for 15–30 minutes with the screen on.
   - **ESP32:** leave the node running.
2. Export:

   ```
   venv\Scripts\python scripts\export_field_sample.py
   ```

   The script refuses to write fewer than 50 readings (`--min` changes the limit). Readings over Wi-Fi, and readings taken from the PC's own network, are left out unless you add `--all`.
3. Commit `data/field/`.

## Anonymisation

- Positions are rounded to 3 decimals (about 110 m), and the zone is recomputed from the rounded position.
- Times are rounded down to the minute.
- Devices appear as `phone-1`, `node-1` and so on, numbered in order of first appearance. No account or device IDs are kept.
- Reading IDs, receipt times, network numbers (ASN) and serving-cell identifiers are dropped.

The same database always produces the same files: rows are sorted, and the gzip header has no timestamp.
