"""fvh.stats — the course's statistics (QPLAN §11.8; design §10.3, §11.1).

Pure functions on the standard library only. Every function is deterministic:
the two that resample take a required keyword `seed` and draw only from
`random.Random(seed)`. Proportion intervals are closed `(lo, hi)` tuples of
floats in [0, 1]. Statistics code lives here and nowhere else (design §9.2
rule 4): learner code composes these functions and never re-derives an
estimator. Q06 composes pass_at_k and wilson_interval; Q09 and Q12 compose the
rest.

  pass_at_k(n, c, k)
      the unbiased pass@k estimator 1 - C(n - c, k) / C(n, k): the
      probability that at least one of k samples drawn without replacement
      from n samples, c of them correct, is correct
  wilson_interval(successes, n, confidence=0.95)
      the Wilson score interval of a binomial proportion
  bootstrap_ci(values, statistic=statistics.fmean, *, n_resamples=10_000,
               confidence=0.95, seed)
      the percentile bootstrap interval of a statistic
  mcnemar(b, c, *, exact=True)
      the two-sided p-value of a paired comparison of two arms on the same
      tasks, from the discordant counts
  permutation_test(x, y, *, paired, n_permutations=10_000, seed)
      the two-sided p-value of a difference in means
  holm(pvalues, alpha=0.05)
      Holm-Bonferroni step-down rejections, in input order
  mde_two_proportions(n, p0, *, alpha=0.05, power=0.8, paired=False)
      the minimum detectable difference at n tasks per arm

Arguments are checked: a count that is not an int (a bool included) is a
TypeError; a value out of range is a ValueError. No function prints.
"""

import math
import random
import statistics
from collections.abc import Callable, Sequence
from statistics import NormalDist

__all__ = ["bootstrap_ci", "holm", "mcnemar", "mde_two_proportions", "pass_at_k",
           "permutation_test", "wilson_interval"]

# Two permutation statistics count as tied when they differ by at most this
# fraction of the observed statistic (floating-point sums of the same values in
# another order may differ in the last bits).
TIE_TOLERANCE = 1e-12


# --- argument checks -------------------------------------------------------------------

def _count(value, name):
    """An int (never a bool), else TypeError."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, not {type(value).__name__}")
    return value


def _real(value, name):
    """A finite real number as a float (never a bool), else TypeError or ValueError."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, not {type(value).__name__}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, not {value!r}")
    return value


def _open_unit(value, name):
    """A probability strictly between 0 and 1."""
    value = _real(value, name)
    if not 0.0 < value < 1.0:
        raise ValueError(f"{name} must lie strictly between 0 and 1, not {value!r}")
    return value


def _z(p):
    """The standard normal quantile at p."""
    return NormalDist().inv_cdf(p)


def _quantile(sorted_values, q):
    """The q-quantile of sorted values, interpolated linearly between order
    statistics at position q * (len - 1) (the common 'linear' definition)."""
    pos = q * (len(sorted_values) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


# --- pass@k ----------------------------------------------------------------------------

def pass_at_k(n: int, c: int, k: int) -> float:
    """The unbiased pass@k estimate from n samples of one task, c of them correct.

    1 - C(n - c, k) / C(n, k), computed in exact integer arithmetic with one
    final division; 1.0 when n - c < k (every draw of k samples holds a
    correct one). ValueError unless 0 <= c <= n and 1 <= k <= n.
    """
    n, c, k = _count(n, "n"), _count(c, "c"), _count(k, "k")
    if not 0 <= c <= n:
        raise ValueError(f"need 0 <= c <= n, got c={c}, n={n}")
    if not 1 <= k <= n:
        raise ValueError(f"need 1 <= k <= n, got k={k}, n={n}")
    if n - c < k:
        return 1.0
    total = math.comb(n, k)
    return (total - math.comb(n - c, k)) / total


# --- intervals -------------------------------------------------------------------------

def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """The Wilson score interval of the proportion successes / n.

    The set of proportions p whose score test |p_hat - p| <= z * sqrt(p (1 - p) / n)
    accepts, with z the standard normal quantile at 1 - (1 - confidence) / 2
    (statistics.NormalDist). The interval is closed and lies in [0, 1]; its lower
    end is exactly 0.0 when successes == 0 and its upper end exactly 1.0 when
    successes == n. ValueError unless 0 <= successes <= n, n >= 1 and
    0 < confidence < 1.
    """
    s, n = _count(successes, "successes"), _count(n, "n")
    confidence = _open_unit(confidence, "confidence")
    if n < 1:
        raise ValueError(f"need n >= 1, got n={n}")
    if not 0 <= s <= n:
        raise ValueError(f"need 0 <= successes <= n, got successes={s}, n={n}")
    z = _z(0.5 + confidence / 2)
    z2 = z * z
    p = s / n
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n))
    lo = 0.0 if s == 0 else max(0.0, centre - half)
    hi = 1.0 if s == n else min(1.0, centre + half)
    return (lo, hi)


