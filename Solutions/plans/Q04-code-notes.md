# Q04 code notes (DV3a Q04 lane, as built)

> **Author-only.** Prediction answers, card-demo outcomes, gate results and the
> deviations of Q04's code from the plan. Never quote, paraphrase or link any of it
> from a learner-visible file. The plan is `QPLAN.md` §9 and
> `Solutions/plans/Q04-Q06-author-notes.md` §2 (with Appendices A.3–A.7, B.1–B.3,
> B.7, B.8); this file records what the Q04 lane built on 2026-10-05 and where it
> differs.

Every result below was captured on the pins through the course wrappers
(`scripts/vcheck`, `scripts/vaudit`, `scripts/pins.py`, `scripts/specfreeze`,
`scripts/firsttry.py`), one solver job at a time, each started with at least 31 GB
available (`free -g`), under the `dvl` caps (Dafny 8 GB, Verus 16 GB),
`DVL_SCRATCH=/tmp/dvl0-dv3a-q04/scratch`. Probe files are lane scratch under
`/tmp/dvl0-dv3a-q04/` (not archived; the decisive probes are quoted here).

## 1. Prediction answers (captured on the real scenarios)

| item | answer | capture |
|---|---|---|
| P1dv | `D:ok V:fail` | `scripts/vcheck --module Q04 p1dv_d.dfy` (module `SplitD`, `import opened QG_L1_BigNat`, the docstring's `SplitSum`): verified, 23. `scripts/vcheck --module Q04 p1dv_v.rs` (`use qg_bignat_l1::*;`, the docstring's `split_sum`): failed, 1 error, `postcondition not satisfied` at the `ensures` clause. The Verus probe the plan lane did not retain is now captured |
| P2d | `1` | `pins.py --ref --module Q04` runs the enabled twin slot (`expect Cmp([5, 1], [7, 0, 0]) == 1;`) under `dafny test`: pass |
| P3dv | `D:3 yes V:1 no` | `scripts/vcheck p3dv_d.dfy` (the top-level lemma `Chain`, alone): failed, 3 errors, each "the calculation step between the previous line and this line could not be proved" at lines 6, 8 and 10 of the file (the three targets). `scripts/vcheck p3dv_v.rs` (`use vstd::prelude::*; use vstd::calc;`, the docstring's `chain`): failed, 1 error, `assertion failed`, located at `calc_macro.rs:52:9` (vstd), not in the file |
| P4d | `FAILS a c` | `pins.py --ref`: the twin's `// FAILS a c` passes |
| P5d | `FAILS b` | `pins.py --ref`: the twin's `// FAILS b` passes |
| P6v | `a b` | `scripts/vcheck p6v_{a,b,c}.rs`, each crate alone: `nonlinear_arith` verified (2), `bit_vector` verified (2), `compute` failed (a "Failed to simplify expression … before sending to Z3" warning, then `assertion failed`) |
| P7v | `V:ok` | `scripts/vcheck --module Q04 p7v_base.rs` (empty body): verified, 1; `p7v_group.rs` (the `broadcast use vstd::arithmetic::mul::group_mul_properties;` line as the only body line): verified, 1, under the wrapper's own 16 GB cap |
| P8dv | `D:err:resolve V:ok` | `scripts/vcheck --module Q04 p8dv_d.dfy` (module `UsePowD`): failed at stage resolve, "The name Pow ambiguously refers to a static member in one of the modules QG_L1_BigNat, Power (try qualifying the member name with the module name)". `p8dv_v.rs` (local `pow` beside `use vstd::arithmetic::power::*;` and `use qg_bignat_l3::*;`): verified, 1 |
| P9v | `FAILS b` | `pins.py --ref`: the twin's `// FAILS b` passes |

`expected/Q04.pins` holds the five salted verdict hashes (`pins.py --update --ref
--module Q04`); `pins.py --ref --module Q04`: 9 checks, 0 problems.

## 2. Holes, test-out items and exits

The references are Appendix A.3–A.6's, unchanged in code; the markers give the
strands of QPLAN §9.2 (H1d S4, X1d S4, the Verus library items S5). Shipped
states (`vcheck --ref --pin-counts Q04`, `expected/Q04.counts`): core 3 holes
(T1d, H1d, H2d), std 2 (H3d, H4d), `lib.rs` 2 (T1v, H2v), `library.rs` 4 (H1v,
H3v, H4v, H5v), check unit 0, exits 2 + 2, agent files 3 + 3; every file
verified. Reference gates: core unit 38 verified, std unit 36, crate 24, check
unit 31, Dafny exit 34, Verus exit 3, agent twins 35 and 3; `vaudit --ref --mode
reference` 0 findings on each twin.

- **H4v** ships the revised shape (Appendix A.6): the labelled `assume(false)` is
  the first statement, the invariant keeps `i <= n`, `n == a@.len()`,
  `n == b@.len()`. The twin marks the two learner regions (`broadcast use
  group_bignat_bounds;` and the clause `forall|j: int| i <= j < n ==> a@[j] ==
  b@[j]`) with `@hole-begin Q04.H4v` / `@hole-end Q04.H4v` and declares
  `// triv: { Ordering::Equal }`; X2v's twin declares `// triv: { false }`.
- **Checks.** Every hole has a commented check under `Uncomment as you go:`; the
  twins run them live with extra edge checks. The H2d check instantiates the
  prefix bound at a variable index `k` only (a concrete prefix would bear on
  Q06.P3d's labels).
- **Exit headers** let the pinned standard library's own source be open beside
  the given spine (X2d asks for a library lemma; the Verus exit names none, but
  the header is the same). Deviation from spec §3.10's "at most the given spine".

## 3. Cards: what each demo shows

WRITE cards (success in the file, failure demo pinned by an in-file `// EXPECT`
at the end of the specimen; `pins.py --ci` checks every one):

| card | success (file) | failure demo | pinned diagnostic | `after:` |
|---|---|---|---|---|
| C1d | `ToNatTwoSteps`: two unfoldings of `ToNat`, one hint | the last step false (`s[0] + s[1] + …`) | "the calculation step between the previous line and this line could not be proved", at the false step | Q04.P3dv |
| C1v | `lemma_seq_to_nat_two_steps` | the casts to `nat` left out: the chain's lines do not all have one type | `mismatched types` (rustc E0308), at the `int` line | Q04.P3dv |
| C2d | `AppendZeroEach` (L1's worked lemma per sequence, `forall` statement) | the call left out | "possible violation of postcondition of forall statement" | — |
| C2v | `lemma_push_zero_each` (`assert forall … implies … by`) | an empty `by` block | `assertion failed` | — |
| C3d | `FromNatShort`: `\|FromNat(n)\| <= n` by a call on `n / BASE` | `{:induction false}`, empty body | "a postcondition could not be proved on this return path" | — |
| C3v | `lemma_weight_above`: `n < weight(n)` | the recursive call left out | `postcondition not satisfied` | — |
| C4d | `ScaleLe` (`Mul.LemmaMulInequality`) | the `requires a <= b` dropped | "a precondition for this call could not be proved" | — |
| C4v | `lemma_scale_le` (`lemma_mul_inequality`) | the same | `precondition not satisfied` | — |
| C5v | `lemma_weight_order_by_name` (two `lemma_weight_mono` calls) and `…_by_group` | the group version without its `broadcast use` line | `postcondition not satisfied` | Q04.P9v |
| C6v | `lemma_product_le_by_hand` (`lemma_mul_upper_bound`) and `…_by_nl` | the nonlinear assertion without its `requires` | `assertion failed` | Q04.P6v |

C7d is comment-only (no demo). False friends C8dv and divergence C9dv
(`.expect` sidecars, `pins.py --update`; sealed where an `after:` line is):

| demo | content | outcome (sidecar) | `after:` |
|---|---|---|---|
| C8dv-1-d | a `calc` chain mixing `<=` and `<`, one false `<` step | failed, 1 error at the false step | Q04.P3dv (sealed) |
| C8dv-1-v | the same in `calc!`: `(<=)` first, a `(<)` override on one step | failed, 1 error in vstd's `calc_macro.rs` | Q04.P3dv (sealed) |
| C8dv-2-d | a `forall` statement whose body calls a lemma that needs the range | verified (the range is assumed in the body) | — |
| C8dv-2-v | `assert forall … ==> … by` with the same call | failed: a warning that `==>` does not assume the antecedent, then `precondition not satisfied` | — |
| C8dv-3-d | `Double(n) == 2 * n` twice, once with `{:induction false}` | failed, 1 error (the attributed lemma); the default one verifies | Q04.P5d (sealed) |
| C8dv-3-v | the same proof fn, empty body | failed, `postcondition not satisfied` | — |
| C8dv-4-d | two opened imports that both define `Pow` (a stand-in module and `Std.Arithmetic.Power`) | resolve error: `Pow` ambiguous | Q04.P8dv (sealed) |
| C8dv-4-v | a local `pow` beside `use vstd::arithmetic::power::*;` | verified (the local item wins) | Q04.P8dv (sealed) |
| C9dv-d | `Std.Arithmetic.Mul.LemmaMulInequality` named with no import | resolve: "unresolved identifier: Std" (2 errors) | Q04.P8dv (sealed) |
| C9dv-v | `vstd::arithmetic::mul::lemma_mul_inequality` named by path, no `use` | verified | — |

A probe with `import Std.Wrappers` (the library switched on) and the same
qualified call gave the same two resolve errors: Dafny names a library module
only through an import of it, while Rust paths reach `vstd` with no `use`.

## 4. Deviations from the plan

1. **C1v's failure demo is a type mismatch, not a false step.** A false `calc!`
   step is reported inside vstd (`calc_macro.rs:52:9`, P3dv's answer), so an
   in-file `// EXPECT` cannot pin it; the vstd-located failure is shown by C8dv
   row 1 instead (sidecar, sealed). The demo keeps `// after: Q04.P3dv`.
2. **C1 chains stop at two steps.** A third step distributing `BASE * (s[1] + BASE
   * …)` fails in Verus (`BASE` is a spec constant, so the product is nonlinear to
   the default solver; probe `c1v.rs`, step 3), and `lib.rs` may use neither
   `nonlinear_arith` (C6v comes later) nor `vstd::arithmetic`.
3. **C5v's named calls are two `lemma_weight_mono` calls** (`weight(k) <= weight(m)
   <= weight(n)`), not `lemma_weight_zero` with `lemma_weight_mono(0, …)`: the
   latter is the positivity step of H3v's answer.
4. **C9dv's Dafny demo** names the library with no import (§3) instead of showing
   "the core unit cannot see `Std`": a specimen is never in a unit, and
   `dvl.dafny` switches the standard library on for a specimen that imports `Std`.
   The demo carries `// after: Q04.P8dv` (§2.3 lists none) because it shows a
   resolve-stage failure about naming a library.
5. **C8dv row 3's Dafny demo carries `// after: Q04.P5d`** (§2.3 lists none for row
   3): its default lemma verifies by the automatic induction a specimen has.
6. **The check unit imports no `Std` module.** QPLAN §6 Q13 is built: the registry
   declares the file `std`, and `dvl.dafny.file_tier` builds it so (verified, 30;
   twin 31). QPLAN §9.1's "and one `Std` module" was the workaround.
7. **The agent files keep Appendix A.7's imports** (L1 and L3 opened, `Mul`,
   `DivMod`, `Power`), though the goals use only `Mul` and `DivMod`.
8. **Hints and prompts** are this lane's; none names a lemma of a hole's answer.

## 5. The agent files

As shipped: Dafny verified with 3 holes (`audit-bodyless-ghost` × 3 in `vaudit`),
Verus verified with 3 holes (`hole-assume` × 3 in `vaudit`); the headers state the
dashboard as one row per open goal. The twins (each body only library calls with
`// found-by:` receipts) pass `vcheck --gate` (35 and 3 verified, only the summary
line). The audit pins `expected/Q04_AgentRetriever.audit` and
`expected/q04_proof_craft_agent.audit` (0 findings) were written by `vaudit
--write` on the delivered files laid at the learner paths, then the shipped files
were restored byte for byte. The soft spots are in each agent twin's closing
section.

## 6. Verification runs (authoring worktree, 2026-10-05)

- `vcheck --ref`: core unit 38 verified, std unit 36, crate 24, check unit 31, Dafny
  exit 34, Verus exit 3, agent twins 35 and 3; 0 holes, 0 errors, silent. `vaudit --ref
  --mode reference` on every twin: 0 findings.
- Learner files, learner loop: core 32 verified with 3 holes, std 32 with 2, crate 6 holes
  (`lib.rs` 2, `library.rs` 4), check unit 30 with 0, exits 2 + 2 holes, agent files 3 + 3
  holes; `vcheck --gate` on each unit fails only on its holes; `vaudit` reports one row
  per hole.
- `vcheck --ref --pin-counts Q04` (3 units, 9 files), `vcheck --shipped Q04`: 9 files,
  0 problems. `specfreeze --pin Q04` (100 statements in 32 files), `--check`: 0 findings.
- `pins.py --update --ref --module Q04` (5 salted pins); `pins.py --ref --module Q04`: 9
  checks, 0 problems; `pins.py --update` on the 10 divergence demos (6 sealed, 4
  readable); `pins.py --ci --module Q04`: 42 pins, 0 problems (the ten in-file `EXPECT`
  pins included).
- `firsttry.py Q04 --lint-hollow`: OK (30 files). `--report`: 9 unfilled slots, 2
  unattempted test-outs, 24 commented checks, as shipped. `CI=true reference_lint.py
  --module Q04`: 0 findings over 10 twins. `vcheck --test dafny/checks/Q04_checks.dfy`:
  1 passed (the shipped, empty P2d). Q04 has no property-test item (QPLAN §6 Q20 does not
  apply).
- H5 guards: `vcheck` refuses `specimens/Q04/P4d.dfy.specimen` and the `after:` demo
  `card-c5v.rs.specimen` while their predictions are unrecorded.
- **Learner-flow simulation** (a scratch git checkout of the worktree without
  `Solutions/`, `main` = the shipped state; `/tmp/dvl0-dv3a-q04/sim/`): the T items
  filled first were refused by `firsttry --check` (QPLAN §6 Q23: "waits for the module's
  predictions", nothing recorded); with the reference answers in the slots, `--check`
  recorded all nine P items as first-try passes and refused the T items again; the next
  `--check` recorded T1d and T1v (predict, pass); an `after:` demo then ran; `--exit` with
  the exit twins scored 4/4 (threshold 3; Dafny 2/2, Verus 2/2) PASS; with every hole
  filled from the twins and every check enabled, `--report --strict` OK (9/9 first tries,
  2/2 test-outs), `vcheck --gate` verified on the three units (38, 36, 24) and on both
  exits (34, 3), `vaudit` 0 findings on each unit, `specfreeze --check` 0 findings,
  `pins.py Q04` 9 pass.
- `check_course_map.py`: every group passes but `import-tiers`, which reports
  `verus/q/q04_proof_craft/src/library.rs:24: uses vstd::calc but its tier is
  arithmetic`, a checker defect (§8).
- Leak checks: the leak-pattern README's verifier (OK, 849 public files, no hit in a Q04
  file); no Q04 learner-visible file names a reference lemma of a hole or exit answer
  (`LemmaMulStrictInequality`, `LemmaPowAdds`, `LemmaPowPositive`,
  `LemmaPowStrictlyIncreases`, `lemma_mul_strict_inequality`, `lemma_mul_is_associative`,
  the agent goals' lemmas, `ToNatBound`); a line scan of the 13 twins' answer lines against
  the 856 learner-visible text files found only checks the learner files ship commented,
  statements, and generic calls of given lemmas (`PowIsStdPow(n);`,
  `lemma_weight_zero();`, `broadcast use group_bignat_bounds;` in the C5v card and the P9v
  specimen); no verdict, obligation or value answer occurs in a Q04 learner-visible file.

## 7. Empty-body gate

`firsttry.py Q04 --empty-body` (every default mode and seed; Verus `BV` bounded at 120 s):
**15/15 holes pass**, in 16 min 26 s. Dafny: maxauto plus seeds 1–3 as shipped; T1d, H4d
and X2d report `lever-needed` (the manual-induction option; never gating), as planned.
Verus proof holes (T1v, H2v, H1v, H3v, H5v, X1v): E0, E0H, E1, E2, EC, EM, NL, BV, seeds
1–3 (EM seed 1), every run failing. H4v: E0, E0H, E1, E2, EC, EM, INV, TRIV (its declared
`{ Ordering::Equal }`) fail, and the region gate (RGN, the twin with both learner regions
blanked) fails on seeds 1–3. X2v: TRIV with its declared `{ false }` fails. No job was
killed.

Agent goals (not gated by `firsttry`; `dvl.dafny.empty_body` / `dvl.verus.empty_body`
on the shipped files through a driver, `/tmp/dvl0-dv3a-q04/eb_agent.py`): Dafny
`ScaleStrict` maxauto verified, seeds 1–3 failed (`lever-needed`: the module's
`{:disableNonlinearArithmetic}`); `HighLimbOfShift` and `ProductMod` maxauto
inconclusive, seeds failed (`empty-body-inconclusive`). Verus `lemma_pow_of_pow`,
`lemma_low_limb_of_power`, `lemma_pow_mod_base`: E0, E0H, E1, E2, EC, EM, NL fail on every
seed; BV does not reach verification (`pow` and `nat` are not bit-vector expressions).
All six goals are admissible, as the plan found.

## 8. Tool problems found (for the tools owner)

1. **`check_course_map.py`'s Verus tiers do not admit `calc!` above `prelude`.**
   `VSTD_ALLOW["seq_lib"]` is a literal set without `calc` and `calc_macro`, and
   `"arithmetic"` extends it, so `library.rs` (tier `arithmetic`, `use vstd::calc;`)
   fails the import-tier group, against Δ131 ("in the `prelude` tier, and so in every
   wider Verus tier") and the checker's own docstring. Fix: build `seq_lib` from
   `VSTD_ALLOW["prelude"]` (`VSTD_ALLOW["prelude"] | {"seq", "seq_lib", …}`). No Q04 file
   changes; until then the checker reports one error on `library.rs:24`.
2. `vcheck` reports a failing `calc!` step at `calc_macro.rs:52:9` under the run's scratch
   directory, so no in-file `// EXPECT` can pin it (deviation 1 above); a remap of
   macro-expanded spans to their call site would allow it.
