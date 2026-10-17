# Q11 code notes (DV5a, the Q11 module lane)

> **Author-only.** Prediction answers, the evidence each was captured from, the hole gate
> results, the admissibility results (the four results of QPLAN §19.0) of every H item, the
> construct-free probes, and every deviation from the plan. Never quote, paraphrase or link
> any of it from a learner-visible file. The item plan is `QPLAN.md` §19 and §21
> (learner-visible) and `Solutions/plans/Q10-Q18-author-notes.md` §3, §13 and Appendices
> A.9, A.10, A.11, A.12 and C.3; this file records what the module lane built and
> re-captured on the real files, 2026-10-07.

Every run went through the course wrappers (`scripts/vcheck`, `scripts/vaudit`,
`scripts/pins.py`, `scripts/firsttry.sh`, `scripts/specfreeze`, `scripts/reference_lint.py`)
at the course pins (Dafny 4.11.0, its bundled Z3 4.12.1, `--resource-limit 5000000`; Verus
and vstd `0.0.0-2026-09-20-0158`), one solver job at a time under the `dvl` caps (Dafny
8 GB, Verus 16 GB; the empty-body sweep also inside a 16 GB `systemd-run` scope, the lane's
share), each started with 101–102 GB available (`free -g`). `DVL_SCRATCH` was
`/tmp/dvl0-dv5a-q11/scratch`. Probes ran from `instructor/scratch/q11/` (deleted at the
end); the variant driver (§4), the variants, the learner-flow root and the raw outputs are
lane scratch under `/tmp/dvl0-dv5a-q11/` (`drv/`, `var/`, `root/`, `scratch/runs/`) and
are not archived; every decisive result is quoted below.

## 1. Files

| learner file | shipped state (tool count) | twin |
|---|---|---|
| `dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy` | verified, 5 holes: H1d, H2d (`{ assume false; }`), H5d (bodyless function with an `ensures`), H7d, H8d (the labelled assumes of `Pre1Exact`, `Pre2Exact`); P1dv, P2dv; W1d; modules `Q11_PracticeIB`, `Q11_VcProg`, `Q11_VcAnswer` (marker `// specfreeze: frozen-imports`, no import, placeholders `true`), `Q11_VcCheck` | twin |
| `dafny/Q/Q11_PracticeIB/std/Q11_Wp.dfy` | verified, 1 hole (H9d, bodyless lemma); W2d | twin |
| unit `dafny/Q/Q11_PracticeIB/std` | learner loop 146 verified, 6 holes | twin 150 verified (`expected/Q11.counts`: 14 symbols, floor 14) |
| `verus/q/q11_practice_ib/src/lib.rs` | verified, 3 holes (H3v, H4v, H6v: `external_body` over `unimplemented!()`) | twin (`// triv:` on each) |
| `verus/q/q11_practice_ib/src/perm.rs` | verified, 1 hole (H10v, `external_body`) | twin (`// triv: { }`) |
| crate `verus/q/q11_practice_ib` | 4 holes | twin 7 verified (4 symbols, floor 4) |
| `dafny/Q/Q11_PracticeIB/exit/Q11_Exit.dfy` | verified, 1 hole (X1d, bodyless lemma) | twin 129 verified |
| `verus/q/q11_practice_ib/src/exit.rs` | verified, 1 hole (X1v, `external_body`) | twin 1 verified (`// triv: { }`) |
| `slots/Q11.slots` (2 lines, unfilled) | — | `Solutions/slots/Q11.slots` |
| — | — | `expected/Q11.pins` (2 salted hashes), `expected/Q11.counts` (schema 2: 2 units, 6 files), `expected/Q11.freeze` (42 statements in 6 files; `open_bodies = ["Q11_PracticeIB.AddCanon", "Q11_VcAnswer.Pre1", "Q11_VcAnswer.Pre2"]`; `[file.frozen_imports] "Q11_VcAnswer" = []`) |

No specimen, card, agent or harness file: QPLAN §21 gives Q11 none (no agent run; practice
modules write no card). Header counts as shipped: 10 holes (Dafny 6, Verus 4), 2
predictions, 2 exit items (1 + 1).

## 2. Prediction answers, captured

Each scenario was run as its own file with `scripts/vcheck --module Q11 <probe>`; the
docstrings quote the probes verbatim.

