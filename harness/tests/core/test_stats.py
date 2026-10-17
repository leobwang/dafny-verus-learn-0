"""The frozen core's own tests: fvh.stats (QPLAN §11.8).

Known values come from outside the core: closed forms worked by hand, the
defining property of each estimator checked by an independent route (the
Wilson interval as the set of proportions its score test accepts, pass@k by
enumerating draws), and published reference values (statsmodels 0.15.0's
`proportion_confint(method="wilson")` and `mcnemar`, captured 2026-10-05).
The resampling functions are checked for determinism, invariance and their
documented formulas.
"""

import itertools
import math
import statistics

import pytest

from fvh import stats


# --- pass_at_k -------------------------------------------------------------------------

@pytest.mark.parametrize("n,c,k,want", [
    (5, 0, 1, 0.0),
    (5, 5, 1, 1.0),
    (4, 1, 1, 0.25),
    (4, 2, 2, 5 / 6),          # 1 - C(2,2)/C(4,2) = 1 - 1/6
    (6, 1, 6, 1.0),            # n - c < k: every draw holds the correct sample
    (8, 2, 7, 1.0),
    (200, 1, 1, 0.005),
    (12, 4, 3, 1 - 56 / 220),  # 1 - C(8,3)/C(12,3)
])
def test_pass_at_k_known_values(n, c, k, want):
    assert stats.pass_at_k(n, c, k) == pytest.approx(want, abs=1e-15)


def test_pass_at_k_is_the_probability_that_a_draw_of_k_holds_a_correct_sample():
    n, c, k = 7, 2, 3
    samples = [True] * c + [False] * (n - c)
    draws = list(itertools.combinations(range(n), k))
    hits = sum(1 for d in draws if any(samples[i] for i in d))
    assert stats.pass_at_k(n, c, k) == pytest.approx(hits / len(draws), abs=1e-15)


def test_pass_at_k_is_exact_for_large_counts():
    # 1 - C(999, 1) / C(1000, 1) = 1/1000, with no cancellation error
    assert stats.pass_at_k(1000, 1, 1) == 0.001
    assert 0.0 < stats.pass_at_k(10_000, 1, 2) < 1.0


@pytest.mark.parametrize("n,c,k", [(5, 6, 1), (5, -1, 1), (5, 2, 0), (5, 2, 6), (0, 0, 1)])
def test_pass_at_k_rejects_out_of_range_arguments(n, c, k):
    with pytest.raises(ValueError):
        stats.pass_at_k(n, c, k)


@pytest.mark.parametrize("args", [(5.0, 1, 1), (5, True, 1), (5, 1, "2")])
def test_pass_at_k_rejects_non_integers(args):
    with pytest.raises(TypeError):
        stats.pass_at_k(*args)


# --- wilson_interval -------------------------------------------------------------------

# statsmodels 0.15.0 proportion_confint(s, n, alpha=1 - confidence, method="wilson")
WILSON = [
    (0, 10, 0.95, 0.0, 0.2775327998628892),
    (10, 10, 0.95, 0.7224672001371107, 1.0),
    (1, 1, 0.95, 0.20654931437723745, 1.0),
    (500, 1000, 0.95, 0.4690696003681042, 0.5309303996318958),
    (3, 50, 0.95, 0.02061497034897397, 0.16217091688838173),
    (3, 50, 0.9, 0.02423125703121838, 0.14094194646069935),
    (17, 40, 0.99, 0.24890358835262436, 0.6224373936735131),
    (1, 7, 0.95, 0.02567962434474355, 0.5131278292743189),
]


@pytest.mark.parametrize("s,n,conf,lo,hi", WILSON)
def test_wilson_interval_reference_values(s, n, conf, lo, hi):
    got = stats.wilson_interval(s, n, conf)
    assert got == pytest.approx((lo, hi), abs=1e-12)


def _accepts(s, n, conf, p):
    """The Wilson interval's defining score test, by an independent route."""
    z = statistics.NormalDist().inv_cdf(0.5 + conf / 2)
    return abs(s / n - p) <= z * math.sqrt(p * (1 - p) / n)


def _edge(s, n, conf, inside, outside):
    for _ in range(200):
        mid = (inside + outside) / 2
        if _accepts(s, n, conf, mid):
            inside = mid
        else:
            outside = mid
    return inside


