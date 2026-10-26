import math

import pandas as pd
import pytest

from ml.features import FEATURE_COLUMNS, empty_feature_dict, validate_feature_dict
from ml.preprocessing import (clean_dataframe, extract_label_series, map_to_common_schema,
                              normalize_columns, normalize_label_value)
from tests.conftest import benign_features


def test_schema_has_ten_unique_features():
    assert len(FEATURE_COLUMNS) == 10 and len(set(FEATURE_COLUMNS)) == 10


def test_validate_returns_values_in_schema_order():
    feats = benign_features()
    ordered = validate_feature_dict(dict(reversed(list(feats.items()))))
    assert ordered == [feats[c] for c in FEATURE_COLUMNS]


def test_validate_rejects_missing_feature():
    feats = benign_features()
    del feats["sent_bytes"]
    with pytest.raises(ValueError, match="Missing features"):
        validate_feature_dict(feats)


@pytest.mark.parametrize("bad", ["abc", None, [1]])
def test_validate_rejects_non_numeric(bad):
    feats = benign_features()
    feats["received_bytes"] = bad
    with pytest.raises(ValueError):
        validate_feature_dict(feats)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_validate_rejects_nan_and_inf(bad):
    feats = benign_features()
    feats["sent_packets"] = bad
    with pytest.raises(ValueError, match="NaN/inf"):
        validate_feature_dict(feats)


def test_validate_rejects_negative():
    feats = benign_features()
    feats["sent_packets"] = -1
    with pytest.raises(ValueError, match="Negative"):
        validate_feature_dict(feats)


def test_empty_feature_dict_is_all_zero():
    assert set(empty_feature_dict()) == set(FEATURE_COLUMNS)
    assert all(v == 0.0 for v in empty_feature_dict().values())


def test_normalize_columns_strips_and_snake_cases():
    df = pd.DataFrame(columns=[" Flow Duration", "Total Fwd Packets", "Bwd-Packet/Length"])
    assert list(normalize_columns(df).columns) == ["flow_duration", "total_fwd_packets", "bwd_packet_length"]


@pytest.mark.parametrize("value,expected", [("BENIGN", "BENIGN"), (" benign ", "BENIGN"), ("Normal", "BENIGN"),
                                             ("0", "BENIGN"), ("DDoS", "ATTACK"), ("PortScan", "ATTACK"), (1, "ATTACK")])
def test_label_normalisation(value, expected):
    assert normalize_label_value(value) == expected


def test_extract_label_falls_back_to_last_column():
    df = pd.DataFrame({"a": [1, 2], "b": ["BENIGN", "DDoS"]})
    assert list(extract_label_series(df)) == ["BENIGN", "ATTACK"]


def test_map_to_common_schema_directions_and_rates():
    raw = pd.DataFrame({" Flow Duration": [2_000_000], " Total Fwd Packets": [10], " Total Backward Packets": [4],
                        "Total Length of Fwd Packets": [1000], " Total Length of Bwd Packets": [800], " Label": ["DDoS"]})
    out = map_to_common_schema(clean_dataframe(raw)).iloc[0]
    assert out["sent_packets"] == 10 and out["received_packets"] == 4
    assert out["sent_packets_per_second"] == pytest.approx(5.0)
    assert out["received_bytes_per_second"] == pytest.approx(400.0)
    assert out["average_sent_packet_size"] == pytest.approx(100.0)
    assert out["average_received_packet_size"] == pytest.approx(200.0)
    assert list(map_to_common_schema(raw).columns) == FEATURE_COLUMNS


def test_zero_packets_gives_zero_average_not_nan():
    raw = pd.DataFrame({"flow_duration": [1000], "total_fwd_packets": [0], "total_backward_packets": [0],
                        "total_length_of_fwd_packets": [0], "total_length_of_bwd_packets": [0], "label": ["BENIGN"]})
    out = map_to_common_schema(raw).iloc[0]
    assert out["average_sent_packet_size"] == 0.0 and out["average_received_packet_size"] == 0.0
    assert not out.isna().any()


def test_zero_duration_does_not_divide_by_zero():
    raw = pd.DataFrame({"flow_duration": [0], "total_fwd_packets": [5], "total_backward_packets": [1],
                        "total_length_of_fwd_packets": [500], "total_length_of_bwd_packets": [60], "label": ["BENIGN"]})
    out = map_to_common_schema(raw).iloc[0]
    assert math.isfinite(out["sent_packets_per_second"]) and out["sent_packets_per_second"] > 0


def test_clean_dataframe_replaces_infinities():
    df = pd.DataFrame({"x": [1.0, float("inf")], "y": [2.0, 3.0]})
    assert clean_dataframe(df)["x"].isna().sum() == 1
