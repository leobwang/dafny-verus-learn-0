# Q17 code notes (DV5c, the Q17 module lane)

> **Author-only.** The references and their line counts, the empty-body gate results, the
> construct-free and shortcut probes, the admissibility results (the four results of QPLAN
> §19.0) of every H item, the plain attempt that fails, the plausible-but-wrong statement of
> H3d with its executed counterexample, the tool changes this lane made, and every deviation
> from the plan. Never quote, paraphrase or link any of it from a learner-visible file. The
> item plan is `QPLAN.md` §19 and §27 (learner-visible) and
> `Solutions/plans/Q10-Q18-author-notes.md` §9 ("designs, not probed"); this file records what
> the module lane built and captured on the real files, 2026-10-11.

Every run went through the course wrappers (`scripts/vcheck`, `scripts/vaudit`,
`scripts/pins.py`, `scripts/firsttry.sh`, `scripts/specfreeze`, `scripts/reference_lint.py`)
at the course pins (Dafny 4.11.0 with its bundled Z3 4.12.1, and 4.14.1 for the `--solvers`
axis, `--resource-limit 5000000`; Verus and vstd `0.0.0-2026-09-20-0158`, `--rlimit 2`), one
solver job at a time under the `dvl` caps (Dafny 8 GB, Verus 16 GB); every sweep (the
empty-body gates, the brittleness sweeps, `--pin-counts`, the chapter captures) also ran
inside a `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, the lane's share.
`free -g` read 47–99 GB available before each batch (other lanes were running). `DVL_SCRATCH`
was `/tmp/dvl0-dv5c-q17/scratch`. The archive is
`~/.cache/dafny-verus-learn-0/author-probes/dv5c/q17/`: `empty-body-1.txt`,
`empty-body-final.txt`, `eb-modes-h2v.txt` (per-mode verdicts of H2v's two gates),
`brit-dafny-unit-first.txt` (the first twin: not stable), `brit-dafny-unit-second.txt`,
`brit-dafny-unit.txt` (final), `brit-verus.txt`, `brit-agent.txt`, and `probes/` (every probe
named below: `p1` the first ArrayPQ, `p2` the generator and its proof, `p3` the
verifier attempt at the counterexample, `p5` the plain invariant, `p6` the seq-field shortcut,
`p7` and `p8` the restructurings of `Insert`, `ExtractMin` and `DescInsert`, `v1` the first
Verus ring, `probe_q17b.dfy` with its output, the executed counterexample).

## 1. Files

| learner file | shipped state (tool count) | twin |
|---|---|---|
| `dafny/Q/Q17_PracticeIIIB/std/Q17_PracticeIIIB.dfy` | verified, 3 holes: H1d's constructor, `Insert`, `ExtractMin` (`assume false;`); the given trait `PQueue`, the class `ArrayPQ` with its fields and a placeholder `Valid()` (`true`, an open body); `Peek` and `ArrayPQCheck` commented under `Uncomment as you go:`; a CALIBRATION block | twin (the learner's helpers `Desc`, `DescLastMin`, `DescInsert`, `Spliced`, and in the class `MakeRoom`, `Shift`, each `// reference-only`; `Peek` live, `// reference-only`) |
| `dafny/Q/Q17_PracticeIIIB/std/Q17_Vcgen.dfy` | verified, 1 hole: H3d, the labelled assume of the given corollary `CountCorrect`; W2d (the language, `Exec`, `Pre`, `Vcs`, `Valid`); the given program `Count`, `CountPost`, `CountVcsValid` (proved); an empty STATEMENTS area; `VcSoundWitness` with an empty body | twin (STATEMENTS holds `VcSound` with the run's proof and the run's helpers `SubstSoundE`, `SubstSound`, all `// reference-only`; the corollary live; the witness written) |
| unit `dafny/Q/Q17_PracticeIIIB/std` | learner loop 157 verified, 4 holes | twin 175 verified (`expected/Q17.counts`: 15 symbols, floor 15); `Solutions/dafny/Q/Q17_PracticeIIIB/std/` has no `dfyconfig.toml` of its own (the twin runs in its learner unit) |
| `verus/q/q17_practice_iiib/src/lib.rs` | verified, no hole, no item; `mod perm;` | twin |
| `verus/q/q17_practice_iiib/src/perm.rs` | verified, 2 holes: H2v's `push_back`, `pop_front` (`external_body`); the given `slot_of`, `PRing` with `cap`, `slot`, `live`, `wf`, `view` and a verified `new`; `ring_check` commented | twin (`// triv: push_back: { }`, `// triv: pop_front: { 0 }`; the learner's helper `grow`, `// reference-only`) |
| crate `verus/q/q17_practice_iiib` | 2 holes | twin 8 verified (3 symbols, floor 3); `Solutions/verus/q/q17_practice_iiib/Cargo.toml` (`solutions_q17_practice_iiib`), a member of `Solutions/verus/Cargo.toml` |
| `dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` | verified, no hole (140 verified; `--gate` 140, `vaudit` 0): the CONTRACT, W2d's language unchanged, empty STATEMENTS and HELPERS, the AUDIT block | twin 145 verified, `vaudit --ref` 0 (STATEMENTS: the reference statement with its proof and the witness; HELPERS: `SubstSoundE`, `SubstSound`) |
| — | — | `expected/Q17.counts` (schema 2: 2 units, 5 files), `expected/Q17.freeze` (52 statements in 4 files; `open_bodies` the two `Valid`s; `lib.rs` unfrozen, no statement), `expected/Q17.chapter.toml` (8 pins). No `expected/Q17.pins` and no `slots/Q17.slots`: Q17 has no prediction |

