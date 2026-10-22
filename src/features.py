from __future__ import annotations

from typing import Dict, List


def moving_average(values: List[float], window: int) -> float:
    if not values:
        return 0.0
    relevant = values[-window:]
    return sum(relevant) / len(relevant)


def build_supervised_rows(series_rows: List[dict], max_lag: int = 7) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    sales = [float(r["sales"]) for r in series_rows]
    for idx in range(max_lag, len(series_rows)):
        current = series_rows[idx]
        history = sales[:idx]
        feature_row: Dict[str, object] = {
            "target": sales[idx],
            "price": float(current["price"]),
            "promotion": int(current["promotion"]),
            "event": int(current["event"]),
            "day_of_week": current["date"].weekday(),
            "month": current["date"].month,
            "is_weekend": 1 if current["date"].weekday() >= 5 else 0,
            "ma_7": moving_average(history, 7),
            "ma_14": moving_average(history, 14),
        }
        for lag in range(1, max_lag + 1):
            feature_row[f"lag_{lag}"] = sales[idx - lag]
        rows.append(feature_row)
    return rows


FEATURE_ORDER = [
    "price",
    "promotion",
    "event",
    "day_of_week",
    "month",
    "is_weekend",
    "ma_7",
    "ma_14",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_4",
    "lag_5",
    "lag_6",
    "lag_7",
]


def vectorize_features(row: Dict[str, object]) -> List[float]:
    return [float(row[name]) for name in FEATURE_ORDER]
