# Datasets

SignalScout uses two public datasets to train and check its models, plus the readings your own phones and sensor nodes collect. Both public datasets are small, so they are committed in full under `data/raw/`. No download is needed after cloning.

| Dataset | Used for | Licence | Size | Committed |
|---|---|---|---|---|
| 4G LTE Speed Dataset (Cork) | Zone classifier, radio-condition estimate, better-signal predictor, sample data | CC BY-SA 4.0 | 19.5 MB, 135 CSV files | complete, `data/raw/lte_speed/` |
| Cellular Network Analysis Dataset (Patna) | Consistency check of the zone classifier on another region | CC0 1.0 | 3.1 MB, 1 CSV file | complete, `data/raw/cellular_network_analysis/` |
| Own field readings | Field validation of the models on this installation | yours | grows with use | anonymised sample in `data/field/` |

`data/raw/MANIFEST.json` records the source, licence, size and SHA-256 hash of every file. `scripts/download_data.py --verify` checks the files against it.

---

## 1. 4G LTE Speed Dataset (Cork)

- **Source:** https://www.kaggle.com/datasets/aeryss/lte-dataset
- **Licence:** CC BY-SA 4.0. Keep the attribution when you share derived data.
- **Content:** 135 drive-test traces recorded in Cork, Ireland, between November 2017 and February 2018 on two mobile operators. Each trace was recorded on one mode of transport: bus (16 traces), car (53), pedestrian (31), static (15) or train (20). There is one row per second.

| Column | Meaning |
|---|---|
| `Timestamp` | Time of the sample |
| `Longitude`, `Latitude` | GPS position |
| `Speed` | Device speed (km/h) |
| `Operatorname` | Operator A or Operator B (anonymised in the source) |
| `CellID` | Serving cell |
| `NetworkMode` | LTE, HSPA+, UMTS, EDGE and so on |
| `RSRP`, `RSRQ`, `SNR`, `CQI` | LTE radio metrics |
| `RSSI` | Received signal strength (all technologies) |
| `DL_bitrate`, `UL_bitrate` | Measured download / upload throughput (kbit/s) |
| `State` | Download (D) or idle (I) |
| `NRxRSRP`, `NRxRSRQ` | Strongest neighbour cell |
| `ServingCell_Lon`, `ServingCell_Lat`, `ServingCell_Distance` | Serving cell position and distance to it (m) |

### Cleaning (`ml/prepare_data.py`)

The report `data/processed/prep_report.json` records the row counts after each step.

| Step | Rows |
|---|---|
| Raw rows from 135 traces | 174,523 |
| Valid time and position | 174,523 |
| Only Operator A and Operator B | 174,243 |
| Level sentinels (such as -200 dBm) set to missing | 69 values |
| Rows that cannot be labelled (no usable metric) dropped | 174,233 |
| Exact duplicates dropped | **173,366** |

Other cleaning rules:

- Values outside the 3GPP reporting range for their technology family become missing. The ranges are in `backend/app/ml/signal_ranges.py`.
- `NetworkMode` is mapped to a family: `lte_nr` (LTE and 5G NR), `3g` (UMTS/HSPA) or `2g` (GSM/EDGE).

The family shares are 69.4% LTE, 29.9% 3G and 0.7% 2G.

### Labels

Each row gets **Strong**, **Weak** or **Dead** from documented 3GPP-style ranges. If a row has several metrics, the worst one decides the label.

| Family | Metric | Strong | Weak | Dead |
|---|---|---|---|---|
| LTE / NR | RSRP | ≥ -100 dBm | -115 to -100 dBm | < -115 dBm |
| LTE / NR | RSRQ | ≥ -15 dB | < -15 dB | - |
| LTE / NR | SINR | ≥ 5 dB | -3 to 5 dB | < -3 dB |
| 3G | RSCP | ≥ -95 dBm | -105 to -95 dBm | < -105 dBm |
| 3G | Ec/No | ≥ -14 dB | < -14 dB | - |
| 2G | RSSI | ≥ -85 dBm | -100 to -85 dBm | < -100 dBm |

