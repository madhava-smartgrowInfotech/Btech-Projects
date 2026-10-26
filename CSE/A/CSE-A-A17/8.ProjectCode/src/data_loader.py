"""
data_loader.py
---------------
Responsible for loading and validating the three H&M CSV files that the
user uploads through the Streamlit interface:

    1. customers.csv
    2. articles.csv
    3. transactions_train.csv

We never hard-code local file paths -- everything comes from an
`st.file_uploader` object (a file-like object) that Streamlit gives us.

We also do lightweight "does this look like the right file?" validation
so beginners get a friendly error message instead of a cryptic KeyError
three steps later in the pipeline.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


# ----------------------------------------------------------------------
# Required columns for each file. These are the columns the rest of the
# pipeline depends on. Everything else in the H&M dataset is optional
# and will be used opportunistically if present.
# ----------------------------------------------------------------------
REQUIRED_TRANSACTION_COLUMNS = ["t_dat", "customer_id", "article_id", "price"]
REQUIRED_ARTICLE_COLUMNS = ["article_id", "prod_name"]
REQUIRED_CUSTOMER_COLUMNS = ["customer_id"]


class DataValidationError(Exception):
    """Raised when an uploaded file is missing required columns."""


def validate_columns(df: pd.DataFrame, required_columns: list[str], file_label: str) -> None:
    """
    WHAT: Checks that `df` contains every column in `required_columns`.
    WHY:  Prevents confusing downstream crashes -- fail fast, fail clearly.
    HOW:  Simple set-difference check.
    """
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"The uploaded {file_label} is missing required column(s): "
            f"{', '.join(missing)}. Please check you uploaded the correct file."
        )


@st.cache_data(show_spinner="Loading transactions...")
def load_transactions(uploaded_file, sample_rows: int | None = None) -> pd.DataFrame:
    """
    Load transactions_train.csv (or a similarly-shaped file).

    Parameters
    ----------
    uploaded_file : Streamlit UploadedFile
    sample_rows : int, optional
        If provided, only read this many rows (for experimentation with
        the notoriously large H&M transactions file).
    """
    if uploaded_file is None:
        return pd.DataFrame()

    df = pd.read_csv(uploaded_file, nrows=sample_rows)
    validate_columns(df, REQUIRED_TRANSACTION_COLUMNS, "transaction dataset")
    return df


@st.cache_data(show_spinner="Loading articles...")
def load_articles(uploaded_file) -> pd.DataFrame:
    """Load articles.csv (product catalogue / attributes)."""
    if uploaded_file is None:
        return pd.DataFrame()

    df = pd.read_csv(uploaded_file)
    validate_columns(df, REQUIRED_ARTICLE_COLUMNS, "article dataset")
    return df


@st.cache_data(show_spinner="Loading customers...")
def load_customers(uploaded_file) -> pd.DataFrame:
    """Load customers.csv (optional but useful for demographic features)."""
    if uploaded_file is None:
        return pd.DataFrame()

    df = pd.read_csv(uploaded_file)
    validate_columns(df, REQUIRED_CUSTOMER_COLUMNS, "customer dataset")
    return df


def friendly_upload_checklist(transactions_ok: bool, articles_ok: bool, customers_ok: bool) -> None:
    """
    WHAT: Renders a small checklist in the sidebar/page showing what has
          been uploaded so far.
    WHY:  Beginners appreciate clear visual feedback on required inputs.
    """
    st.markdown("**Upload status**")
    st.write("✅ Transactions" if transactions_ok else "⬜ Transactions (required)")
    st.write("✅ Articles" if articles_ok else "⬜ Articles (required)")
    st.write("✅ Customers" if customers_ok else "⬜ Customers (optional)")
