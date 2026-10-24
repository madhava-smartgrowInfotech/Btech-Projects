"""SentinelFlow CICIDS2017 preprocessing utilities."""

import numpy as np
import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-/]+", "_", regex=True)
        .str.replace(r"__+", "_", regex=True)
        .str.strip("_")
    )
    return df


def _pick(df: pd.DataFrame, candidates: list) -> str | None:
    for cand in candidates:
        if cand in df.columns:
            return cand
    return None


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.strip().replace(["", "nan", "None", "inf", "-inf"], np.nan), errors="coerce")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    df = df.replace([np.inf, -np.inf], np.nan)
    # Drop rows that are entirely empty
    df = df.dropna(how="all")
    return df


def normalize_label_value(value) -> str:
    text = str(value).strip().lower()
    if text in ("benign", "normal", "0", "0.0"):
        return "BENIGN"
    return "ATTACK"


def extract_label_series(df: pd.DataFrame) -> pd.Series | None:
    label_col = _pick(df, ["label", "class", "attack", "target"])
    if label_col is None:
        # last column fallback when header is missing
        label_col = df.columns[-1]
    return df[label_col].apply(normalize_label_value)


def map_to_common_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Map CICIDS2017-style flow columns into the SentinelFlow common schema.

    Mapping (documented):
      sent_packets     <- forward packet count
      sent_bytes       <- forward byte total
      received_packets <- backward packet count
      received_bytes   <- backward byte total
      duration         <- flow duration (microseconds preferred)
      rates            <- counts / duration_seconds
      averages         <- bytes / packets
    """
    df = normalize_columns(df)

    fwd_pkt_col = _pick(df, [
        "total_fwd_packets", "fwd_packets", "total_fwd_packet",
        "fwd_packet_count", "total_length_of_fwd_packets_count",
    ])
    bwd_pkt_col = _pick(df, [
        "total_backward_packets", "total_bwd_packets", "bwd_packets",
        "total_bwd_packet", "bwd_packet_count",
    ])
    fwd_len_col = _pick(df, [
        "total_length_of_fwd_packets", "total_length_of_fwd_packet",
        "fwd_bytes", "total_fwd_bytes", "fwd_total_bytes",
        "fwd_segment_size_total",
    ])
    bwd_len_col = _pick(df, [
        "total_length_of_bwd_packets", "total_length_of_bwd_packet",
        "bwd_bytes", "total_bwd_bytes", "bwd_total_bytes",
    ])
    dur_col = _pick(df, [
        "flow_duration", "duration", "flow_duration_us",
        "flow_duration_ms", "flow_duration_s",
    ])
    dur_unit = "us"
    if dur_col and dur_col.endswith("_ms"):
        dur_unit = "ms"
    elif dur_col and dur_col.endswith("_s"):
        dur_unit = "s"

    n = len(df)
    if fwd_pkt_col:
        sent_packets = _to_numeric(df[fwd_pkt_col]).fillna(0).clip(lower=0)
    else:
        sent_packets = pd.Series(np.zeros(n), index=df.index)
    if bwd_pkt_col:
        received_packets = _to_numeric(df[bwd_pkt_col]).fillna(0).clip(lower=0)
    else:
        received_packets = pd.Series(np.zeros(n), index=df.index)
    if fwd_len_col:
        sent_bytes = _to_numeric(df[fwd_len_col]).fillna(0).clip(lower=0)
    else:
        sent_bytes = sent_packets * 600.0
    if bwd_len_col:
        received_bytes = _to_numeric(df[bwd_len_col]).fillna(0).clip(lower=0)
    else:
        received_bytes = received_packets * 600.0

    if dur_col:
        raw_dur = _to_numeric(df[dur_col]).fillna(0).clip(lower=0)
        if dur_unit == "us":
            duration_s = raw_dur / 1_000_000.0
        elif dur_unit == "ms":
            duration_s = raw_dur / 1000.0
        else:
            duration_s = raw_dur
    else:
        duration_s = pd.Series(np.full(n, 1.0), index=df.index)
    duration_s = duration_s.replace(0, 1e-6).fillna(1e-6).clip(lower=1e-6, upper=3600.0)

    out = pd.DataFrame(index=df.index)
    out["received_packets"] = received_packets
    out["received_bytes"] = received_bytes
    out["received_packets_per_second"] = received_packets / duration_s
    out["received_bytes_per_second"] = received_bytes / duration_s
    out["average_received_packet_size"] = np.where(
        received_packets.values > 0,
        received_bytes.values / np.maximum(received_packets.values, 1),
        0.0,
    )
    out["sent_packets"] = sent_packets
    out["sent_bytes"] = sent_bytes
    out["sent_packets_per_second"] = sent_packets / duration_s
    out["sent_bytes_per_second"] = sent_bytes / duration_s
    out["average_sent_packet_size"] = np.where(
        sent_packets.values > 0,
        sent_bytes.values / np.maximum(sent_packets.values, 1),
        0.0,
    )
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
