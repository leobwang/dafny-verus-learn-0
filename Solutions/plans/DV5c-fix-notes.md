# DV5c review fix round: notes (author-only)

> **Author-only.** The fix lane's record of the four DV5c reviews (leakage, tool claims,
> admission, harness): each finding reproduced or rejected, the fix, the re-runs, and the
> DELTAS-ready text for the records lane. Never quote it from a learner-visible file.

Working tree: `authoring` @ 5e5d3ee plus the DV5c lanes' uncommitted work (study mode, as
found). Solver jobs one at a time through the wrappers, inside a 32 GB
`systemd-run --user --scope -p MemoryMax=32G -p MemorySwapMax=0` (lane runner
`/tmp/dvl0-dv5c-fix/run.sh`; archive `~/.cache/dafny-verus-learn-0/author-probes/dv5c/fix/`).
One static suite (`test_tools_static`) ran a short `vcheck Q18` beside the Q13 empty-body
job; host memory stayed above 90 GB available.

## 1. Findings and outcomes

| # | finding | severity | reproduced | outcome |
|---|---|---|---|---|
| L1 | plaintext of sealed truth and twins in lane scratch under /tmp | major | yes (paths listed by the review exist, world-readable) | **partly fixed**: guard rule 1 names `/tmp/dvl0-dv…` (tripwire), the simulations refuse to set up while lane scratch exists; this lane's scratch archived and removed. Other lanes' scratch is not this lane's to delete: the orchestrator removes it or reboots (open issue) |
| L2 | bank Q16.K7 hands over H2v's suffix-step lemma; K7's insight quotes H3d's assertion | major | yes | **fixed**: K7 rewritten (prefix identity, `Cairn`), re-captured; fields unchanged (`check_draws.py` OK); a leak pattern retargeted to the suffix-step ensures; verifier OK |
| L3 | Q18 rubric IS.b names the measure | minor | yes | **fixed**: IS.b is a predicate; pins current; the flawed fixture's IS.b finding still needs Probe X |
| C1 | Q18.H1d framed as a solver-swap flip the shipped file never shows | major | yes (11 pasted variants, all six rows `failed`) | **fixed (option b)**: docstring, chapter §0/§3, Q09/Q15 forward pointers say it may fail every row; no flipping proof found |
| C2 | the plant is of agent provenance (container), not host | major | yes (`provenance_of`: fixture `course`, copy `agent`) | **fixed**: chapter, gate_v2 (learner + twin) docstrings, rubric D10 |
| C3 | `--brittleness` without `--solvers` is one solver | minor | yes (vcheck usage) | **fixed**: Q17 table, Q18 §6 |
| C4 | PCell moves values through more than take/put | minor | yes (vstd 0.0.0-2026-09-20-0158 lists `replace`, `write`, `read`, `borrow`, `borrow_mut`, `into_inner`) | **fixed**: Q17 chapter and H2v docstring |
| C5 | `fvh report Q18 --reverify` lacks its argument | minor | yes | **fixed** (`--reverify all`) |
| C6 | Q18 solutions claim an unrecorded plant message | minor | yes (no plant probe archived) | **fixed** by rewording (no verifier claim); no Verus plant run |
| A1 | `loop-dir` reads only the counter | major | yes (both variants static `True`) | **fixed (option a, within D4)**: `loop-dir` reads indices and needs the computing loop; variants are twin `cfree:` lines; Q13 7/7, Q14 7/7; 20 and 13 kept |
| A2 | Q16.H3v copied adder passes | major | yes (static `True`) | **fixed (option a)**: form `no-adder`, `cfree-decl:` mechanism; Q16 4/4; 35 kept |
| A3 | Q13.H5d compiled `ToNat` + dummy loop | major | yes | **fixed**: `no-call:ToNat` (bare lemma calls exempt); cfree lines 3–4 |
| A4 | Q18.H1d decision rests on an unmet premise | major | yes (as C1) | **fixed**: Q18 notes §14 item 1 amended; H1d stays false/0 |
| A5 | padding passes presence forms | minor | yes (static) | **fixed for `loop-dir`** (named and unnamed: the computing-loop rule; Q16.H2v and H3d padded variants are twin `cfree:` lines); **`trigger` (Q15.H1d): DECISION NEEDED** |
| A6 | pcount `in_clause` leak | minor | yes (`mul` 68) | **fixed**: `mul` 66 from the tool; test added; Q16 notes updated; Q17's other hand corrections remain counter gaps |
| H1 | overage stop not sticky | major | yes (review probe) | **fixed** |
| H2 | resume skips drift | major | yes | **fixed** |
| H3 | Ollama version and unit never compared | major | yes (no code read them) | **fixed** |
| H4 | secret scan covers only the transcript | major | yes | **fixed** |
| H5 | a lab plan can turn off the lever check | major | yes | **fixed** |
| H6 | a gate that cannot start burns re-issues | major | yes | **fixed** |
| H7 | fvh state dirs not in the guard, never reaped | minor | yes | **fixed** |
| H8 | `--materialize --truth` keeps a key copy | minor | yes (by code; not re-run, it would copy the key again) | **fixed** |
| H9 | reverify reports an unverified last edit as a difference | minor | yes | **fixed** |
| H10 | a call without an event inherits the last one | minor | yes | **fixed** |
| H11 | ledger undercounts spent calls and GPU-seconds | minor | yes | **fixed** |
| H12 | `resume --dry-run` ignores the plan's max_reissue | minor | yes | **fixed** |

