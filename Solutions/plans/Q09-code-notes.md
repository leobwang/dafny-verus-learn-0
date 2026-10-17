# Q09 code notes (DV3b Q09 lane, as built)

> **Author-only.** Prediction answers, forensic species, the red-team bank's planted lemma,
> card-demo outcomes, gate results and the deviations of Q09's code from the plan. Never
> quote, paraphrase or link any of it from a learner-visible file. The plan is `QPLAN.md`
> §14 and §17 and `Solutions/plans/Q07-Q09-author-notes.md` §4 (with §0, §R and Appendices
> A.10, A.11, A.15); this file records what the Q09 lane built on 2026-10-06 and where it
> differs.

Every result below was captured on the pins through the course wrappers (`scripts/vcheck`,
`scripts/vaudit`, `scripts/specfreeze`, `scripts/pins.py`, `scripts/firsttry.sh`,
`scripts/reference_lint.py`, `scripts/dvl/python.py`) or through vcheck's own sweep
functions (`brittleness_rows`, for the per-row counts the CLI prints only as ranges), one
solver job at a time, each started with at least 87 GB available (`free -g`; the lane's share
is 16 GB, so 31 GB was the floor), under the `dvl` caps (Dafny 8 GB, Verus 16 GB),
`DVL_SCRATCH=/tmp/dvl0-dv3b-q09/dvl`. Probe files are lane scratch under
`/tmp/dvl0-dv3b-q09/` (not archived; the decisive ones are quoted here).

## 1. Files

