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
  success_curve(first_success_calls, budget)
      S(b), b = 1..budget: the share of runs whose first success came within
      b calls (Lab alpha's success-vs-budget curve, DVR4 plan section 3.1)
  auc_budget(first_success_calls, budget)
      (1/B) sum_b S(b), the area under that curve ("budget-weighted success")
  cluster_bootstrap_ci(cluster_values, *, n_resamples=10_000,
                       confidence=0.95, seed)
      the percentile cluster bootstrap of an equal-weight mean over clusters,
      of a number per cluster or of a curve per cluster (one band per point)
  paired_t_pvalue(differences)
      the exact two-sided one-sample Student t p-value of mean 0
  mde_paired_clusters_sim(sizes, repeats, base_auc, icc, tau, eta=0.5, *,
                          budget=10, sigma_w=0.5, alpha=0.05, power=0.8,
                          n_sims=1000, n_delta=30_000, betas=DEFAULT_BETAS, seed)
      the simulated minimum detectable AUC difference of a paired cluster
      design (Lab alpha's power simulation, DVR4 plan section 3.4)

Arguments are checked: a count that is not an int (a bool included) is a
TypeError; a value out of range is a ValueError. No function prints.
"""

import math
import random
import statistics
from collections.abc import Callable, Sequence
from statistics import NormalDist

__all__ = ["DEFAULT_BETAS", "auc_budget", "bootstrap_ci", "cluster_bootstrap_ci", "holm",
           "mcnemar", "mde_paired_clusters_sim", "mde_two_proportions", "paired_t_pvalue",
           "pass_at_k", "permutation_test", "success_curve", "wilson_interval"]

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



# --- success against budget (Lab alpha, DVR4 plan section 3) ------------------------------

def _first_calls(first_success_calls, budget):
    """The runs' first-success calls (int >= 1, or None for no success) and the budget."""
    budget = _count(budget, "budget")
    if budget < 1:
        raise ValueError(f"need budget >= 1, got {budget}")
    out = []
    for t in first_success_calls:
        if t is not None:
            t = _count(t, "a first-success call")
            if t < 1:
                raise ValueError(f"a first-success call is >= 1 (call 1 is the first), got {t}")
        out.append(t)
    if not out:
        raise ValueError("no run: a curve needs at least one run")
    return out, budget


def success_curve(first_success_calls: Sequence[int | None], budget: int) -> list[float]:
    """S(b) for b = 1, ..., budget: the fraction of the runs whose first success
    came within b node calls.

    first_success_calls holds one entry per run: the call T >= 1 whose candidate
    was the run's first verified (and re-judged) success, or None when the run had
    none. A success after the budget counts as none within it. The curve is
    non-decreasing and reads each run as its prefixes (a regime's settings never
    depend on the budget). ValueError for no run, a budget < 1 or a call < 1.
    """
    calls, budget = _first_calls(first_success_calls, budget)
    n = len(calls)
    return [sum(1 for t in calls if t is not None and t <= b) / n for b in range(1, budget + 1)]


def auc_budget(first_success_calls: Sequence[int | None], budget: int) -> float:
    """The area under the success-vs-budget curve, (1/B) sum_{b=1..B} S(b).

    Per run this is max(0, B - T + 1) / B for a first success at call T (0 when
    there is none), so the value lies in [0, 1]: 1 when every run succeeds at
    call 1, 0 when none succeeds within the budget. It is the mean of the per-run
    values (the runs weigh equally; Lab alpha averages a cluster-arm's runs with
    it). Same arguments and errors as success_curve.
    """
    calls, budget = _first_calls(first_success_calls, budget)
    return math.fsum(max(0, budget - t + 1) / budget if t is not None else 0.0
                     for t in calls) / len(calls)


def cluster_bootstrap_ci(cluster_values: Sequence, *, n_resamples: int = 10_000,
                         confidence: float = 0.95, seed: int):
    """The percentile cluster bootstrap of the equal-weight mean over clusters.

    Each element of cluster_values is one cluster's value, already aggregated
    over the cluster's tasks and repeats: a number (e.g. a cluster's difference
    d_c = AUC_obl(c) - AUC_raw(c)), or a sequence of numbers of one common length
    (e.g. a cluster's curve S_c(1..B)). Each resample draws len(cluster_values)
    clusters with replacement (random.Random(seed).choices), whole, and takes the
    mean (per coordinate for curves). Returns (lo, hi) for numbers, and a list of
    (lo, hi) per coordinate for curves, every coordinate's band from the same
    resampled clusters; the quantiles are as in bootstrap_ci. ValueError for no
    cluster, mixed or unequal shapes, n_resamples < 1 or a confidence outside (0, 1).
    """
    data = list(cluster_values)
    if not data:
        raise ValueError("cluster_values is empty: there is no cluster to resample")
    n_resamples = _count(n_resamples, "n_resamples")
    if n_resamples < 1:
        raise ValueError(f"need n_resamples >= 1, got {n_resamples}")
    confidence = _open_unit(confidence, "confidence")
    seed = _count(seed, "seed")
    scalar = not isinstance(data[0], (list, tuple))
    if scalar:
        rows = [[_real(v, "a cluster value")] for v in data]
        if any(isinstance(v, (list, tuple)) for v in data):
            raise ValueError("cluster values are all numbers or all curves")
    else:
        if any(not isinstance(v, (list, tuple)) for v in data):
            raise ValueError("cluster values are all numbers or all curves")
        rows = [[_real(x, "a curve point") for x in v] for v in data]
        width = len(rows[0])
        if width == 0 or any(len(r) != width for r in rows):
            raise ValueError("every cluster's curve needs the same, non-zero length")
    rng = random.Random(seed)
    m, width = len(rows), len(rows[0])
    draws = [[] for _ in range(width)]
    for _ in range(n_resamples):
        pick = rng.choices(rows, k=m)
        for j in range(width):
            draws[j].append(math.fsum(r[j] for r in pick) / m)
    tail = (1.0 - confidence) / 2
    bands = []
    for j in range(width):
        d = sorted(draws[j])
        bands.append((_quantile(d, tail), _quantile(d, 1.0 - tail)))
    return bands[0] if scalar else bands


# --- the paired t-test and the cluster-design power simulation --------------------------

def _betacf(a, b, x):
    """The continued fraction of the regularized incomplete beta (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 201):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-14:
            break
    return h


def _ibeta(a, b, x):
    """The regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def paired_t_pvalue(differences: Sequence[float]) -> float:
    """The exact two-sided p-value of the one-sample Student t-test of mean 0.

    t = mean / (sd / sqrt(n)) on n - 1 degrees of freedom (sd the sample standard
    deviation); p = I_{df / (df + t^2)}(df / 2, 1/2). With every difference
    equal, p is 1.0 when they are 0 and 0.0 otherwise. ValueError for fewer
    than two differences.
    """
    d = [_real(v, "a difference") for v in differences]
    if len(d) < 2:
        raise ValueError("the t-test needs at least two differences")
    mu = math.fsum(d) / len(d)
    sd = statistics.stdev(d)
    if sd == 0.0:
        return 1.0 if mu == 0.0 else 0.0
    t = mu / (sd / math.sqrt(len(d)))
    df = len(d) - 1
    return _ibeta(df / 2.0, 0.5, df / (df + t * t))


DEFAULT_BETAS = (0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0, 1.3, 1.7)


def _logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


def _run_auc(p, budget, rng):
    """One run's AUC: its first-success call is geometric in p (support 1, 2, ...)."""
    if p >= 1.0:
        return 1.0
    u = rng.random()
    t = 1 + int(math.log(1.0 - u) / math.log(1.0 - p))
    return max(0, budget - t + 1) / budget


def _expected_auc(p, budget):
    # a plain left-to-right sum, as the plan's simulation sums it (the port agrees with
    # Solutions/plans/labalpha_power_sim.py's `cell` to the last digit)
    return sum(1 - (1 - p) ** b for b in range(1, budget + 1)) / budget


def _sim_delta(b0, beta, su, sw, tau, eta, budget, rng, n):
    """The population mean AUC difference (obligation - raw) and the raw arm's AUC."""
    acc = base = 0.0
    for _ in range(n):
        uc, zc, wt, it = rng.gauss(0, su), rng.gauss(0, 1), rng.gauss(0, sw), rng.gauss(0, eta)
        p0 = _logistic(b0 + uc + wt)
        p1 = _logistic(b0 + beta + uc + tau * zc + it + wt)
        e0 = _expected_auc(p0, budget)
        acc += _expected_auc(p1, budget) - e0
        base += e0
    return acc / n, base / n


def _sim_dataset(sizes, repeats, b0, beta, su, sw, tau, eta, budget, rng):
    """One simulated design's cluster differences d_c (clusters of the larger size first)."""
    out = []
    for size in sorted(sizes, reverse=True):
        for _ in range(sizes[size]):
            uc, zc = rng.gauss(0, su), rng.gauss(0, 1)
            t0 = t1 = 0.0
            for _t in range(size):
                wt, it = rng.gauss(0, sw), rng.gauss(0, eta)
                p0 = _logistic(b0 + uc + wt)
                p1 = _logistic(b0 + beta + uc + tau * zc + it + wt)
                for _r in range(repeats):
                    t0 += _run_auc(p0, budget, rng)
                    t1 += _run_auc(p1, budget, rng)
            out.append((t1 - t0) / (size * repeats))
    return out


def mde_paired_clusters_sim(sizes, repeats: int, base_auc: float, icc: float, tau: float,
                            eta: float = 0.5, *, budget: int = 10, sigma_w: float = 0.5,
                            alpha: float = 0.05, power: float = 0.8, n_sims: int = 1000,
                            n_delta: int = 30_000, betas: Sequence[float] = DEFAULT_BETAS,
                            seed: int) -> float:
    """The minimum detectable AUC difference of a paired cluster design, by
    Monte-Carlo (Lab alpha's power simulation, DVR4 plan section 3.4).

    The model of one run: the per-call success probability is
        p = logistic(b0 + beta * arm + u_c + arm * (tau * z_c + eta_t) + w_t),
    the first-success call is geometric in p and the run's AUC is
    max(0, B - T + 1) / B (B = budget). u_c ~ N(0, su^2) is the cluster effect,
    with su set so that icc = su^2 / (su^2 + sigma_w^2 + pi^2 / 3) (the latent
    scale); w_t ~ N(0, sigma_w^2) is the task effect both arms share (they run on
    the same tasks); tau * z_c (z_c ~ N(0, 1)) the cluster-level heterogeneity of
    the effect and eta_t ~ N(0, eta^2) a task-by-arm interaction. b0 is found by
    25 bisection steps on [-6, 4] so that the raw arm's expected AUC is base_auc
    (6,000 draws of random.Random(7), tau = eta = 0).

    sizes maps a cluster size (tasks per cluster) to its number of clusters, e.g.
    {2: 50, 1: 30}; every task runs `repeats` times per arm. For each beta of
    `betas` (increasing): its true difference delta(beta) from n_delta draws, and
    its power, the share of n_sims simulated designs whose cluster differences
    give paired_t_pvalue < alpha. The MDE is the delta at which the power reaches
    `power`, interpolated linearly between the two grid points around it.
    Returns math.inf when even the largest beta stays below the power, and the
    smallest beta's delta (an upper bound) when that one already reaches it.
    Randomness: one random.Random(seed), drawn for the deltas in beta order, then
    for the designs in beta order. ValueError for an empty or non-positive size
    table, fewer than two clusters, repeats < 1, base_auc or power or alpha
    outside (0, 1), icc outside [0, 1), negative tau, eta or sigma_w, n_sims or
    n_delta < 1, or betas that are not increasing.
    """
    if not isinstance(sizes, dict) or not sizes:
        raise ValueError("sizes is a non-empty {cluster size: number of clusters} table")
    table = {}
    for size, k in sizes.items():
        size, k = _count(size, "a cluster size"), _count(k, "a cluster count")
        if size < 1 or k < 0:
            raise ValueError("cluster sizes are >= 1 and counts >= 0")
        if k:
            table[size] = k
    if sum(table.values()) < 2:
        raise ValueError("the design needs at least two clusters")
    repeats = _count(repeats, "repeats")
    if repeats < 1:
        raise ValueError(f"need repeats >= 1, got {repeats}")
    base_auc = _open_unit(base_auc, "base_auc")
    icc = _real(icc, "icc")
    if not 0.0 <= icc < 1.0:
        raise ValueError(f"icc lies in [0, 1), not {icc!r}")
    tau, eta, sigma_w = _real(tau, "tau"), _real(eta, "eta"), _real(sigma_w, "sigma_w")
    if tau < 0 or eta < 0 or sigma_w < 0:
        raise ValueError("tau, eta and sigma_w are standard deviations (>= 0)")
    budget = _count(budget, "budget")
    if budget < 1:
        raise ValueError(f"need budget >= 1, got {budget}")
    alpha, power = _open_unit(alpha, "alpha"), _open_unit(power, "power")
    n_sims, n_delta = _count(n_sims, "n_sims"), _count(n_delta, "n_delta")
    if n_sims < 1 or n_delta < 1:
        raise ValueError("n_sims and n_delta are >= 1")
    grid = [_real(b, "beta") for b in betas]
    if not grid or any(b1 <= b0_ for b0_, b1 in zip(grid, grid[1:])):
        raise ValueError("betas is a non-empty increasing sequence")
    seed = _count(seed, "seed")
    su = math.sqrt(icc * (sigma_w ** 2 + math.pi ** 2 / 3) / (1.0 - icc))
    lo, hi = -6.0, 4.0
    for _ in range(25):
        mid = (lo + hi) / 2
        if _sim_delta(mid, 0.0, su, sigma_w, 0.0, 0.0, budget, random.Random(7), 6000)[1] \
                < base_auc:
            lo = mid
        else:
            hi = mid
    b0 = (lo + hi) / 2
    rng = random.Random(seed)
    deltas = [_sim_delta(b0, b, su, sigma_w, tau, eta, budget, rng, n_delta)[0] for b in grid]
    powers = []
    for b in grid:
        hits = sum(1 for _ in range(n_sims)
                   if paired_t_pvalue(_sim_dataset(table, repeats, b0, b, su, sigma_w, tau, eta,
                                                   budget, rng)) < alpha)
        powers.append(hits / n_sims)
    if powers[0] >= power:
        return deltas[0]
    for (d0, p0), (d1, p1) in zip(zip(deltas, powers), zip(deltas[1:], powers[1:])):
        if p0 < power <= p1:
            return d0 + (power - p0) * (d1 - d0) / (p1 - p0)
    return math.inf
