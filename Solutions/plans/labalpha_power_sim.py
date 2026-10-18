#!/usr/bin/env python3
"""Lab alpha power simulation (DVR4 repair plan section 3.4). Author-only; standard library only.

The cleaned copy of the plan's probe scripts (author-probes/dvr4-plan/power_sim.py,
designs.py and checks.py, 2026-10-17): the same model, the same random streams and the
same floating-point order, so `grid`, `designs` and `checks` reproduce the archived
power_results.json, design_results.json and checks_log.txt exactly. The freeze records
this file's sha256 (power_sim_sha256).

Model of one run (one task x one repeat x one arm, budget B = 10 node calls):
  per-call success probability p = logistic(b0 + beta*arm + u_c + arm*(tau*z_c + eta_t) + w_t)
  the first-success call T ~ Geometric(p); the run's AUC = max(0, B - T + 1) / B
  u_c ~ N(0, su^2) cluster effect; z_c ~ N(0, 1) the cluster's effect heterogeneity;
  w_t ~ N(0, sw^2) task effect shared by both arms (they run on the same tasks);
  eta_t ~ N(0, 0.5^2) task-by-arm interaction.
  ICC (latent scale) = su^2 / (su^2 + sw^2 + pi^2/3); b0 is calibrated by bisection so that
  the raw arm's mean AUC is the target (0.35 or 0.60).
Estimand: the mean over clusters of AUC_obl(c) - AUC_raw(c). Test: the exact two-sided
paired t-test on the cluster differences at alpha = 0.05 (checked against the sign-flip
permutation test, the frozen primary test, by `checks`). MDE: the true delta at 80 % power,
linear interpolation in beta.

Usage (run under `systemd-run --user --scope -p MemoryMax=4G`):
  labalpha_power_sim.py grid [REPS]     the MDE grid (archived run: REPS = 600)
  labalpha_power_sim.py designs         the five candidate confirmatory designs
  labalpha_power_sim.py checks          sign-flip vs t, type-I error, the old design, m = 1, r
  labalpha_power_sim.py cell SIZES R BASE ICC TAU [N_SIMS N_DELTA SEED]
                                        one cell in fvh.stats.mde_paired_clusters_sim's
                                        stream order (a fresh random.Random(SEED) per
                                        cell; SIZES like 2:50,1:30): the cross-check of
                                        the frozen-core port, which must print the same
                                        value to the last digit
Outputs go to the current directory (power_results.json, design_results.json).
"""
import itertools
import json
import math
import random
import statistics
import sys

B = 10
SEED = 20261017
SW = 0.5            # task-effect sd
TA = 0.5            # task-by-arm interaction sd (eta)
BETAS = [0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0, 1.3, 1.7]


def logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


def run_auc(p, rng):
    if p >= 1.0:
        return 1.0
    u = rng.random()
    t = 1 + int(math.log(1.0 - u) / math.log(1.0 - p))     # geometric, support 1..
    return max(0, B - t + 1) / B


def dataset(K, m, r, b0, beta, su, sw, tau, rng, ta=TA):
    """K clusters of m tasks, r repeats per arm: the cluster differences d_c."""
    d = []
    for _ in range(K):
        uc = rng.gauss(0, su); zc = rng.gauss(0, 1)
        tot0 = tot1 = 0.0
        for _t in range(m):
            wt = rng.gauss(0, sw); it = rng.gauss(0, ta)
            p0 = logistic(b0 + uc + wt)
            p1 = logistic(b0 + beta + uc + tau * zc + it + wt)
            for _ in range(r):
                tot0 += run_auc(p0, rng); tot1 += run_auc(p1, rng)
        d.append((tot1 - tot0) / (m * r))
    return d


def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > FPMIN else FPMIN); h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > FPMIN else FPMIN)
        c = 1 + aa / c; c = c if abs(c) > FPMIN else FPMIN; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > FPMIN else FPMIN)
        c = 1 + aa / c; c = c if abs(c) > FPMIN else FPMIN
        de = d * c; h *= de
        if abs(de - 1) < EPS:
            break
    return h


def _ibeta(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x)
                  + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def t_pvalue(d):
    """Exact two-sided one-sample Student t p-value (H0: mean 0)."""
    n = len(d); mu = statistics.fmean(d); sd = statistics.stdev(d)
    if sd == 0:
        return 1.0 if mu == 0 else 0.0
    t = mu / (sd / math.sqrt(n)); df = n - 1
    return _ibeta(df / 2, 0.5, df / (df + t * t))


