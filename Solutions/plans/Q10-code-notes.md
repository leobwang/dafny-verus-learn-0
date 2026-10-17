# Q10 code notes (DV5a Q10 lane, as built)

> **Author-only.** Prediction answers, gate results, the four admission results per item,
> the probes behind them and the deviations of Q10's code from the plan. Never quote,
> paraphrase or link any of it from a learner-visible file. The plan is `QPLAN.md` §19–§20
> and `Solutions/plans/Q10-Q18-author-notes.md` §2, §13 and Appendices A.7, A.8, A.11, C.7;
> this file records what the Q10 lane built on 2026-10-07 and where it differs.

Every result below was captured on the pins through the course wrappers (`scripts/vcheck`,
`scripts/vaudit`, `scripts/pins.py`, `scripts/specfreeze`, `scripts/firsttry.py`), one solver
job at a time, under the `dvl` caps (Dafny 8 GB, Verus 16 GB); the two `firsttry --empty-body`
runs ran inside `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`. `free -g`
showed 101–102 GB available before every job (the lane's share is 16 GB, so 31 GB was
needed); no job was killed. `DVL_SCRATCH=/tmp/dvl0-dv5a-q10/scratch`. Probe files are lane
scratch under `/tmp/dvl0-dv5a-q10/probe/` (not archived; the decisive ones are quoted here).

## 1. Files

