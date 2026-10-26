"""
demand_forecasting.py
-----------------------
Turns transaction-level rows (one row per item sold) into daily
product-level demand: how many units of `article_id` were sold on
each `t_dat`.

This aggregated table is the "modeling table" that everything else
(feature engineering, XGBoost, domain adaptation) is built on top of.

IMPORTANT (data leakage):
We aggregate strictly by (date, article_id). We never use information
from a future date to compute a past day's demand -- aggregation by
definition only summarizes rows that occurred on that exact date.
"""

from __future__ import annotations

import pandas as pd


# Attributes we carry along at the product level (first non-null value
# per article_id) so the aggregated table stays informative without
# needing a second merge.
PRODUCT_ATTR_CANDIDATES = [
    "product_type_name",
    "product_group_name",
    "colour_group_name",
    "department_name",
    "section_name",
    "garment_group_name",
    "index_name",
    "index_group_name",
]


def aggregate_daily_demand(merged: pd.DataFrame) -> pd.DataFrame:
    """
    WHAT: Aggregates transaction rows into daily demand per article.
    WHY:  Our target variable is "how many units sold", which only
          exists after aggregation -- raw transactions are one-row-per-sale.
    HOW:  Group by (t_dat, article_id) and count rows = units sold.
          Price is averaged (the typical selling price that day).
          sales_channel_id: take the most frequent channel that day
          (a product can theoretically sell on both channels the same day).

    Returns a DataFrame with columns:
        t_dat, article_id, demand, price, sales_channel_id,
        <product attribute columns...>
    """
    df = merged.copy()

    present_attrs = [c for c in PRODUCT_ATTR_CANDIDATES if c in df.columns]

    def _most_frequent(s: pd.Series):
        mode = s.mode()
        return mode.iloc[0] if not mode.empty else s.iloc[0]

    named_aggs = {
        "demand": ("article_id", "size"),
        "price": ("price", "mean"),
    }
    if "sales_channel_id" in df.columns:
        named_aggs["sales_channel_id"] = ("sales_channel_id", _most_frequent)

    grouped = (
        df.groupby(["t_dat", "article_id"])
        .agg(**named_aggs)
        .reset_index()
    )

    if present_attrs:
        # First non-null value per article_id (product attributes don't
        # change day to day, so this is safe and avoids re-merging).
        attr_lookup = df.groupby("article_id")[present_attrs].first().reset_index()
        grouped = grouped.merge(attr_lookup, on="article_id", how="left")

    grouped = grouped.sort_values(["article_id", "t_dat"]).reset_index(drop=True)
    return grouped


def fill_missing_dates_per_article(
    daily_demand: pd.DataFrame, min_transactions_per_article: int = 5
) -> pd.DataFrame:
    """
    WHAT: For each article, fills in the days it *didn't* sell with
          demand = 0, between that article's first and last observed
          sale date.
    WHY:  Lag/rolling features (lag_7, rolling_mean_28, etc.) need a
          continuous daily series per product -- otherwise "lag_1" would
          quietly jump across gaps of many days.
    HOW:  Reindex each article's sub-series onto a full daily date range.

    Articles with very few transactions (< min_transactions_per_article)
    are excluded from this step since a continuous daily series isn't
    meaningful for them, and are kept as-is for exploration purposes only.
    """
    filled_frames = []

    for article_id, group in daily_demand.groupby("article_id"):
        if len(group) < min_transactions_per_article:
            continue

        full_range = pd.date_range(group["t_dat"].min(), group["t_dat"].max(), freq="D")
        group = group.set_index("t_dat").reindex(full_range)
        group["article_id"] = article_id
        group["demand"] = group["demand"].fillna(0)

        # Forward-fill product attributes / last known price (these are
        # static or slow-changing, forward-filling is safe here since
        # we're only filling gaps, not predicting into the future).
        group = group.ffill().bfill()
        group.index.name = "t_dat"
        filled_frames.append(group.reset_index())

    if not filled_frames:
        return daily_demand

    result = pd.concat(filled_frames, ignore_index=True)
    result = result.sort_values(["article_id", "t_dat"]).reset_index(drop=True)
    return result
