# Q08 code notes (DV3b, the Q08 module lane)

> **Author-only.** Prediction answers, the evidence each was captured from, the hole
> gate results, the admissibility results of the gated items, the flagship's acceptance
> re-run and every deviation from the plan. Never quote, paraphrase or link any of it from a
> learner-visible file. The item plan is `QPLAN.md` §14 and §16 (learner-visible) and
> `Solutions/plans/Q07-Q09-author-notes.md` §3 with Appendices A.3, A.4, A.6b, A.8, A.9,
> A.13 and A.15 (the plan lane's author notes; exit statements in §3.7); this file records
> what the module lane built and re-captured on the real files, 2026-10-06.

Every run below went through the course wrappers (`scripts/vcheck`, `scripts/vaudit`,
`scripts/pins.py`, `scripts/firsttry.sh`, `scripts/specfreeze`, `scripts/reference_lint.py`),
at the course pins (Dafny 4.11.0 with its bundled Z3 4.12.1, `--resource-limit 5000000`,
`--cores 2`; Verus 0.2026.09.27, vstd `0.0.0-2026-09-20-0158`), one solver job at a time
under the `dvl` caps (Dafny 8 GB, Verus 16 GB; the empty-body sweep also inside a 16 GB
`systemd-run` scope, the lane's share), each started with at least 31 GB available
(`free -g` showed 85–92 GB). Probes, the scratch course root and raw outputs are lane
scratch under `/tmp/dvl0-dv3b-q08/` (`probe/`, `root/`, `dvl/runs/`) and are not archived;
the decisive ones are described below.

## 1. Files

| learner file | shipped state (tool count) | twin |
|---|---|---|
| `dafny/Q/Q08_InternalsII/std/Q08_InternalsII.dfy` | verified, 1 hole (T1d); P1dv, P3d, P4dv, P5dv; W1d; C1d (nested `CardNat refines QG_L4_Spec`); C4dv | `Solutions/…/std/Q08_InternalsII.dfy` |
| `dafny/Q/Q08_InternalsII/std/Q08_Canon.dfy` | verified, 3 holes (H1d, H2d, H7d: refined lemmas `{ assume false; }`) | twin with `reference-only` helpers `FromNatCanonical`, `AddCCanonical` |
| `dafny/Q/Q08_InternalsII/std/Q08_Wp.dfy` | verified, 3 holes (H8d, H9d, H10d: bodyless lemmas); W2d | twin |
| unit `dafny/Q/Q08_InternalsII/std` | learner loop 151 verified, 7 holes | twin 157 verified (`expected/Q08.counts`) |
| `verus/q/q08_internals_ii/src/lib.rs` | verified, 3 holes (T1v and H3v: labelled assumes; H4v: `external_body`); P2v, P6v; W1v; C2v; C5dv | twin (`// triv:` on H4v) |
| `verus/q/q08_internals_ii/src/perm.rs` | verified, 2 holes (H5v, H6v: `external_body`); W3v; C3v | twin (`// triv:` on both) |
| crate `verus/q/q08_internals_ii` | 5 holes | twin 22 verified |
| `dafny/Q/Q08_InternalsII/exit/Q08_Exit.dfy` | verified, 2 holes (X1d `{ assume false; }`, X2d bodyless); EXPLAIN-BACK block | twin 139 verified |
| `verus/q/q08_internals_ii/src/exit.rs` | verified, 2 holes (X1v, X2v `external_body`) | twin 4 verified (`// triv:` on both) |
| `dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` | verified, 0 holes, 122 verified; empty STATEMENTS, WITNESSES, HELPERS | twin 129 verified (reference statements, witnesses, delivery after the loud heading) |
| `verus/q/q08_internals_ii/src/agent.rs` | verified, 0 holes | twin 11 verified |
| `specimens/Q08/card-c1d.dfy.specimen`, `card-c2v.rs.specimen`, `card-c3v.rs.specimen` (WRITE failure demos, in-file `// EXPECT`) | red by design | none |
| `specimens/Q08/card-c4dv-{d.dfy,v.rs}.specimen`, `card-c5dv-{d.dfy,v.rs}.specimen` (divergence) | sealed sidecars | none; `expected/specimens/Q08/*.expect` |
| `slots/Q08.slots` (6 lines, unfilled) | — | `Solutions/slots/Q08.slots` |
| — | — | `expected/Q08.pins` (6 salted hashes), `expected/Q08.counts` (schema 2: 2 units, 9 files), `expected/Q08.freeze` (153 statements in 14 files, 2 agent files without statements; `open_specs = ["Odometer::advance", "Odometer::current", "Toggle::flip"]`). No `.audit` pin (QPLAN §16.1) |

## 2. Prediction answers, re-captured

Each scenario was run as its own file with `scripts/vcheck --json --module Q08 <probe>`.

| item | answer | evidence |
|---|---|---|
| P1dv | `D:ok err:resolve V:ok err:resolve` | Dafny [a] (`abstract module Q08_P1Spec` + `RefA`, `ensures x < 15`): verified. [b] (`requires x < 5`): failed, stage resolve, "a refining method is not allowed to add preconditions". Verus [a]: verified. [b]: failed, stage resolve, "trait method implementation cannot declare requires clauses; these can only be inherited from the trait declaration" |
| P2v | `V:err:resolve ok` | [a] failed, stage resolve, "use of moved value: `perm`"; [b] verified |
| P3d | `D:err:resolve` | the docstring's scenario as built (a refiner like QG_L4_Limbs, `Wf = L1.Valid`, `FromNatCorrect` with `decreases n` recursing on `n - 1`): failed, stage resolve, "decreases clause on refining method not supported, unless the refined method was specified with 'decreases *'". The same file without the clause and the recursion: verified (126) |
| P4dv | `D:ok V:err:resolve` | Dafny `Size` over `Leaf \| Node(l, r)`: verified; Verus `size` over the boxed enum: failed, stage resolve, "recursive function must have a decreases clause" |
| P5dv | `b` | by hand: `wp = x + 1 > 0`, i.e. `x >= 0`; four lemmas over a direct semantics: only `<==> x >= 0` verifies (a, c, d fail) |
| P6v | `V:ok fail` | [a] verified; [b] failed, "postcondition not satisfied" |

`pins.py --update --ref --module Q08` wrote the six salted pins; `pins.py --ref --module Q08`:
"6 check(s); 0 problem(s)". The simulation (§8) recorded all six as first-try passes.

## 3. Holes: shipped forms and the empty-body gate

References are the author notes' A.3 (H1d, H2d, H7d, T1d), A.4 (H3v, H5v, H6v), A.8
(H8d–H10d), A.6b and A.15 (exits), with the changes of §7. Shipped forms: T1d `{ assume
false; }` (QPLAN §16.2); H1d, H2d, H7d and X1d refined lemmas `{ assume false; }` with the
inherited statement quoted in the docstring (QPLAN §14.0, Δ154); H8d–H10d and X2d bodyless
lemmas with one `ensures`; T1v and H3v statement holes with a labelled assume in the given
client (§7 item 3); H4v, H5v, H6v, X1v, X2v `external_body` over `unimplemented!()`.

`firsttry.sh Q08 --empty-body` (every default mode and seed, 16 GB scope): **14/16 pass**,
exit 1:

| item | result |
|---|---|
| T1d, H1d, H2d, H7d, H9d, X1d, X2d | the empty body fails in every run |
| H8d | fails in every run; finding `lever-needed` (maxauto, with automatic induction, verifies; the unit's manual induction is the lever) |
| H10d | fails in every run; finding `empty-body-inconclusive` (a non-gating run out of resource) |
| H4v (TRIV `{ T::zero() }`), H5v and H6v (TRIV `{ }`), X1v (TRIV `{ T::zero() }`), X2v (TRIV `{ }`) | every mode fails |
| T1v, H3v | **refused**: "a spec fn without a body is not a hole the empty-body gate can test" (the gate takes the first fn of the block, the trait's spec fn). QPLAN §6 Q40 says these statement holes stay skipped; the tool does not skip them, so the module's run exits 1 (§9). Evidence that both holes are real: in the shipped crate with the two assumes deleted and nothing else changed, `vcheck` fails with 3 errors (T1v's client postcondition; H3v's second `advance` precondition and the client's postcondition) |

No `// cfree:` line: the author notes §0.2 list no construct-free answer for a Q08 item, and
Q08 has no `// form:` line (QPLAN §14.0).

## 4. The gated items (H5v, H6v): the four admissibility results

| result | H5v `bump` | H6v `transfer` |
|---|---|---|
| 1. the reference verifies | twin crate `vcheck --ref`: verified, 22, 0 holes; `vaudit --ref` 0 findings | same |
| 2. the empty-body gate fails | TRIV `{ }` and every other mode fail on every seed (§3) | same |
| 3. stable on seeds 1–3 | `vcheck --ref --brittleness` on the twin crate: stable; the perm twin as a probe: `bump` 3,314..3,320 (CV 0.1%) | `transfer` 4,484 on every seed (CV 0%) |
| 4. the pinned `vstd::cell` API | `vstd-0.0.0-2026-09-20-0158/cell/pcell.rs`: `PCell::new` (returns `(PCell<T>, Tracked<PointsTo<T>>)`, `pt.1@.id() == pt.0.id()`), `read(&self, Tracked<&PointsTo<T>>)`, `write(&self, Tracked<&mut PointsTo<T>>, T)`, `into_inner`, `PointsTo::id()`, `PointsTo::value() -> &T` | same |

All four pass for both items. **Registry change for the integration lane:**
`"Q08.H5v" = { admitted = true, minutes = 6, fallback = … }` and `"Q08.H6v" = { admitted =
true, minutes = 8, fallback = … }` (fallback texts unchanged); `tracked` stays in `write_v`.
API note: the plain `PCell` at the pin has no `is_init` (that is `pcell_maybe_uninit`'s), and
`value()` returns a reference, so C3v's `peek` states `ensures r == *perm.value()` with no
`is_init` precondition.

## 5. Cards and demos

| card | success (in the file) | failure demo | `after:` | pinned outcome |
|---|---|---|---|---|
| C1d refines | nested `module CardNat refines QG_L4_Spec` (`BigNat = nat`, empty proofs, helper `AddCommutes`) | `card-c1d`: `Q08_CardC1Base` (a bodyless `Add` with one `ensures` and a bodyless `AddCorrect`) refined by `Q08_CardC1d` with `Add = a + b + 1` (§7 item 4) | — | `EXPECT @21 "a postcondition could not be proved on this return path"` (2 holes in the base, counted) |
| C2v trait-spec | `Dial`, `Knob`, `leave_zero` | `card-c2v`: the implementation adds `ensures final(self).p == old(self).p + 1`; a generic client relies on it | Q08.P6v | `EXPECT @43 "postcondition not satisfied"` |
| C3v tracked | `peek` (shared borrow) and `is_small` (lends a `&mut` permission with `Tracked(&*perm)`, ghost `assert(perm.id() == cell.id())`) | `card-c3v`: `peek(&a, Tracked(&pb))` | — | `EXPECT @23 "precondition not satisfied"` |
| C4dv (S6) | — | `card-c4dv-d`: a local base and three refined lemmas: [1] adds an `ensures`, [2] adds a `requires`, [3] its own `decreases` and a recursion; `card-c4dv-v`: a trait implementation that [1] adds an `ensures`, [2] adds a `requires` | Q08.P1dv, Q08.P3d (d); Q08.P1dv (v) | sealed; as captured: Dafny stage resolve, 2 errors ([2] "a refining method is not allowed to add preconditions", [3] "decreases clause on refining method not supported…"), 3 base holes; Verus stage resolve, 1 error at [2] |
| C5dv (S7) | — | `card-c5dv-d`: `Depth` and `Dots` over `Dot \| Pair` with no clause; `card-c5dv-v`: `depth` with no clause, `dots` with `decreases s` | Q08.P4dv (both) | sealed; as captured: Dafny verified (2); Verus stage resolve, "recursive function must have a decreases clause" at `depth` |

Leak constraints honoured (author notes §3.3, §6): no Dafny demo declares an abstract module;
no demo uses `seq<nat>` limbs or a change of representation (H1d, H2d, H7d, X1d); C2v folds no
sequence (X1v); C3v neither writes through a `&mut` permission (H5v) nor moves a value between
cells (H6v) nor adds to a cell; C5dv shows no lexicographic measure (X2d). Every demo that
settles a Q08 prediction carries its `after:` lines; `vcheck` refuses `card-c4dv-d` as
shipped (H5).

## 6. The flagship (agent files): acceptance re-run

On a scratch course root (`/tmp/dvl0-dv3b-q08/root`, a git copy of the worktree), with the
twins' reference statements copied into STATEMENTS (bodyless methods; Verus `external_body`
stubs) and the twins' witnesses into WITNESSES, the file copied to
`research/q08_statements.{dfy,rs}`:

| step | Dafny | Verus |
|---|---|---|
| statements as committed: `vcheck`; `vaudit` | verified, 123, 2 holes (`bodyless-method`), the witnesses verify; 2 findings (`audit-bodyless-compiled`) | verified, 2 holes (`external_body`); 2 findings (`hole-external-body`) |
| delivery (bodies + HELPERS): `vcheck --gate` | verified, 129, 0 holes | verified, 11, 0 holes |
| `specfreeze --against research/q08_statements.*` | 0 findings | 0 findings |
| `vaudit` | 0 findings | 0 findings |
| `git diff` from the statements | the two method bodies and HELPERS only | the two stubs' `external_body` lines and bodies, and HELPERS only |

The Verus delivery as A.15 had it reproduced the plan's measurement exactly (`high_limbs`
274,368..4,852,723, CV 81.7%). The twin splits that proof into `lemma_div_by_low` and
`lemma_div_short`: seeds 1–3 stable, widest spread `shift_limbs` 222,393..268,540 (CV 8.1%),
nothing flagged. The Dafny twin: `--brittleness --solvers` stable in all six rows, widest CV
15.2% (4.12.1). Both CONTRACT headers parse with `dvl.contract_local.parse_header` (three keys).

## 7. Deviations from the plan (and why)

1. **H4v re-posed: the multiplier is a `T`.** L4's `NatLike::times_word(&self, x: u64)`
   (requires `self.valid()`, ensures `r.valid(), r.value() == self.value() * x`) is H4v's
   statement as planned: `scale(v, k)` with `k: u64` verified with the one-line body
   `v.times_word(k)` on the pins, so a given layer answered the hole. The least change that
   keeps the item ("by repeated `plus`, through the trait only", the same invariant and the
   same `lemma_mul_is_distributive_add` step): `pub fn scale<T: NatLike>(v: &T, k: &T) ->
   (r: T) requires v.valid(), k.valid(), ensures r.valid(), r.value() == v.value() *
   k.value()`. The learner counts with a `T` (`zero`, `from_word(1)`, `plus`) and stops on
   `compare`; `==` on `Ordering` says nothing to the verifier (probed: invariant and
   `decreases` errors), so the reference tests `matches!(i.compare(k), Ordering::Less)` and
   Hint(1) says so. TRIV `{ T::zero() }` fails. Alternatives probed and not taken: a doubling
   item `v * pow2(k)` (verifies, but changes the item's operation and adds `vstd::arithmetic::power2`).
2. **H3v ships `advance`'s `requires old(self).ok()`.** The given `Odo::advance` calls
   `big_add`, which requires `self.total.wf()`; with no `requires` on the trait method the
   shipped implementation fails, and an implementation cannot add one (P1dv). QPLAN §14.0's
   form allows it ("or with only the ones the item gives"). The learner writes `advance`'s
   `ensures` and `current`'s `requires` and `ensures`; a commented `current_check` makes
   `current`'s specification machine-checked (the given client never calls it).
3. **The labelled assume of T1v and H3v is the first statement of the client**, not its last:
   with the assume last, H3v's client fails at its second `advance` call in the shipped file.
   T1v follows the same form.
4. **C1d's failure demo and C4dv's Dafny demo refine a small base module of their own**, not
   L4's QG_L4_Spec: a Dafny specimen is verified alone (`dvl.dafny._specimen_program`), so it
   cannot reach L4 (probed: "module QG_L4_Spec named as refinement base does not exist"), and
   an abstract base in a specimen is a learner-lint finding (Δ3). The base is a concrete
   module whose bodyless declarations carry one `ensures` each (loud holes, counted in the
   demo's output; the learner lint is clean). C1d's success, in the unit, does refine
   QG_L4_Spec. The author notes' §R.3 alternative rested on the specimen reaching L4.
5. **P3d's scenario** refines like QG_L4_Limbs (`Wf = L1.Valid`) and recurses on `n - 1`, not
   on `n / BASE` under `Canonical` as the plan's probe did: that body was H2d's helper
   recursion. The answer is unchanged.
6. **X2d's twin proves `FlatSame` through a `reference-only` helper** that carries the measure.
   The direct answer of the author notes (`decreases Size(c), LeftSize(c)` on `FlatSame`)
   verifies, but `reference_lint` reports `statement-differs` and `specfreeze --check`
   `freeze-changed` on it (a `decreases` clause is part of the statement; `open_specs` accepts
   added `requires`/`ensures` only). The learner file is as planned. §9 asks the tools lane
   for the fix.
7. **H7d's reference helper `AddCCanonical`** states the one-step unfolding and the tails'
   canonical form: as A.3 had it, it was stable but spread 373,145..2,033,956 under 4.14.1
   (CV 77.3%); restructured, 328,070..434,227 under 4.12.1 and 566,652..709,540 under 4.14.1
   (CV ≤ 12%). `FromNatCanonical` stays (28,201..50,475, CV 26%, flagged, never gating).
8. **Checks the plan did not list**: `AddWithCarryCheck` (T1d), `flip_check` (T1v),
   `current_check` (H3v), `scale_check` (H4v), `bump_check`, `transfer_check` (H5v, H6v),
   each commented under `Uncomment as you go:`, live in the twins.
9. **Names the plan left open**: W1d `SumAbove` (uses `FromNatCorrect`, `AddCorrect`,
   `CmpCorrect` of `QG_L4_Limbs`, imported as `Limbs`); C1d `CardNat`, nested in
   `Q08_InternalsII` (a nested module may refine a top-level abstract module); C2v `Dial`/
   `Knob`/`leave_zero`; W3v `cell_round_trip`; C3v `peek`/`is_small`.
10. **The Verus crate root imports `core::cmp::Ordering`** (H4v's answer needs it; Ordering is
    not re-exported by L4).

## 8. Runs (final files)

- `vcheck`: unit `dafny/Q/Q08_InternalsII/std` 151 verified, 7 holes; crate 5 holes; exits 2 +
  2; agent files 0 holes. `vcheck --ref`: Dafny twin unit 157, Verus twin crate 22, Dafny exit
  twin 139, Verus exit twin 4, agent twins 129 and 11; all 0 holes. `vaudit`: one finding per
  hole (Dafny `audit-assume` or `audit-bodyless-ghost`, Verus `hole-assume` or
  `hole-external-body`), 0 on the agent files; `vaudit --ref` 0 on every twin.
- `vcheck --ref --pin-counts Q08`: Dafny 157 (17 symbols pinned, floor 17), Verus 22 (10,
  floor 10), 9 files. The refined lemmas of `Q08_Canon.dfy` are not among the pinned symbols
  (their statements are inherited, so the learner file gives them no contract); deleting one
  leaves a hole at L4's line and a `freeze-missing`, so the gate still fails. `vcheck
  --shipped Q08`: 9 files, 0 problems.
- `specfreeze --pin Q08`: 153 statements in 14 files, open specs `Odometer::advance`,
  `Odometer::current`, `Toggle::flip`; `--check Q08`: 0 findings.
- `pins.py --ci --module Q08`: 30 pins, 0 problems; `pins.py --ref --module Q08`: 6 checks, 0
  problems; four sealed sidecars written by `pins.py --update`.
- `firsttry.sh Q08 --lint-hollow`: OK (14 files). `--report`: 6 unfilled slots, 2 unattempted
  test-outs, 18 commented checks, 0 missing, vacuous or banned.
- `reference_lint.py --module Q08`: 0 findings (7 twins).
- `check_course_map.py`: no Q08 error (the 30 errors are Q09's, in progress).
- Brittleness (advisory): `--ref --brittleness --solvers` on the Dafny twin unit, exit twin
  and agent twin: stable in all six rows; `--ref --brittleness` on the Verus twin crate, exit
  twin and agent twin: stable on seeds 1–3.
- Leak checks: the leak-pattern verifier reports no Q08 file (its 4 problems are Q07's
  `lib.rs` and installed `bench/public` sets); a line-level check of every Q08 answer line
  (twin lines absent from the learner file inside H/T/X blocks) against every Q07–Q09
  learner-visible file and the given layers found only generic lines (`let mut i: usize =
  0;`, the quoted inherited statement, `QG_L4_Limbs`'s own `L4.AddCorrect(a, b);`).
- **Learner-flow simulation** on the scratch git root (`main` = shipped, branch `work`):
  `--check` with T1d and T1v written and the slots unfilled refused both T items ("waits for
  the module's predictions"); the six reference answers recorded 6/6 first-try passes; the
  next `--check` recorded T1d and T1v as passes (their checks enabled in scratch); `--exit` as
  shipped: 0/4, every block `unattempted`, nothing recorded; with the exit twins: "4/4
  (threshold 3; per language Dafny 2/2 (≥1), Verus 2/2 (≥1)) PASS"; with the twins at the
  learner paths and the switches enabled: `--report --strict` exit 0 ("strict: OK"), `vcheck
  --gate` 157 and 22, `vaudit` 0 and 0, `specfreeze --check Q08` 0, `pins.py Q08` 6 pass.
  Negative controls: X1d's single `L4.AddCorrect(Rev(a), Rev(b))` fails (the parent's
  postcondition, `QG_L4_BigNat.dfy:298`); X2d's proof with no `decreases` fails ("cannot prove
  termination"); X2d's direct answer verifies (138) and gives `freeze-changed —
  Q08_ExitFlat.FlatSame` under `specfreeze --check`.
- QPLAN §6 Q40's confirmations on the built files: `--lint-hollow` OK; `--check` and a dry
  `--exit` as above; `--report --strict` OK; `--empty-body` passes H1d, H2d, H7d and X1d (§3);
  `vcheck --shipped Q08` 0 problems. The refinement-hole form needs nothing more.
- `vcheck --test Q08`: no test in either unit (Q08 has no property-test item), so the tool
  reports "no test ran"; the strict report runs no tests for Q08.

## 9. Open issues

- **Tools (high, for Q08's empty-body run):** `firsttry --empty-body` refuses the statement
  holes T1v and H3v instead of skipping them (QPLAN §6 Q40), so `firsttry.sh Q08
  --empty-body` exits 1 with 14/16. Proposed: skip a block whose hole is a labelled assume and
  whose first fn is a bodyless trait spec fn (a statement hole), reporting it as skipped with
  the reason.
- **Tools (medium):** an exit item that ships a lemma with no `decreases` (X2d) is completed
  by adding one; `open_specs` should also accept an added `decreases` clause where none
  shipped (or an `open_measures` field), in `specfreeze --check` and `reference_lint`. Until
  then a learner's direct X2d answer is a freeze change (rubric A5), and the twin uses a
  helper.
- **Tools or plan (for Q07's lane too):** Dafny specimens cannot import a given layer; Q07's
  `card-c1d.dfy.specimen` (`import opened QG_L1_BigNat`) will stop at resolution.
- **DV5 (low):** H4v's `scale` multiplies any two `NatLike` values by repeated addition. If
  Q16 poses full multiplication of BigNats, a learner's own Q08 code is an O(value) answer to
  copy; DV5 should state the schoolbook form or a form line.
- **Kits:** the chapter states the hole counts of §1 (Dafny 1 + 3 + 3, Verus 3 + 2, exits 2 +
  2, agent files 0), shows the C4dv demos' output only after P1dv's and P3d's boxes and C5dv's
  after P4dv's, and explains that the Dafny demos refine a local base. The rubric's A5 line
  names `Toggle::flip`, `Odometer::advance`, `Odometer::current` as open statements.
- **Accepted exposure (low):** `Q08_CanonRaw.FromNatCorrect` ships proved by L3's
  `FromNatCorrect`, `NormalizeToNat` and `NormalizeCanonical`, the pattern of H1d's answer on
  another argument (the plan's choice, to keep H2d's answer out of the file); the exit's given
  `FromNatMsfRev` recurses on `n / BASE` like H2d's helper (the exit follows H2d).