No finding was rejected.

## 2. What changed (by area)

**Forms** (`scripts/dvl/forms.py`, `scripts/firsttry.py`; tests `tests/wrappers/test_forms_static.py`
59 OK).
- `loop-dir` (D4's rule, extended): each checked loop's body reads every index (`s[e]`,
  slice bounds, `v@[e]`, the index arguments of `.subrange`/`.skip`/`.take`/`.update`/`.set`/
  `.index`) with each body-assigned identifier only as an added term (one-definition locals
  read through their definition); none subtracted, in a product, call or size; a stepping
  identifier there steps the wanted way. At least one checked loop reads an argument of the
  item at an index that adds its counter and assigns (or mutates) an identifier the result is
  computed from (Dafny named results; Verus tail and `return`s, closed under direct
  declarations and assignments).
- `no-call` (Dafny): the arguments of a bare call statement (`L(…);`, a lemma or method call)
  are no compiled use.
- `no-adder` (Verus, new): no exec helper the block reaches states `A == B + C` over value terms
  (`.to_nat()`, `seq_to_nat(…)`) in an `ensures` clause.
- `// cfree-decl:` lines (twin-only, new): declarations a run of `cfree:` answers adds; firsttry
  puts them below the last `// HELPERS` line above the block (`body_variant(…, decls=)`); the
  hollow lint refuses them in learner files.
- Items: Q13.H5d `form: loop-dir:up, no-call:ToNat` (prompt states the ToNat rule), cfree 2–4;
  Q14.H3v cfree 2 (prompt: each limb read at an index that counts with `i`); Q16.H2v cfree 2;
  Q16.H3d cfree 2–3; Q16.H3v `form: …, no-adder`, cfree 2 with its `cfree-decl:` helper.
- Static diff over every twin block with forms (28 items): only the intended results moved.

**Counter** `scripts/pcount.py`: a clause ends with its statement's `;` and with its proof block.

**Banks, leak, rubric, chapters**: Q16 bank K7; `tests/instructor/leak_patterns/Q16.txt` (and its
README row); rubrics Q13 A5/C4, Q14 A5/A7/C5, Q16 A5/C4/C5, Q18 IS.b/D10; chapters Q13 §4,
Q14 §2/§4, Q16 H3v/§4 row, Q17 S8 and instruments table, Q18 §0/§3/§4/§5/§6, Q09 and Q15
forward pointers; learner files Q13 (form line, H5 prompt), Q14 (H3 prompt), Q16 (form line),
Q17 `perm.rs` (H2 prompt), Q18 (H1 docstring), `gate_v2.py` (docstring); twins alike; Q18
solutions (e).

**Guard and simulations**: `.claude/hooks/spoiler-guard.sh` (RX_SPOIL_DIR `/tmp/dvl0-dv…`;
RUNSTATE `fvh-claude-state`, `fvh-qwen-state`; rule 1's message), five must-block and one
must-allow template line (`scripts/test_hooks.sh` 6,754 passed, 0 failed);
`scripts/dvl/sandbox.py` class_drift skips host paths outside the checkout;
`tests/instructor/simulations/skill_sims.py` `lane_scratch()` precondition (+ test, README).

**Harness** (frozen core; `harness/tests/core` 506 passed, sterile and not):
- `fvh.backends.claude`: an ApparatusMismatch after the CLI ran carries `ran`, and an overage
  stop `overage` and the call's event; a call without its own event stops
  (`budget.OverageWatch`). `fvh.backends._call` charges the meter for a call that ran.
- `fvh.batch`: overage stop persisted (window file, sticky `overage-stop` note; `open()`,
  `_window_ok` and resume refuse until `resume --after-overage-check` writes
  `overage-cleared`); the transport or gate failing to start is `apparatus-mismatch` (stops);
  live Qwen batches check the model server before the first attempt; stale per-call state
  reaped; every run-dir file secret-scanned and withheld with name/size/sha256 (gate log after
  the gate stops; reconcile scans too); a lab plan refuses `lever_check = false`; reconcile
  records calls and GPU-seconds; resume checks the apparatus file's sha256 against the
  batch-plan note (`--new-apparatus` records a change), drift, and the registry budget for
  re-issues; `return_summary.files_sha256` recorded.
- `fvh.backends.gate`: `server_facts`, `server_drift` (version, digests, unit environment).
- `fvh.budget`: `Ledger.used` counts calls of infra-failed/deferred moves; `notes`,
  `overage_stop`. `fvh.executor`: each verdict document carries `files_sha256`.
- `fvh.report`: reverify reports "nothing comparable" for a run whose last edit was never
  verified (a returned/ changed after writing is still re-verified); disclosure lines (lab runs
  without the lever check, several apparatus files, withheld files, overage and apparatus notes).
- `fvh.__main__`: run checks the server for a Qwen plan; resume runs the drift check, takes
  `--after-overage-check` and `--new-apparatus`, and its dry run uses the plan's max_reissue;
  `apparatus --check` adds the server drift.
- `scripts/mksandbox-run`: `--truth` refuses `--materialize` and `--selftest-only`
  (`tests/sandbox` 126 OK).

## 3. Runs on the final files

`firsttry.sh --empty-body`: Q13 7/7 (1,291 s), Q14 7/7 (206 s), Q16 4/4 (92 s), Q18 7/7 (168 s);
twins `--ref --gate` and `--ref --brittleness` (Dafny `--solvers`): Q13 137, Q16 141, Q18 136,
Q14 18, Q16 15, Q17 8, all verified and stable; `pins.py --ci --module` Q09 64, Q13 11, Q14 18,
Q15 60, Q16 7, Q17 15, Q18 25 pins, 0 problems (units pins of Q13, Q14, Q16, Q17, Q18
re-captured first); `update_rubric_pins.sh --check` 111 current (7 re-pinned);
`specfreeze --check` Q13, Q14, Q16, Q17, Q18 0; `vcheck --shipped` the same five 0;
`chapter_lint --all` 18 chapters 0; `firsttry --lint-hollow --all` OK; `reference_lint` 0;
`check_course_map` OK; `check_single_route` 0 outside the allowlist; leak verifier Q13, Q14,
Q16, Q18 OK (1,595 public files); `check_draws.py` OK; static wrapper suites 317 OK;
`test_skill_sims` 16 OK. Not run: `tests/wrappers` tool suites, `tests/ci`, `scripts/ci.sh`,
the by-hand `guard_doors.py all` (the guard changed: required before the merge, Δ107).

## 4. DELTAS-ready text (for the records lane to number)

**Δ2xx · The DV5c review fix round: the loop-direction form completed, `no-adder` and
`cfree-decl:`, bank K7, Q18.H1d's framing, the batch runner's overage, drift, server, scan and
budget checks, and the lane-scratch tripwire — adopted (DV5c, 2026-10-12)**
- **Status:** four reviews of the DV5c round (leakage, tool claims, admission, harness) raised
  29 findings (0 blocker, 15 major, 14 minor); the fix lane reproduced all 29 and fixed 27 in
  full, one in part (the other lanes' scratch) and left one to the user (Q15.H1d's trigger
  padding). Like Δ195–Δ205 it names no answer; the detail is in
  `Solutions/plans/DV5c-fix-notes.md`, the Q13 notes §13, the Q14 notes §14, the Q16 and Q18
  notes, and the archive `dv5c/fix/`.
- **Change:**
  - **D4's form, completed.** `loop-dir` also reads each checked loop's indices (an index adds
    the counter, never subtracts it or computes it otherwise, through one-definition locals)
    and needs one checked loop to read an argument at its counter and assign what the result
    is computed from. `no-call` exempts a bare call statement's arguments. Q13.H5d gains
    `no-call:ToNat`. New twin `cfree:` answers: Q13.H5d (reversed index; compiled `ToNat`; the
    same with a dummy loop), Q14.H3v (reversed index through a `let`), Q16.H2v and Q16.H3d
    (padding). `firsttry --empty-body` Q13 7/7, Q14 7/7, Q16 4/4: every known construct-free
    answer fails, so Q13.H5d 20, Q14.H3v 13, Q16.H3d 20 stand under Δ173.
  - **`no-adder`** (Verus): a helper of the learner's that states a whole-number sum in its
    `ensures` is refused; Q16.H3v carries it, and its copied-adder answer is a twin
    `cfree:` answer with **`// cfree-decl:`** lines (new, twin-only: declarations an answer
    adds, placed below the file's HELPERS line). Q16.H3v keeps 35.
  - **The forms are tripwires** where they read code shape: an index computed through a helper
    or another sequence, an inlined row addition, a sum stated another way, and `trigger`'s
    presence check are left to the rubric's reader (Q13 C4, Q14 C5, Q16 C4/C5); Δ173's "every
    known `cfree:` fails" is checked for every recorded answer.
  - **`scripts/pcount.py`**: a clause ends with its statement and with its proof block (Q16
    `mul` 66 from the tool). Remaining counter gaps (hand-corrected in the Q17 notes): a ghost
    predicate's body, ghost field updates and multi-line assertion continuations tagged as code.
  - **Q18.H1d** is retitled "a repair that must hold under a solver swap and a seed sweep";
    docstring and chapter say the delivered proof may fail in some rows or all of them (11
    pasted variants failed every row). The S11 flip is shown by the pace sweep, bank K3 and
    H1v. H1d stays 0 pending the user's decision (Q18 notes §14 item 1, amended).
  - **Text:** Q16 bank K7 (a prefix identity; its fields unchanged, draws OK) and one Q16 leak
    pattern retargeted to H2v's suffix-step helper; Q18 rubric IS.b (no measure named) and D10,
    the plant's provenance (chapter, gate v2, D10: the copy's instruments run in the
    verification container), `--solvers` (Q17, Q18 §6), PCell's API (Q17), `--reverify all`
    (Q18), Q18 solutions (e).
  - **The batch runner** (frozen core): a sticky overage stop (`overage-stop` note, cleared by
    `fvh resume --after-overage-check`); every call without its own `rate_limit_event` stops; a
    call that ran counts against the meter and the ledger; a transport or model gate that does
    not start is `apparatus-mismatch`; a live Qwen batch, `fvh run` and `fvh apparatus --check`
    compare the model server's version, digests and unit settings with the pins
    (`fvh.backends.gate.server_drift`); `fvh resume` checks drift and the batch's apparatus
    file (`--new-apparatus` notes a change) and refuses re-issues past the registry budget;
    `Ledger.used` counts calls spent by infra-failed or deferred attempts; reconcile records
    calls and GPU-seconds; every file of a run directory goes through the secret scan
    (withheld: name, size, sha256); a lab plan cannot turn off the lever check; reverify does
    not report an unverified last edit; stale per-call state is reaped; the report discloses
    lever-less lab runs, several apparatus files, withheld files and the ledger's notes.
    `mksandbox-run --truth` refuses `--materialize` and `--selftest-only`.
  - **The guard** (rule 1, a tripwire, never OS isolation): `/tmp/dvl0-dv…` (author lane
    scratch) and rule 1e's `fvh-claude-state`, `fvh-qwen-state`; `skill_sims.py setup` refuses
    while lane scratch is on the host.
- **Why:** each finding reproduced on the pins before its fix (Q13 notes §13 and this file §1).
- **Touches:** Δ148, Δ173, Δ182, Δ191, Δ195–Δ205 and the D1–D4 entry; `scripts/dvl/forms.py`,
  `scripts/firsttry.py`, `scripts/pcount.py`, `scripts/dvl/sandbox.py`, `scripts/mksandbox-run`,
  `.claude/hooks/spoiler-guard.sh`, `tests/hooks/templates/`, `harness/fvh/{batch,budget,
  executor,report,__main__}.py`, `harness/fvh/backends/{__init__,claude,gate}.py`, the tests,
  the Q13, Q14, Q16, Q17, Q18 files above, `expected/Q13`–`Q18.chapter.toml` (units),
  `paper/rubrics/Q18_rubric.md` pins.
- **Owner:** this round's fix lane; the open items' owners.
- **Open** (owner, severity):
  - **The orchestrator (high: before any study-clone simulation).** Remove the other lanes'
    scratch (`/tmp/dvl0-dv5b-*`, `/tmp/dvl0-dv5c-*` except a running lane's), or reboot; the
    simulations now refuse while it exists.
  - **The user (medium).** Q15.H1d's `trigger` padding (DECISION NEEDED in the round's report);
    Q18.H1d's admission (Q18 notes §14 item 1, amended).
  - **The guard owner (high: before the merge).** `python3 tests/acceptance/guard_doors.py all`
    (the guard changed, Δ107).
  - **The integration lane (high).** `scripts/ci.sh --author` and `scripts/ci.sh` on the final
    tree (this lane ran the touched modules' gates and the static suites only).
  - **DV4 (low).** The secret scan's fallback form (the exact token value the run was given,
    DV4-PLAN §5.7) is not built.