@pytest.mark.parametrize("s,n,conf", [(2, 9, 0.95), (37, 60, 0.95), (8, 11, 0.8), (49, 50, 0.99)])
def test_wilson_interval_is_the_set_its_score_test_accepts(s, n, conf):
    lo, hi = stats.wilson_interval(s, n, conf)
    p_hat = s / n
    assert lo == pytest.approx(_edge(s, n, conf, p_hat, 0.0), abs=1e-12)
    assert hi == pytest.approx(_edge(s, n, conf, p_hat, 1.0), abs=1e-12)


def test_wilson_interval_ends_are_exact_at_the_extremes():
    assert stats.wilson_interval(0, 25)[0] == 0.0
    assert stats.wilson_interval(25, 25)[1] == 1.0


def test_wilson_interval_default_confidence_is_95_percent():
    assert stats.wilson_interval(9, 30) == stats.wilson_interval(9, 30, 0.95)


def test_wilson_interval_widens_with_confidence_and_narrows_with_n():
    a, b, c = (stats.wilson_interval(12, 40, x) for x in (0.8, 0.95, 0.99))
    assert a[0] > b[0] > c[0] and a[1] < b[1] < c[1]
    small, big = stats.wilson_interval(12, 40), stats.wilson_interval(120, 400)
    assert big[1] - big[0] < small[1] - small[0]


@pytest.mark.parametrize("args", [(3, 0), (-1, 5), (6, 5), (2, 5, 0.0), (2, 5, 1.0), (2, 5, 1.5)])
def test_wilson_interval_rejects_out_of_range_arguments(args):
    with pytest.raises(ValueError):
        stats.wilson_interval(*args)


# --- bootstrap_ci ----------------------------------------------------------------------

VALUES = [0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0]


def test_bootstrap_ci_is_deterministic_given_the_seed():
    data = [0.31, 1.7, 2.25, 0.9, 4.4, 3.05, 2.6, 0.12, 1.15]
    a = stats.bootstrap_ci(data, seed=7, n_resamples=2000)
    assert a == stats.bootstrap_ci(data, seed=7, n_resamples=2000)
    assert a != stats.bootstrap_ci(data, seed=8, n_resamples=2000)


def test_bootstrap_ci_brackets_the_statistic_and_lies_in_the_data_range():
    lo, hi = stats.bootstrap_ci(VALUES, seed=3)
    assert 0.0 <= lo <= statistics.fmean(VALUES) <= hi <= 1.0
    assert lo < hi


def test_bootstrap_ci_of_constant_data_is_a_point():
    assert stats.bootstrap_ci([2.5] * 9, seed=1, n_resamples=500) == (2.5, 2.5)


def test_bootstrap_ci_takes_any_statistic():
    lo, hi = stats.bootstrap_ci([1.0, 2.0, 3.0, 4.0, 100.0], statistics.median, seed=5,
                                n_resamples=3000)
    assert 1.0 <= lo <= 3.0 <= hi <= 100.0


def test_bootstrap_ci_is_the_percentile_interval_of_the_resampled_statistics():
    import random
    data = [3.0, 7.5, 1.25, 9.0, 4.0, 6.5, 2.0]
    rng = random.Random(11)
    reps = [statistics.fmean(rng.choices(data, k=len(data))) for _ in range(401)]
    # the 'inclusive' quantiles interpolate linearly at position q * (N - 1): at 90%,
    # the 1st and 19th of the 20-quantiles are the 0.05 and 0.95 quantiles
    cuts = statistics.quantiles(reps, n=20, method="inclusive")
    got = stats.bootstrap_ci(data, seed=11, n_resamples=401, confidence=0.9)
    assert got == pytest.approx((cuts[0], cuts[18]), abs=1e-12)


@pytest.mark.parametrize("kwargs", [dict(values=[]), dict(values=[1.0], n_resamples=0),
                                    dict(values=[1.0], confidence=1.0)])
def test_bootstrap_ci_rejects_bad_arguments(kwargs):
    with pytest.raises(ValueError):
        stats.bootstrap_ci(seed=0, **kwargs)


