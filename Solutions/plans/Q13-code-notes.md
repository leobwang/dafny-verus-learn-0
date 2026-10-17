# Q13 code notes (DV5b Q13 lane, as built)

> **Author-only.** The prediction answer, gate results, the four admission results per item,
> the probes behind them, the prose item's checks and the deviations of Q13's code from the
> plan. Never quote, paraphrase or link any of it from a learner-visible file. The plan is
> `QPLAN.md` §19 and §23 and `Solutions/plans/Q10-Q18-author-notes.md` §5, §13.2 and
> Appendices A.13, A.14, A.15 (X1v), C.4, C.5; this file records what was built (dd24798 and
> this lane, 2026-10-11) and where it differs.

Every result below was captured on the pins (Dafny 4.11.0, Verus 0.2026.09.27.3cf1832)
through the course wrappers (`scripts/vcheck`, `scripts/vaudit`, `scripts/specfreeze`,
`scripts/pins.py`, `scripts/firsttry.py`), one solver job at a time, under the wrappers' caps
(Dafny 8 GB, Verus 16 GB) and inside `systemd-run --user --scope -p MemoryMax=16G
-p MemorySwapMax=0` (the lane's share). `free -g` showed 92–103 GB available before every
batch (31 GB needed); no job was killed. `DVL_SCRATCH=/tmp/dvl0-dv5b-q13/scratch`. Probes and
gate logs are archived under `~/.cache/dafny-verus-learn-0/author-probes/dv5b/q13/`
(`empty-body-{1,2,3}.txt`, `h3v-gate-3.txt`, `ref.txt`, `brit-d.txt`, `brit-v.txt`, `l6.txt`,
`learner.txt`, `h3v/`, `h5d/`, `probe/`, `bank/`, `rubric/`); B2's card probes of dd24798
are in `dv5b/q13-kit/`.

## 1. Files

| file | shipped state | twin |
|---|---|---|
| `dafny/given/Q/QG_L6_BigNat.dfy` (`module {:disableNonlinearArithmetic} QG_L6_BigNat`) | given, frozen: `FromNatCanonical`, `NormalizeAddCorrect`, ghost `Sub` by value | — (gate 130 verified) |
| `verus/given/qg_bignat_l6` | given, frozen: exec `normalize` | — (gate 2 verified) |
| `dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy` (`Q13_PracticeIIA` with L1–L6; then, last, `{:disableNonlinearArithmetic} Q13_Library` with L1, L2, L4, L5, `Std.Arithmetic.Mul`) | verified, 3 holes (H2d, H4d bodyless lemmas; H5d an exec `assume false;`), 132 verified | 137 verified |
| `verus/q/q13_practice_iia/src/lib.rs` | verified, 3 holes (H1v `external_body`; H3v the client's labelled assume; H4v a `proof_note` assume) | 9 verified |
| `dafny/Q/Q13_PracticeIIA/exit/Q13_Exit.dfy` | an empty module, no hole (exits come in pairs) | 130 verified |
| `verus/q/q13_practice_iia/src/exit.rs` | verified, 1 hole (X1v) | 1 verified |
| `slots/Q13.slots`, `Solutions/slots/Q13.slots` | `P1dv = ???` / the answer below | — |
| `expected/Q13.pins` (1 salted), `expected/Q13.counts` (Dafny unit 137 / floor 3, crate 9 / floor 2; files 3, 3, 0, 1 holes), `expected/Q13.freeze` (11 statements in 3 files; the Dafny exit unfrozen), `expected/Q13.chapter.toml` (3 pins) | author-written | — |

No specimens, no check unit, no agent file, no card section (§19.0).

## 2. The prediction (captured on the real scenario)

| item | answer | capture |
|---|---|---|
| P1dv | `D:none V:none` | the docstring's scenario as two probe files, run with `scripts/vcheck --module Q13`, pinned as chapter fences `p1dv-d` (Dafny: `failed — 25 verified, 0 holes, 2 errors`, both clients' assertions) and `p1dv-v` (Verus: `failed — 2 verified, 0 holes, 2 errors`, both clients' assertions). The chapter quotes both after P1's box. |

`pins.py --ref --module Q13`: 1 check, 0 problems; `pins.py --ci --module Q13`: 11 pins, 0
problems (after the `units` fence was re-captured, §7).

## 3. References, counts and stability

Counts are QPLAN §19.0's rule, with the plan's counter (author notes C.8); the intermediate
band is D 10–30 / V 15–45, at most one invented lemma.

| item | reference | proof lines | band | invented |
|---|---|---|---|---|
| H1v `sub` + `lemma_sub_lift` | C.5 (A.14's lift unchanged) | 18 + lift 13 + its statement 13 = **44** | 15–45 | `lemma_sub_lift` |
| H2d `NormalizeConcat` + `NormalizeIdem` | A.13 | 7 + 2 + statement 3 = **12** | 10–30 | `NormalizeIdem` |
| H3v `lemma_lt_at_any` + `lemma_eq_any`, `tail` | A.14 | 9 + 9 + 1 + statements 6 + 1 = **26** (34 with the prose statement the learner writes) | 15–45 | `lemma_eq_any` (`tail` is a one-line spec fn, a definition) |
| H4d `RepeatValue` | A.13 | **22** | 10–30 | none |
| H4v `lemma_repeat_value` | A.14 | **20** | 15–45 | none |
| H5d `ValueLoop` | C.4 | **13** (7 exec) | 10–30 | none |
| X1v `lemma_value_below_top` | A.15 | 9 | exit | none |

The twin of `sub` writes its two one-statement proof blocks on one line each, as C.5 measured
(46 lines with them on three lines each, one above the band).

**Stability** (`vcheck --ref --brittleness`, Dafny with `--solvers`):
- Dafny unit twin: all six rows (4.12.1 and 4.14.1 × seeds 1–3) verified, `stable`; one flag,
  `ValueLoop` (H5d), 44,402–76,240 (CV 27.3%, solver 4.14.1), every count at or below 1.6% of
  the 5,000,000 limit; nothing else above 20%.
- Crate twin: seeds 1–3 verified, `stable`; widest spread 13.2% (a declaration outside the
  crate's files). Exit twins: Verus seeds 1–3 `stable` (4.4%); Dafny six rows `stable` (13.9%,
  L1's `ToNatAppendZero`).
- L6: Dafny six rows `stable` (13.9%, the same L1 symbol); Verus seeds 1–3 `stable` (0.3%).

**H5d's flag stays** (QPLAN §23.4 asked the lane to restructure or record why). Measured in a
probe module of Q13's unit (`h5d/`), each under `--brittleness --solvers`: the reference as
built (27.3%, 44,380–76,265), the reference plus an assertion of the next state's invariant
after the four library calls (25.4%, 44,474–83,678), and the four calls moved inside `assert
… by` that next-state assertion (31.9%, 45,804–85,844). None clears the 20% flag; every row
verifies under both solvers and every seed, at under 1.8% of the limit. The flag is advisory
and never gating (`vcheck`'s own wording), so the reference stays as C.4 wrote it.

**APIs** (all at the pins; every twin verifies): layers L1–L6 (L3's `weight` lemmas,
`group_bignat_bounds`, `limb_at`, `lemma_seq_to_nat_upper`; L4's `MulNonneg` and
`lemma_seq_to_nat_append`; L5's `PowPositive`; L6's `normalize`); `Std.Arithmetic.Mul`'s
`LemmaMulBasics`, `LemmaMulIsDistributiveAdd`, `LemmaMulIsDistributiveAddOtherWay`,
`LemmaMulIsDistributiveSub`, `LemmaMulIsAssociative`, `LemmaMulIsCommutative`;
`vstd::arithmetic::mul`'s `lemma_mul_is_distributive_add_other_way`,
`lemma_mul_is_associative`, `lemma_mul_is_distributive_sub`, `lemma_mul_is_commutative`;
`Vec::new`, `Vec::push`, indexing, `Seq::new`, `Seq::push`, `drop_first`, `drop_last`.

## 4. The empty-body gate (`firsttry.py Q13 --empty-body`)

Three runs. Run 1 (before this lane's file edits, with the prose rule fixed): **7/7**. Run 2
(after the `form: no-nl` lines and `cfree:` lines): **7/7**. Run 3 (final files, after the use
site became symbolic, §5): **7/7**, exit 0 (`empty-body-3.txt`); the H3v gate was also re-run
alone before it (`h3v-gate-3.txt`). Per item:

| item | result |
|---|---|
| H2d | ✓ maxauto and seeds 1–3 fail |
| H4d | ✓ maxauto and seeds 1–3 fail (maxauto also strips the module's nonlinear attribute) |
| H5d | ✓ maxauto and seeds 1–3 fail |
| H1v | ✓ every mode fails (E0, E0H, E1, E2, EC, EM, INV, TRIV `{ BigNat { limbs: Vec::new() } }`) |
| H3v | shipped gate skipped (a prose item); ✓ client gate: the given client, its assume blanked and its use-site check uncommented, does not resolve without `lemma_lt_at_any`; ✓ prose proof gate: the twin's `lemma_lt_at_any` with an empty body fails in every light mode and seed |
| H4v | ✓ every mode fails; ✓ the twin meets `no-nl`; ✓ its `cfree:` answer fails its forms |
| X1v | ✓ every mode fails; ✓ the twin meets `no-nl`; ✓ its `cfree:` answer fails its forms |

The first run of dd24798 (before the prose rule existed) gave 6/7: H3v's shipped gate emptied
`prose_use_site`, which has no `ensures`, so it verified (archive `dv5b/q13-empty-body.txt`).

**Construct-free answers** (`// cfree:` in the twins; each fails, Δ173):
- H4v: the recursion with one `assert(…) by (nonlinear_arith) requires …` in place of the
  library calls. Run alone as a probe (`probe/h4v_nl.rs`): **verified** (2 verified). Hence H4v's
  block carries `// form: no-nl` (its prompt already said "no `nonlinear_arith`"), and the
  forms gate kills the answer.
- X1v: the reference's split with one `nonlinear_arith` step in place of distributivity and
  commutativity. Probe (`probe/x1v_nl.rs`): **verified**. X1v's block carries `// form: no-nl`
  (its prompt said so too).
- H4d and H5d (Dafny): no construct-free answer exists in the shipped module, whose attribute
  turns nonlinear arithmetic off. **With the attribute deleted** from `Q13_Library`'s `module`
  line, H4d falls to the recursion and two assertions (`probe/h4d_nlon.dfy`: verified, 132),
  and neither `specfreeze --check Q13` (0 findings) nor `firsttry --report --strict` (no
  finding beyond the unfilled slot) sees the deletion (both probed on a temporary copy of the
  learner file, restored after). The attribute is the items' lever, as Q12's hole + lever
  items name theirs; the rubric's C7 makes its removal a grade-1 finding with a `git diff`
  anchor, and the chapter (§5, §6) says no tool checks it. Tools item in §8.
- H1v, H2d, H3v: no shortcut known beyond the gates above (H1v's trivial body is the TRIV
  run; H3v's statement-level shortcuts are §5's hand checks).

## 5. The prose item (H3v): its gate, its use site, its hand checks

**The rule** (`scripts/firsttry.py`, this lane; tests `EmptyBodyProseItems`, 5 cases, in
`tests/wrappers/test_forms_static.py`): a block with `// prose: <name>` is skipped as a
statement hole; `client_gate` refuses it unless the block holds a commented use-site check that
calls `<name>`, blanks the client's labelled assume, uncomments the block's commented checks,
and passes only if the variant fails at those use-site lines (does not resolve) or inside the
block; `prose_proof_gate` then empties the twin's `<name>` (which must be declared in the twin's
block) and requires every light mode and seed to fail. dd24798's rule had only the
uncommenting and accepted any resolve error inside the block; it worked on H3v as shipped, but
said nothing about the proof.

**The use site is symbolic** (a deviation from author notes §5.3, which used the literals
`seq![5u64, 0u64, 0u64]` and `seq![1u64, 1u64]`). With the literal use site, a statement whose
`ensures` is only `seq_to_nat(a) <= seq_to_nat(b)` **verified** the use site
(`h3v/weak.rs`): the call puts the literal terms in context and the solver evaluates them, so the
strict assertion held without the lemma's conclusion (the assertion alone, without the call,
fails: `h3v/alone.rs`). The shipped client is now `prose_use_site(a: Seq<u64>, b: Seq<u64>)
requires a.len() == 3, b.len() == 2, a[1] < b[1], a[2] == 0`, calling the lemma at index 1 and
asserting the strict inequality. Hand checks on the final client, each statement under
`#[verifier::external_body]` so that only the client is judged (`h3v/s_*.rs`, `--module Q13`):

| statement | use site | witness `(empty, [1], 0)` |
|---|---|---|
| the reference (§5.3) | verified | verified |
| + `a.len() == b.len()` (L3's equal-length form) | precondition not satisfied | precondition not satisfied |
| `ensures` weakened to `<=` | assertion failed | — |
| `requires false` | precondition not satisfied | precondition not satisfied |
| + `a.len() == 0 \|\| a.last() != 0` (canonical first argument) | precondition not satisfied | — |

`specfreeze --pin Q13` re-pinned the one changed statement (`prose_use_site`); the counts are
unchanged (137 / 9). The hidden equivalence check stays pending on the grader container (QPLAN
§19.0, §30 Q49); the rubric (A7, C5, Probe E) says so.

## 6. Admission: the four results, item by item (QPLAN §19.0, Δ173)

(1) reference complete and in band (§3); (2) empty-body gate fails (§4); (3) twin stable,
seeds 1–3 and for Dafny both bundled solvers (§3); (4) only pinned APIs (§3).

| item | (1) | (2) | (3) | (4) | registry |
|---|---|---|---|---|---|
| H1v | ✓ 44 (43 under D1, §11) | ✓ (TRIV included) | ✓ | ✓ | true, 35 |
| H2d | ✓ 12 | ✓ | ✓ | ✓ | true, 30 |
| H3v | ✓ 26 (34) | ✓ client gate + prose proof gate; hand checks §5 | ✓ | ✓ | true, 25 |
| H4d | ✓ 22 | ✓ (lever: the module's nonlinear attribute, §4; frozen by `specfreeze --check` since the fix round, §10) | ✓ | ✓ | true, 15 |
| H4v | ✓ 20 | ✓ (+ `no-nl`, its `cfree:` killed) | ✓ | ✓ | true, 15 |
| H5d | ✓ 13 (12 under D1, §11) | ✓ since DV5c: its `form: loop-dir:up` kills the loop from the top limb (§11); before, ✗ (§10) | ✓ (flag recorded, §3, §11.1) | ✓ | **true, 20** (DV5c; false, 0 in the fix round) |

Every entry of `[module.admissible]` stayed as dd24798 wrote it (admitted, QPLAN §23.5's
minutes) until the review fix round (§10) set H5d to `admitted = false, minutes = 0`: hole
minutes now D 45 / V 75, 120 of the module's 200 (H5d's 20 short). No fallback was built or measured,
so each fallback stays a name with 0 minutes. X1v (the exit) passes the gate and is stable.

## 7. Other checks run (final files)

`vcheck Q13` (both units verified, 6 holes; the chapter's `units` fence re-captured with
`pins.py --update --chapter Q13 --entry units`, because the Verus hole lines moved: 90 → 96
and 116 → 121); `vaudit` one finding per hole (Dafny unit 3, crate 3, exit 1); `vcheck
--shipped Q13` (4 files, 0 problems); `vcheck --ref --gate` on the four twins (137, 130, 9, 1;
0 holes); `vcheck --ref --pin-counts Q13` (no change); `specfreeze --check Q13` 0 findings;
`reference_lint.py --module Q13` 0 findings; `firsttry Q13 --lint-hollow` OK (4 files);
`--report` (1 unfilled slot, 8 commented checks, 0 forms not met); `chapter_lint Q13` 0
problems (2,391 words, 3 pinned fences); `pins.py --ci` and `--ref`; `gen_units.py --check`;
`check_course_map.py` (OK; `--only vocab` OK); `avoid.sh` OK (0 hits); L6 `vcheck --gate`,
`vaudit` (0 findings each), brittleness (§3); the leak verifier, 13 modules OK; the static
suites `tests/wrappers/test_{dafny,forms,practice_tools,tools,verus}_static.py` (55, 45, 31,
107 with 1 skipped, 49: OK); the five Q13 paper files (problems, answers, solutions, both
fixtures) compiled with latexmk in a scratch copy.

A line-level answer check: every twin line of ≥ 16 characters that the learner file lacks was
searched in the chapter, bank, rubric, problems, answers, learner files, QPLAN and the chapter
pins: the only hits are the commented checks (shipped by design), the prose item's signature
(given in its prompt and in QPLAN) and `assert a + b == a;` (a generic one-line identity, in a
bank probe's base case).

## 8. Open issues

1. **Closed (fix round, §10).** The lever freeze for automation-off attributes:
   `specfreeze --pin/--check/--against` now freeze them (`frozen_levers`,
   `freeze-lever-removed`). `firsttry --report --strict` still does not run the freeze; the
   learner's done check names `specfreeze --check` beside it (chapter §6, rubric A4).
5. **Closed (DV5c, §11).** H5d is admitted at 20 under the `loop-dir:up` form (the user's
   decision D4).
2. **Orchestrator (low).** Author notes §5.3 still describe the literal use site; this file's
   §5 supersedes it.
3. **DV4 (pending).** The prose item's hidden equivalence check (grader container).
4. **Records.** A DELTAS entry for Q13 as built (draft in §9), numbered by the integration lane
   (other lanes write entries in this round).

## 9. Draft DELTAS entry (for the integration lane to number)

> **Δ? · Q13 code and kit as built; the prose-item gate — adopted (DV5b, 2026-10-11)**
> - **Status:** Q13's code (practice II-A, family A) and kit, on Δ186's and Δ190's models, with
>   the prose-item rule of `firsttry --empty-body`. Like Δ160–Δ194, it names no answer, no exit
>   statement and no prediction answer; the detail is in `Solutions/plans/Q13-code-notes.md`.
> - **Change:** layer L6 and the files of QPLAN §23.1 (dd24798); `firsttry`'s prose items: a
>   `// prose: <name>` block is a statement hole whose client gate uncomments its use-site
>   check (which must call `<name>`) and must fail there, plus a proof gate that empties the
>   twin's `<name>`; H3v's shipped client takes two symbolic sequences instead of literals (a
>   literal use site let a weaker conclusion through); H4v and X1v carry `// form: no-nl`, with
>   targeted `cfree:` answers in the twins; every H item admitted at QPLAN §23.5's minutes; the
>   chapter, written pair, rubric (design-judgment bar), bank (8 questions, the tier-viva
>   groups for Q15), fixtures and 8 leak patterns; Q01's A1d pattern tightened rightwards.
> - **Why:** the four results (code notes §6); the empty-body gate 7/7.
> - **Fix round (DV5b review, 2026-10-11):** H5d not admitted (0 minutes: a loop from the top
>   limb passes every gate; recorded as its twin's `cfree:` line; rubric C4 reads the loop's
>   direction); H1v's 44 lines rest on the twin's one-line proof blocks (46 in the counter's
>   three-line layout, one above the band): admitted under a recorded band-edge exception,
>   to be confirmed by the orchestrator or replaced by a layout rule (a one-statement block
>   counts one line); `specfreeze` freezes automation-off levers in every practice file
>   (`frozen_levers`; re-pinned Q01, Q02, Q04, Q07-Q11, Q13, Q14), which closes the
>   lever-deletion shortcut of H4d (and of Q10's and Q11's nonlinear-off items); Q13.P1dv's
>   toy renames its result `t`, so Q01.A1d's leak pattern is bare again.
> - **Open:** the hidden equivalence check (DV4); the skill simulations of Q13
>   (orchestrator); H5d's 20 minutes (a loop-direction form); H1v's band-edge exception.

## 10. The review fix round (DV5b, 2026-10-11)

Re-verified on the pins, one solver job at a time under a 32 GB scope (probes archived under
`~/.cache/dafny-verus-learn-0/author-probes/dv5b/fix/`):

- **H5d's shortcut (reproduced).** A loop from the top limb (`v := s[i - 1] + BASE * v`, `i`
  down from `|s|`, invariant `v == ToNat(s[i..])`, two slice assertions) in a module with
  nonlinear arithmetic off: `scripts/vcheck --module Q13` verified (132). It uses no library
  call and no power variable, and no form rule sees a loop's direction. Recorded as the twin's
  `// cfree:` line; H5d is `admitted = false, minutes = 0` (Q14.H3v's precedent); rubric C4
  makes a loop from the top limb a grade-1 finding read by a reader; the chapter's §6 table
  says a reader checks the direction.
- **The lever freeze (built).** `dvl.levers.turns_off`/`off_levers`/`off_lever_findings`;
  `specfreeze --pin` writes `frozen_levers` for each file with an automation-off lever
  (`{:disableNonlinearArithmetic}`, `@DisableNonlinearArithmetic`, `{:induction false}`,
  `@Induction(false)`), `--check` and `--against` report one that is gone as
  `freeze-lever-removed`; adding a lever, or removing a trust escape or a lint-refused option
  (Q05's infra agent removes one), is no finding. Probe: the learner file with only
  `Q13_Library`'s attribute deleted gives `freeze-lever-removed — module Q13_Library
  {:disableNonlinearArithmetic}` (exit 1) under `--against`. Static test
  `SpecFreeze.test_an_automation_off_lever_is_frozen`. Every armed module re-pinned: only the
  header comment and the `frozen_levers` lines changed (no statement hash moved). H4d keeps
  its 15 minutes: its shortcut now fails a tool gate. Chapter §5–§6 and rubric A4/C7 say so.
- **H1v's line count.** 44 as laid out, 46 in the three-line layout of its two one-statement
  proof blocks: a band-edge reading, kept and recorded in §9's draft for the orchestrator.
- **Q13.P1dv's toy** names its result `t` (learner and twin docstrings, the chapter's probes
  and box); `tests/instructor/leak_patterns/Q01.txt`'s A1d pattern is the bare assignment
  again.
- **Runs on the final files:** `firsttry.sh Q13 --empty-body` 7/7, exit 0 (H5d's `cfree:`
  reported as passing every gate, not failing: not admitted); `specfreeze --pin`/`--check` 0;
  `vcheck --ref --pin-counts Q13` (unit 137, crate 9); `vcheck --shipped Q13` 0 problems;
  chapter pins re-captured (`--ci` 11 pins, 0 problems); `chapter_lint` 0; rubric pins
  current; the leak verifier OK with Q01.A1d's bare pattern.


## 11. DV5c: the user's decisions D1 and D4, admitted (2026-10-12)

The user's decisions (DELTAS, replacing Δ204 items 1, 2 and 5) applied by the DV5c decisions
and tools lane, one solver job at a time inside a 16 GB `systemd-run` scope (`free -g` 95–98
GB available before each batch; no job killed). Scratch `/tmp/dvl0-dv5c-tools/`; archive
`~/.cache/dafny-verus-learn-0/author-probes/dv5c/tools/`.

**D1, the layout rule.** The counter is now a course tool, `scripts/pcount.py` (C.8's counter
moved in, with tests `tests/wrappers/test_pcount_static.py`): a proof block (`proof { … }`, an
assertion's `by { … }`) whose braces hold one statement counts as one proof line, however it
is laid out. `--no-layout-rule` reproduces C.8 exactly on every declaration of every twin
(1,112 declarations compared, 0 differences; `cmp_pcount.py`). Re-count (`recount.py` and the
counter on each item's declarations; statements of invented lemmas by `--stmt`):

| item | before (C.8) | under D1 | band | status |
|---|---|---|---|---|
| H1v `sub` + `lemma_sub_lift` | 44 (46 in a three-line layout of `sub`'s blocks) | 18 + 12 + statement 13 = **43**, in either layout | 15–45 | in, no edge reading needed |
| H2d | 12 | 12 | 10–30 | in |
| H3v `lemma_lt_at_any` + `lemma_eq_any`, `tail` | 26 | 8 + 8 + 1 + statements 6 + 1 = **24** (32 with the prose statement) | 15–45 | in |
| H4d / H4v | 22 / 20 | 22 / 20 | 10–30 / 15–45 | in |
| H5d `ValueLoop` | 13 | **12** (7 exec) | 10–30 | in |

`lemma_sub_lift`'s one-statement `assert forall … by { … }` block and `ValueLoop`'s one-statement
`by { … }` block are what moved. H1v stays admitted at 35, now inside the band on the rule.

**D4, the loop-direction form.** `dvl.forms` gains `loop-dir:[<x>:]up|down` (Dafny and Verus,
static; tests `FormLoopDirection`, 4 cases). H5d's learner block and twin carry `// form:
loop-dir:up` (the prompt already says "from the LOW limb"); the twin's `cfree:` loop from the
top limb is now killed by the form. `scripts/firsttry.sh Q13 --empty-body` (1,290 s): **7/7**,
exit 0; H5d: "the empty body fails in every run", "the twin meets its forms (loop-dir:up)",
"construct-free answer 1 fails its forms: form loop-dir:up not met (the while loop at line 172
counts down, not up)" (`eb-Q13.txt`). Stability: §11.1 below. H5d's four results now hold:
(1) 12 in band; (2) the gate fails and its known shortcut is killed; (3) stable (the CV flag
of §3 is advisory and recorded); (4) pinned APIs. **Registry: `Q13.H5d` admitted, 20
minutes**; Q13's hole minutes D 65 / V 75, 140 of the module's 200 (H lines whole).

Chapter §4 (H5d's paragraph), §5 (the lever) and §6 (the `--report --strict` row), rubric A5
(the form line and the strict report's lever line), C4 (the form is the anchor of a wrong
direction; a reversed index is still read) and C7 now say which tool checks what. The units
fence was re-captured (the H5d hole moved from line 160 to 161).

**§11.1 Stability and the other checks (DV5c, final files).** `vcheck --ref --brittleness
--solvers` on the Dafny twin unit: six rows verified, `stable`; one advisory flag, `ValueLoop`
(line 170) 44,402–76,240 (CV 27.3%, solver 4.14.1), the same as §3 (the form line moved no
count); `vcheck --ref --gate` on the unit twin 137 verified, 0 holes; `vcheck --shipped Q13` 4
files, 0 problems; `specfreeze --check Q13` 0; `pins.py --ci --module Q13` 11 pins, 0
problems after the units fence's re-capture; `chapter_lint Q13` 0 problems; rubric pins
current; the leak verifier OK (15 modules).

**Other tool fixes seen from Q13.** `vcheck --gate` on the shipped Dafny unit no longer adds
`pinned-symbol-missing` for `NormalizeConcat` (a bodyless hole runs no task; its hole is now
read as holding it); `firsttry --report --strict` runs the lever freeze, so a deleted
`{:disableNonlinearArithmetic}` on `Q13_Library` is a `lever:` line there too.

## 12. DELTAS-ready text for the records lane (DV5c decisions and tools lane)

> **Δ? · The user's decisions D1–D4 (2026-10-12), replacing Δ204 items 1, 2 and 5 — adopted (the user; DV5c)**
> - **Status:** the user's decisions on the orchestrator's open items of Δ204 and Δ205. Items 1, 2 and 5 of Δ204 are replaced by D1, D2 and D3; Δ199's and Δ205's open item on Q13.H5d and Q14.H3v is closed by D4.
> - **Change:**
>   - **D1, the layout rule.** A proof block that holds one statement (Verus `proof { … }`; an assertion's `by { … }` in either language) counts as one proof line, however it is laid out, for every item of both tracks (Δ173's line-count rule gains it). The counter is a course tool, `scripts/pcount.py` (the author notes' C.8 counter moved in; `--no-layout-rule` reproduces C.8 on all 1,112 twin declarations), with one fix (a proof block opened and closed on one line no longer tags later nested exec lines as proof; only Q05's `count_ones`, outside Δ173's scope, moved). Every admitted item of Q10–Q15 re-counted: none leaves its band; Q13.H1v 43 (it stays admitted at 35, now inside the band on the rule), Q13.H3v 24, Q13.H5d 12, Q14.H2v 23, Q14.H3v 29, Q14.H5v 19, Q15.H1v 4, four intro items one lower (Q10.H7v, Q11.H4v, Q12.H4v, Q12.H7v; caps only).
>   - **D2, a declared band exception.** Q15.H1d and H1v are admitted at the S11 line's 15 minutes (8 and 7) under a short-format band exception: the registry's `[module.admissible]` entry gains an optional fourth key, `exception = "short-format band: <why>"`, which `scripts/check_course_map.py` accepts only on an admitted item, only of a known kind and only with a reason.
>   - **D3, policy mode keeps opencode** for both modes (no direct Ollama transport; DV4-PLAN §14 Q3's proposal is not built); the title-call fix and the pinned options of Δ202 stay.
>   - **D4, the loop-direction form.** `dvl.forms` gains `loop-dir:[<x>:]up|down` (Dafny and Verus, static): a `while` loop's counters are its guard's identifiers that its body assigns, each assignment a step up (`x := x + e`; `x = x + e`, `x += e`), down, or another; a loop counts up when a counter only steps up and none only steps down; a `for` loop by its range (Dafny `to`/`downto`; Verus `rev`); `loop-dir:up` needs a loop and every loop of the answer region counting up, `loop-dir:<x>:up` every loop on `x` stepping `x` up only. Q13.H5d carries `form: loop-dir:up`, Q14.H3v `form: loop-dir:i:down`; each twin's `cfree:` loop the other way is killed by its form (`firsttry --empty-body` Q13 7/7, Q14 7/7); both admitted, Q13.H5d 20 and Q14.H3v 13 (Q13's H lines 140 of 140, Q14's 150 of 150).
> - **Why:** the user's decisions of 2026-10-12, on the lanes' recorded results (Q13 code notes §11, Q14 §13, Q15 §17).
> - **Touches:** Δ173, Δ191, Δ195–Δ199, Δ202, Δ204, Δ205; QPLAN §19.0, §23.5, §24.5, §25.7, §29 (line counts and admissions); DV4-PLAN §14 Q3; `MODULES.toml` (Q13, Q14, Q15); `scripts/pcount.py`, `scripts/dvl/forms.py`, `scripts/check_course_map.py`; the Q13 and Q14 learner files and twins; the Q13/Q14 chapters and rubrics.
> - **Owner:** the user; applied by the DV5c decisions and tools lane.
>
> **Δ? · DV5c tool fixes: the freeze's open specs and Dafny triggers, the strict report's lever freeze, the exec prose item's TRIV, the held-hole count pin, the decoy and rule 2c's `--build-verify`, calibration over Q01–Q15 — adopted (DV5c, 2026-10-12)**
> - **Change:**
>   - **`open_spec_symbols`** (`scripts/vcheck`) compares the twin's core as written and with its measures blanked, so a declaration shipped with a `decreases` whose twin adds an `ensures` is an open spec (Δ197's open item); re-pinning every freeze found no new open spec.
>   - **Dafny statement triggers are frozen** (Δ204 item 9): `dvl.dafny.statement_attr_skip` keeps a clause's `{:trigger …}` in the statement hash, the open-spec core and the frame core, as Verus keeps `#[trigger]`; other attributes stay dropped. `expected/Q03.freeze`, `Q06.freeze`, `Q15.freeze` re-pinned (hash lines only); every battery repair and both forensic agent twins still pass `--against`. Q15 chapter §12, rubric D6 and bank K3 now say a trigger in a statement clause is a changed statement in both languages.
>   - **`firsttry --report --strict` runs the lever freeze** (Δ199's open item): a `frozen_levers` entry the file no longer carries prints a `lever:` line (`freeze-lever-removed`) and fails the strict report.
>   - **An exec prose item's TRIV** (Δ197's open item): `prose_proof_gate` runs TRIV with the twin block's `triv:` body for a Verus exec prose item, and TRIV alone when the twin's code holds no proof text. Q15.H5v's twin declares its trivial body; its proof gate now passes (Q15 18/18).
>   - **The count pin's held holes:** `vcheck --gate` no longer reports `pinned-symbol-missing` for a pinned declaration still in the file whose lines hold a counted hole (a bodyless lemma runs no task: Q14_Term.InterleaveSpec, Q13's NormalizeConcat; the DV5b simulations' finding); a deleted, renamed or emptied declaration is still reported.
>   - **`--exit` with an empty exit file:** a static test of the skip and of the refusal.
>   - **The decoy** `Solutions/decoy/Q15/` (QPLAN §30 Q60): `DECOY.md` and `answers.txt`, a canary and no reference content; hook fixtures show rule 1 refusing a study session's Read, `cat`, `ls`, Grep, Glob and a relative Read of it.
>   - **Rule 2c allows `mksandbox-run --build-verify`** (Δ201's open item): it prints one command's manifest and starts no container (its mode group excludes a run); only the whole word counts, so a live run whose `--argv` text names it stays refused (hook header, the guard's rule text and fixtures; `scripts/test_hooks.sh` 6,721 passed).
>   - **Calibration** (`tests/instructor/calibration/calibrate.py`): default modules Q01–Q15, budget 60; tutor holes Q13.H2d, Q14.H1d, Q15.H2d, each covered by a pattern cut from its answer (self-tests: defaults, the hole in the file the tutor case names, the pattern, author-only).
>   - **Q12's bank Opening** (QPLAN §29: the hand part's first tries), ahead of its draw table.
> - **Touches:** Δ11, Δ44, Δ195, Δ197, Δ198, Δ199, Δ201, Δ204, Δ205; `scripts/vcheck`, `scripts/specfreeze`, `scripts/dvl/dafny.py`, `scripts/firsttry.py`, `.claude/hooks/spoiler-guard.sh`, `tests/hooks/templates/`, `tests/wrappers/`, `tests/instructor/calibration/`, `.claude/skills/instructor/banks/Q12.md`, `.claude/skills/instructor/banks/Q15.md` (K3).
> - **Records lane:** `CLAUDE.md`'s **Not built yet** line drops `Solutions/decoy/Q15/`, and its rule 2c sentence ("`scripts/mksandbox-run` other than `--check-access` and `--dry-run`") adds `--build-verify`; DV4-PLAN §12's rule table row 2c likewise; QPLAN §29's line-count and admissibility cells (Q13.H1v 43; Q13 6 of 6 admitted, Q14 6 of 6, Q15.H1d/H1v under the exception); QPLAN §23.5/§24.5 status; Δ204 items 1, 2, 5 marked replaced.

## 13. The DV5c review fix round (2026-10-12)

The DV5c admission review found that H5d's `loop-dir:up` read only the counter: the loop
from the top limb rewritten with an up-counting `j` (index `|s| - j - 1`) verified and passed
the form, and `v := ToNat(s)` (L1's `ToNat` is compiled) beside a dummy up loop passed it too.
Both reproduced (static forms on the twin variant; the twin unit verified under an 8G scope,
as the review's runs). Fixed:

- `dvl.forms`' `loop-dir` now also reads the loop's indices (every index of the body adds the
  counter, read through one-definition locals; none subtracts it or sits in a product, call or
  size; a stepping identifier in an index steps the wanted way) and needs one checked loop to
  read an argument at its counter and assign what the result is computed from.
  `no-call` treats a bare call statement's arguments (a lemma call) as no compiled use, so the
  twin's `LemmaMulBasics(ToNat(s));` passes.
- H5d's learner block and twin: `// form: loop-dir:up, no-call:ToNat`; the prompt says `ToNat`
  may appear in invariants, assertions and lemma calls, never in compiled code. Twin `cfree:`
  answers 2 (the reversed index), 3 (`v := ToNat(s)`) and 4 (the same plus a dummy loop).
- `firsttry.sh Q13 --empty-body` (1,291 s): **7/7**, exit 0. H5d: the twin meets
  `loop-dir:up, no-call:ToNat`; answers 1–4 each verify and fail their forms (1: counts down;
  2: index `| s | - j - 1` subtracts `j`; 3: no loop, compiled `ToNat`; 4: no loop carries the
  computation, compiled `ToNat`). H5d keeps `admitted = true, minutes = 20` (D4): every known
  construct-free answer fails.
- Chapter §4 and the `--report --strict` row, rubric A5 and C4 now name the index and
  computation checks and `no-call:ToNat`; what the form cannot follow (an index through a
  helper or another sequence) stays a reader check (C4).

## 14. DV5d: the prose item's hidden equivalence check (2026-10-12)

Built and run by DV5d's judging lane (`Solutions/plans/DV5d-judge-notes.md`; archive
`dv5d/judge/`). `Hidden/labs/Q13/` was re-sealed with the frozen reference oracles
(`judge/oracles.py`), and `truthcheck judge Q13` ran in a 16 GB Verus verification container on
the final image (`dvl-toolchain@sha256:ee8b0f7c…03de`): the sealed statement of H3v against
the twin's (`faithful`), against §5's four recorded statements (equal length: `weak`; `<=`:
`weak`; `requires false`: `vacuous`; canonical first argument: `weak`), and against two the lane
added (the agreement hypothesis dropped: `strong`; a stronger conclusion: `strong`): 7 of 7 as
expected, 166 s. H3v keeps its 25 minutes; §11's "its hidden equivalence check still waits on
the grader's judging step" is superseded: the learner runs it as
`scripts/mksandbox-run --truth Hidden/labs/Q13/verdicts.tar.age --truth-check judge --judge
SPEC` (SPEC: `[[candidate]] id = "mine" item = "Q13.H3v"`), which a study session's guard
refuses (rule 1c). Rubric A7 and C5 still call the check pending (the kits lane's item).