| file | shipped state | twin |
|---|---|---|
| `dafny/Q/Q10_PracticeIA/std/Q10_PracticeIA.dfy` (modules `Q10_PracticeIA`, then `{:disableNonlinearArithmetic} Q10_Search`, last) | verified, 5 holes (H1d exec `assume false;`, H2d the client's labelled assume, H3d and H5d bodyless lemmas, H4d an annotation hole) | `Solutions/…` 139 verified |
| `verus/q/q10_practice_ia/src/lib.rs` | verified, 7 holes (H1v, H6v, H7v `external_body`; H2v the client's labelled assume; H3v, H5v `proof_note` assumes; H4v an annotation hole) | `Solutions/…` 14 verified |
| `dafny/Q/Q10_PracticeIA/exit/Q10_Exit.dfy` | verified, 1 hole (X1d) | 129 verified |
| `verus/q/q10_practice_ia/src/exit.rs` | verified, 1 hole (X1v) | 1 verified |
| `slots/Q10.slots`, `Solutions/slots/Q10.slots` | `P1dv P2dv = ???` / the answers below | — |
| `expected/Q10.pins` (2 salted), `expected/Q10.counts` (schema 2: Dafny unit 139 / floor 5, crate 14 / floor 8; files 5, 7, 1, 1 holes), `expected/Q10.freeze` (27 statements in 4 files; `open_specs`: `Q10_PracticeIA.Shift`, `high_limb`) | author-written | — |

No specimens (both predictions are docstring scenarios), no check unit, no agent file
(`agentic = []`), no card section (§19.0).

## 2. Prediction answers (captured on the real scenarios)

| item | answer | capture |
|---|---|---|
| P1dv | `D:timeout V:ok` | Dafny: the docstring's `Low` in a module of Q10's unit with L1 opened (`vcheck --module Q10 p1d.dfy`): `inconclusive — 23 verified, 0 holes, 1 error`, "Verification out of resource (P1D.Low)"; `--brittleness --solvers`: inconclusive in all six rows (4.12.1 and 4.14.1 × seeds 1–3). Verus: the docstring's `low` alone (vstd prelude only): verified, 1; seeds 1–3 verified (rlimit count 432, CV 0.0%). |
| P2dv | `D:ok V:ok` | Dafny: the docstring's `Count` (no `decreases`), module of its own in Q10's unit: verified; six rows verified. Verus: the docstring's `count`: verified, 2; seeds 1–3 verified. |

P2dv and Q02.P4dv: the author notes (§2.1) asked for the Dafny half to be replaced if it
repeated Q02.P4dv's lesson exactly. Q02.P4dv's Dafny half is a `<` guard with no `decreases`
(`D:ok`); this one is a `!=` guard, whose guessed measure is sound only because of the
invariant `i <= |s|`. The verdict is the same token, the question is not (does Dafny guess a
measure for `!=` at all, and is it sound here?), so the scenario stays as QPLAN §20.2 states
it. Recorded as a judgement for the kits lane, which may still redraw it.

`pins.py --update --ref --module Q10`: 2 pins; `pins.py --ci --module Q10`: 10 pins, 0
problems; `pins.py --ref --module Q10`: 2 checks, 0 problems.

## 3. References, counts and stability

Counts are QPLAN §19.0's rule (proof lines plus invented statements; exec code excluded); no
item asks for an invented lemma.

| item | reference | proof lines | band | notes |
|---|---|---|---|---|
| H1d `ToU64` | A.7, plus one assertion `BASE <= Pow(\|s\| - 1)` in the many-limb branch and the singleton branch's two lines swapped (identity first) | 5 | ≤ 10 | the edits are for stability (below) |
| H1v `to_u64` | A.8 verbatim | 8 | ≤ 15 | |
| H2d `Shift` (spec) | ensures `Valid(r) && ToNat(r) == BASE * ToNat(s) && (Canonical(s) ==> Canonical(r))` | 1 | ≤ 10 | the body ships **without** A.7's `ToNatCons`/`ValidCons` calls: it verifies against the reference ensures without them (so the given code hints at no conjunct) |
| H2v `high_limb` (spec) | ensures `r == 0 <==> a@.len() == 0` | 1 | ≤ 15 | |
| H3d `ToNatTopLimb` | A.7 plus one assertion `Pow(\|s\| - 1) * s[\|s\| - 1] == BASE * (Pow(\|s\| - 2) * s[\|s\| - 1])` | 6 | ≤ 10 | the quoted attempt is the reference minus the sequence identity (so it carries the product assertion too) |
| H3v `lemma_top_limb` | A.8 verbatim | 4 | ≤ 15 | quoted attempt: the reference minus `assert(s =~= s.drop_last() + seq![s.last()]);` |
| H4d `NormLen` | A.7's three invariants | 3 | ≤ 10 | learner region marked `@hole-begin/@hole-end Q10.H4d` |
| H4v `norm_len` | A.8's three invariant clauses | 3 | ≤ 15 | region marked |
| H5d `ModPowSucc` | `PowPositive(n); LemmaModMod(x, Pow(n), BASE);` | 2 | ≤ 10 | |
| H5v `lemma_mod_weight_succ` | A.8 verbatim (`vstd::arithmetic::div_mod::lemma_mod_mod` by full path) | 4 | ≤ 15 | |
| H6v `Ring::get` | A.8 verbatim | 0 (4 code) | ≤ 15 | |
| H7v `Ring::push_back` | A.8 verbatim | 3 (4 code) | ≤ 15 | |
| X1d `SumLimbs` | A.11 verbatim | — | exit | `Sum` is **ghost** (§6) |
| X1v `halve_words` | C.7 verbatim | — | exit | |

**Stability.** Final runs: `vcheck --ref --brittleness --solvers` on the Dafny twin unit:
all six rows verified, **no flag** (largest spreads: `ToU64` CV 10.9% under 4.12.1 at
36,613–47,459; `Shift` 8.8%; `ToNatTopLimb` below 6%). `vcheck --ref --brittleness` on the
crate twin: seeds 1–3 verified, no flag (largest spread 14.3%, a declaration outside the
crate's files, 3,635–4,865). Exit twins: Dafny six rows verified (widest spread in L1's
`ToNatAppendZero`, 13.9%), Verus seeds 1–3 verified.

The H3d flag the plan carried (CV 27.6% under 4.14.1) reproduced on the plan's A.7 text in
this file (27.5%). Restructurings tried, each measured on the whole twin unit (spreads move
with the file's text): the identity before the call (18.5% in a probe file); `|s| == 1`
first (12.4%); an assertion `Pow(|s| - 1) == BASE * Pow(|s| - 2)` (3–4% in a probe, 10.6%
and later 22.6% in the twin); the product assertion above (below 6% in every later run, in
the twin). The same sweeps flagged `Shift` (23.3%, 39–67k) and `ToU64` (21.5–31.8%, 34–71k)
in some runs; `Shift`'s body without lemma calls and `ToU64`'s explicit bound clear both in
the final run. Every flagged spread was below 1.9% of the 5,000,000 limit.

## 4. The empty-body gate (`firsttry.py Q10 --empty-body`)

Run twice (after the first build, and on the final files): **12/14 hole(s) pass the gate**,
exit 1, both times. Per item:

| item | result |
|---|---|
| H1d | empty body fails maxauto and seeds 1–3; **✗ CONSTRUCT NOT REQUIRED**: the twin's `cfree:` answer `{ var v := ToNat(s); if v < BASE { r := Some(v); } else { r := None; } }` verifies (129 verified in a probe module; `ToNat` is a compiled layer function, so code may call it). Not admitted (§5). |
| H2d | reported ✓, but only because the empty `Shift` body leaves `r` unassigned ("out-parameter 'r' … might be uninitialized"): `firsttry` runs a Dafny statement hole's first method, not its client. Not evidence; the client check is §5's |
| H3d | ✓ maxauto and seeds 1–3 fail |
| H4d | ✓ empty body; ✓ region gate (twin without its learner region); ✓ `cfree: { n := \|Normalize(s)\|; }` fails verification |
| H5d | ✓ seeds 1–3 fail; maxauto `inconclusive` (out of resources at the pinned limit), counted as failing (QPLAN §30 Q66; finding `empty-body-inconclusive`) |
| H1v | ✓ every mode (E0 … EM, TRIV `{ None }`) fails |
| H2v | **✗ FALLS TO AUTOMATION**: an open statement, so the gate lays the twin's `ensures` over the shipped `high_limb` and the E modes keep its given (correct) exec code, which then verifies (E0, E0H, E1, E2, EC seeds 1–3, EM). The statement hole's real gate is its client (§5) |
| H3v | ✓ every mode fails |
| H4v | ✓ every mode fails; ✓ region gate |
| H5v | ✓ every mode fails |
| H6v | ✓ (TRIV default `0` fails; the E modes run the shipped `unimplemented!()` body) |
| H7v | ✓ |
| X1d | ✓ |
| X1v | ✓ TRIV `{ (0, 0) }`; ✓ `cfree: { (lo / 2, hi / 2) }` fails |

**The statement holes' gate, by hand on the built files** (QPLAN §19.0: "a statement hole
skipped with its reason … and checked by its given client instead"): a copy of the shipped
learner file with only the client's labelled assume deleted —
- Dafny (`h2d_client.dfy`, the shipped `Q10_PracticeIA.dfy` minus H2d's assume line): failed,
  4 errors: `ShiftTwice`'s three postcondition conjuncts and the second call's precondition
  `Valid(r1)`.
- Verus (`h2v_client.rs`, the shipped `lib.rs` minus H2v's proof block): failed, 1 error,
  `assertion failed` at `high_client`'s `assert(a.to_nat() == 0)`.
- Too weak / too strong (same copies, `ensures` added): Dafny without the canonicity
  conjunct fails `ShiftTwice`'s `Canonical(r)`; Dafny `ensures r == [0] + s` fails the body
  (empty input). Verus `a@.len() == 0 ==> r == 0` fails the client's assertion; Verus
  `r == a@.last()` fails the body (postcondition). The reference `ensures` verifies in both
  copies (`h2v_ref.rs`: 0 errors).

**Other construct-free or shortcut answers probed:** `NormLen` by `n := |Normalize(s)|`
fails (two postcondition errors). X1d: `t := Sum(s)` is refused at resolve once `Sum` is
ghost ("a call to a ghost function is allowed only in specification contexts"); a
**recursive** `SumLimbs` (no loop) verifies (24 verified): the prompt asks for a loop and no
form rule can check it (§8). X1v by `u128` arithmetic (`v / 2`, then `% 2^64` and `/ 2^64`)
verifies: a different idiom, not a shortcut of the statement (S1 is exec checking).

## 5. Admission: the four results, item by item (QPLAN §19.0, Δ173)

(1) reference complete and in band (§3); (2) empty-body gate fails (§4); (3) twin stable,
seeds 1–3 and for Dafny both bundled solvers (§3); (4) only pinned APIs (the layers L1–L5 at
this worktree, `Std.Wrappers`, `Std.Arithmetic.DivMod.LemmaModMod`,
`vstd::arithmetic::div_mod::lemma_mod_mod`, `Vec::set`, `Seq::new`).

| item | (1) | (2) | (3) | (4) | registry |
|---|---|---|---|---|---|
| H1d | ✓ | **✗** (its `cfree:` verifies) | ✓ | ✓ | `admitted = false, minutes = 0` |
| H1v | ✓ | ✓ | ✓ | ✓ | true, 14 |
| H2d | ✓ | ✓ by its client (by hand, above) | ✓ | ✓ | true, 7 |
| H2v | ✓ | ✓ by its client (by hand, above) | ✓ | ✓ | true, 8 |
| H3d | ✓ | ✓ | ✓ | ✓ | true, 8 |
| H3v | ✓ | ✓ | ✓ | ✓ | true, 8 |
| H4d | ✓ | ✓ (+ region, cfree) | ✓ | ✓ | true, 12 |
| H4v | ✓ | ✓ (+ region) | ✓ | ✓ | true, 12 |
| H5d | ✓ | ✓ (maxauto out of resources: failing, Q66) | ✓ | ✓ | true, 10 |
| H5v | ✓ | ✓ | ✓ | ✓ | true, 10 |
| H6v | ✓ | ✓ (TRIV) | ✓ | ✓ | true, 10 |
| H7v | ✓ | ✓ (TRIV) | ✓ | ✓ | true, 10 |

**H1d's shortfall.** Its fallback F-H1d (`ToU64` restricted to `|s| <= 2`) has the same
shortcut (a compiled `ToNat` call), so it has no four results either and carries 0. The
`u64` round-trip line (24 minutes) is therefore 14 admitted (H1v) and 10 short; the
module's admitted hole minutes are D 37 / V 72 (the itemized lines of QPLAN §20.4 sum to
D 47 / V 72; §20.3's "D 49 / V 70" predates the review's rebalance of the round-trip
pair to H1d 10 / H1v 14, author notes §13.1 M8). The records lane
writes the shortfall note (Δ173). Two ways to close it, neither in this lane's files: a
Dafny form rule that refuses a named call in the item's code (QPLAN §30 Q62 considered a
`no-call:` form; `firsttry`/`dvl.forms` has no Dafny rule but `trigger` and `stable`), or a
re-posed statement whose specification no compiled function computes. The method clause is
stated in the prompt in words, as Q07 did for its forms before they existed.

Fallbacks: no fallback was built or measured (every other item has its own four results),
so each fallback stays a name with 0 minutes.

## 6. Deviations from the plan

- **The statement holes' labelled assume comes first** in `ShiftTwice` and `high_client`
  (QPLAN §20.2 says the client "ends in" it): at the end, `ShiftTwice`'s second call fails
  its precondition before the assume, so the shipped file would not be green. Q08 did the
  same (QPLAN §18.3).
- **H2d's `Shift` body ships without lemma calls** (A.7 had `ToNatCons`, `ValidCons`): it
  verifies against the reference without them.
- **H3d's reference and quoted attempt carry one product assertion** (§3), for stability;
  the repair asked for is still the sequence identity alone.
- **H1d's reference adds one bound assertion** and swaps two lines, for stability (§3).
- **X1d's given `Sum` is a `ghost function`** (the author notes: `function`): with a compiled
  `Sum`, `t := Sum(s)` is a one-line answer.
- **`Ring::new` (W1v) states `r.len == 0` and `r.buf@.len() == cap`** beside `inv` and the
  empty view, so the ring check can call `push_back`.
- **Checks added** under `Uncomment as you go:` (live in the twins): `ToU64Check`
  (`ToU64([5]) == Some(5)`), `NormLenCheck` (`NormLen([3, 0]) == 1`), `norm_len_check` and
  `ring_check` (one `push_back`, then `get(0)`; `push_back`'s statement says nothing about
  `buf@.len()`, so a second push would not verify). The Verus checks name the view
  elements (`v@[0]`, `q@.len()`) so that the solver has the terms to instantiate.
- **The quoted attempts sit in the docstrings** (`firsttry --lint-hollow` refuses commented
  `assert` lines outside an `Uncomment as you go:` block), as Q09's are.
- **No EXPLAIN-BACK block** in the exit files: QPLAN §19.0's timed exit names none for the
  practice tier (it is the detailed tier's, §14.0).
- **`lib.rs` imports no `vstd::arithmetic` module**: the search item's lemma is named by its
  full path in the reference; the prompt says only "in `vstd::arithmetic`".
- **P2dv kept** as QPLAN states it (§2).

## 7. Leak and re-pose checks

- The leak-pattern README's verifier: `9 module(s), 1241 public files scanned, OK` (Q10 has
  no pattern file yet: the kits lane writes `tests/instructor/leak_patterns/Q10.txt`).
- Lane scan (`/tmp/dvl0-dv5a-q10/leak/scan.py`): the 98 answer lines of the four twins (twin
  lines a line diff leaves unmatched against the learner file, comments stripped, at least 12
  code characters) and the two reference slot values, searched in the four learner files,
  `slots/Q10.slots`, `expected/Q10.*`, QPLAN, PLAN, `MODULES.toml`, DELTAS, README,
  CLAUDE.md and the layers L1–L5. 23 hits, all reviewed: the commented checks and the two
  quoted attempts (shipped by design), statements, generic `let` lines, layer lemma calls
  that also occur in L4/L5's own proofs (`lemma_weight_zero();`), and one idiom line of X1d's
  answer, `assert s[i..][1..] == s[i + 1..];`, which L4's `MulLimbLoop` already holds. That
  line is a step, not the exit's answer (the loop, its invariant and the final identity are
  the learner's); the given spine may stay open during the exit (§19.0), and QPLAN §19.6
  rule 3 forbids a layer only the whole answer. No slot value occurs anywhere public.
- Re-pose (author notes §2.3, re-checked on the built statements): H1v vs Q03.H4v, H4d/H4v vs
  Q02.H2d/H2v, H3v vs L4's append lemma, H5v vs Q07.H5v: unchanged statements, same
  conclusions. No Q10 file holds Q01's targets (F22); `NormalizeTrim(s, 0)` with
  `NormalizeToNat` still gives `AllZeroToNat` in two calls, as recorded.
- No regex artifact (F23). `avoid.sh` was not run by this lane (its armed-module run is the
  avoid lane's).

## 8. Tool problems found (for the tools owner)

1. **Dafny and free-function Verus statement holes are not skipped** by
   `firsttry --empty-body` (`eb_skip_reason` recognises only a Verus block that opens with a
   bodyless trait method). Q10.H2d is gated on its `Shift` body (a spurious ✓ through
   definite assignment) and Q10.H2v on `high_limb`'s twin clauses (a spurious ✗). Proposed:
   skip, with QPLAN §14.0's reason, any H block whose only hole forms are the labelled
   assume of a given client (Dafny `assume false;` in a method after the block's first
   declaration; Verus `proof_note("<id>")`), in either language and whatever the first
   declaration's shape; and run the client with the assume deleted as the statement gate
   (it must fail), which is what §5 did by hand. Δ168's open item foresaw the Dafny half.
2. **No Dafny form rule can refuse a named call** (H1d's `ToNat`), and **no rule can ask for
   a loop** (X1d's recursive answer). Both are prose-only at the pin.

## 9. Learner-flow simulation (`/tmp/dvl0-dv5a-q10/sim`)

A git copy of the worktree's tracked and untracked non-ignored files without `Solutions/`,
`paper/solutions/` and the leak patterns, branch `work` off a `main` holding the shipped
state, toolchain linked. Slots filled with the reference answers, then
`firsttry.sh Q10 --check`: 2/2 first tries pass, recorded; switches enabled; the two
exercise twins laid over the learner files: `vcheck --gate` 139 (Dafny) and 14 (Verus)
verified, 0 holes; `vaudit` 0 findings each; `specfreeze --check Q10` 0 findings;
`firsttry.sh Q10 --report --strict` OK; `pins.py Q10` 2 pass. Exit twins laid over the exit
files: `firsttry.sh Q10 --exit`: 2/2 (threshold 1) PASS; the strict report stays OK.