def bootstrap_ci(values: Sequence[float],
                 statistic: Callable[[Sequence[float]], float] = statistics.fmean, *,
                 n_resamples: int = 10_000, confidence: float = 0.95,
                 seed: int) -> tuple[float, float]:
    """The percentile bootstrap interval of statistic(values).

    Draws n_resamples resamples of len(values) values with replacement
    (random.Random(seed).choices), applies `statistic` to each, and returns the
    (1 - confidence) / 2 and 1 - (1 - confidence) / 2 quantiles of the results
    (linear interpolation between order statistics). The same arguments and seed
    always give the same interval. ValueError for an empty `values`, for
    n_resamples < 1 or for a confidence outside (0, 1).
    """
    data = list(values)
    if not data:
        raise ValueError("values is empty: there is nothing to resample")
    n_resamples = _count(n_resamples, "n_resamples")
    if n_resamples < 1:
        raise ValueError(f"need n_resamples >= 1, got {n_resamples}")
    confidence = _open_unit(confidence, "confidence")
    seed = _count(seed, "seed")
    rng = random.Random(seed)
    m = len(data)
    results = sorted(float(statistic(rng.choices(data, k=m))) for _ in range(n_resamples))
    tail = (1.0 - confidence) / 2
    return (_quantile(results, tail), _quantile(results, 1.0 - tail))


# --- tests -----------------------------------------------------------------------------

def mcnemar(b: int, c: int, *, exact: bool = True) -> float:
    """The two-sided p-value of McNemar's test from the discordant counts.

    b: tasks the first arm solved and the second did not; c: the reverse.
    exact=True: the exact binomial test of b against Binomial(b + c, 1/2), twice
    the smaller tail, capped at 1. exact=False: the continuity-corrected
    chi-square statistic max(|b - c| - 1, 0)^2 / (b + c) on one degree of
    freedom. 1.0 when b + c == 0 (no discordant pair, no evidence).
    ValueError for a negative count.
    """
    b, c = _count(b, "b"), _count(c, "c")
    if b < 0 or c < 0:
        raise ValueError(f"counts must be >= 0, got b={b}, c={c}")
    n = b + c
    if n == 0:
        return 1.0
    if exact:
        tail = sum(math.comb(n, i) for i in range(min(b, c) + 1))
        return min(1.0, (2 * tail) / (2 ** n))
    stat = max(abs(b - c) - 1, 0) ** 2 / n
    return math.erfc(math.sqrt(stat / 2.0))


def permutation_test(x: Sequence[float], y: Sequence[float], *, paired: bool,
                     n_permutations: int = 10_000, seed: int) -> float:
    """The two-sided p-value of the difference in means of x and y.

    paired=True (x[i] and y[i] measured on the same task): the statistic is
    |sum of the differences x[i] - y[i]|, and each permutation flips the sign of
    every difference with probability 1/2. paired=False: the statistic is
    |mean(x) - mean(y)|, and each permutation shuffles the pooled values (from
    their sorted order, so the order inside each sample does not matter) and
    splits them into groups of len(x) and len(y). The p-value is
    (1 + the number of permutations at least as extreme) / (1 + n_permutations),
    so it is never 0; ties within a relative TIE_TOLERANCE count as at least as
    extreme. Randomness comes only from random.Random(seed). ValueError for an
    empty sample, for paired samples of different lengths, or for
    n_permutations < 1.
    """
    xs = [_real(v, "x value") for v in x]
    ys = [_real(v, "y value") for v in y]
    if not xs or not ys:
        raise ValueError("both samples need at least one value")
    if not isinstance(paired, bool):
        raise TypeError("paired must be True or False")
    n_permutations = _count(n_permutations, "n_permutations")
    if n_permutations < 1:
        raise ValueError(f"need n_permutations >= 1, got {n_permutations}")
    seed = _count(seed, "seed")
    rng = random.Random(seed)
    if paired:
        if len(xs) != len(ys):
            raise ValueError(f"paired samples need equal lengths, got {len(xs)} and {len(ys)}")
        diffs = [a - b for a, b in zip(xs, ys)]
        observed = abs(math.fsum(diffs))

        def one():
            bits = rng.getrandbits(len(diffs))
            return abs(math.fsum(-d if (bits >> i) & 1 else d for i, d in enumerate(diffs)))
    else:
        pooled = sorted(xs + ys)   # the result depends on the two samples' values only
        nx = len(xs)

        def stat(a, b):
            return abs(math.fsum(a) / len(a) - math.fsum(b) / len(b))
        observed = stat(xs, ys)

        def one():
            rng.shuffle(pooled)
            return stat(pooled[:nx], pooled[nx:])
    bar = observed - TIE_TOLERANCE * max(1.0, observed)
    hits = sum(1 for _ in range(n_permutations) if one() >= bar)
    return (hits + 1) / (n_permutations + 1)


