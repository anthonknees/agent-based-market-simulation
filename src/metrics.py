from __future__ import annotations
import numpy as np
import pandas as pd


def compute_log_returns(prices: list[float]) -> np.ndarray:
    p = np.array(prices, dtype=float)
    return np.log(p[1:] / p[:-1])


def rolling_volatility(log_returns: np.ndarray, window: int) -> np.ndarray:
    # rolling std (sample)
    if len(log_returns) < window:
        return np.array([])
    out = []
    for i in range(window, len(log_returns) + 1):
        chunk = log_returns[i-window:i]
        out.append(np.std(chunk, ddof=1))
    return np.array(out)


def write_metrics_csv(path: str, rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)