| learner file | twin | shipped state (tool) |
|---|---|---|
| `dafny/Q/Q09_InternalsIII/std/Q09_InternalsIII.dfy` (unit `dafny/Q/Q09_InternalsIII/std`, nonlinear arithmetic on) | `Solutions/…/std/Q09_InternalsIII.dfy` | verified, 1 hole (H1d), 0 errors; prediction block P1d, P2dv, P3dv; W1d; C1d, C2d |
| `dafny/Q/Q09_InternalsIII/std/Q09_Triggers.dfy` (same unit; `module {:disableNonlinearArithmetic} Q09_Triggers`) | `Solutions/…/std/Q09_Triggers.dfy` | verified, 1 hole (T1d); unit 128 verified, 2 holes; twin unit 130 verified |
| `verus/q/q09_internals_iii/src/lib.rs` | `Solutions/…/src/lib.rs` | verified, 2 holes (T1v, H1v); twin crate 10 verified |
| `dafny/Q/Q09_InternalsIII/exit/Q09_Exit.dfy` | `Solutions/…/exit/Q09_Exit.dfy` | verified, 2 holes (X1d, X2d); twin 126 verified; the EXPLAIN-BACK block at its end |
| `verus/q/q09_internals_iii/src/exit.rs` | `Solutions/…/src/exit.rs` | verified, 2 holes (X1v, X2v); twin 6 verified |
| `dafny/Q/Q09_InternalsIII/agent/Q09_AgentRedTeam.dfy` | `Solutions/…/agent/Q09_AgentRedTeam.dfy` | verified, 4 holes (the BANK); twin 129 verified, `vaudit --ref` 0 |
| `verus/q/q09_internals_iii/src/agent.rs` | `Solutions/…/src/agent.rs` | verified, 4 holes; twin 4 verified, `vaudit --ref` 0 |
| `harness/q/fvh_q/gate/__init__.py` (empty), `harness/q/fvh_q/gate/core.py` | `Solutions/harness/q/fvh_q/gate/core.py` | 4 AST holes (H2py-H5py); acceptance tests 4 passed, 65 failed as shipped (4 passed, 66 failed after §11's added test); twin 68 passed + 1 skipped in the tools' overlay, 69 passed in place (69 + 1 skipped in the overlay after §11) |
| `harness/tests/q/gate/test_core.py` (frozen acceptance tests) | — | §4 |
| `harness/tests/q/fixtures/q09/<lang>/<ID>/*.json` (97 recordings, 43 fixtures) | — | §4 |
| `specimens/Q09/P6d … P10d.dfy.specimen`, `P11v … P15v.rs.specimen` | `Solutions/specimens/Q09/` (all ten) | slots unfilled; each delivery green in the learner loop (§3) |
| `specimens/Q09/P9d-frozen.dfy.specimen`, `P13v-witness.rs.specimen` (companions) | — | `// after:` the delivery's item, so H5 holds them closed |
| `specimens/Q09/card-c1d.dfy.specimen`, `card-c1v.rs.specimen` (`// after: Q09.P1d`), `card-c2d.dfy.specimen`, `card-c2v.rs.specimen` (`// after: Q09.P2dv`) | — | WRITE failure demos, in-file `// EXPECT` pins (§5) |
| `slots/Q09.slots` | `Solutions/slots/Q09.slots` | 15 verdict lines `???` |
| `research/q09_forensics.md` (the DIAGNOSIS form), `research/EVAL.md` (a pointer comment under `Q-v1 — Q09`) | — | learner-owned, empty |

Pins: `expected/Q09.pins` (15 salted), `expected/Q09.counts` (schema 2: 2 units, Dafny reference 130 / floor 6, Verus 10 / floor 6; 8 files: the two exercise files of the Dafny unit 1 + 1 holes, `lib.rs` 2, exits 2 + 2, agents 4 + 4, `core.py` role harness, failed, 4 holes), `expected/Q09.freeze` (82 statements in 24 files, Python included; no `open_specs`: no Q09 item is a statement hole). No sidecar: Q09 has no divergence card, and the card demos are pinned in-file. No `.audit` pin (QPLAN §17.1).

## 2. Prediction answers (captured on the real scenarios)

| item | answer | capture |
|---|---|---|
| P1d | `D:timeout ok` | the quoted attempt as a probe, `scripts/vcheck --module Q09 --solver 4.12.1` (inconclusive, "Verification out of resource" at the lemma) and `--solver 4.14.1` (verified). `vcheck --module Q09 --brittleness --solvers`: 4.12.1 seeds 1-3 inconclusive (5,006,649 / 5,006,650 / 5,006,649), 4.14.1 seeds 1-3 verified (38,789 / 38,790 / 38,789); per-row counts through vcheck's `brittleness_rows` |
| P2dv | `D:timeout,timeout,timeout,unstable V:timeout,timeout,timeout,unstable` | the two quoted attempts as probes: Dafny in a `{:disableNonlinearArithmetic}` module (`vcheck --module Q09 --brittleness`: `seed 1: inconclusive · seed 2: inconclusive · seed 3: inconclusive — NOT stable`); Verus in the crate's context (the same line; rlimit 6,000,000 on each seed) |
| P3dv | `D:verified number V:verified null` | the two quoted files, `vcheck --json`: Dafny `verified`, `verified_count` 1, the hole `bodyless-method` listed; Verus `verified`, `verified_count` null, the `assume` hole listed |
| P4py | `c` | `fvh.stats.mde_two_proportions(60, 0.5)` = 0.2455 |
| P5py | `c` | `fvh.stats.wilson_interval(0, 9)` = (0.0, 0.2991) |
| P6d-P15v | §3 | |

`pins.py --update --ref --module Q09` wrote the pins; `pins.py --ref --module Q09`: 15 checks, 0 problems; `pins.py --ci --module Q09`: 44 pins, 0 problems (the four card EXPECT pins included).

## 3. The forensic deliveries

Species vocabulary (each delivery's header): `hole` a placeholder where nothing was written (a body-less lemma, `assume(false)`, `admit()`, an external body around nothing); `trusted` a step taken on trust although something was written (an assumption or axiom stating a fact, an external body around real code); `unchecked`, `vacuous`, `weak`, `healthy` as spec §3.14. The `hole`/`trusted` line is drawn so that Q03.P13v (`external_body` on an empty proof fn: `hole`) and P11v (`external_body` on real code: `trusted`) both hold (deviation 5).

| item | delivery | species | planted line | evidence (the scratch root `/tmp/dvl0-dv3b-q09/root`, first tries faked there only) |
|---|---|---|---|---|
| P6d | `MulLimbLengthBound` through `MulLimbCLength`, whose body is `assume {:axiom}` of the (true) length fact | trusted | the assume | learner loop and gate verified (5); `vaudit` 2 findings at it (`assume-axiom`, `audit-assume-axiom`) |
| P7d | `AddCommutes` through `{:verify false} AddCCommutes` (transparent copy of `AddC`) | unchecked | the attribute | learner loop verified with the `{:verify false}` warning; gate failed (warnings fail the gate); `vaudit` 2 findings (`verify-false`, `audit-verify-false`) |
| P8d | `CarryIsLimb`, `requires … && x + d >= 2 * BASE` (the claim is L4's `MulLimbDigit`) | vacuous | the `requires` | gate verified, `vaudit` 0; the swap copy (`ensures false`) verifies under `--gate` |
| P9d | `CmpSelf` delivered `ensures Cmp(a, a) <= 0`, claimed and frozen `== 0` | weak | the `ensures` | gate verified, `vaudit` 0; `specfreeze --against specimens/Q09/P9d-frozen.dfy.specimen` 1 finding, freeze-changed `Q09_P9.CmpSelf` |
| P10d | `AppendEmpty`, proved by `assert a + [] == a` | healthy | the assert | gate verified (3), `vaudit` 0 |
| P11v | `top_limb` through `#[verifier::external_body] last_limb`, whose code returns `v[0]`; its tests use one-limb numbers | trusted | `external_body` | learner loop verified, 1 hole (`external_body`); gate failed; `vaudit` 1 finding (`hole-external-body`); `vcheck --test`: 2 passed; with an added test on `vec![1, 2]` expecting 2: failed |
| P12v | `add_three` written outside `verus!`; inside, only the spec fn of its claim | unchecked | the fn line | learner loop verified, 0 verified; gate failed (verified 0 < 1; `outside-verus`); `vaudit` 1 finding (`outside-verus`) |
| P13v | `lemma_top_limb`, `requires seq_wf(s), s.len() > 0, s.last() == 0` | vacuous | the third `requires` | gate verified (1), `vaudit` 0; the witness companion (`lemma_top_limb(seq![5u64, 1u64])`) fails under `--gate`, "precondition not satisfied" |
| P14v | `lemma_value_of_first`, `ensures high_limbs_zero(s) ==> seq_to_nat(s) == s[0]` with `high_limbs_zero` ranging over `1 <= i <= s.len()` (one past the end) | weak | the quantifier | gate verified (1), `vaudit` 0 |
| P15v | `add_zero`, `big_add(a, &from_u64(0))` | healthy | the `let` | gate verified (1), `vaudit` 0 |

One feasible assignment of eight different instruments (the rubric accepts others): P6d the audit, P7d the lint (`verify-false`), P8d swap-to-false, P9d the freeze diff, P11v compiled code on inputs the tests avoided, P12v JSON completeness, P13v the witness, P14v a property sampler after reading the statement. `reference_lint.py --module Q09`: 0 findings (the ten twins carry a "Reference Solution:" paragraph in place of the slot instructions, as Q03's do).

## 4. The gate core, its tests and its recordings

- **Recording.** `env -u CI python -m fvh.tools.record --half Q --instrument "vcheck --gate" --instrument vaudit --instrument "specfreeze --check" --instrument witness --instrument swap-to-false` from `harness/` (memory preflight: 91 GB available, 31 needed): 97 results for 43 fixtures (Dafny 23, Verus 20), 0 failed, every exit 0 or 1 and matching the manifests' outcomes. `seed-rerun` was left out (the gate never calls it; G20, the resource DoS, is flagged by `vcheck --gate`'s inconclusive verdict). The recordings hold results only.
- **The reference** (`Solutions/harness/q/fvh_q/gate/core.py`) as the author notes §4.6, with the checks spelled out in each docstring: `json_complete` seven checks on the document's own fields (the document's `exit_code` is the verifier's, not vcheck's: a Verus gate failure on a lint finding carries verifier exit 0); `classify` FAILs on a missing gate or audit result, a killed or non-0/1 result, an incomplete or failing gate document, a flagging audit, freeze, witness or seed-rerun, or a swap that verifies, else PASS with GRADER_ONLY minus X07 (a witness ran and passed) and X08 (a freeze check ran and passed); `gate` picks the companions from `delivery.files` and calls `run` or `tools.run` (looked up at call time); `corpus_report` per the docstring. On the recorded Q half: 33 constructs FAIL, V14 PASS with (X07, X08, X14) and so held by `unknown`, the 9 controls PASS (C-07 and C-7 with (X08, X14)); `false_pass` 0, `fp` 0 of 9, `fp_interval` = `wilson_interval(0, 9)`.
- **Tests** (69; 70 after §11): synthetic documents and results for every check; the replayed Q half for `json_complete`, `classify`, `gate` and `corpus_report`; `classify(results)` and `gate(delivery, *, run=None)` signatures; label independence (the same verdicts under a neutral id, under a neutral id with neutral paths (§11), and with `fvh.corpus.load_half` replaced by a function that raises); `gate` through a replaced `fvh.tools.run`; a killed run FAILs; an instrument that cannot run raises; `corpus_report` composes `fvh.stats.wilson_interval` (replaced by a recording wrapper). The Q half's deliveries and labels are written out in the test file (`Q_HALF`), because the tools' scratch overlay (`dvl.python`'s `ref` and TRIV modes) copies only `harness/` and `fvh.corpus.load_half` cannot see `tests/corpus/` there; `test_q_half_matches_the_corpus` checks the table against `load_half` wherever the corpus is present (it passes in place and skips in the overlay).
- **Results.** `python3 scripts/dvl/python.py ref` on the twin: verified, 68 passed (1 skipped); `triv`: 4/4 (each `# triv:` body fails the tests); the learner file: failed, 4 passed, 65 failed, 4 holes; `hollow` and `lint` (learner and reference): 0 findings. The whole harness suite: only the hollow Q06 and Q09 tests fail (81), `tests/core` passes.
- **Live run** (the learner's own check; simulation copy, the twin as the learner's file): §7.

## 5. Cards

| card | success (in the exercise file) | failure demo (pinned in-file) | measurement |
|---|---|---|---|
| C1d `write:proof-split` | `ThreeLimbProduct`: four `Std.Arithmetic.Mul` facts | empty body: `a postcondition could not be proved` (line 15) in the specimen's own options | in the module's options: the split proof 9,866..10,054 in all six rows (both solvers × seeds 1-3); the empty body inconclusive in all six; a one-assertion version (`assert x * y < BASE * BASE;`) seed-brittle (verified under 4.12.1 seed 1 and 4.14.1 seed 1, failed or out of resource otherwise), so it is not the demo |
| C1v `write:proof-split` | `lemma_three_limb_product`: two scoped `nonlinear_arith` steps (4,358..4,383, seeds 1-3) | one whole-goal `nonlinear_arith` with no `requires`: `assertion failed` (line 21) | the failure fails quickly on every seed (1,671..1,699) |
| C2d `write:trigger-rewrite` | `ZerosNonEmpty`: the step `|Zeros(k + 1)| == |Zeros(k)| + 1` (opaque `Zeros`) triggered on `Zeros(k + 1)` | the same step triggered on `Zeros(k)`: `a postcondition could not be proved` (line 22) | good 11,306..11,522, looping 41,010..42,028, both solvers × seeds 1-3: from the goal's `Zeros(m + 1)` the looping trigger fires at `k = m + 1` and climbs, and never makes the instance at `k = m` the proof needs |
| C2v `write:trigger-rewrite` | `lemma_zeros_nonempty` (same design, `#[verifier::opaque] zeros`) | trigger on `zeros(k)`: `postcondition not satisfied` (line 32) | good 2,096, looping 1,065,819..1,067,765 (seeds 1-3) |

Rejected C2 designs (probes `c2d.dfy`, `c2x.dfy`, `c2y.dfy`, `c2z.dfy`, `c2d2.dfy`, `c2v.rs`): in Dafny's default options a looping trigger on a provable linear goal still verifies (the needed instances arrive early: costs 1.5x-100x the moved trigger, never a failure), and nonlinear goals made the moved-trigger version brittle too; a recursive monotonicity design failed only in Verus. The one-sided design fails for a reason the trigger alone decides. The notes' constraints hold: no `Pow`, `weight` or stand-in, no multi-pattern, no concatenation or limb sum in a stated fact; C1 bounds three factors below `BASE` with strict steps (no `(p - 1)` bound, which is X1's).

## 6. Holes, test-outs and exits: references, sweeps and the empty-body gate

References: the author notes §4.2 and §4.8 (A.10, A.15), unchanged in code; X1d/H1d call `Std.Arithmetic.Mul` as `Mul.`; the twins carry `// did:` receipts on every `nonlinear_arith` step. Sweeps (`vcheck --ref --brittleness`, Dafny `--solvers`): the Dafny unit twin and the Dafny exit twin stable in all six rows, the Verus crate twin and exit twin stable on seeds 1-3. Re-captured probes: H1d's reference 11,090..11,091 (4.12.1) and 11,203..11,204 (4.14.1); H1v's attempt failed on seeds 1-3 (1,210..1,244), its reference verified (3,898..3,947); X1d's empty body and its one-assertion `x * y <= (p - 1) * (p - 1)` out of resource in all six rows, X2d's quoted multi-trigger attempt out of resource in all six (5,010,369..5,010,385), X2d's three direct calls verified in all six; X1v's one scoped step verified (4,362..4,530), X2v's attempt at the rlimit on seeds 1-3, its three direct calls verified; T1d's reference stable under both solvers, its `cfree:` (no quantifier) stable too.

`firsttry.sh Q09 --empty-body` (2026-10-06, the pins, default modes and seeds): **10/12**, exit 1.

- Pass: H1d (every run fails; maxauto and the seeds `empty-body-inconclusive`), T1d (`lever-needed`: maxauto verifies, the shipped options fail), T1v, X1d, X2d, X2v; the forms gate on every form-carrying item: each twin meets its forms (the `stable` sweeps included), and each `cfree:` answer (T1d, T1v, H1v, X1v, X2d, X2v) fails its forms; the Python TRIV mode 4/4.
- **Fail: H1v and X1v, "FALLS TO AUTOMATION: the empty body verifies in NL seed=1, 2, 3".** The NL variant is `assert(<ensures>) by (nonlinear_arith) requires <requires>;`, which is exactly each item's construct-free answer (one scoped step) that the author notes §0.2 measured and that the `nl-steps:2` form exists to stop (QPLAN §6 Q43); the forms gate shows that answer failing the form. The tool judges the NL variant on verification alone. Not changed here: the statements are QPLAN §17.2's and §4.8's (paired with the Dafny halves), and only the tools can let the empty-body gate judge an NL or BV variant against the item's forms (open issue).

## 7. Learner-flow simulation (`/tmp/dvl0-dv3b-q09/sim`: a git copy of the worktree without `Solutions/`, branch `work` off a `main` holding the shipped state)

- `firsttry.sh Q09 --check` with the reference answers in `slots/Q09.slots`: all 15 predictions `predict pass`; T1d and T1v unattempted (nothing recorded). With the twins' T1 bodies: both `first try passes` (forms `trigger` and `stable` checked, the sweeps run).
- The switches enabled, H1d, H1v and the gate core filled from the twins, the exit blocks filled: `firsttry.sh Q09 --exit`: `Q09 exit: 4/4 (threshold 3; per language Dafny 2/2 (≥1), Verus 2/2 (≥1)) PASS`.
- `firsttry.sh Q09 --report --strict`: `strict: OK (unfilled 0, test-outs unattempted 0, missing 0, vacuous 0, commented checks 0, banned 0, budget 0, forms not met 0, failing enabled slots 0, failing property-test runs 0, unrecorded first tries 0)`. Negative checks: `{:resource_limit 9000000}` on H1d gives `banned: Q09.H1d: resource-attribute` and `form stable not met`; H1v as one scoped step gives `form nl-steps:2 not met`; strict FAIL.
- `vcheck --gate`: Dafny unit 130 verified, Verus crate 10 verified, `core.py` 69 passed, 0 holes; `vaudit` 0 findings on both units; `pins.py Q09` (learner): 15 pass; the four card demos give their pinned diagnostics once P1d and P2dv are recorded.
- The live run, the learner's own check (`cd harness && PYTHONPATH=q uv run python -m fvh_q.gate.core --half Q`, on the host, one instrument at a time through `HostRunner`): exit 0; the 33 constructs `FAIL`, V14 and the seven controls other than C-07 and C-7 `PASS · UNKNOWN: X07, X08, X14`, C-07 and C-7 `PASS · UNKNOWN: X08, X14`; `detected: X01 3, X02 4, X03 3, X04 1, X05 2, X06 2, X07 2, X08 1, X10 4, X11 4, X12 2, X13 2, X16 2, X17 1`; `held by unknown: 1; false passes: 0; false positives: 0 of 9 controls (95% Wilson interval 0.000..0.299)`. The same verdicts as the replay.

## 8. The red-team bank (agent files)

- **Dafny** (`{:disableNonlinearArithmetic} Q09_AgentRedTeam`): `AddCLengthBound(a, b, c)` (true), `MulLimbByZero(s)` (true), `CmpAntisymmetric(a, b)` (true), and the planted false `CmpZeroMeansEqual(a, b)` (`[1, 0]` and `[1]`). Refutation `{:fuel Cmp, 4} CmpZeroMeansEqualRefuted()`.
- **Verus**: `lemma_canonical_value_positive(s)` (true), `lemma_value_unfold(s)` (true: the definition, one unfolding), `lemma_sum_le_add(a, b)` (true), and the planted false `lemma_equal_values_equal_limbs(a, b)` (`seq![1u64, 0u64]` and `seq![1u64]`). Refutation `refute_equal_values_equal_limbs()`.
- **The acceptance lines on a correct delivery** (the twin's proofs at their BANK places, the refutation under REFUTATIONS, the false lemma as shipped; written over the agent path for the run and restored byte for byte; the committed bank was a copy of the shipped file): Dafny `vcheck --json` verified, 129, one hole (`bodyless-method`, label `Q09.A1d`) at `CmpZeroMeansEqual`'s `ensures`, every other lemma and the refutation `verified`; `vaudit` exactly 1 finding, `audit-bodyless-ghost` at its declaration line; `specfreeze --against` 0 findings; the diff touches bodies and REFUTATIONS only. Verus: verified, one hole (`assume`, `Q09.A1v`) in `lemma_equal_values_equal_limbs`, the others `no-error`; `vaudit` exactly 1 finding, `hole-assume` on that line; `specfreeze --against` 0 findings.
- The twins hold no BANK declaration (a hole-free twin cannot hold the false lemma; `reference_lint` does not compare agent files, which are "answered inside the main twin"), and the reference delivery after the loud heading, with the soft spots.

## 9. Deviations from the plan

1. **The acceptance tests are `harness/tests/q/gate/test_core.py`, not `harness/tests/q/test_q09_gate.py`** (QPLAN §17.1, §17.7, §6 Q33; DV4-PLAN; DELTAS Δ145). `dvl.python.acceptance_tests` maps `harness/q/fvh_q/<rest>.py` to `harness/tests/q/<dirname(rest)>/test_<basename(rest)>.py`, so `gate/core.py` finds only `tests/q/gate/test_core.py`; with the planned name `vcheck` refuses the file, `--pin-counts` writes nothing, and the TRIV gate cannot run.
2. **The Dafny bank's first lemma is `AddCLengthBound(a, b, c)`**, A.11's helper `AddCLength` posed directly, in place of `AddLengthBound(a, b)` proved through that helper: the contract's `git diff` line allows only bodies and REFUTATIONS, so a delivery that adds a helper breaks it (§R.1 #2's probe added one under a HELPERS section).
3. **The Verus bank's second lemma is `lemma_value_unfold`** in place of `lemma_two_limbs_value`: Q07's card C1v (`lemma_two_limbs_by_hand`, `_by_fuel`, learner-visible given code) proves that statement, which F15 forbids for an item of the tier.
4. **P15v is `add_zero`** (an honest exec delivery) in place of `lemma_two_limbs`: the same statement as reason 3 (and Q06.H2v's with `pack` unfolded), and a specimen is learner-visible.
5. **Species vocabulary.** P11v (`external_body` on real code) is `trusted` only if `hole` means "nothing written"; each delivery's header says so (Q03's wording put every reported placeholder under `hole`).
6. **P9d is `CmpSelf` (`<= 0` against the frozen `== 0`)** in place of `AddValue` (`>=` against `AddCorrect`): a self-contained specimen proving `AddValue` would carry a copy of L4's `AddCCorrect` proof.
7. **P13v's contradiction is `seq_wf(s), s.len() > 0, s.last() == 0`** (the notes: `s.len() > 0, s.len() == 0`, contradictory at a glance).
8. **P14v's past-the-end read is in a spec fn of the `ensures`' antecedent** (`high_limbs_zero`, two limbs), so the lemma is provable and says less than its claim; the notes' `lemma_value_of_top` had no worked statement. Its proof uses L3's `lemma_seq_to_nat_drop_last_zero`, not an all-zero lemma (Q01.H3v's statement).
9. **C1d's failure demo is the empty body and pins `could not be proved`**: in a specimen's own options the empty body fails quickly; the one-step version is seed-brittle (§5). C2's design is §5's (the notes left C2 unprobed).
10. **The recording omits `seed-rerun`** (the gate never calls it).
11. **Companions carry `// after: <item>`** so that `vcheck` keeps them closed until the delivery's first try (H5); the plan named them but not their guard.
12. **W1d and W1v are comment blocks** with the commands and a filled table captured 2026-10-06 (no live declaration: the measured proofs are L4's).
13. **`research/TRUST.md` is not edited**: its `Q-v1` section is Q18's.

## 10. Open

- **Tools (high: `firsttry.sh Q09 --empty-body` exits 1).** H1v and X1v fall to the NL variant, which is their construct-free answer; the gate should judge an NL or BV variant against the item's forms, as it judges a `cfree:` answer (§6).
- **Tools or records (high).** The acceptance-test path (deviation 1): either `dvl.python.acceptance_tests` learns the planned name, or QPLAN §17.1, §17.7, §6 Q33 and the as-built DELTAS entry name `harness/tests/q/gate/test_core.py`.
- **Records.** The as-built DELTAS entry for Q09 (this file's §1-§9), and CLAUDE.md's Armed line.
- **Kits lane.** The chapter (`docs/Q09_InternalsIII.md`), the rubric, the bank and the written pair are not built here. The chapter quotes nothing from the twins; the C1 and C2 measurements of §5 are author-side.

## 11. Follow-up (DV3b kits phase, Q09 + fvh lane, 2026-10-06): the frozen core's `command` and H4py; neutral paths

Closes Δ167's **Open** item "the leak scan's one residual between the frozen core and a gate-core hole" (the author notes §9, "The frozen core and the gate core") and the residual of Δ166's **Open** item on `Delivery.id`. Scratch `/tmp/dvl0-dv3bk-q09/` (not archived).

**Decision: the composition is allowed and said so; no interface changes.** `fvh.tools.command` stays public with the same signature and behaviour (Δ145's stable interface; Δ161 lists it). Its docstrings (`harness/fvh/tools/__init__.py`, `runners.py`) now say that its paths besides the target are the companion files of `tests/corpus/README.md`'s public layout, that a gate may compose it, and that whether a delivery brings them and what a result means stay the gate's own work; `_input_paths` stays private. H4py's docstring (learner file and twin, identical; docstrings are outside the freeze pin's statements, so `expected/Q09.freeze` is unchanged) adds that the layout is public, that `fvh.tools.command(instrument, target)` encodes it and may be composed in place of writing the paths out, and that the rest is the gate's: whether the delivery brings an instrument's companions (a companion directory counts when a file of the delivery lies under it) and a verdict from the results alone. The reference body is unchanged.

Why not the alternative (move `command` out of the public interface): the layout is already public in `tests/corpus/README.md` and spelled out in H4py's own docstring, so hiding the function would remove no information; the frozen core stays learner-readable, so a private name is still callable; and it would change Δ145's stable interface (a new entry, and edits to `harness/tests/core/test_tools.py`, which compares `tools.command` with `test_corpus.command` on every fixture). What composing `command` saves is the path joins; what H4py teaches stays: the two always-run instruments, the companion test (all of an instrument's companions present; a Verus companion directory through a file under it, and `specfreeze --check`'s Verus argv also names the crate's own `src/lib.rs`), `run` looked up at call time, no label, a kill or a refusal never a PASS.

Checked: over all 85 deliveries of both halves (`fvh.corpus.load_half`), the instruments chosen by composing `command` (every path argument other than the target present as a file of the delivery, or as a directory holding one) equal the reference's: 0 differ. Scratch variants of the twin with `gate` composing `command`: requiring all of an instrument's paths passes every test (69 passed, 1 skipped); accepting any one of them runs `specfreeze --check` on every Verus crate (its argv names `src/lib.rs`), finds no recording and fails five tests (`test_h4_on_the_recorded_q_half` among them), so the tests separate the two.

**Neutral paths (new test `test_h4_decides_from_the_layout_not_the_names`).** The neutral-id test left the target path, which names the fixture (`tests/corpus/<lang>/<ID>/…`, a control's `C-` prefix included). The new test moves each delivery to `tests/q09/delivery-<k>/` under the id `Q09-<k>`, every file kept at its place below the fixture directory (V-4's and C-5's multi-crate layouts included), runs `gate` through a stub that maps the neutral target back to the recorded one, and requires the same verdict and the same instruments. A scratch mutant of the twin that FAILs a witnessed mechanical PASS unless `/C-` is in the target passed every earlier test (68 passed, 1 skipped) and failed only this one.

Runs (authoring worktree, this lane's files and the other lanes' uncommitted `scripts/` changes; no solver job except `pins.py --ref`, one at a time, 97 GB available): `vcheck --ref Solutions/harness/q/fvh_q/gate/core.py` verified, 69 passed (1 skipped, the corpus check in the overlay), 0 holes; the learner file failed, 4 passed, 66 failed, 4 holes; `pytest tests/core` 246 passed; firsttry's empty-body item loop on Q09's Python items (the TRIV gate) 4/4; `firsttry.sh --lint-hollow Q09` OK (22 files); `--report Q09` exit 0; `pins.py --ci --module Q09` 44 pins, 0 problems; `pins.py --ref --module Q09` 15 checks, 0 problems; `reference_lint.py --module Q09` 0 findings over 16 twins; `specfreeze --check Q09` 0 findings; `vcheck --shipped Q09 py` 0 problems; `check_course_map.py` OK; `ci.sh --author --job harness` PASS (28 s). The Dafny and Verus items of `--empty-body Q09` were not re-run: this lane changed none of their files, and the Verus cap (16 GB) is above the lane's 8 GB share.

For the kits lane: Q09's rubric should accept either route for H4py's companions (the layout written out, or `fvh.tools.command` composed), and the chapter may say the layout is public.
