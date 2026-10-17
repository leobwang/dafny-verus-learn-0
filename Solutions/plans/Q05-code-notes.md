# Q05 code notes (DV3a, the Q05 module lane)

> **Author-only.** Prediction answers, the evidence each was captured from, the hole
> gate results, the agent files' receipts and every deviation from the plan. Never quote,
> paraphrase or link any of it from a learner-visible file. The item plan is `QPLAN.md`
> §10 (learner-visible) and `Solutions/plans/Q04-Q06-author-notes.md` §3 with Appendices
> A.5 and A.8–A.12 and B.4, B.6, B.7, B.9 (the plan lane's author notes; exit statements
> in §3.5); this file records what the module lane built and re-captured on the real
> files, 2026-10-05.

Every run below went through the course wrappers (`scripts/vcheck`, `scripts/vaudit`,
`scripts/pins.py`, `scripts/firsttry.sh`, `scripts/specfreeze`, or the `dvl` library
functions they call), at the course pins (Dafny 4.11.0, `--resource-limit 5000000`,
`--cores 2`; Verus 0.2026.09.27, `--rlimit 2`), one solver job at a time under the `dvl`
caps (Dafny 8 GB, Verus 16 GB), each started only with at least 31 GB available
(`free -g` showed 93–104 GB). The one plain-binary run (P3dv's `dafny build --target py`)
went through `dvl.common.run_capped` with an 8 GB cap. Probes, drivers and scratch course
roots are lane scratch under `/tmp/dvl0-dv3a-q05/` (`probe/`, `root/`, `logs/`, raw
outputs under `scratch/runs/`) and are not archived; the decisive ones are described
below.

## 1. Files

| learner file | shipped state (tool count) | twin |
|---|---|---|
| `dafny/Q/Q05_Frames/std/Q05_Frames.dfy` | verified, 5 holes (H1d–H5d), 58 tasks; T1d empty with one commented check | `Solutions/dafny/Q/Q05_Frames/std/Q05_Frames.dfy` (66 tasks; regions on H1d–H5d) |
| `dafny/checks/Q05_checks.dfy` (P8d) | verified, 0 holes | `Solutions/dafny/checks/Q05_checks.dfy` |
| `verus/q/q05_frames/src/lib.rs` | verified, 4 holes (H1v, H2v, H4v, H5v); T1v empty with one commented check | `Solutions/verus/q/q05_frames/src/lib.rs` (28 verified; `// triv:` on every exec item) |
| `dafny/Q/Q05_Frames/exit/Q05_Exit.dfy` | verified, 2 holes (X1d, X2d) | `Solutions/dafny/Q/Q05_Frames/exit/Q05_Exit.dfy` (36) |
| `verus/q/q05_frames/src/exit.rs` | verified, 2 holes (X1v, X2v) | `Solutions/verus/q/q05_frames/src/exit.rs` (3; `// triv:` on both) |
| `dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` | failed at resolve: 1 error, 0 holes | `Solutions/dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` (32; the reference section) |
| `verus/q/q05_frames/src/agent.rs` | failed at resolve: 1 error, 0 holes | `Solutions/verus/q/q05_frames/src/agent.rs` (2; the reference section) |
| `specimens/Q05/P4d.dfy.specimen`, `P5v.rs.specimen`, `P6d.dfy.specimen` (obligation) | slots unfilled | `Solutions/specimens/Q05/` (same names; §6 item 2) |
| `specimens/Q05/card-c{1,2,3,4}d.dfy.specimen`, `card-c{3,4,5,6}v.rs.specimen` (WRITE demos, in-file `// EXPECT`) | red by design | none (demos are given) |
| `specimens/Q05/card-c7dv-{d.dfy,v.rs}.specimen`, `card-c8dv-{d.dfy,v.rs}.specimen` (divergence demos) | C7dv: red / test; C8dv: both verify | none; sidecars `expected/specimens/Q05/*.expect` (C7dv's two sealed) |
| `slots/Q05.slots` (4 lines, unfilled) | — | `Solutions/slots/Q05.slots` |
| — | — | `expected/Q05.pins` (4 salted hashes), `expected/Q05.counts` (schema 2: 2 units, 7 files), `expected/Q05.freeze` (126 statements in 22 files; `open_frames` Pop), `expected/Q05_AgentInfra.audit` and `expected/q05_frames_agent.audit` (0 findings each, the repaired files) |

## 2. Prediction answers, re-captured

| item | answer | evidence (2026-10-05) |
|---|---|---|
| P1dv | `D:fail V:ok` | `vcheck --json --module Q05 probe/p1dv_d.dfy` (the docstring's class `Counter` verbatim): verdict failed, stage verify, 22 verified, one error at the field read: "insufficient reads clause to read field; Consider adding 'reads this' …". `p1dv_v.rs`: verified (0 verified: a spec fn alone has no obligation) |
| P2dv | `D:ok V:fail` | `p2dv_d.dfy` (G, no clause): verified, 23. `p2dv_v.rs` (g, `decreases m`): `--json` verdict failed, stage verify, one error "could not prove termination" at `g(m, (n - 1) as nat)` |
| P3dv | `D:no V:8` | Dafny: `dafny build --target py` of the docstring's file in `probe/py3/` through `run_capped` (8 GB): exit 0, "2 verified, 0 errors"; the generated `p3dv_d-py/` holds `P3.py`, `module_.py`, `__main__.py`, `_dafny/`, `System_/`; no line of any of them mentions `Shadow` (class `Tagged` has `x` and `ctor__` only). Verus: `vcheck --test probe/p3dv_v.rs`: `size_is_8` PASSED, `size_is_16` FAILED |
| P9dv | `b` | paper (the author notes §3.1): the call's precondition, and the assertion under the postcondition and the frame for the havocked contents; a) drops the assertion, c) inlines a body the caller never sees, d) drops the precondition and the frame |
| P4d | `FAILS b` | `pins.py --ref --module Q05` on the twin (and the demo driver on both files): four errors on [b]'s line, one per conjunct of `Valid()` (related locations on `Valid`'s line); the learner specimen as shipped: 11 verified, 1 hole (`bodyless-method`), the same four errors on [b] |
| P5v | `FAILS b` | twin: one "assertion failed" on [b]'s line, 5 verified; the learner specimen: 1 hole (`external_body`), the same error |
| P6d | `FAILS d` | "a postcondition could not be proved on this return path" in `OtherLimbNoFrame`, related location on [d]'s `ensures` line |
| P8d | `3` | `pins.py --ref`: the enabled check passes (`dafny test`) |

`pins.py --update --ref --module Q05` wrote the four salted pins; `pins.py --ref --module
Q05`: "8 check(s); 0 problem(s)" (the four verdict pins, the three obligation twins, the
value slot). A learner-flow simulation (§7) recorded all eight as first-try passes.

**Test-out answers** (author notes §3.1): `Odometer` / `odometer` with `decreases hi, lo`.
Re-probed: without a clause Dafny reports "cannot prove termination; try supplying a
decreases clause" at `Odometer(9, hi - 1)`; Verus with `decreases lo, hi` reports "could
not prove termination" at the same call. The reference forms pass their checks (the twins'
live `OdometerCheck` / `odometer_check`).

## 3. Holes: references, shipped forms and the empty-body gate

References are the author notes' Appendix A.8 (H1d–H5d), A.9 (X1d, X2d), A.10 (H1v, H2v,
H4v, H5v) and A.11 (X1v, X2v), unchanged in code. The shipped forms are §8.0's:

