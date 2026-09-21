"""CSV/Excel transaction import: validate, clean, auto-categorize, preview, commit."""
from __future__ import annotations

import pandas as pd
from datetime import datetime

from ml.expense_classifier import predict_category
from services.transaction_service import add_transaction, DEFAULT_CATEGORIES

REQUIRED_COLUMNS = {"date", "description", "amount", "category", "type"}


def load_and_validate(file) -> tuple[pd.DataFrame | None, list[str]]:
    """Load an uploaded CSV/Excel file-like object. Returns (dataframe, errors).
    dataframe is None if the file could not be parsed at all."""
    errors = []
    try:
        name = getattr(file, "name", "")
        if name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
    except Exception as e:
        return None, [f"Could not read the file: {e}"]

    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        errors.append(f"Missing required column(s): {', '.join(sorted(missing))}")
        return None, errors

    return df, errors


def clean_and_prepare(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Clean rows, auto-categorize where category is missing/unknown, and
    report row-level problems without crashing on any single bad row."""
    warnings = []
    df = df.copy()

    def parse_row(row):
        try:
            txn_date = pd.to_datetime(row["date"]).date()
        except Exception:
            return None
        try:
            amount = float(row["amount"])
        except (TypeError, ValueError):
            return None
        if amount <= 0:
            return None
        description = str(row["description"]).strip() if not pd.isna(row["description"]) else ""
        if not description:
            return None
        txn_type = str(row["type"]).strip().lower()
        if txn_type not in ("income", "expense"):
            txn_type = "expense"
        category = str(row["category"]).strip() if not pd.isna(row.get("category")) else ""
        if not category or category.lower() == "nan":
            category = predict_category(description)
        return {"date": txn_date, "description": description, "amount": amount,
                "category": category, "transaction_type": txn_type}

    cleaned_rows = []
    for idx, row in df.iterrows():
        parsed = parse_row(row)
        if parsed is None:
            warnings.append(f"Row {idx + 2}: skipped (invalid date, amount, or missing description).")
        else:
            cleaned_rows.append(parsed)

    return pd.DataFrame(cleaned_rows), warnings


def commit_import(user_id: int, cleaned_df: pd.DataFrame) -> int:
    """Insert all cleaned rows as transactions for the given user. Returns count inserted."""
    count = 0
    for _, row in cleaned_df.iterrows():
        add_transaction(
            user_id=user_id, txn_date=row["date"], description=row["description"],
            category=row["category"], amount=row["amount"], transaction_type=row["transaction_type"],
        )
        count += 1
    return count
