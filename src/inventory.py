from __future__ import annotations

import math
from typing import Dict, List


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def recommend_order_quantity(
    forecast: List[float],
    lead_time_days: int = 7,
    service_factor: float = 1.65,
    current_stock: float = 0.0,
    in_transit: float = 0.0,
) -> Dict[str, float]:
    if not forecast:
        return {
            "forecast_demand": 0.0,
            "safety_stock": 0.0,
            "reorder_point": 0.0,
            "order_quantity": 0.0,
        }

    avg_daily_demand = sum(forecast) / len(forecast)
    demand_std = _std(forecast)
    safety_stock = service_factor * demand_std * math.sqrt(max(1, lead_time_days))
    reorder_point = avg_daily_demand * lead_time_days + safety_stock
    stock_position = current_stock + in_transit
    order_quantity = max(0.0, math.ceil(reorder_point - stock_position))

    return {
        "forecast_demand": round(sum(forecast), 2),
        "safety_stock": round(safety_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "order_quantity": float(order_quantity),
    }
