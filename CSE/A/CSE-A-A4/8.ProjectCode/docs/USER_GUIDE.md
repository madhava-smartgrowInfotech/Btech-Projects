# User Guide — SecurePay AI

## Dashboard
- **Live Transaction Monitoring** chart refreshes every 2 sec.
- **Recent High-Risk Alerts**: auto-generated from fraud cases.
- **Recent Transactions**: 6-row live feed (Time, Amount, Merchant, Type, Status, Risk).

## Verify Transaction (Single)
1. Fill Amount, Merchant Category, Channel, Card Present, Country Match, Time, 3 history scores.
2. Click **Run Fraud Check**.
3. Read result: color (green=approve, red=fraud), Risk Score %, Decision.

**Demo values:**
- *Legit demo:* Amount 80, Grocery, Chip, Yes, Yes → LOW (Approve)
- *Fraud demo:* Amount 1200, Online, Online, No, No → HIGH (Decline)

## Bulk Verification
1. Go to **Bulk Verification**.
2. Browse → select `data/sample_batch.csv` (20 rows, has `Class`).
3. **Upload & Analyze** → see badges (20 transactions, 8 flagged) + metrics + preview.
4. **Download Results** → `batch_predictions.csv` with `Predicted_Class, Fraud_Probability, Risk`.

For your own CSV, keep columns `Amount,Time,Merchant_Category,Transaction_Type,Card_Present,Country_Match,V1..V22` (Class optional).

## Analytics
- **Fraud Trend (7 days)**: Attempts vs Blocked.
- **Risk by Merchant**: Doughnut (Online highest).
- **Fraud by Hour**: Bar (peak 16h).
- **System Performance**: Detection 98.7%, Precision 94%, Response 47ms.

No training UI is exposed — product is ready to use. For retraining (advanced), see README §13 and `seed_models.py`.