`research/q17_statements.dfy` is the learner's (absent until written, QPLAN §27.1). No
specimen, exit, harness or slot file.

## 2. The four results, item by item (QPLAN §19.0, Δ173)

Line counts under QPLAN §19.0's rule and D1's layout rule (`scripts/pcount.py` on the twins,
`--stmt` for invented statements; exec code excluded). Every figure below is the tool's
since the DV5d small-fixes lane (`scripts/pcount.py` now counts a ghost predicate's body, a
ghost or tracked field update and a multi-line assertion's continuation lines as proof, and an
exec helper method's call as code; this note had corrected those by hand).

| item | reference | proof lines | band | invented |
|---|---|---|---|---|
| H1d | `Valid@2` 2 + `constructor` 2 + `MakeRoom` 5 + `Shift` 7 + `Insert@2` 3 + `ExtractMin@2` 5 + `Desc` 1 + `DescLastMin` 3 + `DescInsert` 1 + `Spliced` 0; statements `Desc` 1, `DescLastMin` 3, `DescInsert` 5, `Spliced` 5, `MakeRoom` 5, `Shift` 6 | **54** | D 30–80 | 3 lemmas, 1 predicate, 2 helper methods |
| H2v | `grow` 39 + statement 9; `push_back` 7; `pop_front` 4 (58 by hand before DV5d: the hand count missed `grow`'s tracked field update `self.perms = Tracked(…)`, which the Q14 notes count, H5v) | **59** | V 45–120 | 1 helper fn |
| H3d | the learner's part: `VcSound`'s statement 4 (signature, two `requires`, one `ensures`) + `VcSoundWitness` 6 | **10** | D 30–80: **below** | 0 |
| H3d with A1d | the twin's whole: `VcSound` 5 (the run adds the `decreases` line) + 26, `SubstSound` 2 + 12, `SubstSoundE` 2 + 6, the witness 6 | 59 | (in D 30–80) | (2 helpers, the run's) |

| item | 1. complete, in band | 2. empty-body gate fails | 3. stable | 4. pinned API | entry |
|---|---|---|---|---|---|
| H1d | twin unit 175, 0 holes, `vaudit --ref` 0; 54 lines | yes: one gate per hole method (§4), each fails in every run (maxauto and seeds 1–3); the plain invariant fails (§3); the seq-field shortcut fails at the shipped `Peek` (§3) | `--ref --brittleness --solvers` on the unit: all six rows verified, stable; flagged (advisory): `DescInsert` CV 70.8% (4.12.1, 269,437..1,161,609), `ExtractMin` CV 50.7% (4.14.1), `ArrayPQCheck` CV 28.9% (4.14.1) | Dafny built-ins only (multisets, sequences, arrays, traits) | **admitted, 50** |
| H2v (gated) | crate twin 8, 0 holes, `vaudit --ref` 0; 59 lines (§2) | yes: one gate per hole method (`PRing::push_back`, `PRing::pop_front`), each fails in every light mode and seed (E0, E0H, E1, E2, EC under seeds 1–3, EM, and TRIV with the twin's `{ }` and `{ 0 }`), every run `fails(error)`: each variant reached verification (no compile error, no VIR error) | `--ref --brittleness`: seeds 1–3 verified, stable; widest spread CV 15.1% | vstd `cell/pcell_maybe_uninit.rs`: `PCell::empty` (l. 106), `PCell::new` (l. 115), `put` (l. 127), `take` (l. 141), `PointsTo::id`, `mem_contents`, `is_init`, `is_uninit`, `value` (l. 59–88); `seq.rs` `Seq::tracked_empty` (l. 1147), `tracked_push` (l. 1212), `tracked_borrow_mut` (l. 1201); `Tracked::borrow_mut` (verus_builtin) | **admitted, 50** (the lane's recorded gate, as Q14's lane admitted its gated items, Δ196) |
| H3d | the statements' twin complete (with A1d's proof) and stable; the learner's part 10 lines, below the band | the client gate: the given corollary's use site does not resolve without `VcSound` (✓); the prose proof gate: the twin's `VcSound` with an empty body fails in every run (✓) | the unit's sweep above (all rows); the agent twin `--ref --brittleness --solvers`: six rows verified, stable, widest CV 13.9% | — | **not admitted, 0**: DECISION NEEDED (§8, item 1) |
| A1d (contract) | the agent twin 145, `vaudit` 0 | — | stable (above) | — | (a contract item: no minutes entry) |

**Admitted hole minutes:** H1d 50 + H2v 50 = 100 of the H lines' 135 (design §7.5: H1 50,
H2 50, H3 35). H3's 35 is the shortfall, pending the decision (§8). F-H1d, F-H2v and F-H3d have
no reference (none is needed while their items are admitted; F-H3d would need one if the
decision keeps H3d out).