def signflip_p(d, rng, nperm=2000):
    obs = abs(sum(d)); cnt = 1
    for _ in range(nperm):
        s = sum(x if rng.random() < 0.5 else -x for x in d)
        if abs(s) >= obs - 1e-12:
            cnt += 1
    return cnt / (nperm + 1)


def true_delta(b0, beta, su, sw, tau, rng, n=40000, ta=TA):
    """The population mean of the per-run AUC difference (the estimand), and the raw AUC."""
    acc = 0.0; base = 0.0
    for _ in range(n):
        uc = rng.gauss(0, su); zc = rng.gauss(0, 1); wt = rng.gauss(0, sw); it = rng.gauss(0, ta)
        p0 = logistic(b0 + uc + wt); p1 = logistic(b0 + beta + uc + tau * zc + it + wt)
        e0 = sum(1 - (1 - p0) ** b for b in range(1, B + 1)) / B   # a geometric run's AUC
        e1 = sum(1 - (1 - p1) ** b for b in range(1, B + 1)) / B
        acc += e1 - e0; base += e0
    return acc / n, base / n


def su_for_icc(icc, sw):
    resid = sw * sw + math.pi ** 2 / 3
    return math.sqrt(icc * resid / (1 - icc))


def calibrate_b0(target, su, sw=SW):
    lo, hi = -6.0, 4.0
    for _ in range(25):
        mid = (lo + hi) / 2
        if true_delta(mid, 0.0, su, sw, 0.0, random.Random(7), 6000, 0.0)[1] < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def interpolate(seq, level=0.8):
    for (d0, p0), (d1, p1) in zip(seq, seq[1:]):
        if p0 < level <= p1:
            return d0 + (level - p0) * (d1 - d0) / (p1 - p0)
    return None


def grid(reps):
    rng = random.Random(SEED)
    targets = {"base~0.35": 0.35, "base~0.60": 0.60}
    rows = []
    for (blabel, target), icc, tau in itertools.product(targets.items(), [0.05, 0.15, 0.30],
                                                        [0.0, 0.5, 1.0]):
        su = su_for_icc(icc, SW)
        b0 = calibrate_b0(target, su)
        deltas = {beta: true_delta(b0, beta, su, SW, tau, rng) for beta in BETAS}
        for K in [20, 40, 60, 80, 100, 120]:
            pw = {}
            for beta in BETAS:
                hits = 0
                for _ in range(reps):
                    if t_pvalue(dataset(K, 2, 3, b0, beta, su, SW, tau, rng)) < 0.05:
                        hits += 1
                pw[beta] = hits / reps
            seq = [(deltas[b][0], pw[b]) for b in BETAS]
            mde = interpolate(seq)
            if mde is None and seq[0][1] >= 0.8:
                mde = f"<= {seq[0][0]:.3f}"
            rows.append(dict(baseline=blabel, base_auc=round(deltas[BETAS[0]][1], 3), icc=icc,
                             tau=tau, K=K, power={f"{deltas[b][0]:.3f}": pw[b] for b in BETAS},
                             mde=(round(mde, 3) if isinstance(mde, float) else mde)))
            print(json.dumps(rows[-1]), flush=True)
    json.dump(rows, open("power_results.json", "w"), indent=1)


def dataset_mix(Kr, Kp, r, b0, beta, su, sw, tau, rng):
    return dataset(Kr, 2, r, b0, beta, su, sw, tau, rng) + dataset(Kp, 1, r, b0, beta, su, sw,
                                                                    tau, rng)


DESIGNS = {"A 40x2+20x1 r3": (40, 20, 3), "B 50x2+30x1 r2": (50, 30, 2),
           "C 50x2+30x1 r3": (50, 30, 3), "D 60x2+40x1 r2": (60, 40, 2),
           "E 60x2+0x1 r3": (60, 0, 3)}


