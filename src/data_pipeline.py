from __future__ import annotations

import csv
from datetime import datetime
from typing import Dict, List, Tuple


SalesRow = Dict[str, object]
SeriesKey = Tuple[str, str]


def _parse_date(raw: str) -> datetime.date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _to_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    value = str(value).strip()
    if value == "":
        return default
    return float(value)


def _to_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    value = str(value).strip()
    if value == "":
        return default
    return int(float(value))


def load_sales_csv(path: str) -> List[SalesRow]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    parsed: List[SalesRow] = []
    for row in rows:
        parsed.append(
            {
                "date": _parse_date(row["date"]),
                "store_id": row["store_id"],
                "product_id": row["product_id"],
                "sales": _to_float(row.get("sales"), default=0.0),
                "price": _to_float(row.get("price"), default=0.0),
                "promotion": _to_int(row.get("promotion"), default=0),
                "event": _to_int(row.get("event"), default=0),
            }
        )
    return parsed


def clean_sales_data(rows: List[SalesRow]) -> List[SalesRow]:
    cleaned: List[SalesRow] = []
    seen = set()
    last_price: Dict[SeriesKey, float] = {}

    sorted_rows = sorted(rows, key=lambda r: (r["store_id"], r["product_id"], r["date"]))
    for row in sorted_rows:
        key = (str(row["date"]), row["store_id"], row["product_id"])
        if key in seen:
            continue
        seen.add(key)

        series_key = (row["store_id"], row["product_id"])
        sales = float(row.get("sales", 0.0) or 0.0)
        price = float(row.get("price", 0.0) or 0.0)
        if price <= 0:
            price = last_price.get(series_key, 0.0)
        last_price[series_key] = price

        cleaned.append(
            {
                "date": row["date"],
                "store_id": row["store_id"],
                "product_id": row["product_id"],
                "sales": max(0.0, sales),
                "price": max(0.0, price),
                "promotion": int(row.get("promotion", 0) or 0),
                "event": int(row.get("event", 0) or 0),
            }
        )
    return cleaned


def group_by_series(rows: List[SalesRow]) -> Dict[SeriesKey, List[SalesRow]]:
    grouped: Dict[SeriesKey, List[SalesRow]] = {}
    for row in sorted(rows, key=lambda r: (r["store_id"], r["product_id"], r["date"])):
        key = (row["store_id"], row["product_id"])
        grouped.setdefault(key, []).append(row)
    return grouped
