"""Statistics: Wilson interval for proportions, cluster bootstrap over items."""
import numpy as np


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def bootstrap_ci(item_rates, B=2000, seed=0, alpha=0.05):
    """item_rates: per-item mean over trials. Resample ITEMS (attacks are the unit, trials are
    not independent samples of the attack set). Returns (mean, lo, hi)."""
    x = np.asarray(item_rates, dtype=float)
    if len(x) == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), size=(B, len(x)))].mean(axis=1)
    return float(x.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))