def holm(pvalues: Sequence[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni rejections at family-wise level alpha, in input order.

    The p-values are taken in ascending order (ties in input order); the i-th
    smallest (i = 0, 1, …) is rejected while p <= alpha / (m - i), and the first
    one that is not stops the procedure (none after it is rejected). An empty
    list gives an empty list. ValueError for a p-value outside [0, 1] or an
    alpha outside (0, 1).
    """
    alpha = _open_unit(alpha, "alpha")
    ps = [_real(p, "p-value") for p in pvalues]
    for p in ps:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"p-values lie in [0, 1], got {p!r}")
    m = len(ps)
    reject = [False] * m
    for rank, i in enumerate(sorted(range(m), key=lambda j: ps[j])):
        if ps[i] <= alpha / (m - rank):
            reject[i] = True
        else:
            break
    return reject


# --- planning --------------------------------------------------------------------------

def _required_n(delta, p0, za, zb, paired):
    """Tasks per arm a two-sided test needs to detect p1 = p0 + delta."""
    p1 = p0 + delta
    if paired:
        # McNemar's test (Connor 1987) with the discordant-pair rate the two arms
        # would have if they succeeded independently on each task.
        psi = p0 * (1.0 - p1) + p1 * (1.0 - p0)
        num = za * math.sqrt(psi) + zb * math.sqrt(max(psi - delta * delta, 0.0))
    else:
        # the two-proportion z-test with equal arms (Fleiss, no continuity correction)
        pbar = (p0 + p1) / 2.0
        num = za * math.sqrt(2.0 * pbar * (1.0 - pbar)) \
            + zb * math.sqrt(p0 * (1.0 - p0) + p1 * (1.0 - p1))
    return (num / delta) ** 2


def mde_two_proportions(n: int, p0: float, *, alpha: float = 0.05, power: float = 0.8,
                        paired: bool = False) -> float:
    """The minimum detectable difference in success rate at n tasks per arm.

    The smallest delta > 0 such that a two-sided test at level alpha detects a
    rise from the baseline rate p0 to p0 + delta with the given power, found by
    bisection on the normal-approximation sample-size formula:
      paired=False  two independent arms of n tasks each: the two-proportion
                    z-test, n = (z_a sqrt(2 pbar (1 - pbar)) + z_b sqrt(p0 q0 +
                    p1 q1))^2 / delta^2 with pbar = (p0 + p1) / 2;
      paired=True   both arms on the same n tasks: McNemar's test (Connor 1987),
                    n = (z_a sqrt(psi) + z_b sqrt(psi - delta^2))^2 / delta^2, with
                    the discordant-pair rate psi = p0 (1 - p1) + p1 (1 - p0) that
                    independent arms would give (correlated arms discord less, so
                    their true MDE is smaller: this is the conservative value);
    where z_a = z(1 - alpha / 2), z_b = z(power), p1 = p0 + delta, q = 1 - p.
    Returns delta as a proportion (0.25 is 25 points), or math.inf when not even
    delta = 1 - p0 is detectable at this n. ValueError unless n >= 1 and p0,
    alpha and power lie strictly between 0 and 1.
    """
    n = _count(n, "n")
    if n < 1:
        raise ValueError(f"need n >= 1, got n={n}")
    p0 = _open_unit(p0, "p0")
    alpha = _open_unit(alpha, "alpha")
    power = _open_unit(power, "power")
    if not isinstance(paired, bool):
        raise TypeError("paired must be True or False")
    za, zb = _z(1.0 - alpha / 2.0), _z(power)
    hi = 1.0 - p0
    if _required_n(hi, p0, za, zb, paired) > n:
        return math.inf
    lo = 0.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if mid <= lo or mid >= hi:
            break
        if _required_n(mid, p0, za, zb, paired) <= n:
            hi = mid
        else:
            lo = mid
    return hi
