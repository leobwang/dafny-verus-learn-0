# DV5d decisions lane: the user's decisions D5–D18 in the tree (as built, 2026-10-12)

> **Author-only.** Records which of the user's decisions of 2026-10-12 this lane applied, how,
> what it ran, and the DELTAS-ready text for the integration lane (§3). It names no answer:
> the capstone's reference statements and delivery, the line counts' detail and the probes
> are in the module notes (`Q15-code-notes.md` §18, `Q17-code-notes.md` §13,
> `Q18-code-notes.md` §16) and the archive.

Authoring worktree, `authoring` @ e43077c plus the round's working tree (uncommitted; other
DV5d lanes edited other files at the same time). One solver job at a time, each under the
wrappers' caps (Dafny 8 GB, Verus 16 GB) inside `systemd-run --user --scope -p MemoryMax=16G
-p MemorySwapMax=0` (the lane's share), through `/tmp/dvl0-dv5d-decisions/run.sh`, which
refuses below 31 GB available (`free -g` showed 97–98 GB available). No job was killed for
memory. No model was called and no container started. Captures:
`~/.cache/dafny-verus-learn-0/author-probes/dv5d/decisions/`.

## 1. The decisions and where each went

| decision | what this lane did | files |
|---|---|---|
| D5 (age key custody) | not this lane's | — |
| D6 Q17.H3d at 35, `statement-item` | new exception kind, validated; H3d admitted | `scripts/check_course_map.py`, `scripts/test_course_map.py`, `MODULES.toml` (Q17) |
| D7 Q18.H1d 25, H1v 15, short-format | admitted; H1d's wording in the chapter, QPLAN §28 and design §7.5 | `MODULES.toml` (Q18), `docs/Q18_PracticeIIIC.md`, `QPLAN.md` §28, `docs/design/DESIGN-PROPOSAL.md` §7.5 |
| D8 (Qwen agent-mode batches) | not this lane's (the chapter's §0 keeps its one pending item) | — |
| D9 Q18.H2d/H2v, statement items | the statement route in `firsttry --empty-body`; the reference statements; admitted 12 / 13 | `scripts/firsttry.py`, `Solutions/research/q18_statements.{dfy,rs}`, `MODULES.toml`, `tests/wrappers/test_capstone_routes_static.py` |
| D10 Claude arms harness-executed | B2's template, solutions, rubric DI.a, the chapter's §0 and §5, the two calibration fixtures | `paper/Q18_answers.tex`, `paper/solutions/Q18_solutions.tex`, `paper/rubrics/Q18_rubric.md`, `docs/Q18_PracticeIIIC.md`, `tests/instructor/fixtures/Q18_{gold,flawed}_answers.tex` |
| D11 Q15.H1d keeps 8 (tripwire) | Q15 rubric C1 closes padding; Δ173's bullet (§3) | `paper/rubrics/Q15_rubric.md`, `Solutions/plans/Q15-code-notes.md` §18 |
| D12 Q15 S11 split 8 + 7 | recorded (no change: the registry was built so) | `Solutions/plans/Q15-code-notes.md` §18 |
| D13 L7's `big_sub` | QPLAN §19.1, §19.4–§19.6 and §28.3 read `big_sub` | `QPLAN.md` |
| D14 Q16's Verus `no-call`/`no-adder`; H3 at 55 | recorded (no change) | §2 below |
| D15 Q17's implemented-trait lint | recorded (no change) | `Solutions/plans/Q17-code-notes.md` §13 |
| D16 the capstone CLI's build route | `[[bin]]` from `gen_units`; `vcheck --bin` (`dvl.verus.run_bin`); a shipped `main.rs` stub; tests; the chapter's ship step and a pinned fence | `scripts/gen_units.py`, `scripts/dvl/verus.py`, `scripts/vcheck`, `scripts/check_course_map.py`, `verus/q/q18_practice_iiic/{Cargo.toml,src/main.rs}`, `MODULES.toml` (Q18 imports), `tests/wrappers/test_capstone_routes_{static,tool}.py`, `tests/wrappers/fixtures/verus/cli/`, `docs/Q18_PracticeIIIC.md`, `expected/Q18.chapter.toml` |
| D17 arm G as built | the chapter's §5, solutions, rubric CA.d and D14 | as D10 |
| D18 simulation case g | README's case g | `tests/instructor/simulations/README.md` |
| D19 (other lanes' scratch) | nothing to do; this lane's scratch is removed at the end | — |

`calibrate.py` already covered Q16–Q18 (Δ215: `DEFAULT_MODULES` Q01–Q18, budget 72, tutor
holes Q16.H1d, Q17.H1d, Q18.H1d); this lane changed nothing there and re-ran its self-tests.

## 2. D13 and D14 as decided (no code change)

- **D13.** L7's Verus subtraction stays `big_sub` (Δ209): beside `use vstd::prelude::*;`,
  which every Q16–Q18 file has, a call of `sub` is ambiguous (E0659). QPLAN §19.1 rule 1,
  §19.4's table and its `BigNatCore` row, §19.5's L7 line, §19.6 point 4 and §28.3 step 4 now
  read `big_sub` (§19.4's row gives the reason). Δ209's "the rename awaits the user's
  confirmation" and Δ216 item 4 are closed.
- **D14.** Q16's Verus `no-call:` (Δ210) and `no-adder` (Δ214) stay, with the H3 pair's 55
  admitted minutes (H3v 35, H3d 20). Δ216 item 5 is closed. No file changed.

## 3. DELTAS-ready text (for the integration lane to number and place)

### Δ2xx · The user's decisions D6, D7 and D9–D18 (2026-10-12) in the tree: two exception kinds, the statement route, the binary route, Lab 3's routes and arms — adopted (the user, 2026-10-12; applied by DV5d's decisions lane)
- **Status:** the user's answers to Δ216 items 1, 2 and 4–12 and to the Q18 lane's three open
  choices, applied. **Δ216 items 1, 2, 4, 5, 6, 7, 8, 9, 10, 11 and 12's Claude half are
  closed** (item 3 is D5's, item 12's Qwen half D8's: other lanes). Like Δ195–Δ217, it names no
  answer, no capstone statement and no prediction answer; the detail is in
  `Solutions/plans/DV5d-decisions-notes.md` and the Q15 (§18), Q17 (§13) and Q18 (§16) code
  notes.
- **Change:**
  - **D6, a second exception kind.** `[module.admissible]`'s `exception` accepts
    `"statement-item: <why>"` beside `"short-format band: <why>"`: the learner writes the
    item's statements and a contractor their proof, so a proof's line band does not apply.
    `scripts/check_course_map.py` (`STATEMENT_ITEM_KIND`, `statement_item_problem`) accepts it
    only on an admitted H item whose block is a prose item (`// prose: <name>`) or sits in one
    of the module's agentic files. **Q17.H3d admitted at 35**; Q17's H lines carry 135 of 135.
  - **D7.** **Q18.H1d 25 and H1v 15 admitted** under the short-format band exception (12 and 19
    proof lines; the 40-minute S11 pair line). H1d is "a repair that must hold under a solver
    swap and a seed sweep" in its docstring, the chapter's §3, QPLAN §28 (header, §28.2,
    §28.7) and design §7.5's Q18 row.
  - **D9, the statement route.** `scripts/firsttry.py --empty-body` checks every admitted
    `statement-item` that holds no hole (`statement_route`): its file's CONTRACT names one
    `scripts/specfreeze --against <statements> <file>` line; the reference statements are that
    path's twin and add at least one statement to the shipped file; the reference delivery (the
    file's twin) passes the reference gate with zero holes; and `specfreeze --against` the
    reference statements reports 0 findings on it, the lever freeze included. One summary line
    after the hole gates (`<ID> statement items: n/N pass the statement route`); `--eb-modes`
    names it `STMT`. New reference files `Solutions/research/q18_statements.dfy` and `.rs`.
    **Q18.H2d 12 and H2v 13 admitted** (the capstone round's statements line, 25; the split
    gives QPLAN's per-language totals). `firsttry.sh Q18 --empty-body`: 7/7 holes, 2/2 statement
    items. The hard tier's admitted hole minutes: Dafny 187, Verus 163 (QPLAN's 187 and 163),
    Python 70 (75); Δ216's verifier shortfall is closed.
  - **D10.** Lab 3's Claude arms run harness-executed; Claude Code in a container is not part
    of Lab 3, and step 4c waits until R16 needs agent mode. B2's template, the solutions' B2,
    rubric DI.a, the chapter's §0 and §5 and the two calibration fixtures say so.
  - **D11.** Q15.H1d keeps 8 minutes: its `trigger` form is a tripwire, and rubric C1's reader
    closes padding (Q15 rubric C1). Δ173's **Change** gains the bullet below.
  - **D12.** The S11 pair's 15 minutes stay split Q15.H1d 8 + H1v 7.
  - **D13.** L7's Verus subtraction stays `big_sub`; QPLAN §19.1, §19.4–§19.6 and §28.3 read
    it.
  - **D14, D15.** Q16's Verus `no-call:` and `no-adder` with the H3 pair's 55 minutes, and
    Q17's implemented-trait lint relaxation with H1d's 50, stay as built.
  - **D16, the binary route.** `scripts/gen_units.py` emits one `[[bin]]` target for the
    capstone crate (`CRATE_BINS`: `bignat`, `src/main.rs`) and reports a missing root; the
    learner file `verus/q/q18_practice_iiic/src/main.rs` ships as a stub (a usage line, exit 2),
    holds no item or hole, and is declared in Q18's imports (`check_course_map.py` accepts a
    crate's binary root there). `scripts/vcheck --bin <crate> [-- <args>]`
    (`dvl.verus.run_bin`): the layer chain, the library verified (normal mode, as `--test`) and
    compiled, the binary root compiled by the pinned `verus --crate-type=bin --compile`, the
    binary run once with the arguments, all under the memory cap; cargo never runs. Tests:
    `tests/wrappers/test_capstone_routes_tool.py` (an invented crate builds and its tool prints
    42 for `sum 2 40`) and `test_capstone_routes_static.py`. The chapter's ship step (§1, §4
    step 6) uses it, with a pinned fence of the shipped stub's run (`bin-shipped`). QPLAN §30
    Q59 is built.
  - **D17.** Arm G as Δ215 built it: every `Verify` runs gate v2 on the work copy in the
    verification container, a `Stop` is refused until it passes, the run ends at the first pass
    or its budget, and the outcome is the plain lab gate's verdict in both arms. The chapter's
    §5, the solutions, rubric CA.d and runs-debrief D14 say so.
  - **D18.** Simulation case g grades Q18's flawed fixture as a drop-in with the plain
    `/grade-paper Q18` (the simulations README).
