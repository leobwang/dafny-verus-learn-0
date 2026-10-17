# Q12 code notes (DV5a module lane: Practice I-C + Lab 1)

> **Author-only.** This file holds Q12's references, captured verdicts, the battery's and the
> stratum's answers, the flawed fixture's planted flaws and the lane's gate records. Never quote,
> paraphrase or link it from a learner-visible file. The learner-visible plan is QPLAN §22.

Written 2026-10-07 by the Q12 module lane, in the authoring worktree (branch `authoring`, HEAD
941dbe1, nothing committed). Every solver job ran one at a time through the course wrappers
(`scripts/vcheck`, `scripts/firsttry.sh`, `fvh.tools.HostRunner`), each under the wrappers' own
caps (Dafny 8 GB, Verus 16 GB, systemd-run MemoryMax), with `DVL_SCRATCH=/tmp/dvl0-dv5a-q12/scratch`;
`free -g` showed 95–102 GB available before every batch (the lane's share is 16 GB, so 31 GB was
needed). No job was killed. No model was called and no container was started.

## 1. Files

| file | state |
|---|---|
| `dafny/Q/Q12_PracticeIC/std/Q12_PracticeIC.dfy` | module `Q12_PracticeIC`, imports L1–L4, `// specfreeze: frozen-imports`; 1 hole (H3d) |
| `dafny/Q/Q12_PracticeIC/std/Q12_Lab1Hand.dfy` | module `Q12_Lab1Hand`, imports L1–L4, frozen imports; 4 holes (H4d–H7d); a HAND block |
| `dafny/Q/Q12_PracticeIC/exit/Q12_Exit.dfy` | module `Q12_Exit`, imports L1–L4; 1 hole (X1d) |
| `verus/q/q12_practice_ic/src/lib.rs` | `use qg_bignat_l5::*`, `mod lab1_hand;`; 1 hole (H3v) |
| `verus/q/q12_practice_ic/src/lab1_hand.rs` | 4 holes (H4v–H7v) |
| `verus/q/q12_practice_ic/src/exit.rs` | 1 hole (X1v) |
| `specimens/Q12/P1d … P6v` | six stage specimens, `// SLOT: CHECK` switches |
| `slots/Q12.slots`, `expected/Q12.pins` | 6 verdict slots; 6 salted pins |
| `harness/q/fvh_q/retry.py` | H1py, H2py (practice S9) |
| `harness/q/fvh_q/policies.py` | H8py–H11py (Lab 1's arms and renderer; pending `fvh.protocol`) |
| `harness/q/fvh_q/report.py` | H12py, H13py (Lab 1's tables) |
| `harness/tests/q/test_retry.py`, `test_policies.py`, `test_report.py` | frozen acceptance tests (36, 26, 15 tests) |
| `harness/tests/q/fixtures/q12/battery.toml`, `battery/`, `rec/` | the battery: 12 goals × 3 candidates, 36 recorded `vcheck --gate` results |
| `expected/Q12.battery` | k = 3, solved 8 of 12, the recordings' digest |
| `tools/Q12/holecount.py` | the toolwright's file: CONTRACT docstring, header, empty INTERFACE and AUDIT blocks |
| `bench/local/q/lab1/<card>/tasks/<card>.{dfy,rs}`, `STRATUM.toml` | 22 local task forms (12 Dafny, 10 Verus) and the stratum manifest |
| `paper/Q12_problems.tex`, `paper/Q12_answers.tex` | B1 (pre-registration, the PREREG template) and B2 (lab report) only; the cards are the kits phase's (B3–B5) |
| `paper/fixtures/Q12_flawed_prereg.tex` | the grade-the-grader fixture (§7) |
| `research/q12_grade_the_grader.md` | the S12 record form |
| `expected/Q12.counts`, `expected/Q12.freeze` | count pins (Dafny unit 136, Verus crate 5; 9 file states), freeze (48 statements, 15 files, 2 frozen import lists) |
| `Solutions/…` twins | every exercise, exit and harness file; five specimen twins (P5d has none, §3); `Solutions/slots/Q12.slots`; `Solutions/bench/local/q/lab1/<card>/` (22 answers); `Solutions/plans/Q12-record-battery.py` (the battery recorder) |

## 2. The verifier items

References are A.11/A.12 of the Q10–Q18 author notes, except H6d (below). Line counts under QPLAN
§19.0 (Δ173): H3d 3, H3v 1, H4d 2, H5d 3, H6d 3, H7d 2, H4v 4, H5v 4 (exec 4), H6v 0 (exec 3),
H7v 2 (exec 1); exits X1d 3, X1v 1. Every item is inside the intro band (D ≤ 10, V ≤ 15), with no
invented lemma.

**Empty-body gate** (`scripts/firsttry.sh Q12 --empty-body`, default modes and seeds; first run
12/12, re-run in §9): every hole's empty body fails. H4d, H7d and X1d are `lever-needed`: their
empty bodies fail under the shipped options (manual lemma induction; L4's opaque `AddC`) and
verify under maximal automation; the lever is the unit's `manual-lemma-induction = true` (and,
for X1d, `AddC`'s opacity), as Q09's T1d. The exec items run TRIV with their declared bodies
(`{ false }`, `{ false }`, `{ 0 }`). The `cfree:` answers all fail:

- H3d: `{ NormalizeTrim([5, 0, 0, 0], 1); }` and the qualified `QG_L5_BigNat.NormalizeTrim(…)`
  fail at resolve (the module imports L1–L4 only). Probed on the learner file: the same body
  with an added `import opened QG_L5_BigNat` verifies (the unit includes L5), and
  `scripts/specfreeze --check Q12` reports `freeze-imports-changed — module Q12_PracticeIC`: the
  frozen import list (QPLAN §30 Q62) is what closes the shortcut. A fuel attribute
  (`{:fuel Normalize, 4}`) with an empty body verifies: that is the item's construct (`uses:
  fuel`), an accepted answer.
- H3v: `{ assert(limb_at(b, k) <= limb_at(c, k)); }` (the second hop alone) fails.
- H5v: `{ a.limbs.len() == 0 }` (the code without its proof) fails; H7v: `{ a.limbs.len() }`
  fails.

**Stability:** `vcheck --ref --brittleness --solvers` on the Dafny unit twin and the Dafny exit
twin: verified in all six rows (4.12.1 and 4.14.1 × seeds 1–3), stable; `vcheck --ref
--brittleness` on the Verus crate twin and exit twin: seeds 1–3 verified, stable. **APIs:** L1–L4
(and L5 only through the Verus prelude glob), no vstd lemma beyond the layers.

**H6d replaced** (a deviation from QPLAN §22.2). The plan's `lemma CmpSelf(a) ensures Cmp(a, a) ==
0` is answered in a learner-visible file: Q09's forensic specimen `specimens/Q09/P9d.dfy.specimen`
(DV3b) proves `Cmp(a, a) <= 0` by `if |a| > 0 { CmpSelf(Tail(a)); }`, which proves `== 0` as
it stands, and its companion `P9d-frozen` states the `== 0` form. H6d is now `lemma
CmpTrailingZero(a: seq<nat>) ensures Cmp(a, a + [0]) == 0` (decreases |a|): reference `if |a| >
0 { assert Tail(a + [0]) == Tail(a) + [0]; CmpTrailingZero(Tail(a)); }`. Probed: the reference
verifies; the empty body, the body without the assertion and `{:induction a}` with an empty body
all fail, so it fails under maximal automation too (a local-stratum task in both cases). Searched
first: `CmpAntisymmetric` is in Q09's agent bank and `CmpAntisym` is Q14.X1d's planned exit, so
neither was taken; no learner-visible file or author note holds `Cmp(a, a + [0])`.

**Related, kept:** (renamed 2026-10-07 to `MulLimbZeroLimbs`, orchestrator decision) Q09's agent bank holds a lemma named `MulLimbByZero` with another statement
(`requires Valid(s) ensures ToNat(MulLimb(s, 0)) == 0`; true), whose proof the learner's Q09
contractor writes. H5d keeps the plan's name and its structural statement (length and every
limb); the two share a name and a recursion. Open issue 4.

**Imports** (a deviation from QPLAN §22.1's "imports L1–L5"): both Dafny modules import L1–L4
and carry the frozen-imports marker, per the spine lane's finding; the hand file needs no L5
lemma, and L5's `NormalizeTrim` would otherwise reach H3d.

## 3. The stage specimens

Captured on the pins (copies in `instructor/scratch/`, now deleted; Verus with Q12's chain via
`--module Q12`, as a specimen of Q12 gets it):

| item | file | command | captured | answer |
|---|---|---|---|---|
| P1d | an `if` block never closed | `vcheck --json` | `stage` "parse", verdict failed, `verified_count` null, `rbrace expected` | `parse` |
| P2v | a correct proof fn | `vcheck --json … -- --no-verify` | `stage` "cli", verdict refused, `exit_code` null, vcheck exit 3 | `cli` |
| P3d | `import opened QG_L1_BigNat` in a standalone specimen | `vcheck` | `failed — … 1 error, stage resolve` (`module QG_L1_BigNat does not exist`) | `resolve` |
| P4v | an exec fn whose `ensures r > 0` fails for zero | `vcheck` | `failed — 0 verified, 0 holes, 1 error` (no stage on the line), `postcondition not satisfied` | `verify` |
| P5d | a bodyless compiled method called by a `{:test}` method | `vcheck --test` | `failed — 0 passed, 0 failed, stage compile` (`has no body so it cannot be compiled`); the plain run verifies with 1 hole | `compile` |
| P6v | a `requires` clause missing a comma | `vcheck` | `failed — 0 verified, 0 holes, 1 error, stage parse` (`expected curly braces`) | `parse` |

The six stay inside Q's stages (cli, parse, resolve, verify, compile) and cover all five. Changes
from the author notes §4.1's planned set: P2v's planned scenario (an undefined spec function) gives
`resolve`, which Q02.P7dv, Q03.P6dv and Q08's predictions settle for Verus; P6v's planned scenario
(a path that is no crate) is refused before any document or stage is printed (`vcheck: refused:
… not a Dafny or Verus target`), so it has no answer in either channel. P2v became the
pass-through refusal (the JSON channel names `cli`; the text line says only `refused (no tool
ran)`, so `cli` is a JSON item), and P6v the Verus parse error.

**The H5 guard.** `scripts/vcheck`'s H5 guard (`h5_guard`) refuses a specimen whose items carry
slots in the file itself; a verdict item's slot lives in `slots/<ID>.slots`, so a verdict
specimen was NOT refused before its first try (observed: `vcheck specimens/Q12/P3d.dfy.specimen`
printed `stage resolve` with no first try recorded). Each Q12 specimen therefore carries `// after:
Q12.P<n><l>` (its own id), which the guard does honour: probed, the run is refused (exit 3,
"waits for Q12.P3d, whose first try is not recorded") until `firsttry --check` records it.
Q09's forensic deliveries (P6d–P15v) have the same gap (open issue 8). In a study-like copy of the
tree (tracked and new files, no reference trees; `/tmp/dvl0-dv5a-q12/sim`): slots filled,
`firsttry.sh Q12 --check` recorded 6/6 passing first tries, the switches enabled, and each
specimen's own command printed the pinned stage (parse, cli, resolve, no stage, compile, parse);
P2v without the flag verifies. P5d has no specimen twin: its
twin would hold the scenario's bodyless method, which `reference_lint` reports as a hole in a
reference file (specimen twins are optional, `reference_lint` doc).

## 4. The retry battery (S9)

`harness/tests/q/fixtures/q12/battery.toml`: goals D1–D6 (Dafny) and V1–V6 (Verus), three
standalone candidates each, over battery-local copies of the definitions (`ToNat`, `AddLimb`,
`Head`/`Tail`, a local `CountZeros`; Verus `seq_to_nat`, a local `count_zeros`). No goal states an
item of Q01–Q18 (checked against the three author-notes files and the built Q10/Q11 files; the
first draft's V4, the one-limb value `seq_to_nat(seq![d]) == d`, was replaced because its
candidates held Q11.H6v's idiom).

Recorded by `Solutions/plans/Q12-record-battery.py` (fvh.tools.HostRunner + write_recording; the
frozen core is unchanged; QPLAN §30 Q53 had proposed extending `fvh.tools.record`). 36 results,
every exit 0 or 1. Outcome at k = 3: solved D1 (try 1), D2 (2), D3 (3), D5 (1), D6 (2), V1 (1),
V2 (2), V3 (3) = **8 of 12**; unsolved D4 (first failure `verdict:failed`), V4 (`holes:1`), V5
(`verdict:failed`), V6 (`stage:resolve`). At k = 1: 3. The designed D6 was meant to be unsolved,
but its second candidate verifies (Dafny proves the sequence identity itself), and V5's
"correct" candidate fails (two unfoldings of `count_zeros`): the battery keeps the recorded
outcomes. D1's c2 (an empty body) also verifies; the client never reaches it. Digest pinned in
`expected/Q12.battery`.

References: H1py, H2py (twin): 35 tests pass, 1 skipped (the pin-parity test, outside the
overlay); TRIV 2/2 fail. The learner file: 2 passed, 34 failed, 2 holes.

## 5. Lab 1's local stratum

Task forms are standalone files (copies of the definitions, as the public sets' tasks are), each
a statement with an empty (proof) or trivial (exec: `{ false }`, `{ 0 }`) body; the Dafny forms
ship `{:induction false}`. Validation (`/tmp/dvl0-dv5a-q12/stratum/validate.py`, one job at a
time): every answer `vcheck --gate` verified, 0 holes; every task form fails the gate;
`maxauto_fails` = the task form with `{:induction false}` dropped still fails: dh5, dh6, da3 only.
`vcheck --gate --lab-task <form> <delivery>` probed on dh4: the answer passes; the empty body with
the lever dropped verifies but is refused (`lab-lever-removed`).

Answers (`Solutions/bench/local/q/lab1/`): the hand items' references, plus da1 `AddLimbAllMax`
(`if |s| > 0 { AddLimbAllMax(s[1..]); }`), da2 `CmpZerosEmpty` (recursion on `Tail`), da3
`MulLimbOne` (recursion, `s[0] * 1 + 0 == s[0]`, `[s[0]] + s[1..] == s`), da4 `NormalizeValid`,
da5 `CmpEmptyLeft`, da6 `FromNatLast` (recursion on `n / BASE`), da7 `NormalizeLast`, da8
`NormalizeEmptyZeros`; va1 `lemma_shorter_smaller` (upper, lower, `weight` monotone), va2 `is_one`,
va3 `at_least_weight`, va4 `lemma_push_ge` (`=~=` on `push`, recursion, one `nonlinear_arith`
step), va5 `limb_or_zero`, va6 `lemma_prefix_le`. Replaced during the build: `ToNatSnoc` (it is
Q10.H3d's statement, rearranged), `lemma_two_low_limbs` (Q11.H6v's unfolding), a
`seq_to_nat(s) % BASE` lemma and a `seq_wf(s.drop_first())` lemma (both verify with an empty body).

Composition: with the lever check (the built `--lab-task`), dh4–dh7 + da1–da6 and vh4–vh7 +
va1–va6. Without it, only 3 Dafny tasks qualify: six more maxauto-failing Dafny tasks would be
needed (open issue 6).

## 6. Lab 1's Python pieces

**policies.py** (H8py–H11py, not admitted): written on `fvh.protocol` as DV4-PLAN §3.2 gives it.
What the file and its tests assume, for DV4 to meet or for this file to follow: `protocol.Edit(path,
old, new)`, `protocol.Verify(mode)`, `protocol.Stop(reason, note)` constructible by keyword and
comparable by value; `State.step` (0 at the first proposal) and `State.last_verify` (the last gate
document or None); `Context.target`, `lang`, `statement` and `material` with the keys
`instructions` and `text` (the task form's full text of the target); `Budget.exhausted`. The arm
receives an `ask(prompt, seed) -> str` callable (the transport, the pinned settings and the reply
check reduced to one candidate file's text: DV4's `ModelPolicy` side) and submits each candidate
as one whole-file `Edit` over the text it last wrote, then `Verify("gate")`. A3 keeps every
candidate in its frontier (a state may be expanded again), ranked by `failing(doc)` (error
diagnostics plus holes; a document that stopped before verification counts 10**6), ties to the
earlier. Until `fvh.protocol` exists the tests put a stand-in for the three actions in its place
and skip `test_core_protocol_has_the_actions`; on the stand-in the twin passes 25 tests, 1 skipped,
and TRIV 4/4 fail.

Signatures beyond QPLAN §22.2: `render` takes a keyword `focus` (the candidate a repair or
expansion is about, with its document), and the arms are built with `ask` and a `seed` (A1) or a
`seeds` list (A2, A3), the pre-registered request seeds.

**report.py** (H12py, H13py, admitted): takes `LabRun(record: RunRecord, repeat, outcome)` rows,
which the report driver must build from `fvh.runlog.split` (open issue 3). `compare` adds a
required `seed` keyword to QPLAN's signature (the bootstrap and the permutation test need one).
Twin: 15 tests pass; TRIV 2/2 fail.

## 7. The pre-registration template, the fixture and the S12 form

`paper/Q12_answers.tex` B1 holds QPLAN §22.6's fifteen template fields between the PREREG markers;
B2 the report's fields. Both pair files compile (`latexmk`, scratch outdir).

**The fixture's planted flaws** (`paper/fixtures/Q12_flawed_prereg.tex`; author notes §4.1's five):
(1) the budget arithmetic omits the repeats: "40 × 6 × 2 = 480 calls, run as 3 repeats" (1,440),
and the seed lists and the GPU figure follow the same undercount; (2) no MDE field; (3) the
stopping rule skips an arm's remaining repeats once it leads by 20 points; (4) the Claude arm's
repeated runs are called "three seeds"; (5) no rule for truncated attempts (exclusions name
`infra-failed` only). Also arguable, not planted as a flaw: "No pilot".

## 8. Registry and minutes

`[module.admissible]` (Q12's record only): admitted H1py 10, H2py 10, H3d 7, H3v 8, H4d–H7d 12
each, H4v–H7v 12 each, H12py 15, H13py 20; not admitted, 0 minutes, fallbacks unchanged:
H8py–H11py (pending `fvh.protocol`). Line by line (QPLAN §22.7): S9 retry client 20 of 20; S11
15 of 15; hand items 96 of 96; policies + report 35 of 110 (H8py 15, H9py 20, H10py 30, H11py 10
at 0: **75 minutes short**, pending DV4 step 1a; no fallback has its four results, so each
carries 0, Δ173). No other field changed (`budget` is Δ176's).

## 9. Checks run

`scripts/firsttry.sh Q12 --lint-hollow` OK (15 files); `--report` (6 unfilled slots, 18 open
holes, 0 problems); `--empty-body` 12/12 at the first run and 20/20 at the re-run with the Python files (the
eight Python TRIV bodies fail their tests); `python3 scripts/dvl/python.py ref|triv` on the three twins; `scripts/pins.py
--ci --module Q12` (23 pins, 0 problems) and `--ref --module Q12` (6 checks, 0 problems);
`scripts/vcheck --ref --pin-counts Q12`; `scripts/specfreeze --pin Q12` and `--check Q12` (0
findings); `python3 scripts/reference_lint.py --module Q12` (0 findings); `python3
scripts/check_course_map.py` (course map OK); the leak verifier (9 modules, OK).

## 10. Open issues

1. Records: a DELTAS entry for Q12 as built (H6d replaced; Dafny modules import L1–L4 with
   frozen imports; the specimens' P2v and P6v scenarios; the battery recorded without changing
   `fvh.tools.record`; H1py, H2py, H12py and H13py admitted although QPLAN §22.8 kept them
   pending; `compare`'s `seed`; `report.py`'s LabRun rows; the 75-minute shortfall).
2. DV4: `fvh.protocol` as §6 assumes, or a change to `policies.py` and its tests.
3. DV4: the report driver's rows (LabRun from `runlog.split`).
4. Orchestrator: H5d's name `MulLimbByZero` is also a Q09 agent-bank lemma (another statement).
5. Skills owner: `/grade-paper`'s fixture mode (QPLAN §30 Q54) for the S12 block.
6. Before Lab 1's runs: fvh's lab gate must call the lever check, or six more Dafny local tasks
   that fail under maximal automation are needed.
7. DV5 integration: the public strata's validation and the HumanEval-Verus stripping (Q57).
8. Tools owner: `vcheck`'s H5 guard does not see a verdict item's slot (it lives in
   `slots/<ID>.slots`), so a verdict specimen without an `after:` line runs before its first try;
   Q09's ten forensic deliveries are open to it.
9. Integration/tools (not this lane's files): `tests/wrappers/test_tools_static.py`'s
   `test_cli_usage_and_refusals` expects `vcheck Q10` to be refused as planned, and
   `scripts/test_course_map.py` has 5 failures on Q10/Q11 stand-ins (the spine lane's list).

## 11. H8py–H11py admitted on the real protocol (DV4 step 1a remainder, 2026-10-11)

`fvh.protocol` is built (DV4 step 1a remainder) with exactly §6's assumptions: `Edit(path, old,
new)`, `Verify(mode)`, `Stop(reason, note="")` keyword-built frozen dataclasses compared by value;
`State.step` (0 first) and `State.last_verify`; `Context.target`, `lang`, `statement`, `material`;
`Budget.exhausted` (a property: any capped unit at or below 0). No line of `policies.py` or its
twin's arms changed; the twin's module docstring lost its PENDING paragraph. `ask` is
`fvh.backends.candidate_ask(transport, target=…, meter=…)`: one model call; the reply must validate
against `ACTION_SCHEMA` and hold exactly one whole-file `Edit` of the target (`old` empty), whose
`new` is the candidate (anything else is `malformed`). Lab 1's `material["instructions"]` must
ask for that reply form (DV5's material).

The four results, on the built files (Python items, QPLAN §19.0's Python row):
1. **Reference complete:** `scripts/vcheck --ref Solutions/harness/q/fvh_q/policies.py`: verified,
   26 passed, 0 failed, 0 holes (the protocol test runs now; nothing skipped).
2. **Empty-body gate:** `python3 scripts/dvl/python.py triv …/policies.py`: 4/4 (each `# triv:`
   body fails the frozen tests). The CI harness job's author run repeats both (log archived).
3. **Stable:** three consecutive reference runs, 26 passed each (no randomness: `render` is pure,
   the seeds are the arm's). Also driven end to end through the real `fvh.executor`, a scripted
   transport behind `candidate_ask`, an isolated fake gate runner and a call cap B = 4, then each
   recorded run re-derived by `fvh.report.rederive`: A1 solve/fail 1 call each; A2 solved at its
   third call (3 calls, seeds 0–2), A2 unsolved 4 calls then `Stop(give-up)`; A3 solved at its
   fourth, A3 unsolved 4 calls; every run ended `stop` and reproduced from its logs.
4. **Pinned APIs:** the standard library and `fvh.protocol` only (`check_course_map.py`'s import
   tiers: `py-fvh`, within its allowlist).

Registry: H8py 15, H9py 20, H10py 30, H11py 10 admitted (QPLAN §22.7's split); the policies +
report line is whole again (110 of 110). Probe archive:
`~/.cache/dafny-verus-learn-0/author-probes/dv5b/dv4a/` (`q12_arms_on_executor.{py,out}`, the CI
harness logs). Still stale, not this lane's files: the learner file's PENDING paragraph and the
frozen test file's docstring (they say the protocol is not built), and the chapter's "pending
DV4's protocol" lines (§0 "What is pending", the files table, the Done line).
