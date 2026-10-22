from __future__ import annotations

import csv
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd


SalesRow = Dict[str, object]
SeriesKey = Tuple[str, str]
MarjaneRow = Dict[str, object]


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
        reader = csv.DictReader(handle)
        rows = list(reader)
        headers = set(reader.fieldnames or [])

    sample_schema = {"date", "store_id", "product_id", "sales"}
    marjane_schema = {"ticket", "date", "magasin", "sku", "produit", "categorie", "quantite", "prix"}

    if sample_schema.issubset(headers):
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

    if marjane_schema.issubset(headers):
        return _load_marjane_sales(rows)

    raise ValueError(
        "Schema CSV non supporté. Colonnes attendues: "
        "['date','store_id','product_id','sales',...] ou "
        "['ticket','date','magasin','sku','produit','categorie','quantite','prix']."
    )


def _clean_marjane_rows(rows: List[MarjaneRow]) -> pd.DataFrame:
    df = pd.DataFrame(rows).copy()
    if df.empty:
        return df

    df["produit"] = df["produit"].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
    df["categorie"] = df["categorie"].astype(str).str.strip().str.lower()
    df = df.drop_duplicates()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce")
    df["prix"] = pd.to_numeric(df["prix"], errors="coerce")

    df = df[(df["quantite"].isna()) | (df["quantite"] > 0)]
    df = df[df["prix"] > 0]

    df["quantite"] = df.groupby(["sku", "magasin"])["quantite"].transform(lambda s: s.fillna(s.median()))
    df["quantite"] = df["quantite"].fillna(df["quantite"].median())
    df = df.dropna(subset=["quantite"])

    q1 = df["quantite"].quantile(0.25)
    q3 = df["quantite"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 3 * iqr
    df = df[df["quantite"] <= upper_bound]

    df = df.reset_index(drop=True)
    return df


def _load_marjane_sales(rows: List[MarjaneRow]) -> List[SalesRow]:
    cleaned = _clean_marjane_rows(rows)
    if cleaned.empty:
        return []

    grouped = (
        cleaned.groupby(["date", "magasin", "sku"], as_index=False)
        .agg(sales=("quantite", "sum"), price=("prix", "mean"))
        .sort_values(["magasin", "sku", "date"])
    )

    parsed: List[SalesRow] = []
    for row in grouped.to_dict(orient="records"):
        parsed.append(
            {
                "date": row["date"].date(),
                "store_id": str(row["magasin"]),
                "product_id": str(row["sku"]),
                "sales": float(row["sales"]),
                "price": float(row["price"]),
                "promotion": 0,
                "event": 0,
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
