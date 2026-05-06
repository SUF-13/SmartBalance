import numpy as np
from collections import deque


class TrafficPredictor:
    """
    AI-based load predictor using a simple moving-average + linear-regression model.

    Approach:
    - Maintains a sliding window of recent connection counts
    - Fits a linear trend to predict short-term future load
    - Normalizes prediction to [0, 1] for use as a routing weight

    This implements the 'AI-Based Optimization' component of the project.
    """

    WINDOW = 20  # samples kept

    def __init__(self):
        self._history: deque[float] = deque(maxlen=self.WINDOW)
        self._max_seen: float = 1.0  # for normalization

    def record(self, connection_count: int):
        """Feed a new data point into the predictor."""
        self._history.append(float(connection_count))
        if connection_count > self._max_seen:
            self._max_seen = float(connection_count)

    def predict(self) -> float:
        """
        Returns a predicted load score in [0.0, 1.0].
        Higher means more load expected.
        Falls back to 0.5 (neutral) when insufficient data.
        """
        if len(self._history) < 3:
            return 0.5

        y = np.array(list(self._history))
        x = np.arange(len(y))

        # Fit degree-1 polynomial (linear trend)
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        # Predict next value
        next_x = len(y)
        predicted = np.polyval(coeffs, next_x)

        # Clamp and normalize
        predicted = max(0.0, predicted)
        normalized = predicted / max(self._max_seen, 1.0)
        normalized = min(1.0, max(0.0, normalized))

        return round(float(normalized), 4)

    def trend(self) -> str:
        """Human-readable trend label."""
        if len(self._history) < 3:
            return "stable"
        y = list(self._history)
        slope = (y[-1] - y[0]) / max(len(y), 1)
        if slope > 1.5:
            return "rising_fast"
        elif slope > 0.3:
            return "rising"
        elif slope < -1.5:
            return "falling_fast"
        elif slope < -0.3:
            return "falling"
        return "stable"

    def history(self) -> list[float]:
        return list(self._history)

    def to_dict(self) -> dict:
        return {
            "predicted_load": self.predict(),
            "trend": self.trend(),
            "samples": len(self._history),
            "history": self.history(),
        }