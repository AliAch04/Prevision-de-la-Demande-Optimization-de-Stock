from __future__ import annotations

import csv
from datetime import datetime
from statistics import median
from typing import Dict, List, Tuple


SalesRow = Dict[str, object]
SeriesKey = Tuple[str, str]
MarjaneRow = Dict[str, object]


def _parse_date(raw: str) -> datetime.date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


def _parse_flexible_date(raw: str | None) -> datetime.date | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if text == "":
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _to_float(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    value = str(value).strip()
    if value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    value = str(value).strip()
    if value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _quantile(sorted_values: List[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lower = int(pos)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = pos - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


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


def _load_marjane_sales(rows: List[MarjaneRow]) -> List[SalesRow]:
    prepared: List[dict] = []
    seen = set()
    for raw in rows:
        produit = " ".join(str(raw.get("produit", "")).strip().lower().split())
        categorie = str(raw.get("categorie", "")).strip().lower()
        date_value = _parse_flexible_date(raw.get("date"))
        quantite_text = raw.get("quantite")
        prix_text = raw.get("prix")
        quantite = _to_float(quantite_text, default=float("nan")) if str(quantite_text).strip() != "" else float("nan")
        prix = _to_float(prix_text, default=float("nan")) if str(prix_text).strip() != "" else float("nan")

        dedup_key = (
            raw.get("ticket"),
            raw.get("date"),
            raw.get("magasin"),
            raw.get("sku"),
            produit,
            categorie,
            raw.get("quantite"),
            raw.get("prix"),
        )
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        if date_value is None:
            continue
        if not (prix > 0):
            continue
        if not ((quantite != quantite) or (quantite > 0)):  # NaN or > 0
            continue

        prepared.append(
            {
                "date": date_value,
                "magasin": str(raw.get("magasin", "")).strip(),
                "sku": str(raw.get("sku", "")).strip(),
                "quantite": quantite,
                "prix": prix,
            }
        )

    if not prepared:
        return []

    group_quantities: Dict[Tuple[str, str], List[float]] = {}
    all_quantities: List[float] = []
    for row in prepared:
        qty = row["quantite"]
        if qty == qty:  # not NaN
            key = (row["sku"], row["magasin"])
            group_quantities.setdefault(key, []).append(qty)
            all_quantities.append(qty)

    default_qty = median(all_quantities) if all_quantities else 1.0
    for row in prepared:
        if row["quantite"] == row["quantite"]:
            continue
        key = (row["sku"], row["magasin"])
        if key in group_quantities and group_quantities[key]:
            row["quantite"] = median(group_quantities[key])
        else:
            row["quantite"] = default_qty

    cleaned_quantities = sorted([float(r["quantite"]) for r in prepared])
    q1 = _quantile(cleaned_quantities, 0.25)
    q3 = _quantile(cleaned_quantities, 0.75)
    iqr = q3 - q1
    upper_bound = q3 + 3 * iqr
    filtered = [r for r in prepared if float(r["quantite"]) <= upper_bound]

    aggregated: Dict[Tuple[datetime.date, str, str], Dict[str, float]] = {}
    for row in filtered:
        key = (row["date"], row["magasin"], row["sku"])
        bucket = aggregated.setdefault(key, {"sales": 0.0, "price_sum": 0.0, "price_count": 0.0})
        bucket["sales"] += float(row["quantite"])
        bucket["price_sum"] += float(row["prix"])
        bucket["price_count"] += 1.0

    parsed: List[SalesRow] = []
    for (date_value, magasin, sku), metrics in sorted(aggregated.items(), key=lambda item: (item[0][1], item[0][2], item[0][0])):
        mean_price = metrics["price_sum"] / metrics["price_count"] if metrics["price_count"] else 0.0
        parsed.append(
            {
                "date": date_value,
                "store_id": magasin,
                "product_id": sku,
                "sales": float(metrics["sales"]),
                "price": float(mean_price),
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