## 3. H1d: the plain attempt, the shortcuts, the stability work

- **The plain implementation fails** (QPLAN §19.0's hard-tier rule): the twin with `Valid()`
  reduced to `this in Repr && a in Repr && n <= a.Length && 0 < a.Length && Model ==
  multiset(a[..n])` (no order) and the order lemmas' calls replaced by the identity
  assertions: `failed — 22 verified, 1 error`, `ExtractMin`'s postcondition, at the clause
  `forall y | y in old(Model) :: m <= y` (`probes/p5`).
- **The seq-field shortcut** (the F-H1d design, a `var s: seq<nat>` added to the class and
  the array left unused): every method verifies, and the shipped `Peek` (uncommented, its body
  `m := a[n - 1]`) fails: `failed — 20 verified, 3 errors`, two postconditions and an index
  at `Peek` (`probes/p6`). `Peek`'s `ensures` was strengthened from `m in Model` to the
  minimum too (it verifies against the reference invariant with no lemma call), so it also
  binds the prompt's direction (the minimum at the top of the prefix). No `cfree:` line: the
  shortcut changes the class's fields, which a `cfree:` body cannot express; it is killed by a
  given check, and `--report --strict` counts that check until it is uncommented. The report
  counts commented lines, not their text: rubric A5 has a reader compare each uncommented check
  with the shipped file.
- **`Valid() := false`**: the constructor's `ensures Valid()` fails; not a shortcut.
- **An unsorted array with a linear-search `ExtractMin`** is a correct implementation of the
  trait, but the strengthened `Peek` needs the minimum at the top of the prefix, so it must
  also keep that; it is not construct-free (an invariant, frames, a loop invariant), so it is
  not a shortcut under Δ173.
- **Stability.** The first twin (one `Insert` with the copy and the shift inline, then with a
  `Grow` helper called under `if n == a.Length`) verified at the default seed and was
  `inconclusive` (out of resource) in every seeded row (`brit-dafny-unit-first.txt`). Measured
  variants (`probes/p7`, `p8`): the cost is the join of the two paths of the growth branch
  under 4.14.1; a helper that grows only when full and is called unconditionally (`MakeRoom`),
  with the shift in its own helper (`Shift`), verifies in all six rows; `ExtractMin`'s proof
  over a ghost copy of the prefix cut its worst count from 1.94 M to 0.52 M. Two rewrites of
  `DescInsert` (an explicit `forall` with a case split, a pointwise characterization) were
  worse (out of resource in most rows) and were not kept.

## 4. H2v: the design, the diversification, W19

- **Design.** Q10's ring buffer with one `PCell` per slot from
  `vstd::cell::pcell_maybe_uninit` (a cell that may be empty), the permissions in a
  `Tracked<Seq<PointsTo<u64>>>`, `head`/`len` as Q10's, and a given `wf` that ties each
  permission to its slot's cell by id and makes exactly the live slots the initialized ones.
  Holes: `push_back` (no room precondition: when full it grows) and `pop_front`. The reference
  grows through a learner helper `grow` (moving each element, in order, with `take` from its
  old cell into `PCell::new`, then pushing empty cells to twice the capacity) and borrows each
  changed permission with `tracked_borrow_mut`.
- **Why growth.** The first probe (`probes/v1`'s first form: always-full cells from
  `vstd::cell::pcell`, a tracked sequence, a fixed capacity, `push_back` only) verified at the
  first try with 4 proof lines: the two operations alone would sit far below the hard Verus
  band (45–120). Cells that may be empty (the init-tracking conjunct of `wf`) and growth on a
  full `push_back` bring the item to 59 (§2). The plan's tracked-map form was not probed.
- **W19 (Δ177).** The permissions are a tracked *sequence*, each borrowed in place
  (`tracked_borrow_mut`); no permission is moved out of a tracked map and put back, which is
  W19's genre (design §9.3: "moving one permission out of a tracked map and back"). So Q17.H2v
  is diversified, and with Q14.H5v (no map, Δ196) the Q side of W19 is gone: by Δ177, W19 is
  dropped from design §9.3, PLAN §5.4 and `scripts/avoid.waivers.tsv` (records lane and avoid
  lane). `avoid.sh` is clean with W19 still listed (provisional).
- **Bounds.** `wf` bounds the capacity by `0x4000_0000` and `push_back` requires
  `old(self)@.len() < 0x2000_0000`: `usize::MAX` is not a constant Verus knows, so a client
  could not meet a bound written with it (`ring_check` failed until the bounds were literals,
  and until the room precondition was stated on the view).
- **Δ182's open item for this lane** ("whether the tracked E0 variants compile is checked on
  the built files"): the shipped holes hold `unimplemented!()` and no `let tracked` line, and
  every E-mode variant of both methods reached verification and failed (`fails(error)`, no
  compile error; `eb-modes-h2v.txt`). Nothing to fix.

## 5. H3d and A1d: the statements, the plausible-but-wrong one, the band

- **The language** is Q14's W2d with a two-armed `If` in place of `IfThen`, `Update` given as a
  function, and the generator named `Pre`/`Vcs`. The given text holds no proof of any case of
  soundness (Q14.H4d's answer is the While case of A1d's proof, in the twins only).
- **The reference statement** (the agent twin and the Vcgen twin):
  `lemma VcSound(c: Cmd, q: BExp, s: State, fuel: nat) requires forall p | p in Vcs(c, q) ::
  Valid(p) requires Holds(Pre(c, q), s) ensures Exec(c, s, fuel).Done? ==> Holds(q, Exec(c, s,
  fuel).s)`; the run adds `decreases fuel, c` (an added measure is no freeze change) and proves
  it by recursion with the substitution lemma `SubstSound` (and `SubstSoundE` for expressions)
  under HELPERS. The witness: `Assign(0, Const(1))`, `Lt(Const(0), Var(0))`, any state, fuel 0.
- **The plausible-but-wrong statement** (author notes §9): the side conditions required only
  in the start state, `forall p | p in Vcs(c, q) :: Holds(p, s)`. It is false: at
  `While(Lt(Var(0), Const(1)), Lt(Const(0), Const(1)), Assign(0, Const(1)))`,
  `q = Lt(Var(0), Const(1))`, the all-zero state and fuel 2, the run ends `Done` with `x0 = 1`,
  the precondition and both side conditions hold in the start state, and `q` is false in the
  final one. Executed by the rubric's Probe B (a `{:test}` method appended to a copy of the
  shipped agent file): `vcheck --test: 1 passed, 0 failed` (`probes/probe_q17b.dfy`). A verifier
  proof of the same refutation over W2d (an `{:axiom}` copy of the wrong statement and a lemma
  deriving `false`, `probes/p3`) ran out of resources at the pin in every isolated assertion
  about a concrete updated state, so the executed check is the anchor.