| item | answer | evidence |
|---|---|---|
| P1dv | `D:fail V:ok` | Dafny `Cell.CopyTo(other)` with `modifies this` writing `other.n`: failed (22 verified, 1 error) "assignment might update an object not in the enclosing context's modifies clause". Verus `copy_to(&mut self, other: &mut Self)` writing `other.n`: verified (1) |
| P2dv | `D:ok V:err:resolve` | Dafny `ghost var g := x; var y := g + 1;` in a method: verified (23): the local `y` is not used in compiled code, and Dafny accepts it. Verus `let ghost g = x; let y = g + 1;` (`x: u64`): failed, stage resolve, "cannot access spec-mode place in executable context" (the same with and without a `requires x < 100`) |

P2dv's Dafny answer is not the planner's expectation (the plan's prose says "used in a
compiled expression"); the scenario is QPLAN §21.2's code verbatim, and the module lane
captures the answer on the built scenario (author notes §0.2). It is not settled by an
earlier prediction (Q03.P4v asks about Verus mode crossings between functions, Q05.P3dv
about erasure in compiled output). `pins.py --update --ref --module Q11` wrote the two
salted pins; `pins.py --ref --module Q11`: "2 check(s); 0 problem(s)".

## 3. Holes: references, line counts and the empty-body gate

References are A.9, A.10, A.11 (X1d), A.12 (X1v) and C.3 (the VC layout), verbatim in their
proofs; the checks are new (§6). Line counts under QPLAN §19.0's rule (`rev/pcount.py`,
C.8, run on the twins; exec code excluded): H1d 0 (2 code), H2d 2 (6 code), H5d 3 (1 code),
H7d 1, H8d 1 (the predicate bodies), H9d 3, H3v 0 (5 code), H4v 2 (8 code), H6v 8 (6 code),
H10v 0 (4 code), X1d 2, X1v 0 (5 code): every item inside its band (Dafny ≤ 10, Verus ≤ 15),
as §13.2 of the author notes has them. No invented lemma. `scripts/pcount.py` (DV5d) counts the ghost update
`Contents := a[..n]` as proof: H1d 1 (1 code), H2d 3 (5 code); both stay in the band.

`systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 scripts/firsttry.sh Q11
--empty-body` (2 m 38 s): **11/12 pass**, exit 1:

| item | result |
|---|---|
| H1d, H2d, H9d | the empty body fails in every run (maxauto and seeds 1–3) |
| H7d, H8d | the empty body of `Pre1Exact` / `Pre2Exact` fails in every run, with the shipped placeholder `true` in `Pre1` / `Pre2` |
| H3v (TRIV `{ Ok(()) }`), H4v (TRIV `{ Err(AccError::TooSmall) }`), H6v (TRIV `{ 0 }`), H10v (TRIV `{ }`) | every mode fails, the declared TRIV body included |
| X1d | fails in every shipped run; finding `lever-needed` (maxauto, with automatic induction, verifies: a hole + lever exit, as the plan says) |
| X1v (TRIV `{ }`) | every mode fails |
| **H5d** | **no verdict** ("error" in all four runs): the gate gives a bodyless *function* the body `{}`, which is a parse error ("invalid UnaryExpression" at the inserted body). Tools gap, §8. The forms gate of the same run: "construct-free answer 1 fails verification" (the twin's `// cfree: { Normalize(Add(a, b)) }`, the body without its lemma calls) |

**H5d by the variant driver.** `drv/varrun.py` runs a variant of the learner file exactly as
`dvl.dafny.empty_body` runs its variants (the same `program`, `_scratch_copy`,
`_lever_edits`, `--manual-lemma-induction false --disable-nonlinear-arithmetic false` for
maxauto, `_verify_program` on the one symbol under each pinned seed; the dvl caps), with the
item's body given instead of `{}`. `AddCanon` with the body `Normalize(Add(a, b))`: failed
in maxauto and seeds 1–3 ("value does not satisfy the subset constraints of 'CanonSeq'" and
the postcondition); with the body `a`: failed in all four (postcondition). This is the
empty-body result for H5d: the function body without the lemma calls fails at maximal
automation and under the shipped options.

## 4. The VC items (H7d, H8d): the three-module layout, `cfree:` and the restating answer

All on the learner file with the labelled assumes deleted and the Exact lemmas' bodies empty
(`var/vc_*.dfy`), through `drv/varrun.py` (maxauto and seeds 1–3, symbols
`Q11_VcCheck.Pre1Exact` and `Pre2Exact`):

| `Pre1` / `Pre2` body | result |
|---|---|
| the reference (`x + 2 * y > 0 && x + y < 10`; the two-implication `Pre2`) | verified in all eight runs |
| `true` / `true` (the shipped placeholders) | failed in all eight runs (postcondition) |
| `false` / `false` | failed in all eight runs (postcondition) |
| `Post1(Prog1(x, y))` / `Post2(Prog2(x, y))` (the planned `cfree:` answers) | failed at resolve in all eight runs ("unresolved identifier: Post1", "Prog1", "Post2"): the import-free `Q11_VcAnswer` cannot name the given program |
| the same, with `import opened Q11_VcProg` added to `Q11_VcAnswer` | verified in all eight runs; on the learner-flow root (§7) `specfreeze --check Q11` reports `freeze-imports-changed — module Q11_VcAnswer` (the tools lane's Q62 marker catches it) |
| **the program restated with `var` bindings**: `Pre1 { var x1 := x + 2 * y; var y1 := x1 - y; x1 > 0 && y1 < 10 }`, `Pre2 { var y1 := if x > y then x - y else y - x; var x1 := x + y1; x1 >= 5 && y1 <= 3 }` | **verified in all eight runs**; on the learner-flow root with everything else complete: `vcheck --gate` verified (150, 0 holes), `specfreeze --check Q11` 0 findings (the predicate bodies are open bodies) |

The last row is a construct-free answer the module lane found: it pastes the given program's
`var` bindings and the postcondition into the predicate, computes no precondition, imports
nothing and calls no given name, so neither the frozen import list nor the freeze sees it.
It is the plan review's blocker 1 (author notes §13.1 B1) in another form. QPLAN §19.0
requires every construct-free answer the author knows of to fail; this one passes, so **H7d
and H8d are not admitted** (`admitted = false, minutes = 0`), and their fallbacks (a
precondition for one assignment; a branch-free program) carry 0 too: the same restatement
answers them. The VCs-by-hand line (20 min) has no minutes until the orchestrator decides
(§9).

The twin carries the planned `cfree:` lines beside `Pre1` and `Pre2` in `Q11_VcAnswer`,
outside any item block, so `firsttry`'s forms gate does not run them (it would put them in
place of the first declaration of the H7d block, which is `Pre1Exact`, a lemma: a parse
error it would count as "killed"). The H7d and H8d markers sit in `Q11_VcCheck` above the
Exact lemmas, so that each block holds its counted hole (the labelled assume): an item
block ends at the `}` of its module, and `Pre1` and `Pre1Exact` are in different modules.
The `true`/`false` "triv" bodies of the plan were run by the driver (above), not as
`// triv:` lines (the TRIV mode is Verus-only).

## 5. Admissibility: the four results

| item | 1. reference complete, in band | 2. empty-body gate fails | 3. stable | 4. pinned API | entry |
|---|---|---|---|---|---|
| H1d | twin unit 150, 0 holes; 0 proof lines | yes (firsttry) | 4.12.1/4.14.1 × seeds 1–3: `Set` 43,249..44,325 (CV ≤ 0.2%) | Dafny 4.11.0 | admitted, 10 |
| H2d | 2 | yes | `CopyFrom` 109,116..142,810 (CV 10.9%, 4.12.1), 135,925..139,121 (4.14.1) | — | admitted, 10 |
| H5d | 3 | yes, by the driver (§3); firsttry: no verdict (tools gap) | `AddCanon` 34,672..35,547 (CV ≤ 0.6%) | L3 `NormalizeCanonical`, `NormalizeToNat`, L4 `AddCorrect` | admitted, 12 |
| H7d, H8d | 1, 1 | yes (placeholders fail) | `Pre1Exact` 9,657..9,696; `Pre2Exact` 14,487..14,939 | — | **not admitted** (§4) |
| H9d | 3 | yes | `WpSoundIfThen` 65,964..68,444 (CV ≤ 0.1%) | — | admitted, 15 |
| H3v | crate twin 7, 0 holes; 0 proof lines | yes, every mode with TRIV | seeds 1–3: `add_word` 6,698..7,946 (CV 7.6%) | L3 `add_limb` | admitted, 10 |
| H4v | 2 | yes | `take_if_at_least` 9,639..9,691 | L4 `cmp`, `core::mem::swap` | admitted, 10 |
| H6v | 8 | yes | `value_two` 90,400..92,698 (CV 1.1%) | — | admitted, 12 |
| H10v (gated) | 0 (4 code) | yes, every mode with TRIV `{ }` | `max_into` 3,351 on every seed (CV 0%) | vstd `0.0.0-2026-09-20-0158` `cell/pcell.rs`: `PCell::new` (l. 141, returns `(PCell<T>, Tracked<PointsTo<T>>)`), `read(&self, Tracked<&PointsTo<T>>)` (l. 232, `returns *perm.value()`), `write(&self, Tracked<&mut PointsTo<T>>, T)` (l. 218, keeps `id()`), `PointsTo::id`, `PointsTo::value -> &T`; no `is_init` | admitted, 15 (design §7.5: admitted by the module lane's gate) |

Stability: `vcheck --ref --brittleness --solvers` on the Dafny twin unit: stable in all six
rows (widest spread outside the target's files, CV 13.9%); `--brittleness --solvers --json
--module Q11` on the twin files as probes gave the per-symbol figures above, nothing
flagged. `vcheck --ref --brittleness` on the Verus twin crate and the exit twin: stable; the
per-symbol figures from the crate as one probe (perm inlined). The exits: X1d
`DigitsLength` 16,913..17,140 (both solvers), X1v stable (26,573..26,673).

Registry (Q11's record, written by this lane): `admitted = true` with QPLAN §21.5's minutes
for H1d, H2d, H3v, H4v, H5d, H6v, H9d and H10v (94 min); H7d and H8d `admitted = false,
minutes = 0` with their fallback texts. Of design §7.5's 177, the H lines carry 94 of 114;
the shortfall is the VCs line's 20 (a DELTAS note, QPLAN §19.0).

## 6. Deviations from the plan (and why)

1. **H7d's and H8d's markers are in `Q11_VcCheck`** (over `Pre1Exact` and `Pre2Exact`),
   not beside the predicates: a block ends at its module's `}`, and the counted hole (the
   labelled assume) must be inside the block (`--lint-hollow`: "an H item ships a hole
   form"). The prompts say to edit `Pre1` / `Pre2` in `Q11_VcAnswer`.
2. **Both placeholders ship as `true`** (QPLAN says `true` for H7d and "as H7d" for H8d);
   `false` was run as the second trivial body by the driver.
3. **The `cfree:` lines of the VC items sit outside any block** (§4), and the twin header
   says so; H5d gained a `cfree:` line in its block (`{ Normalize(Add(a, b)) }`), which
   `firsttry`'s forms gate runs.
4. **The Dafny exit ships `DigitsLength` without a `decreases`**; its default measure is
   `n`, and the twin keeps the shipped header (no measure added).
5. **Checks the plan did not list**: `SetCheck`, `CopyCheck` (frame checks with a second,
   disjoint vector), `AddCanonCheck` (a nested call, so the result is used as a
   `CanonSeq`), `acc_check`, `value_two_check`, `max_into_check`; commented under
   `Uncomment as you go:`, live in the twins.
6. **Names the plan left open**: P1's `Cell`/`CopyTo`/`copy_to`, P2's `Bump`/`bump`; the
   `AccError` variants `Overflow`, `TooSmall`; the exit's `Digits`, `Counter2` as in the
   author notes.
7. **`uses:` lines**: X1v carries `mut-ref, old` (the plan's exit table gives none); X1d
   none.

## 7. Runs (final files)

- `vcheck --module Q11`: Dafny unit 146 verified, 6 holes; crate 4 holes (each hole labelled
  with its item id). Exits: 128 verified + 1 hole; 1 hole. `vcheck --ref`: Dafny twin unit
  150, crate twin 7, Dafny exit twin 129, Verus exit twin 1, all 0 holes.
- `vaudit`: one finding per hole (Dafny `audit-assume` ×4, `audit-bodyless-compiled` (H5d),
  `audit-bodyless-ghost` (H9d, X1d); Verus `hole-external-body` ×5); `vaudit --ref` 0 on
  every twin.
- `vcheck --ref --pin-counts Q11`: Dafny 150 (14 of 20 contract declarations pinned, floor
  14), Verus 7 (4 of 4, floor 4), 6 files. `vcheck --shipped Q11`: 6 files, 0 problems.
- `specfreeze --pin Q11`: 42 statements in 6 files; open bodies `AddCanon`, `Pre1`, `Pre2`;
  frozen imports `Q11_VcAnswer = []`. `--check Q11`: 0 findings.
- `pins.py --ci --module Q11`: 12 pins, 0 problems; `--ref`: 2 checks, 0 problems.
- `firsttry.sh Q11 --lint-hollow`: OK (6 files). `--report`: 2 unfilled slots, 27 commented
  checks, 0 missing, vacuous or banned.
- `reference_lint.py --module Q11`: 0 findings (6 twins).
- `check_course_map.py`: no Q11 error (its one remaining error is in Q12's harness file).
  `--items Q11`: 16 items parse.
- `avoid.sh --track both`: OK, 0 hits.
- Leak checks: the leak-pattern verifier (`tests/instructor/leak_patterns/README.md`):
  "9 module(s), 1284 public files scanned, OK". A line-level check of every twin line inside
  an H/X block that is absent from its learner file, and of the two predicate answers,
  against every learner-visible file (`git ls-files -co` minus the reference trees): hits
  only on the learner files' own commented checks, `Pre2`'s header, L4's own
  `AddCorrect(a, b);`, QPLAN's "the normalized sum" wording and two generic Verus lines of
  Q08's chapter (`self.lo = self.lo + 1;`, `self.hi = self.hi + 1;`). Neither predicate
  answer appears.
- **Learner-flow simulation** on `/tmp/dvl0-dv5a-q11/root` (a git copy of the worktree
  without the reference trees; `main` = shipped, branch `work`): the two reference answers
  recorded 2/2 first-try passes; `--exit` as shipped: 0/2, both blocks unattempted, nothing
  recorded; with the exit twins: "2/2 (threshold 1) PASS"; with the twins at the learner
  paths: `--report --strict` "strict: OK", `vcheck --gate` 150 and 7, `vaudit` 0 and 0,
  `specfreeze --check Q11` 0, `pins.py Q11` 2 pass. Negative controls: §4's import variant
  (gate verified; freeze `freeze-imports-changed`), the restating variant (gate verified;
  freeze 0), the call variant (gate failed at resolve, 4 errors).

## 8. Tools issues

- **High (H5d, and every Dafny bodyless-function hole):** `dvl.dafny.empty_body` gives a
  bodyless function the body `{}`, a Dafny parse error, so `firsttry --empty-body` has no
  verdict for H5d and exits 1. Proposed: for a function or predicate, run the twin's
  `cfree:` bodies in the shipped and maxauto runs (or a declared `// triv:` expression), as
  `drv/varrun.py` did; or skip the shipped gate with a reason when the forms gate has a
  `cfree:` answer.
- **High (H7d, H8d):** a construct form over the answer is needed: a Dafny rule such as
  `no-let` / `arith` (no `var` binding, `if`, `match` or call in the named predicate's
  body), checked at `--check`, `--exit` and `--report --strict`, or a `no-call:` form plus
  a let ban. `forms.py` has no Dafny rule but `trigger` and `stable`. And `cfree:` lines
  need a target (`// cfree: Pre1: { … }`, like `triv: <method>:`) so the forms gate can run
  an answer that lives in another module than the block's first declaration.

## 9. Open issues

- **Orchestrator:** H7d and H8d (§4): admit them on a form check (above) or with
  `/review-code` checking the restatement (the interim rule QPLAN §30 Q62 used for the
  import residual), or keep them at 0. Until then the VCs line carries 0 of its 20 minutes.
- **Records lane:** an as-built DELTAS entry for Q11: the marker placement of H7d/H8d,
  the placeholder `true` twice, the restating answer and the 0-minute line, P2dv's Dafny
  answer as captured, the H5d gate gap and the driver evidence, H10v admitted with its four
  results.
- **Kits lane:** the chapter states the hole counts of §1; the rubric names `AddCanon`,
  `Pre1`, `Pre2` as open bodies and `Q11_VcAnswer`'s import list as frozen; `/review-code`
  checks that `Pre1`/`Pre2` are formulas, not the program restated.