- **H1d** (annotation hole, loop frame missing): `assume false;` first; the copy loop keeps
  `decreases n - i`; region = the two invariants and `modifies b`.
- **H2d** (frame annotation hole): `assume false;` first; no `modifies`; the functional
  `ensures` given; region (in the twin's header) = `modifies this` and `ensures Valid() &&
  Repr == old(Repr)`. `PopCheck` ships commented after the class.
- **H3d** (annotation hole in a `by method` body): `assume false;` first in the by-method
  body; loop, `decreases i`, scan and `return r` given; four regions (the pre-loop
  assertion, the invariants, the two `DropStep` calls, the post-loop assertion).
- **H4d** (annotation hole with the measure missing): `assume false;` first; no loop
  annotation; region = two invariants and `decreases |s| - i, x`.
- **H5d** (code hole with given annotations): `assume false;` first; loop header and its
  three invariants and the two final lines given, empty loop body; two regions (the case
  before the loop, the loop body).
- **H1v, H2v, H4v, H5v, X1v, X2v**: `external_body` over `unimplemented!()`; TRIV bodies
  `{ }`, `{ Err(Full) }`, `{ 0 }`, `{ Err(ParseError::Empty) }`, `{ Err(Short) }`,
  `{ Err(ParseError::Empty) }`. H2v's `try_push` sits in its own `impl LimbStack` block
  under the marker, so the given `inv`/`new` stay above it.
- **X1d** `by method { assume false; }`; **X2d** `{ assume false; }`.

`firsttry.sh Q05 --empty-body` (every default mode and seed; the region gate on the twin
for H1d–H5d, QPLAN §6 Q18 as built): **13/13 holes pass**, exit 0, in about 8 minutes
(run 1, 18:45–18:53) and again on the final files (run 2, 19:02–19:07, 13/13). Per hole: H1d–H5d "the empty
body fails in every run" and "the twin without its 1/1/4/1/2 learner region(s) fails in
every run"; H1v, H2v, H4v, H5v, X1v, X2v run their declared TRIV bodies and fail in every
run; X1d (the whole-body gate now empties only its by-method body) and X2d fail in every
run. No hole is `lever-needed`. §6 Q18's by-method evidence is therefore a gate result,
no longer a bare probe.

## 4. Cards and demos

The author notes §3.3 fixed constraints only; the lane wrote the cards as follows, each
demo captured through the `dvl` library (as `pins.py` runs it):

| card | success (in the file) | failure demo | `after:` | pinned outcome |
|---|---|---|---|---|
| C1d dynamic-frames | class `Meter` (`Repr`, `Valid`, `modifies Repr`, `fresh(Repr - old(Repr))`; `Tick` writes `log[0]`, no growth, no pop) | `card-c1d`: `Meter.Count()` reads `count` with no `reads` | Q05.P1dv | `EXPECT @12 "insufficient reads clause to read field"` (stage verify) |
| C2d by-method | `Triangle(n)` = `0 + 1 + … + n` by an upward loop | `card-c2d`: the loop without `t == Triangle(k)` | — | `EXPECT @20 "a postcondition could not be proved on this return path"` |
| C3d error-propagation | `FirstLimb`, `FirstIsZero` (one `:-`) | `card-c3d`: `FirstIsZero` with `ensures r.Success?` | — | `EXPECT @21 "a postcondition could not be proved on this return path"` (the `:-` line) |
| C4d lexicographic-decreases | `Ack` (`decreases m, n`) and `WalkPairs` (`decreases i, i - j`) | `card-c4d`: `Steps(a, b)` with no clause, the call `Steps(3, b - 1)` | Q05.P2dv | `EXPECT @9 "cannot prove termination"` |
| C3v error-propagation | `first_limb`, `first_is_zero` (one `?`) | `card-c3v`: `ensures r is Ok` | — | `EXPECT @25 "postcondition not satisfied"` (Verus reports the clause's line) |
| C4v lexicographic-decreases | `ack`, `walk_pairs` | `card-c4v`: `steps` with `decreases b` | Q05.P2dv | `EXPECT @18 "could not prove termination"` |
| C5v mut-ref | `Counter::bump`, `swap_limbs` (`*final(a) == *old(b)`) | `card-c5v`: `Counter::check_room(&mut self)` whose contract says nothing about `hits`; a client asserts `hits` unchanged after `Err` | Q05.P5v | `EXPECT @36 "assertion failed"` |
| C6v result | `get_limb` | `card-c6v`: the body skips limb 0 (`i > 0 && i < v.len()`) | — | `EXPECT @13 "postcondition not satisfied"` |
| C7dv (erasure) | — | `card-c7dv-d`: a compiled method reads a ghost field; `card-c7dv-v`: `size_of::<Tagged>() == size_of::<Plain>()` in a test | Q05.P3dv (both) | sealed sidecars; as captured: Dafny resolve error "a ghost field is allowed only in specification contexts"; Verus `command: test`, `same_size` passed |
| C8dv (`:-` vs `?`) | — | `card-c8dv-d`: a user `Outcome<T>` with `IsFailure`/`PropagateFailure`/`Extract` and two `:-` steps; `card-c8dv-v`: two `?` steps whose error converts by `impl From<Odd> for ParseFail` | — | readable sidecars: both verified (Dafny 6, Verus 3); the Verus sidecar is 509 lines (func-details lists vstd's `From` impls) |

Leak constraints honoured: no demo grows an array or pops (H1d, H2d), no by-method fold over
a suffix (X1d), no loop over digits or two-field parse (H5d/H5v, X2d/X2v), no odometer or bit
count (T1, H4), no stack push or two-account move (H2v, X1v). C5v's failure method mutates
nothing (a conditional bump with a `Result` would be H2v's answer shape). Every demo whose
output settles a Q05 prediction carries its `after:` line. The WRITE demos' in-file `EXPECT`
lines stay readable (Δ120's Open item: an `after:` line cannot hide in-file text).

## 5. Agent files (infra debugger): receipts as captured

The planted failures and the given code are the author notes' §3.4 and A.12; the files add
the CONTRACT block (line 1), a header that states the shipped counts, and RECEIPTS and
DIAGNOSIS blocks at the end (after the code, so filling them moves no receipt's line).

| file | state | `vcheck --json` | `vaudit` |
|---|---|---|---|
| Dafny | shipped | exit 1 (record `exit_code` 2), failed, stage resolve, 0 holes, one diagnostic at 55:13 "unresolved identifier: Cmp" | exit 1, 3 findings: two `audit-error` (no summary line; did not complete, exit 2) and `options-attribute` at line 43 |
| | import repaired | verified, 32 | 1 finding: `options-attribute` at line 43 |
| | both repaired (twin) | `--gate` verified, 32, 0 holes, 0 errors | 0 findings; `--compare expected/Q05_AgentInfra.audit` matches |
| Verus | shipped | exit 1, failed, stage resolve, 0 holes, one diagnostic at 49:5 E0425 "cannot find function `add_limb` in this scope" | exit 1, 2 findings: `audit-incomplete` (the `--no-cheating` run stopped at resolve) and `outside-verus` at line 55 |
| | import repaired | verified, 1 | 1 finding: `outside-verus` at line 55 |
| | both repaired (twin) | `--gate` verified, 2, 0 holes, 0 errors | 0 findings; `--compare expected/q05_frames_agent.audit` matches |

The audit pins were written with `vaudit --write` on a scratch course root holding the
repaired files at the learner paths, so `expected/` names no reference path (Δ113). The
twins carry the receipts, the DIAGNOSIS and the soft-spot note in their closing section.

## 6. Deviations from the plan (and why)

1. **Dafny file order.** QPLAN §8.0 orders W items before WRITE cards. W1d is the given
   `LimbStack` class, and H1d and H2d are methods of that class (a Dafny class cannot be
   split), so W1d sits after the WRITE cards, directly before the holes: P block, T1d,
   C1d–C4d, W1d (with H1d, H2d inside), H3d–H5d, final section. The cards still precede
   every hole that uses them; the Verus file keeps §8.0's order (H2v's method is in its own
   `impl` block).
2. **P4d and P5v twins carry reference bodies.** The learner specimens declare `Push` and
   `maybe_push` by contract only (author notes B2), but `reference_lint.py` rejects the
   bodyless and `external_body` hole forms in a twin. The twins give the reference bodies
   (Solutions only); a caller sees the contract either way, and `pins.py --ref` confirms
   `FAILS b` on both twins.
3. **C4's loop example** is a triangular pair walk (`decreases i, i - j`), not a refill
   loop: a refill (reset to a constant) is T1's odometer in loop form. The plan constrained
   only the demos.
4. **Check fns.** Each hole but H3d gets a commented check (`PushCheck`, `PopCheck`,
   `CountOnesCheck`, `ParseDecimalCheck`; Verus `*_check`), live in the twins (the Dafny twin
   adds an `"7x"` case). H3d's check is its by-method postcondition. The Verus checks use
   empty inputs where a literal would need unfolding steps of its own.
5. **`// did:` receipt** on T1v's `compute_only` check, in both files (the reference lint
   requires it), as Q02's T1v.
