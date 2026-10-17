# Q06 code notes (DV3a module lane, author-only)

> **Author-only.** Prediction answers, reference proofs, gate results and the evidence behind them. Never quote, paraphrase or link any of it from a learner-visible file. The plan is `QPLAN.md` §8 and §11 and `Solutions/plans/Q04-Q06-author-notes.md` §4 (with Appendices A.13–A.21 and B.5, B.7); this file records what the Q06 module lane built on 2026-10-05 and where it differs from them.

## 1. Files

| learner file | twin | shipped state (tool) |
|---|---|---|
| `dafny/Q/Q06_Machine/std/Q06_Machine.dfy` (unit `dafny/Q/Q06_Machine/std`) | `Solutions/dafny/Q/Q06_Machine/std/Q06_Machine.dfy` | verified, 5 holes (T1d, H1d–H4d), 0 errors; twin 61 verified |
| `verus/q/q06_machine/src/lib.rs` (crate `q06_machine`) | `Solutions/verus/q/q06_machine/src/lib.rs` | verified, 5 holes (T1v, H1v–H4v), 0 errors; twin 18 verified |
| `dafny/Q/Q06_Machine/exit/Q06_Exit.dfy` | `Solutions/…/exit/Q06_Exit.dfy` | verified, 2 holes (X1d, X2d), X1's `@Test` suite commented; twin 40 verified, suite live (`vcheck --test`: 2 passed) |
| `verus/q/q06_machine/src/exit.rs` | `Solutions/…/src/exit.rs` (`// triv: { None }` for X1v) | verified, 2 holes (X1v, X2v), X1's `#[cfg(test)]` suite commented after `verus!`; twin 3 verified, suite live (`vcheck --test`: 2 passed) |
| `dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy` | `Solutions/…/agent/Q06_AgentProver.dfy` | verified, 1 hole (the top lemma), empty SKELETON; twin (delivered state) 35 verified under `--gate`, `vaudit` 0 findings; the reference skeleton (top lemma proved, three leaves bodyless) verified with 3 holes |
| `harness/q/fvh_q/q06_stats.py` (the fvh lane's file; this lane added Hint lines after the three holes) | `Solutions/harness/q/fvh_q/q06_stats.py` | 3 AST holes; acceptance tests 16 failed as shipped, 16 passed on the twin; TRIV 3/3 |
| `specimens/Q06/P3d.dfy.specimen`, `P4v.rs.specimen` | `Solutions/specimens/Q06/…` | obligation slots unfilled; twins enabled |
| `specimens/Q06/card-c{1,2,3,4}{d,v}.*.specimen` | — | WRITE failure demos, in-file `// EXPECT` pins; C1–C3 carry `// after:` |
| `specimens/Q06/card-c5dv-{d,v}`, `card-c6dv-{d,v}` | — | divergence demos, sealed sidecars under `expected/specimens/Q06/` |
| `slots/Q06.slots` | `Solutions/slots/Q06.slots` | 7 verdict lines `???` |

Pins: `expected/Q06.pins` (7 salted), `expected/Q06.counts` (schema 2: 2 units, 5 files; no harness entry, §5), `expected/Q06.freeze` (85 statements in 19 files), `expected/Q06_AgentProver.audit` (0 findings, captured in learner mode on a scratch root holding the twin at the learner path), four sealed sidecars.

## 2. Verdict answers (captured 2026-10-05, on the pins)

| item | answer | capture |
|---|---|---|
| P1dv | `D:0 V:0 true` | `dvl.common.run_capped` (8 GB) in a scratch directory: `dafny test --no-verify --target py p1.dfy` exit 0 ("Dafny program verifier did not attempt verification", "P1.Passes: PASSED"); `verus p1.rs --crate-type=lib --no-verify --output-json` (`dvl.verus.job_env`) exit 0, `"success": true`, `"verified": 0`. The files are the docstring's, verbatim |
| P2dv | `D:1 inconclusive V:1 inconclusive` | `scripts/vcheck --json --module Q06` on H3d's quoted attempt (exit 1; JSON `verdict` inconclusive, its own `exit_code` 4; "Verification out of resource") and on H3v's quoted attempt (exit 1; inconclusive; "Resource limit (rlimit) exceeded") |
| P5dv | `D:fail V:fail` | `vcheck --module Q06` on the docstring's two scenarios: Dafny "a postcondition could not be proved", Verus "postcondition not satisfied" |
| P6dv | `a c` | the three docstring files: each verifies under `vcheck`; `vaudit` reports [a] `resource-attribute`, [b] nothing (`rlimit(1)` is at most the pin), [c] `rlimit-inflation` |
| P8dv | `D:no V:no` | `vaudit dafny/Q/Q06_Machine/std` lists only the file's own 5 holes; `vaudit --ref` on the twin: 0 findings (the 81 pinned standard-library rows are excluded, Δ98); `vcheck --json verus/q/q06_machine/src/exit.rs` (uses `vstd::arithmetic::div_mod`): only the file's 2 holes, no diagnostic in `vstd` |
| P7py | `c` | `fvh.stats.wilson_interval(14, 20)` = (0.4810, 0.8545), half-width 0.1867 |
| P9py | `c` | `fvh.stats.pass_at_k(10, 3, 5)` = 0.9167 (the naive `1 - 0.7^5` = 0.8319 is option b) |

Obligation answers (`pins.py --ref` re-checks the twins): **P3d `FAILS b`**, **P4v `FAILS b c`** (§4, deviation 1).

## 3. Holes, references and gates

References are the twins (A.13–A.16, A.19 as adapted below). The quoted budget attempts were re-captured on the pins with `vcheck --module Q06` probes: H3d's attempt, Dafny "Verification out of resource" at 5M; X2d's transparent `LowT` attempt, out of resource; H3v's and X2v's attempts, "Resource limit (rlimit) exceeded" at `--rlimit 2`. No twin carries a resource attribute.

Empty-body gate: §6.

## 4. Deviations from the plan

1. **P4v's answer is `FAILS b c`, not `FAILS b`.** The specimen is "the same four" as P3d with empty bodies. In Verus `weight` is opaque, so in [c] the prefix trigger fires (bound `weight(2)`) but nothing gives `weight(2) == BASE * BASE`. The plan lane's probe was not retained and it named only [b]. Every way of giving [c] the weight equations (a body calling `lemma_weight_succ(1)`, a `weight(2)` fact in a `requires`) puts a `weight(2)` term in front of the solver and makes [b] hold too, so the two cannot be separated with one shared body. The prompt names `weight` as L3's and the twin explains the opacity; P3d stays `FAILS b`, which makes P3/P4 a cross-language contrast.
2. **Given definitions sit above the hole's marker**, not inside its block as in A.13–A.16 (`Pack`, `RefSplit`, `pack`, `split_matches`; `Low`/`low` at the top of the exit files). `dvl.dafny.empty_body` and `dvl.verus.empty_body` empty the first lemma/method/function (fn) of an item's block, so a given definition placed after the marker would be the one emptied. They therefore sit in the previous item's block (a given definition there carries no lint finding and no resource attribute).
3. **C3 demos differ per language.** Dafny: `FourthPowerMono` (x ≤ y ⇒ x⁴ ≤ y⁴), empty body out of resource at the pin, fitted by four `Mul.LemmaMulInequality` calls. Verus: the same goal is proved at the pin by `nonlinear_arith`, and a `group_mul_properties` flood fails outright (no out-of-resource), so the Verus demo is `tri(60) == 1830` under `reveal_with_fuel(tri, 61)` (out of resource), fitted by `by (compute_only)`. Neither is TwoShifts, the append value or a remainder, and neither uses a self-feeding trigger. Candidates probed and rejected for Dafny: cube monotonicity (verifies), square equality and cancellation (fail outright), the two-pairs Cauchy–Schwarz inequality (verifies; its Verus `nonlinear_arith` run panicked Verus's SMT process, exit 134, not a verdict).
4. **C4 failure demos** are a one-sided checker whose body is the constant `false` (it verifies) plus a caller's `assert ok`, which fails: an in-file `EXPECT` pin needs a verifier diagnostic.
5. **C6dv demos carry no flagged resource attribute.** The hollow lint applies the learner-mode lint to every shipped specimen and only S12 delivery specimens may carry a `// planted:` exemption, so the Dafny demo has no attribute and the Verus demo only `#[verifier::rlimit(1)]` (at the pin, no finding). The Dafny demo waits for P8dv only; the Verus demo for P6dv and P8dv. The chapter shows the flagged attributes through scratch probes after P6's box.
6. **The agent twin** keeps the shipped order (top lemma above an empty SKELETON, QPLAN §11.4) and holds the reference leaves after the "clearly marked" heading, where `reference_lint.py` allows twin-only declarations.
7. **H3v's twin** keeps `lemma_mul_is_distributive_add` (A.15 as verified; the notes say it can be dropped).
8. **`research/EVAL.md` and `research/TRUST.md`**: a pointer comment under each `Q-v0` heading names what Q06 asks for (QPLAN §11.3); the sections stay unwritten.
9. **X1d and X1v ship a commented suite** (the moved §8.0 property-test row in the Q04–Q06 notes §4.7: "a commented suite under `Uncomment as you go:`"; A.14/A.16 had none). Without one, `firsttry --report --strict` (§6 Q20 as built) fails on the scored exit files with "no test ran" (seen in the simulation, §7). Dafny: given `Half`, `HalfA` (agrees) and `HalfB` (rounds up; first disagreement at index 2) after the method, inside X1d's block, and two commented `@Test` methods, so X1d's exit block passes only once they are uncommented and verify. Verus: two commented `#[test]`s after `verus!` (outside X1v's block), comparing result vectors of `x % 2 == 0` with `x & 1 == 0` (agrees: `None`) and `x % 4 == 0` (planted: `Some(2)`). Both exit headers say so. The gate was re-run on X1d (maxauto and seeds 1–3 fail) and X1v (E0, E0H, E1, E2, EC, EM, TRIV `{ None }` fail).
10. **H4d's docstring** no longer says the suite runs only once the unit has no hole left: `vcheck --test` on the shipped unit compiles and runs the card's two tests (2 passed).

## 5. Open (tools)

- **High: blocks Q06's learner flow.** Without the Python wiring, `firsttry --check` never records P7py and P9py, and §6 Q23 refuses T1d's and T1v's first tries while they are unrecorded (§7).
- The Python wiring patch (`/tmp/dvl0-dv3a-harness/wiring/dv4-wiring.patch`) is not applied, so `vcheck --pin-counts Q06` writes no harness entry and `firsttry` (lint-hollow, report, empty-body) does not see the Python items; the Python checks ran through `scripts/dvl/python.py` directly. Re-pin `vcheck --ref --pin-counts Q06` after it lands (expected: `harness/q/fvh_q/q06_stats.py`, role harness, failed, 3 holes, 0 errors).
- `specfreeze` does not freeze Dafny's `opaque` modifier (removing it from `Pack` changes no statement hash; Verus's `#[verifier::opaque]` is caught). A learner could make `Pack` (H2d) or `Low` (X2d) transparent unnoticed.
- The C3 demos' in-file `EXPECT` fragments name the out-of-resource message, which bears on P2dv (the Q03 precedent, Δ120/Δ122 Open: in-file text cannot be sealed).

## 6. Empty-body gate (`firsttry.sh Q06 --empty-body`)

Run 2026-10-05 18:56–19:13 (`DVL_SCRATCH` lane scratch, default modes and seeds, BV at its pinned 120 s): **`Q06 empty-body: 14/14 hole(s) pass the gate`**, exit 0. T1d, H1d–H4d, X1d, X2d: the empty body fails in every run (X2d flagged `empty-body-inconclusive`, as the plan lane saw: maxauto with opacity stripped is inconclusive, every seed fails). T1v, H1v–H4v, X1v (TRIV from its twin's `triv:` line), X2v: every mode fails. No Q06 hole is an annotation hole, so no twin carries `@hole-begin` regions and no region gate applies. After the X1 suites were added (§4.9), X1d and X1v were re-gated through `dvl.dafny.empty_body` / `dvl.verus.empty_body`: both `failed` in every run. The Python holes: `scripts/dvl/python.py triv` 3/3 (each declared trivial body fails its own tests).

## 7. Learner-flow simulation (`/tmp/dvl0-dv3a-q06/sim`, a git copy of the worktree without `Solutions/`)

With the tools as they stand, `firsttry --check` records the 7 verifier predictions but never P7py and P9py, while §6 Q23's waiting list counts all 9 P items, so **T1d and T1v can never be recorded until the Python wiring lands** (§5). With the wiring patch applied to the simulation's scripts copy: T before predictions refused (nothing recorded); all 9 predictions recorded `predict pass`, T still refused in that run; the next `--check` recorded T1d and T1v; the `after:` demos then run (card-c3d: inconclusive, its EXPECT); `--exit` with the reference blocks: `Q06 exit: 4/4 (threshold 3; per language Dafny 2/2 (≥1), Verus 2/2 (≥1)) PASS`; with every hole filled from the twins, slots enabled and suites uncommented, `firsttry --report --strict`: `strict: OK (… budget 0, failing enabled slots 0, failing property-test runs 0, unrecorded first tries 0)` (property tests: Dafny unit 4 passed, Verus crate 4 passed, each exit 2 passed); `vcheck --gate`: Dafny unit 61, Verus crate 18, Python 16 passed with 0 holes; `vaudit` 0 findings on both units. Negative check: `{:resource_limit 50000000}` on `TwoShifts` makes strict fail with `banned: Q06.H3d: resource-attribute`. The wiring would add `harness/q/fvh_q/q06_stats.py` to `expected/Q06.counts` as role harness, verdict failed, 3 holes, 0 errors (rendered on a scratch root).