- **Why:** the user's decisions of 2026-10-12; the lane's runs (16 GB scope, one job at a
  time): `firsttry.sh Q18 --empty-body` 7/7 and 2/2, `Q17` 3/3; `check_course_map.py` and
  `--only vocab` OK; `test_course_map.py` 381 passed; `gen_units --check` 37 units match;
  `pins.py --ci` Q15 60, Q17 15, Q18 26 pins, 0 problems; `chapter_lint Q18` 0;
  `update_rubric_pins --check` 111 current; the leak verifier 18 modules, 1,608 public files,
  OK; `vcheck --shipped Q18`, `specfreeze --check Q18`, `reference_lint --module Q18`,
  `--lint-hollow`, `avoid.sh` clean; `make -C paper paper` 36 and `paper-solutions` 18; the
  fixtures compile as drop-ins; `tests/wrappers` 493 OK (1 skipped); the calibration self-tests 16 OK.
- **Touches:** Δ173, Δ206, Δ209–Δ212, Δ214–Δ217; QPLAN §19.1, §19.4–§19.6, §28 (header,
  §28.2, §28.3, §28.7), §30 Q59; design §7.5; `MODULES.toml` (Q17, Q18); `scripts/
  {check_course_map,test_course_map,firsttry,gen_units}.py`, `scripts/vcheck`,
  `scripts/dvl/verus.py`; the Q15, Q17 and Q18 notes; `docs/Q18_PracticeIIIC.md`;
  `expected/Q18.chapter.toml`; `paper/Q18_answers.tex`, `paper/solutions/Q18_solutions.tex`,
  `paper/rubrics/Q15_rubric.md`, `paper/rubrics/Q18_rubric.md`; `tests/wrappers/`,
  `tests/instructor/fixtures/Q18_*`, `tests/instructor/simulations/README.md`;
  `verus/q/q18_practice_iiic/`; `Solutions/research/`.