The resulting class shares are Strong 53.9%, Weak 32.9% and Dead 13.2%.

### Splits

Splits are always made **by trace file**, and stratified by mode of transport, so one trip never appears in both training and test data:

- Test: 20 traces (81,859 rows across the four device profiles).
- Validation: 20 traces.
- Training: 95 traces.
- Model selection uses 5-fold cross-validation on the training traces, grouped by trace.

---

## 2. Cellular Network Analysis Dataset (Patna)

- **Source:** https://www.kaggle.com/datasets/suraj520/cellular-network-analysis-dataset
- **Licence:** CC0 1.0 (public domain)
- **Content:** 16,829 measurements from 20 localities in Patna, India, recorded between May and June 2023, with 3G, 4G, LTE and 5G rows.

| Column | Meaning |
|---|---|
| `Timestamp`, `Latitude`, `Longitude`, `Locality` | When and where |
| `Network Type` | 3G / 4G / LTE / 5G |
| `Signal Strength (dBm)` | Signal level |
| `Data Throughput (Mbps)`, `Latency (ms)` | Service measurements |
| `BB60C / srsRAN / BladeRF Measurement (dBm)` | Readings from three measurement radios |

**Cleaning:**

- All 16,829 rows are valid.
- `Signal Quality (%)` is 0 in every row, so it is not used.
- The BB60C, srsRAN and BladeRF columns are 0 for 3G rows, so they are not used either.

**Use:** this dataset has only a signal level, and almost every row is Strong (95.7%). So it cannot train a three-class model, but it serves as a **consistency check**: the zone classifier sees level-only input from another region and unseen network-type strings. The classifier agrees with the documented ranges on 100% of rows, for all network types. This shows consistent behaviour; it is not an accuracy measurement.

---

## 3. Sample data shown in the app

On first start, the backend replays 16 of the longest Cork traces (8 per operator) through the same ingestion pipeline a phone uses. Only the city area is used, every second reading is kept, and timestamps are moved forward by whole weeks so the data looks recent. That gives 15,601 readings in about 90 zones.

- Sample readings, zones and complaints are tagged **Sample** everywhere in the interface.
- Sample complaints never send notifications.
- An admin can remove the sample, or load it again, under **Settings → Sample data**.
- Set `SEED_SAMPLE_DATA=false` in `.env` to start without it.

The sample is generated from the committed dataset by `backend/app/services/sample_data.py`, which is deterministic, so every installation gets the same data.

---

## 4. Own field readings (`data/field/`)

Readings from your phone probe and ESP32 nodes are stored in the database (`data/app.db`, not committed). To share them, export an anonymised sample:

```
venv\Scripts\python scripts\export_field_sample.py
```

The export:

- rounds positions to about 110 m and times down to the minute;
- replaces device and account identifiers with pseudonyms;
- drops IDs, network numbers and serving-cell identifiers.

`data/field/README.md` describes the columns and the rules. The **Model performance → Field validation** page in the app uses the same readings. It shows how the better-signal predictor and the speed-based estimate behave on your own data.

---

## 5. Downloading the datasets again

`setup.bat` runs `scripts/download_data.py`, which verifies the committed files and downloads any that are missing or damaged.

```
venv\Scripts\python scripts\download_data.py            # verify, download what is missing
venv\Scripts\python scripts\download_data.py --verify   # only check the files against MANIFEST.json
venv\Scripts\python scripts\download_data.py --force    # download everything again
```

Both datasets download anonymously. If Kaggle ever requires signing in, the script falls back to `kagglehub` with your API token. To create one:

1. Sign in at https://www.kaggle.com (a free account is enough).
2. Click your profile picture → **Settings**.
3. Under **API**, click **Create New Token**. A file `kaggle.json` is downloaded.
4. Open it in Notepad. Copy `username` into `KAGGLE_USERNAME` and `key` into `KAGGLE_KEY` in `.env`.
5. Run `venv\Scripts\python scripts\download_data.py` again.

After a download, `ml/prepare_data.py` rebuilds `data/processed/`. `ml/train_all.py` runs it automatically.
