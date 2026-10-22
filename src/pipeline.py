from __future__ import annotations

import argparse
import json
from datetime import timedelta
from typing import Dict, List, Tuple

from data_pipeline import clean_sales_data, group_by_series, load_sales_csv
from features import FEATURE_ORDER, build_supervised_rows, vectorize_features
from forecast import BaselineForecaster, LinearRegressionGD, mae, rmse
from inventory import recommend_order_quantity


def _recursive_ml_forecast(
    train_rows: List[dict],
    horizon: int,
    model: LinearRegressionGD,
) -> List[float]:
    history_sales = [float(r["sales"]) for r in train_rows]
    last_date = train_rows[-1]["date"]
    last_price = float(train_rows[-1]["price"])
    predictions: List[float] = []

    for step in range(1, horizon + 1):
        next_date = last_date + timedelta(days=step)
        lagged = (history_sales + predictions)[-(7):]
        lagged = list(reversed(lagged))
        while len(lagged) < 7:
            lagged.append(0.0)

        feature_row = {
            "price": last_price,
            "promotion": 0,
            "event": 0,
            "day_of_week": next_date.weekday(),
            "month": next_date.month,
            "is_weekend": 1 if next_date.weekday() >= 5 else 0,
            "ma_7": sum((history_sales + predictions)[-7:]) / min(7, len(history_sales + predictions)),
            "ma_14": sum((history_sales + predictions)[-14:]) / min(14, len(history_sales + predictions)),
        }
        for idx in range(1, 8):
            feature_row[f"lag_{idx}"] = lagged[idx - 1]
        x_vector = vectorize_features(feature_row)
        pred = model.predict([x_vector])[0]
        predictions.append(pred)
    return predictions


def run_pipeline(input_path: str, horizon: int = 7) -> Dict[str, object]:
    raw = load_sales_csv(input_path)
    cleaned = clean_sales_data(raw)
    grouped = group_by_series(cleaned)
    baseline = BaselineForecaster()

    evaluations: List[Dict[str, object]] = []
    recommendations: List[Dict[str, object]] = []

    for (store_id, product_id), rows in grouped.items():
        if len(rows) < horizon + 8:
            continue

        train_rows = rows[:-horizon]
        test_rows = rows[-horizon:]
        train_sales = [float(r["sales"]) for r in train_rows]
        actual = [float(r["sales"]) for r in test_rows]

        baseline_preds = baseline.predict(train_sales, horizon)
        baseline_mae = mae(actual, baseline_preds)
        baseline_rmse = rmse(actual, baseline_preds)

        supervised = build_supervised_rows(train_rows, max_lag=7)
        x_train = [vectorize_features(row) for row in supervised]
        y_train = [float(row["target"]) for row in supervised]

        ml_preds = baseline_preds
        ml_mae = baseline_mae
        ml_rmse = baseline_rmse
        if x_train and y_train:
            model = LinearRegressionGD(learning_rate=0.00005, epochs=1800)
            model.fit(x_train, y_train)
            ml_preds = _recursive_ml_forecast(train_rows, horizon, model)
            ml_mae = mae(actual, ml_preds)
            ml_rmse = rmse(actual, ml_preds)

        if ml_rmse <= baseline_rmse:
            selected_model = "linear_regression_gd"
            selected_forecast = ml_preds
            selected_mae = ml_mae
            selected_rmse = ml_rmse
        else:
            selected_model = "baseline_last_value"
            selected_forecast = baseline_preds
            selected_mae = baseline_mae
            selected_rmse = baseline_rmse

        evaluations.append(
            {
                "store_id": store_id,
                "product_id": product_id,
                "baseline_mae": round(baseline_mae, 3),
                "baseline_rmse": round(baseline_rmse, 3),
                "ml_mae": round(ml_mae, 3),
                "ml_rmse": round(ml_rmse, 3),
                "selected_model": selected_model,
                "selected_mae": round(selected_mae, 3),
                "selected_rmse": round(selected_rmse, 3),
                "feature_count": len(FEATURE_ORDER),
            }
        )

        rec = recommend_order_quantity(
            selected_forecast,
            lead_time_days=7,
            service_factor=1.65,
            current_stock=20.0,
            in_transit=0.0,
        )
        recommendations.append(
            {
                "store_id": store_id,
                "product_id": product_id,
                "selected_model": selected_model,
                **rec,
            }
        )

    return {
        "n_input_rows": len(raw),
        "n_clean_rows": len(cleaned),
        "evaluations": evaluations,
        "recommendations": recommendations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Demand forecasting and stock recommendation pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--horizon", type=int, default=7, help="Forecast horizon in days")
    args = parser.parse_args()
    output = run_pipeline(args.input, horizon=args.horizon)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