def test_bootstrap_ci_needs_a_seed():
    with pytest.raises(TypeError):
        stats.bootstrap_ci(VALUES)


# --- mcnemar ---------------------------------------------------------------------------

# statsmodels 0.15.0 mcnemar([[0, b], [c, 0]], exact=True / exact=False, correction=True)
MCNEMAR = [
    (10, 2, 0.03857421875, 0.04330814281079206),
    (0, 6, 0.03125, 0.041226833337163815),
    (1, 0, 1.0, 1.0),
    (25, 12, 0.04703102743951604, 0.04851973828025081),
    (3, 9, 0.14599609375, 0.14891467317876161),
]


@pytest.mark.parametrize("b,c,exact,approx", MCNEMAR)
def test_mcnemar_reference_values(b, c, exact, approx):
    assert stats.mcnemar(b, c) == pytest.approx(exact, abs=1e-15)
    assert stats.mcnemar(b, c, exact=False) == pytest.approx(approx, abs=1e-12)


def test_mcnemar_exact_is_twice_the_smaller_binomial_tail():
    # b = 10, c = 2: 2 * (C(12,0) + C(12,1) + C(12,2)) / 2^12 = 158 / 4096
    assert stats.mcnemar(10, 2) == 158 / 4096
    assert stats.mcnemar(2, 10) == stats.mcnemar(10, 2)


def test_mcnemar_without_discordant_pairs_or_with_balanced_ones_is_one():
    assert stats.mcnemar(0, 0) == 1.0
    assert stats.mcnemar(0, 0, exact=False) == 1.0
    assert stats.mcnemar(5, 5) == 1.0
    # the continuity correction never pushes |b - c| - 1 below zero
    assert stats.mcnemar(5, 5, exact=False) == 1.0


def test_mcnemar_rejects_negative_counts():
    with pytest.raises(ValueError):
        stats.mcnemar(-1, 3)


# --- permutation_test ------------------------------------------------------------------

def test_permutation_test_identical_samples_give_one():
    x = [0.2, 0.5, 0.9, 0.4]
    assert stats.permutation_test(x, list(x), paired=True, seed=1) == 1.0
    assert stats.permutation_test(x, list(x), paired=False, seed=1) == 1.0


def test_permutation_test_paired_one_sided_shift_matches_the_exact_sign_flip_value():
    # 12 differences all +1: of the 2^12 sign patterns exactly 2 reach |sum| = 12, so
    # the exact p-value is 2/4096; the Monte Carlo estimate (hits + 1)/(N + 1) is close.
    y = [float(v) for v in range(12)]
    x = [v + 1.0 for v in y]
    p = stats.permutation_test(x, y, paired=True, n_permutations=20_000, seed=4)
    assert 1 / 20_001 <= p <= 0.002
    assert p == stats.permutation_test(x, y, paired=True, n_permutations=20_000, seed=4)


def test_permutation_test_unpaired_separated_groups_give_a_small_p():
    x = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    y = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    # exact: 2 of the C(12,6) = 924 splits are as extreme
    p = stats.permutation_test(x, y, paired=False, n_permutations=20_000, seed=9)
    assert p == pytest.approx(2 / 924, abs=0.0015)


def test_permutation_test_is_symmetric_and_deterministic():
    x, y = [1.0, 4.0, 2.0, 8.0, 5.0], [2.0, 1.0, 0.5, 3.0, 1.0]
    for paired in (True, False):
        a = stats.permutation_test(x, y, paired=paired, n_permutations=3000, seed=2)
        assert a == stats.permutation_test(y, x, paired=paired, n_permutations=3000, seed=2)
        assert a == stats.permutation_test(x, y, paired=paired, n_permutations=3000, seed=2)
        assert 0.0 < a <= 1.0


def test_permutation_test_unpaired_ignores_the_order_inside_each_sample():
    x, y = [1.0, 4.0, 2.0, 8.0], [2.0, 1.0, 0.5, 3.0, 1.0, 7.0]
    a = stats.permutation_test(x, y, paired=False, n_permutations=2000, seed=6)
    assert a == stats.permutation_test(x[::-1], sorted(y), paired=False, n_permutations=2000,
                                       seed=6)


@pytest.mark.parametrize("x,y,paired", [([], [1.0], False), ([1.0], [], True),
                                        ([1.0, 2.0], [1.0], True)])