def designs():
    betas = [0.2, 0.3, 0.45, 0.6, 0.8, 1.0, 1.3]
    rng = random.Random(SEED); out = []
    for base in (0.35, 0.60):
        for icc in (0.15,):
            su = su_for_icc(icc, SW)
            b0 = calibrate_b0(base, su)
            for tau in (0.5, 1.0):
                deltas = {b: true_delta(b0, b, su, SW, tau, rng, 30000)[0] for b in betas}
                for name, (Kr, Kp, r) in DESIGNS.items():
                    pw = {}
                    for b in betas:
                        pw[b] = sum(t_pvalue(dataset_mix(Kr, Kp, r, b0, b, su, SW, tau, rng)) < 0.05
                                    for _ in range(1000)) / 1000
                    seq = [(deltas[b], pw[b]) for b in betas]
                    mde = interpolate(seq)
                    mde = round(mde, 3) if mde is not None else None
                    calls = (2 * Kr + Kp) * r * 10
                    row = dict(base=base, icc=icc, tau=tau, design=name, mde=mde,
                               primary_calls=2 * calls, four_arm_calls=4 * calls)
                    out.append(row); print(json.dumps(row), flush=True)
    json.dump(out, open("design_results.json", "w"), indent=1)


def checks():
    rng = random.Random(99)
    su = su_for_icc(0.15, SW)
    b0 = calibrate_b0(0.35, su)
    print("b0", round(b0, 3))
    for K, beta in [(60, 0.45), (20, 0.6)]:          # 1) t vs sign-flip agreement
        ht = hp = 0; R = 300
        for _ in range(R):
            d = dataset(K, 2, 3, b0, beta, su, SW, 0.5, rng)
            ht += t_pvalue(d) < 0.05; hp += signflip_p(d, rng, 999) < 0.05
        print("K", K, "beta", beta, "t-power", ht / R, "signflip-power", hp / R, "delta",
              round(true_delta(b0, beta, su, SW, 0.5, rng, 20000)[0], 3))
    for K in [20, 60]:                               # 2) type-I error at beta = 0
        h = 0; R = 1000
        for _ in range(R):
            h += t_pvalue(dataset(K, 2, 3, b0, 0.0, su, SW, 0.5, rng)) < 0.05
        print("type I K", K, h / R)
    for beta in [0.45, 0.8, 1.3]:                    # 3) the old design: 20 clusters, alpha/40
        h = 0; R = 1000
        for _ in range(R):
            h += t_pvalue(dataset(20, 2, 3, b0, beta, su, SW, 0.5, rng)) < 0.05 / 40
        print("current-design K20 alpha/40 beta", beta, "power", h / R, "delta",
              round(true_delta(b0, beta, su, SW, 0.5, rng, 20000)[0], 3))
    for beta in [0.45, 0.8]:                         # 4) single-task clusters, K = 60
        h = 0; R = 1000
        for _ in range(R):
            h += t_pvalue(dataset(60, 1, 3, b0, beta, su, SW, 0.5, rng)) < 0.05
        print("m=1 K60 beta", beta, "power", h / R)
    for r in [2, 3]:                                 # 5) two vs three repeats at K = 80
        h = 0; R = 1000
        for _ in range(R):
            h += t_pvalue(dataset(80, 2, r, b0, 0.45, su, SW, 1.0, rng)) < 0.05
        print("r", r, "K80 beta0.45 tau1.0 power", h / R)


def cell(sizes, repeats, base, icc, tau, n_sims=1000, n_delta=30000, seed=SEED, betas=BETAS):
    """One design cell in fvh.stats.mde_paired_clusters_sim's stream order."""
    su = su_for_icc(icc, SW)
    b0 = calibrate_b0(base, su)
    rng = random.Random(seed)
    deltas = [true_delta(b0, b, su, SW, tau, rng, n_delta)[0] for b in betas]
    powers = []
    for b in betas:
        hits = 0
        for _ in range(n_sims):
            d = []
            for size in sorted(sizes, reverse=True):
                d += dataset(sizes[size], size, repeats, b0, b, su, SW, tau, rng)
            hits += t_pvalue(d) < 0.05
        powers.append(hits / n_sims)
    if powers[0] >= 0.8:
        return deltas[0]
    mde = interpolate(list(zip(deltas, powers)))
    return math.inf if mde is None else mde


def main(argv):
    if not argv:
        print(__doc__); return 2
    cmd = argv[0]
    if cmd == "grid":
        grid(int(argv[1]) if len(argv) > 1 else 600)
    elif cmd == "designs":
        designs()
    elif cmd == "checks":
        checks()
    elif cmd == "cell":
        sizes = {int(a): int(b) for a, b in (x.split(":") for x in argv[1].split(","))}
        rest = [int(x) for x in argv[6:9]]
        print(repr(cell(sizes, int(argv[2]), float(argv[3]), float(argv[4]), float(argv[5]),
                        *rest)))
    else:
        print(__doc__); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