- **Owner:** the user; applied by DV5d's decisions lane.
- **Open** (owner, severity): the records lane (low): QPLAN §28.2's H2d/H2v cells ("statement
  item · not probed") and §28.6's "Claude in agent mode only if DV4 step 4c's decision allows
  it" (superseded by D9 and D10), QPLAN §30 Q59's disposition line, `CLAUDE.md`'s Not-built
  line (drop the capstone CLI's binary target) and its `vcheck` usage line (`--bin`); the
  tools owner (medium): review the statement route, `run_bin` and the two exception kinds
  with Δ217's group; the kits lane (low): the Q15 chapter could name the `trigger` form a
  tripwire as rubric C1 now does.

**For Δ173's Change (D11), in place, after "The fallback rule":**

  - **Declared band exceptions and tripwire forms** (the user's decisions D2, D6, D7, D9 and
    D11, 2026-10-12). An admitted item outside its line band carries a declared exception,
    `exception = "<kind>: <why>"` in `[module.admissible]`: `short-format band` (its minutes
    line is short by design: Q15.H1d/H1v, Q18.H1d/H1v) or `statement-item` (the learner
    writes its statements and a contractor their proof: Q17.H3d, Q18.H2d/H2v); a statement
    item with no shipped hole takes `firsttry --empty-body`'s statement route in place of the
    empty-body result. Q15.H1d keeps its 8 minutes although its `trigger` form is a presence
    check (a tripwire): rubric C1's `/review-code` reader closes the padding (the user's
    decision D11). (Scoped to Q15.H1d by the DV5d review fix round: D11 names that item only,
    so no general rule for other forms is stated here.)

## 4. Runs and open items

- `scripts/test_course_map.py`: 381 passed, 0 failed (one new case's expected line was fixed
  after a first run that matched the wrong summary line). The full `tests/wrappers` suite:
  493 tests OK (1 skipped; 478 before, 15 new: 12 static, 3 tool), 849 s.
- `tests/ci`: 80 of 81 passed; the failure is the harness tripwire test, whose sterile run of
  `tests/sandbox` fails in another lane's in-progress `tests/sandbox/test_agent_batch.py` (an
  agent-batch form test against `scripts/mksandbox-run`'s message); none of this lane's files
  is involved. Re-run `scripts/ci.sh` once that lane lands.
- Not run: `scripts/ci.sh` (the integration lane's), `firsttry --empty-body` of Q15 and Q16
  (their registries and files did not change), the skill simulations and `calibrate.py all`
  (they call a model).