def test_permutation_test_rejects_bad_samples(x, y, paired):
    with pytest.raises(ValueError):
        stats.permutation_test(x, y, paired=paired, seed=0)


# --- holm ------------------------------------------------------------------------------

def test_holm_steps_down_and_stops_at_the_first_acceptance():
    # sorted 0.005 <= .05/4, 0.01 <= .05/3, 0.03 > .05/2: stop
    assert stats.holm([0.01, 0.04, 0.03, 0.005]) == [True, False, False, True]


def test_holm_rejects_everything_below_the_bonferroni_bar_and_nothing_above_alpha():
    assert stats.holm([0.001, 0.002, 0.003]) == [True, True, True]
    assert stats.holm([0.2, 0.6]) == [False, False]


def test_holm_stops_even_if_a_later_p_would_pass_its_own_bar():
    # 0.03 > 0.05/2 stops the procedure, so 0.04 <= 0.05/1 is not rejected
    assert stats.holm([0.03, 0.04]) == [False, False]


def test_holm_uses_alpha_and_keeps_input_order():
    assert stats.holm([0.04, 0.001], alpha=0.1) == [True, True]
    assert stats.holm([]) == []


@pytest.mark.parametrize("ps,alpha", [([1.2], 0.05), ([-0.1], 0.05), ([0.1], 0.0)])
def test_holm_rejects_bad_arguments(ps, alpha):
    with pytest.raises(ValueError):
        stats.holm(ps, alpha)


# --- mde_two_proportions ---------------------------------------------------------------

def _n_unpaired(p0, p1, alpha=0.05, power=0.8):
    """Fleiss's per-arm sample size (no continuity correction), written out."""
    nd = statistics.NormalDist()
    za, zb = nd.inv_cdf(1 - alpha / 2), nd.inv_cdf(power)
    pbar = (p0 + p1) / 2
    num = za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))
    return (num / (p1 - p0)) ** 2


def _n_paired(p0, p1, alpha=0.05, power=0.8):
    """Connor's McNemar sample size with the independence discordance rate."""
    nd = statistics.NormalDist()
    za, zb = nd.inv_cdf(1 - alpha / 2), nd.inv_cdf(power)
    d = p1 - p0
    psi = p0 * (1 - p1) + p1 * (1 - p0)
    return ((za * math.sqrt(psi) + zb * math.sqrt(psi - d * d)) / d) ** 2


def test_mde_unpaired_matches_the_textbook_sample_size():
    # 0.50 -> 0.75 needs 57.7 tasks per arm (the familiar 58 of the tables)
    assert _n_unpaired(0.5, 0.75) == pytest.approx(57.67, abs=0.01)
    assert stats.mde_two_proportions(58, 0.5) < 0.25 < stats.mde_two_proportions(57, 0.5)


@pytest.mark.parametrize("n,p0,paired", [(30, 0.3, False), (120, 0.6, False), (45, 0.5, True),
                                         (200, 0.2, True)])
def test_mde_round_trips_through_the_sample_size_formula(n, p0, paired):
    d = stats.mde_two_proportions(n, p0, paired=paired)
    need = _n_paired if paired else _n_unpaired
    assert 0.0 < d <= 1.0 - p0
    assert need(p0, p0 + d) == pytest.approx(n, rel=1e-9)


def test_mde_shrinks_with_n_and_with_lower_power():
    a, b = stats.mde_two_proportions(40, 0.4), stats.mde_two_proportions(160, 0.4)
    assert b < a
    assert stats.mde_two_proportions(40, 0.4, power=0.5) < a
    assert stats.mde_two_proportions(40, 0.4, alpha=0.01) > a


def test_mde_is_infinite_when_no_difference_is_detectable():
    assert stats.mde_two_proportions(2, 0.5) == math.inf


@pytest.mark.parametrize("args,kwargs", [((0, 0.5), {}), ((10, 0.0), {}), ((10, 1.0), {}),
                                         ((10, 0.5), {"power": 1.0}), ((10, 0.5), {"alpha": 0.0})])
def test_mde_rejects_bad_arguments(args, kwargs):
    with pytest.raises(ValueError):
        stats.mde_two_proportions(*args, **kwargs)