6. **Verus exit file:** the given `ParseError`, `is_digit` and `parse_digit` sit above the
   X1v block with `Account` and `Short` (A.11 had them between the blocks; the plan's
   §10.1 row says "above the blocks").
7. **P9dv's block** writes the caller as a method `Caller` (`requires a.Length == 2`,
   `modifies a`) and gives the options without the author notes' parenthetical reasons.
8. **`swap_limbs`'s postcondition** is `*final(a) == *old(b)`: this Verus requires the
   dereference of `final` on a `&mut` parameter of a non-struct type.

## 7. Runs (final files)

- `vcheck --ref`: Dafny std twin 66, check twin 31, exit twin 36, agent twin 32; Verus
  crate twin 28, exit twin 3, agent twin 2; all verified, 0 holes. `vaudit --ref`: 0
  findings on every twin.
- Learner files: `vcheck dafny/Q/Q05_Frames/std` 58 verified, 5 holes; `vcheck
  verus/q/q05_frames` 4 holes; exits 2 + 2 holes; check unit 0. `vaudit`: one finding per
  hole (Dafny `audit-assume`, Verus `hole-external-body`), 0 on the check unit.
- `vcheck --ref --pin-counts Q05`: Dafny 66 (21 symbols, floor 21), Verus 28 (18, floor 18),
  7 files. `vcheck --shipped Q05`: 7 files, 0 problems.