- **The shortcuts of a statement item.** A false statement lets `CountCorrect` verify as well
  as a true one (a bodyless lemma is not checked); the contractor cannot prove it, and the
  learner's unit gate passes only after the delivered proofs are copied back, so a false
  statement never reaches the Done line. A true statement specialized to `Count` passes the
  client and could be proved; the hidden equivalence check (QPLAN §30 Q49, not built) would
  catch it, and until then rubric C6 has a reader catch it, as for Q13–Q15's prose items.
- **The band.** The learner writes 10 proof lines (the statement and the witness), below the
  hard Dafny band (30–80); the complete twin, with the run's proof, is 59. QPLAN §29 already
  lists Q17.H3d's 35 minutes as below the hard tier's per-item range. Admission needs a reading
  of the band for a statement item: §8, item 1.

## 6. Tool changes (for the tools owner's review)

1. **`scripts/firsttry.py`: per-method empty-body gates for a Dafny item with several hole
   methods** (`dafny_hole_methods`, `dafny_methods_gate`). `dvl.dafny.empty_body` empties an
   item's first method-like declaration only, and H1d's block opens with the class's
   placeholder `Valid` (a predicate), so its three hole methods would have gone ungated (and
   the predicate's empty body is not even well formed). A block holding two or more hole
   methods (methods, constructors, lemmas; never a function or predicate) is now gated once
   per hole method, by its qualified symbol (`Q17_PracticeIIIB.ArrayPQ._ctor`, `….Insert`,
   `….ExtractMin`); a block with one keeps its first declaration's gate, so no earlier item's
   gate changes (no other armed Dafny block has two hole methods). The docstring says so;
   `TraitImplItems.test_dafny_class_hole_methods` (static).
2. **`scripts/dvl/dafny.py`: a trait that a class of its file implements in full is allowed
   in a learner file** (`implemented_traits`, `_implemented_trait_lines`). Δ3's lint flagged
   every Dafny trait in a learner, agent or reference file (`trait`, and `bodyless-abstract`
   on each bodyless member), and `dafny audit` reports each bodyless compiled trait method
   (`audit-bodyless-compiled`), so H1d's given `PQueue` made `vaudit` fail on the learner's
   finished unit, with no way to reach Done. Δ3's hazard (G3) is a trait nothing implements: its
   members are silent assumptions. A trait whose every bodyless member has a body of the same
   name in a class of the same file that extends it is now no `trait` finding and no
   `bodyless-abstract` findings, and `vaudit` drops the auditor's bodyless rows on exactly those
   members' lines; Dafny itself refuses a class that leaves a member out, and checks the
   class's member against the trait's contract. Every other trait stays a finding in every mode.
   Static tests: `Lint.test_a_trait_a_class_implements_in_full_is_allowed`,
   `Lint.test_the_audit_keeps_an_implemented_trait_s_members_as_statements`. QPLAN §27.1 and the
   author notes §12 planned a Dafny trait for H1d; the lint's rule predates them.

`tests/wrappers/test_dafny_static`, `test_practice_tools_static`, `test_forms_static`: 144 OK.

## 7. Deviations from the plan (QPLAN §27) and why

1. **The main Dafny file imports nothing** (QPLAN: "imports L1–L7"): H1d uses no spine
   declaration; the unit includes L1–L7 as every unit of the tier does (as Q14's loop file).
2. **The trait's methods are restated by the class**: Dafny refuses an overriding method
   without them ("the method must provide an equal or more detailed postcondition than in its
   parent trait"); the freeze pins both.
3. **`Valid()` ships with the placeholder body `true`** (an open body), and two given checks
   ship commented: `Peek` (inside the class) and `ArrayPQCheck`. The constructor is a hole
   with the trait-style `ensures` given.
4. **H2v**: a tracked sequence of permissions, not a map (§4, W19); `push_back` grows; capacity
   bounds as literals; `new` given and verified (four empty cells).
5. **H3d**: a prose item (`// prose: VcSound`) with the course's prose gates; `VcSound`'s
   parameters fixed by the corollary's use site; STATEMENTS inside the item's block; the
   learner copies the delivered proofs back so the unit can pass its gate (the file's header,
   step 3), since a bodyless statement is a counted hole.
6. **The agent file** carries W2d's language unchanged (a second copy, frozen in both files)
   and no corollary; `research/q17_statements.dfy` is the agent file as shipped plus the
   learner's statements, so `specfreeze --against` compares the language too.
7. **The worked example keeps QPLAN's id W2d** though the module has no W1 (as Q14).
8. **The written pair**: B1 also asks for a plausible-but-wrong statement with a concrete run
   and a too-weak one (the audit skill of rung 13, before the run), beside QPLAN's "H1d's
   invariant and lemmas; H3d's statements in words"; B2's closing line asks which trusted part
   of the module the card's lesson applies to.

## 8. DECISION NEEDED (the user's)

1. **Q17.H3d's band and minutes.** The learner's part of the statement item is 10 proof lines,
   below the hard Dafny band (30–80); the complete reference with the contractor's proof is 59.
   The other three results hold; the prose item's hidden equivalence check is not built.
   Options: (a) admit H3d at 35 with a declared exception `statement-item band: the learner
   writes the statements, the contractor the proof` (the checker would need the new exception
   kind); (b) count the complete reference (59, in band) and admit at 35 with no exception;
   (c) keep it at 0 until the hidden equivalence check exists (QPLAN §30 Q49) and record the
   35-minute shortfall. Recommendation: (a): it states plainly why the band does not apply,
   like D2's short-format exception, and rubric C6 and the audit cover what the hidden check
   will.

## 9. Runs (final files)

- `vcheck Q17`: Dafny unit 157 verified, 4 holes; crate 2 holes; 6 in all (the chapter's
  `units` pin). `vcheck --ref`: Dafny twin unit 175, crate twin 8, agent twin 145, 0 holes;
  the agent file 140 (`--gate` passes).
- `vaudit`: the learner unit 4 findings, one `audit-assume` per hole; the crate 2,
  `hole-external-body`; the agent file 0; `vaudit --ref` 0 on every twin.
- `vcheck --ref --pin-counts Q17`; `vcheck --shipped Q17`: 5 files, 0 problems.
- `specfreeze --pin Q17`: 52 statements in 4 files; `--check Q17`: 0 findings.
- `firsttry.sh Q17 --empty-body` (16 GB scope): 3/3 (`empty-body-final.txt`).
- `firsttry.sh Q17 --lint-hollow`: OK (4 files). `--report`: 0 slots, 24 commented checks, 0
  missing, vacuous, banned or forms not met.
- `reference_lint.py --module Q17`: 0 findings (4 twins).
- `pins.py --update --chapter Q17` (8 entries) and `--ci --module Q17`: 0 problems.
- `chapter_lint.py Q17`: 0 problems (3 strand sections, 3 diagrams, 8 pinned fences, about
  3,000 words).
- `make -C paper paper` and `paper-solutions`: green; the two fixtures compile.
- `update_rubric_pins.sh` (6 pins of the Q17 rubric written) and `--check`: 0 pending, stale,
  missing or bad (one required rubric absent: Q18's, another lane's).
- The leak README's verifier: 17 modules, 1,586 public files, OK (Q17: 8 patterns OK).
- `check_course_map.py` and `--only vocab`: OK; `gen_units.py --check`: 37 units match;
  `avoid.sh`: OK, 0 hits.

## 10. Open issues

- **`scripts/test_course_map.py`** stops at its first line: "the planned stand-in Q18 is no
  longer planned" (the Q18 lane armed Q18; with Q16–Q18 armed no practice module is planned).
  Owner: the integration lane or the tools owner, who moves the stand-in cases to a module still
  planned (Q19 or an R module).
- **The hidden equivalence check** for H3d (QPLAN §30 Q49): DV4/DV5 integration, with the
  grader container's judging step.
- **H1d's flagged spreads** (advisory; §2).
- **Tools owner**: review the two tool changes (§6).
- **The skill simulations of Q17** (Δ205's model) and its part of the hard tier's viva draws
  (Q18's bank tables them; the bank notes name Q17's candidates).

## 11. DELTAS-ready text (for the records lane)

### Δ2xx · Q17 code and kit as built: the priority queue over a trait, the permission ring buffer, the VC generator's statements and the metatheory contractor; two tool changes — adopted (DV5c, 2026-10-12)
- **Status:** Q17's code (practice III-B, family B), chapter and kit on Δ195–Δ198's model. Like
  Δ160–Δ205, it names no answer, no statement the learner writes and no invariant; the detail
  is in `Solutions/plans/Q17-code-notes.md`.
- **Change:**
  - **Files.** The Dafny unit `dafny/Q/Q17_PracticeIIIB/std/` (`Q17_PracticeIIIB.dfy`: the
    given trait `PQueue` and the class `ArrayPQ`, H1d; `Q17_Vcgen.dfy`: W2d, the given program
    and corollary, the statement item H3d), the crate `verus/q/q17_practice_iiib` (`lib.rs`,
    `perm.rs`: H2v), the agent file `dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy`
    (rung 13). 6 holes (Dafny 4, Verus 2), no prediction, no exit.
  - **Pins.** `expected/Q17.counts` (Dafny unit 175, floor 15; crate 8, floor 3; 5 files),
    `expected/Q17.freeze` (52 statements in 4 files), `expected/Q17.chapter.toml` (8 pins).
  - **Admissions:** H1d 50; H2v 50 (gated; admitted on the lane's recorded gate, as Δ196's);
    **H3d not admitted** (0 minutes): its learner-written part is below the hard band, pending
    the user's decision (code notes §8). Admitted hole minutes 100 of the H lines' 135.
  - **W19 dropped** (Δ177): Q17.H2v keeps its permissions in a tracked sequence, each borrowed
    in place, and moves none out of a map and back; with Q14.H5v (Δ196) the Q side of the genre
    is gone. Design §9.3, PLAN §5.4 and `scripts/avoid.waivers.tsv` drop W19.
  - **Tools.** `scripts/firsttry.py` gates a Dafny item with several hole methods once per
    method (`dafny_hole_methods`); `scripts/dvl/dafny.py` allows, in every lint mode, a trait
    that a class of its own file implements in full, and `vaudit` drops `dafny audit`'s bodyless
    rows on that trait's members (`implemented_traits`); three static tests.
  - **Kit.** `docs/Q17_PracticeIIIB.md` (about 3,000 words, 8 pinned fences, 3 diagrams, the
    CONTRACT blockquote); `paper/Q17_problems.tex` B1 the blueprint of H1 and H3, B2 card 12.12
    (lines 5507–5533, sha256 `533d07ab…dabba`), with answers and solutions; the rubric at
    `library-pr` (Probes A–F; Probe B an executed run on a copy of the agent file) with its
    audit debrief; the bank of eight (K1–K8, all `viva: yes`, four predicts, six backward edges,
    three parallel problems); the flawed and gold fixtures; eight leak patterns and the README's
    row.
  - **Deviations from QPLAN §27** (code notes §7): the main file imports nothing; the class
    restates the trait's contracts; H2v's tracked sequence, growth and literal bounds; H3d as a
    prose item whose statements are copied back after the run; the agent file's own copy of
    W2d; B1's audit parts.
- **Why:** the Q17 lane's runs (code notes §9): `firsttry Q17 --empty-body` 3/3; the twins gate
  175 / 8 / 145 with 0 holes; `--brittleness` stable on every twin (Dafny both solvers);
  `vcheck --shipped`, `specfreeze --check`, `reference_lint`, `pins.py --ci`, `chapter_lint`,
  the paper builds, the rubric pins, the leak verifier, the course map and `avoid.sh` clean.
- **Touches:** Δ3, Δ173, Δ177, Δ182, Δ195, Δ196; QPLAN §27, §29; `MODULES.toml` (Q17);
  `verus/Cargo.toml` (generated); `Solutions/verus/Cargo.toml`; `scripts/firsttry.py`,
  `scripts/dvl/dafny.py`; `tests/wrappers/test_dafny_static.py`,
  `tests/wrappers/test_practice_tools_static.py`; `tests/instructor/leak_patterns/README.md`;
  the files above and their twins.
- **Owner:** this round's Q17 lane.
- **Open** (owner, severity): the user (high: before Q17 ships): H3d's band and minutes (code
  notes §8); DV4 with the DV5 integration lane (medium): the hidden equivalence check of H3d
  (QPLAN §30 Q49); the tools owner (medium): review the two tool changes; the integration lane
  (high): `scripts/test_course_map.py`'s planned stand-in (Q18 is armed); the simulations owner
  (high: before Q16–Q18 ship): Q17's skill simulations; the Q18 lane: the hard tier's viva
  draws (Q17's candidates in its bank notes); the records lane (low): QPLAN §27.1–§27.4 and §29
  text that this entry supersedes (the imports, H2v's map, the admissions), and W19.

## 12. Interfaces for later lanes

- **The trait lint rule** (`dvl.dafny.implemented_traits(src) -> set[str]` of trait quals) is
  available to any learner file: a Dafny trait is allowed when a class of the same file extends
  it and gives every bodyless member a body of the same name.
- **The Dafny per-method gate** (`firsttry.dafny_hole_methods(text, rel, it) -> [(symbol,
  name)]`) applies to any block with two or more hole methods.
- **Q18's viva draws**: Q17's candidates are K1, K3, K4, K5, K6, K8 (bank notes); K2 and K7
  are spare.

## 13. DV5d: the user's decisions D6 and D15 (2026-10-12)

Applied by DV5d's decisions lane (16 GB scope, one solver job at a time; archive
`~/.cache/dafny-verus-learn-0/author-probes/dv5d/decisions/`; the lane's notes with the
DELTAS-ready text: `Solutions/plans/DV5d-decisions-notes.md`).

- **D6: H3d admitted at 35 under a new band exception kind, `statement-item`** (§8 item 1,
  option (a)): `"Q17.H3d" = { admitted = true, minutes = 35, fallback = …, exception =
  "statement-item: the learner writes the soundness statements and their witness (10 proof
  lines, below 30), the metatheory contractor (A1d) their proof (59 in all); the user's
  decision D6" }`. `scripts/check_course_map.py` knows the kind (`STATEMENT_ITEM_KIND`) and
  accepts it only on an admitted H item whose block is a prose item (a `// prose: <name>`
  line, as H3d's) or sits in one of the module's agentic files; `scripts/test_course_map.py`
  covers both routes, the refusal on another item, a missing reason and a gated item. H3d's
  other three results are §2's, unchanged (re-gated: `firsttry.sh Q17 --empty-body` 3/3 on
  this tree: the client gate and the prose proof gate pass). The hidden equivalence check
  (QPLAN §30 Q49) stays the grader's pending step; rubric C6's reader covers it until then.
  **Admitted hole minutes: 135 of the H lines' 135** (H1 50, H2 50, H3 35); Q17's shortfall
  note (Δ216) is closed.
- **D15: the implemented-trait lint relaxation stays** as §6 item 2 built it (Δ211); H1d's 50
  minutes rest on it. No code changed.
- Runs on this tree: `check_course_map.py` OK; `pins.py --ci --module Q17` 15 pins, 0 problems.

## 14. DV5d: H3d's hidden equivalence check (2026-10-12)

Built and run by DV5d's judging lane (`Solutions/plans/DV5d-judge-notes.md`; archive
`dv5d/judge/`). `Hidden/labs/Q17/` was re-sealed with the frozen reference oracles, and
`truthcheck judge Q17` ran in an 11.5 GB Dafny verification container on the final image: the
sealed `VcSound` against the twin's (`faithful`), against §5's plausible-but-wrong statement
(side conditions in the start state only: `strong`, the candidate's requires does not give the
reference's), and against four the lane added (the precondition dropped: `strong`; `fuel > 0`
added: `weak`; total correctness: `strong`; `requires false`: `vacuous`): 6 of 6 as expected,
50 s. The check is a refinement both ways, not the Lab 2 oracles' implication, which judges
inside the reference's requires and would have called the plausible-but-wrong statement
faithful. §13's "the hidden equivalence check stays the grader's pending step" is superseded;
H3d keeps D6's 35 minutes.
