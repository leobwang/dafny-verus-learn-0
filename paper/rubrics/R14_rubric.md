# R14 rubric — SMT mechanics

Use CORE.md and code-review bar production. Fixture compilation is local validation; live
model grading and contractor sessions remain D45 debt.

Solution pins (filled by scripts/update_rubric_pins.sh):
paper/solutions/R14_solutions.tex  sha256 89c13097f2c154a4a0cc46799a27e8621dde3d8cec1317051aa677abb780ca01
paper/R14_problems.tex  sha256 78c46d3881aa11ab4fecdf76f801b76aab0ee2fc59614f44f081d4974350070e
Solutions/dafny/R/R14_Smt/std/R14_Smt.dfy  sha256 558de5dcd1b5f730b9eae509dd9ce0e849c1d31ce9684bfcbf8b9755d01a8127
Solutions/verus/r/r14_smt/src/lib.rs  sha256 7a2ecd0b29983f220a07379c0362b484e053cb5e8d5214a9c08263c310242c15
Solutions/tools/R14/trigscan.py  sha256 7d4055fcd43163672f8504573bbbc99b1e4595ef9dc57c7cc0af53f637a847d5

## Verifier anchors

- **Probe A:** reproduce the exact B1 local source hash; drift needs an author re-pin.
- **Probe B:** for the learner's dischargeability example, run the true fact with an empty
  body and with the learner's trigger term or theory annotation; retain both verdicts.
- **Probe C:** recompute the learner's B2 statistics from their table: the CV over the
  verified runs and `fvh.stats.bootstrap_ci` of the mean with the stated seed; for any
  out-of-resource run, a Wilson interval for the proportion (`fvh.stats.wilson_interval`).
- **Probe D:** rerun one row of the learner's table (`scripts/vcheck --json --measures
  --seed N` on the stated target); a verdict that differs is drift, recorded, not graded.
- **Probe E:** the trigscan delivery against `python3 tools/R14/test_trigscan.py` and one
  fresh capture (`scripts/vcheck <file> -- --triggers-mode verbose`), never a filtered goal.

## B1 — Solver-aware agentic program verification (paper-card; dimension: card-fidelity)

### card-fidelity

- **CF.a:** grade all eight fields separately; the minimum is the card score. Empty fields
  score 1 and accurate source-bounded paraphrases score 4.
- **CF.b:** the oracle is the solvers' `unsat` on every local obligation plus concrete
  replay for "unsafe", with lemma sufficiency and justification checks and a final source
  re-check; SMT-file edits are diagnostic only. An answer that makes the agent the judge, or
  omits the justification check, scores at most 2.
- **CF.c:** the rates keep their suites and denominators (1367 of 1475; per-suite rates);
  baselines with different models are not controlled comparisons; no repeated runs means no
  variance or interval. An invented interval, cost or pooled ranking scores at most 2,
  quoting source and learner lines.
- **CF.d:** dischargeability is illustrated with a true fact from R14 that needs a trigger
  term, fuel or a theory annotation (Probe B), and the course tools' scope is stated: they
  read patterns the solver was given, not instances, and decide nothing. Claiming that
  `trigscan` or the SMT log implements the card's interface scores at most 2.

## B2 — What a CV sweep licenses (statistics; dimension: inference-scope)

### inference-scope

- **IS.a:** every run reported with seed, verdict, resource count and wall time, and the
  fixed settings named (pins, limit, target digest, machine). A dropped run, or an
  out-of-resource run reported without its seed, scores at most 2.
- **IS.b:** the CV is computed over the verified runs only and the interval with the
  stated method and seed (Probe C); out-of-resource runs are reported as a proportion, not
  averaged (their count is the limit, a censored value). Averaging them in scores at most 2.
- **IS.c:** the licence is scoped to these seeds, this toolchain and this machine; no claim
  about another Z3 version, another seed range or "stability" in general; the done rule
  (gate) and the sweep (measurement) are distinguished. An unscoped stability claim scores
  at most 2.
- **IS.d:** a comparison is a test only if fixed before the runs, with its statistic named.
  A post-hoc comparison called a test scores at most 2.

## Code and toolsmith

All hand references and final deliveries gate at zero counted holes, audit clean, and
preserve the shipped statements (`scripts/specfreeze --check R14`). H1 is `CatIntroV`
(the slice equations that make the left part's match a trigger term), H2 `StarPowV` (an
induction whose step names the first chunk's slice), H3 `DerivSizeV` (a structural
induction ending in product inequalities; in Verus `by (nonlinear_arith)` in a helper and
`reveal_with_fuel(node_count, 3)` in the Cat case). Under the production bar, look for:
the trigger term stated rather than a lemma that restates the goal; no lever added
(`{:induction}`, `{:fuel}` on a hole's lemma, resource attributes); nonlinear queries whose
`requires` lists exactly what they need. The toolsmith's delivery implements only
`scan_trigger_notes_r14`: every claim it reports is backed by bytes of the supplied capture;
missing, external and malformed spans stay so; nothing is read from another file. The
battery report is read cell by cell: the learner's audit names why each baseline failed and
why the closing candidate closed it. All five predictions keep their first-try records.

## Calibration fixtures

Gold: 4 in both dimensions. Flawed: B1 calls the course's `trigscan` an implementation of the
card's obligation interface and invents a 95 % interval for the 92.7 % rate (CF.c, CF.d), and
B2 averages out-of-resource runs into the mean, claims the proof "is stable under any seed"
and calls a comparison chosen after the runs a test (IS.b–IS.d), so both dimensions score at
most 2 with quoted learner lines. These are expected outcomes, not completed live grading
sessions.