- `specfreeze --pin Q05`: 126 statements in 22 files, `open_frames = ["Q05_Frames.LimbStack.Pop"]`
  with its `frame_ensures`; `--check Q05`: 0 findings. On a scratch root with the twin at the
  learner path: 0 findings; with Pop's functional `ensures` deleted: `freeze-changed`.
- `vcheck --test dafny/checks/Q05_checks.dfy`: 1 passed (as shipped the slot is commented;
  with the slot enabled on the simulation root: `P8d` PASSED).
- `pins.py --ci --module Q05`: 29 pins, 0 problems. `pins.py --ref --module Q05`: 8 checks,
  0 problems.
- `firsttry.sh Q05 --lint-hollow`: OK (20 files). `--report`: 8 unfilled slots, 2
  unattempted test-outs, 37 commented checks, 0 missing, vacuous or banned.
- `reference_lint.py --module Q05` (CI=true): 1 finding, `statement-differs` on Pop, the
  tools lane's known gap (§8).
- Learner-flow simulation on a scratch git root (`main` = shipped, branch `work`):
  `--check` with T1d/T1v written and the predictions unfilled refused both T items ("waits
  for the module's predictions", exit 1, nothing recorded: §6 Q23 as built); filling the
  eight slots with the reference answers recorded 8/8 first-try passes (the T items refused
  again in that run); the next `--check` recorded T1d and T1v as passes; `--exit` with the
  exit twins' bodies: "4/4 (threshold 3; per language Dafny 2/2 (≥1), Verus 2/2 (≥1))
  PASS"; with the twins at the learner paths and the slots enabled, `--report --strict`
  exit 0 ("strict: OK"), `vcheck --gate` 66 and 28, `vaudit` 0 and 0, `specfreeze --check`
  0 findings.
- `check_course_map.py`: no Q05 error (the full run's one error is Q04's `library.rs`).

## 8. Open issues

- **Tools (reference lint):** `reference_lint.py` reports `statement-differs` on
  `Q05_Frames.LimbStack.Pop` (the twin's added frame clauses). The tools lane's report gives
  the fix in `compare_declarations` (honour `frame_symbols`/`open_frames`, check the shipped
  `ensures` as a subsequence). Until then the static job's reference lint fails on Q05.
- **Chapter lane:** `docs/Q05_Frames.md` does not exist, so `chapter_lint.py --all` fails
  on Q05. The files table quotes: exercise 5 + 4 holes, check unit 0, exits 2 + 2, agent
  files 1 planted error each (`expected/Q05.counts`). The chapter shows the C7dv demos'
  output only after P3dv's box, and C4/C1/C5 demo outputs only after P2dv's, P1dv's and
  P5v's boxes.
- **Kit lane:** no leak patterns, bank, rubric or paper pair for Q05 yet.
- **Accepted exposure (low):** the given `ParseField` of the Dafny exit file opens with
  the same empty-input line as H5d's answer and parses digits in a loop (A.9 as planned);
  the exit file is closed until the exit, which follows the holes. The exit X1d reuses the
  slice assertion that H4d's given code shows (a shared technique).
