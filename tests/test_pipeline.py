import os
import sys
import unittest

ROOT = "/home/runner/work/Prevision-de-la-Demande-Optimization-de-Stock/Prevision-de-la-Demande-Optimization-de-Stock"
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from data_pipeline import clean_sales_data, load_sales_csv
from inventory import recommend_order_quantity
from pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_clean_sales_data_removes_duplicates(self):
        rows = [
            {"date": __import__("datetime").date(2026, 1, 1), "store_id": "s1", "product_id": "p1", "sales": 5, "price": 2, "promotion": 0, "event": 0},
            {"date": __import__("datetime").date(2026, 1, 1), "store_id": "s1", "product_id": "p1", "sales": 5, "price": 2, "promotion": 0, "event": 0},
        ]
        cleaned = clean_sales_data(rows)
        self.assertEqual(len(cleaned), 1)

    def test_recommend_order_quantity_non_negative(self):
        rec = recommend_order_quantity([10, 11, 12, 13, 14, 15, 16], current_stock=500, in_transit=0)
        self.assertEqual(rec["order_quantity"], 0.0)

    def test_run_pipeline_returns_evaluation_and_recommendations(self):
        sample_path = os.path.join(ROOT, "data", "sample_sales.csv")
        result = run_pipeline(sample_path, horizon=7)
        self.assertGreaterEqual(result["n_clean_rows"], 1)
        self.assertGreaterEqual(len(result["evaluations"]), 1)
        self.assertGreaterEqual(len(result["recommendations"]), 1)

    def test_load_sales_csv_supports_marjane_schema(self):
        marjane_path = os.path.join(ROOT, "data", "ventes_brut_marjane.csv")
        rows = load_sales_csv(marjane_path)
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn("store_id", rows[0])
        self.assertIn("product_id", rows[0])
        self.assertIn("sales", rows[0])
        self.assertIn("price", rows[0])


if __name__ == "__main__":
    unittest.main()
