from __future__ import annotations

import math
from typing import Iterable, List


def mae(actual: Iterable[float], predicted: Iterable[float]) -> float:
    values = [abs(a - p) for a, p in zip(actual, predicted)]
    return sum(values) / len(values) if values else 0.0


def rmse(actual: Iterable[float], predicted: Iterable[float]) -> float:
    values = [(a - p) ** 2 for a, p in zip(actual, predicted)]
    return math.sqrt(sum(values) / len(values)) if values else 0.0


class BaselineForecaster:
    def predict(self, history: List[float], horizon: int) -> List[float]:
        last = history[-1] if history else 0.0
        return [float(last) for _ in range(horizon)]


class LinearRegressionGD:
    def __init__(self, learning_rate: float = 0.001, epochs: int = 1200):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.weights: List[float] = []
        self.bias: float = 0.0

    def fit(self, x_matrix: List[List[float]], y: List[float]) -> None:
        if not x_matrix:
            self.weights = []
            self.bias = 0.0
            return
        n_features = len(x_matrix[0])
        self.weights = [0.0 for _ in range(n_features)]
        self.bias = 0.0
        n_samples = len(x_matrix)

        for _ in range(self.epochs):
            grad_w = [0.0 for _ in range(n_features)]
            grad_b = 0.0
            for row, target in zip(x_matrix, y):
                pred = self._predict_row(row)
                error = pred - target
                for idx in range(n_features):
                    grad_w[idx] += (2.0 / n_samples) * error * row[idx]
                grad_b += (2.0 / n_samples) * error
            for idx in range(n_features):
                self.weights[idx] -= self.learning_rate * grad_w[idx]
            self.bias -= self.learning_rate * grad_b

    def _predict_row(self, row: List[float]) -> float:
        return sum(weight * value for weight, value in zip(self.weights, row)) + self.bias

    def predict(self, x_matrix: List[List[float]]) -> List[float]:
        return [max(0.0, self._predict_row(row)) for row in x_matrix]
