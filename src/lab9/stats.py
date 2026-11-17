"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb
from numbers import Integral

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge labels must be paired")
    cells = {("FAIL", "FAIL"): "tp", ("PASS", "FAIL"): "fp",
             ("FAIL", "PASS"): "fn", ("PASS", "PASS"): "tn"}
    counts = dict.fromkeys(cells.values(), 0)
    for pair in zip(human, judge):
        if pair not in cells:
            raise ValueError("labels must be PASS or FAIL")
        counts[cells[pair]] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    tp = cm["tp"]
    return tp / (tp + cm["fp"] or 1), tp / (tp + cm["fn"] or 1)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = len(human)
    human_fail, judge_fail = cm["tp"] + cm["fn"], cm["tp"] + cm["fp"]
    chance = human_fail * judge_fail + (n - human_fail) * (n - judge_fail)
    if chance == n * n:
        raise ValueError("Cohen's kappa is undefined with unanimous agreement by chance")
    observed = (cm["tp"] + cm["tn"]) * n
    return (observed - chance) / (n * n - chance)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    if not all(0 <= value <= 1 for value in (observed_rate, sensitivity, specificity)):
        raise ValueError("rates must be in [0, 1]")
    signal = sensitivity + specificity - 1
    if signal == 0:
        raise ValueError("failure prevalence is undefined for a chance-level judge")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / signal))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    left, right = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if left.ndim != 1 or left.shape != right.shape or not left.size:
        raise ValueError("bootstrap requires nonempty, paired item scores")
    if not (np.isfinite(left).all() and np.isfinite(right).all()):
        raise ValueError("bootstrap requires finite item scores")

    def mean_diff(x, y, axis=-1):
        return np.mean(x - y, axis=axis)

    delta = float(mean_diff(left, right))
    if left.size == 1 or np.array_equal(left, right):
        return delta, delta, delta
    ci = bootstrap((left, right), mean_diff, paired=True, method="percentile",
                   n_resamples=n_resamples, confidence_level=confidence,
                   rng=np.random.default_rng(rng)).confidence_interval
    return delta, float(ci.low), float(ci.high)


def _validate_trials(n: int, c: int, k: int) -> None:
    if any(isinstance(v, bool) or not isinstance(v, Integral) for v in (n, c, k)):
        raise ValueError("n, c and k must be integers")
    if not (0 <= c <= n and 1 <= k <= n):
        raise ValueError("require 0 <= c <= n and 1 <= k <= n")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_trials(n, c, k)
    total = comb(n, k)
    return (total - comb(n - c, k)) / total


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_trials(n, c, k)
    return comb(c, k) / comb(n, k)
