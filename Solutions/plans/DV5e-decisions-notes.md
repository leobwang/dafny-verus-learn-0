# DV5e decisions lane: the user's decisions D21–D24 in the tree (as built, 2026-10-13)

> **Author-only.** Records how this lane applied the user's decisions D21–D24 of 2026-10-13,
> what it ran, and the DELTAS-ready text for the integration lane (§4). It names no answer:
> the line counts' detail is in the Q15 notes (§20), the overlap in the Q18 notes (§17) and
> the judging notes (§6), and the probes in the archive.

Authoring worktree, `authoring` @ db398e4 plus the round's working tree (uncommitted; other
DV5e lanes edit other files at the same time). One solver job at a time, each under the
wrappers' caps (Dafny 8 GB, Verus 16 GB) inside `systemd-run --user --scope -p MemoryMax=16G
-p MemorySwapMax=0` (the lane's share), through `/tmp/dvl0-dv5e-decisions/run.sh`, which waits
below 31 GB available (`free -g` showed 96–98 GB available throughout). Three verification
containers ran one at a time (two Dafny at their own 11.5 GB bound, one Verus at `--mem-gb
16`). No job was killed for memory. No model was called. Captures:
`~/.cache/dafny-verus-learn-0/author-probes/dv5e/decisions/`.

## 1. The decisions and where each went

| decision | what this lane did | files |
|---|---|---|
| D21 `hidden-check spec` kind; Q15's five at 18 | new exception kind, validated in the coverage group; five entries admitted | `scripts/check_course_map.py`, `scripts/test_course_map.py`, `MODULES.toml` (Q15) |
| D22 H11's and the Verdict glosses | text only, learner file and twin; tests unchanged and passing; pins re-captured | `harness/q/fvh_q/oracles.py`, `Solutions/harness/q/fvh_q/oracles.py`, `docs/Q15_PracticeIIC.md` (the `py-oracles` fence only, by `pins.py`), `expected/Q15.chapter.toml`, `paper/rubrics/Q15_rubric.md` (the twin's pin, by `update_rubric_pins.sh`) |
| D23 Q18.H1v / Q16.H2v overlap | declared beside the leak README's tier exemption and in the Q18 notes; the item unchanged | `tests/instructor/leak_patterns/README.md`, `Solutions/plans/Q18-code-notes.md` §17 |
| D24 the lab gate applies vaudit's rules | `vcheck --gate --lab-task` runs vaudit's audit on a delivery still verified after the lever check | `scripts/vcheck`, `tests/wrappers/test_practice_tools_{static,tool}.py`, `tests/wrappers/fixtures/{dafny,verus}/lab/` (3 new fixtures + 1 delivery), the fixture READMEs |
| the DV5d notes | the judging notes §6 marked decided; Q15 notes §20, Q18 notes §17 | `Solutions/plans/DV5d-judge-notes.md`, `Solutions/plans/Q15-code-notes.md`, `Solutions/plans/Q18-code-notes.md` |

## 2. As built

### D21

- `ADMISSIBLE_EXCEPTION_KINDS` gains `HIDDEN_CHECK_KIND = "hidden-check spec"`; the registry
  group's message lists the three kinds. The coverage group (where the items are parsed) calls
  `hidden_check_problem(root, m, item)` for each entry of that kind and refuses it unless the
  item is an H item, not in one of the module's agentic files, of one of its exercise files,
  whose block has a `// prose: <name>` line and no `// contractor:` line (that is a statement
  item), whose id is in `HIDDEN_CHECKS_HELD` (the record of judging runs that held; each entry
  cites its DELTAS entry: Q13.H3v, Q15.H3d–H5v and Q17.H3d, Δ220) and whose module has a
  `[[lab]]` with an archive in `sandbox/truth.toml` (`sealed_labs`). The registry-only path
  (`--resolve`, which `vcheck` and the sandbox use) checks the kind's name only, so a
  container without `sandbox/truth.toml` is unaffected.
- `MODULES.toml`: Q15.H3d, H4d, H5d, H3v and H5v `admitted = true, minutes = 18`, each with
  `exception = "hidden-check spec: …"` naming its pcount figures and D21.
- `scripts/test_course_map.py`: `sandbox` joins the linked trees; seven subprocess cases (the
  committed registry's coverage group; refused on a plain block (Q15.H1d), on a prose block
  naming a contractor (Q17.H3d), on an agentic-file item (Q18.H2d), with no sealed truth (an
  overlaid `sandbox/truth.toml`), on a gated item, with no reason) and one in-process unit
  (`_hidden_check_unit`: accepted; refused unrecorded, unsealed, contractor, agentic,
  outside the exercise files, plain, P item; `sealed_labs` on a good, a partial and an
  unreadable file; `exception_kind`). The statement-item "no reason" case's expected message
  now lists the three kinds.
- Minutes: Q15's H items carry 225: S9 27/27, S11 15/15, S12 0/15 (Δ199), Lab 2's prose
  specifications **108/108** (design §7.5's "prose specs 108", QPLAN §25.7's 6 × 18), the
  oracles 75/75.

### D22

- The `Verdict` docstring gains a paragraph (the two lemmas read requires and ensures together
  inside the reference's requires; an added requires the reference's requires and ensures do
  not give narrows the specification and counts as `STRONG`; a dropped requires is not seen);
  STRONG's comment reads "it claims more (correct behaviours fail it) or adds a requires"; the
  `Implication` docstring and one sentence of H11's say the same of each lemma. Both files,
  the same 28 changed lines. No code, test, freeze statement or classification changed.
- The sealed copies: this lane re-sealed nothing. DV5e's Lab 2 public-forms lane re-sealed
  `Hidden/labs/Q15/` afterwards (72 files) with `judge/oracles.py` re-copied from the new twin
  (`6cb4f036…a259`; its notes, `DV5e-lab2pub-notes.md`). Q13's and Q17's archives keep
  `e168aaed…7665d`, whose code equals the new twin's (AST comparison, docstrings removed);
  only comment text differs. VERSIONS.md §1.4's row names `e168aaed…`.

### D23

- The leak README's rule 2 gains a *Declared later-tier overlap* bullet beside the
  exemption: the overlap, why it stands (Q18 after Q16; the learner norms keep later
  modules' files closed), that it is a structural overlap with no answer line (so no pattern
  and no `exempt:` line), where it is recorded, and that a new one is the user's to declare.
  The verifier's code is unchanged.

### D24

- `scripts/vcheck`: `lab_gate(res, task, delivery, audit=None)` runs the lever check as
  before, then, on a result still verified, `audit()`; each finding becomes a `lab-audit`
  finding ("the assumption audit (vaudit) reports <kind>: <message>") and the verdict
  `failed`. An audit that cannot run is a `lab-audit` finding too; an audit run killed by
  memory (its `audit-error` / `audit-incomplete` message says `killed(memory)`) makes the
  result `killed(memory)` with exit code 137, and a wall-clock stop `inconclusive` with 124,
  never a verdict. `lab_audit(t)` is `scripts/vaudit`'s own `audit(t, "learner", None)` (the
  one rule set, loaded as a module: Dafny's `dafny audit` plus the lint; Verus's
  `--no-cheating` audit of the crate and its path dependencies against the trust allowlist plus
  the lint). The CLI always passes it; `audit=None` is the lever check alone (static tests).
  The usage text says so. `specfreeze --lab` stays the static half (no audit). The container
  route needs no manifest change (`scripts/vaudit` and `expected/verus_trust.toml` are staged
  already).
- What D24 changes in practice: Dafny task forms that ship `assume {:axiom}` or an `{:axiom}`
  declaration (the plain gate counts neither; the lever check allows a shipped lever). For
  Verus every shipped assumption form probed (`external_body`, `assume`, `admit`,
  `#[verifier::external]`, `exec_allows_no_decreases_clause`) already fails the gate (holes
  under `--no-cheating`, or the lint), so D24 is a second check there.

## 3. Runs (this tree)

| run | result |
|---|---|
| `check_course_map.py`; `--only vocab` | OK (49 modules, 18 authoring, 138 import files, 81 coverage rows); vocab OK (18 banks) |
| `test_course_map.py` | **390 passed, 0 failed** (382 before; 8 new) |
| `firsttry.sh Q15 --empty-body` (16 GB) | **18/18** hole(s) pass the gate, exit 0 (the five admitted items: client gate and prose proof gate ✓) |
| `vcheck --ref --gate Solutions/harness/q/fvh_q/oracles.py` | verified — 26 passed, 0 failed, 0 holes (the H11/H12 tests unchanged) |
| `vcheck harness/q/fvh_q/oracles.py` (shipped) | failed — 1 passed, 25 failed, 4 holes (as before) |
| `specfreeze --check Q15` | 0 findings |
| `pins.py --update --chapter Q15 --entry py-oracles`; `pins.py --ci --module Q15` | captured (7 fence lines, exit 1); 60 pins, 0 problems |
| `update_rubric_pins.sh` then `--check` | 1 written; all 111 current |
| `chapter_lint Q15`; `reference_lint --module Q15` | 0 problems (26 pinned fences); 0 findings (12 twins) |
| the leak README's verifier; `avoid.sh`; `check_single_route.py` | OK (18 modules, 1,631 public files at the last run); OK (Q 1,961 declarations, 0 hits); 0 outside the allowlist |
| fixture probes, lab gate before / after (scratch root) | `kept.dfy` verified / verified; `axiom_task.dfy` delivered unchanged verified / **failed** (2 `lab-audit`); `axiom_lemma_task.dfy` verified / **failed** (2); `kept.rs` verified / verified; `external_task.rs` failed / failed (1 hole) |
| the course's lab references through the new lab gate (scratch root) | Lab 1's 22 and Lab 2's 20 reference deliveries: 42/42 verified (67.8 s; 48.2 s before); Lab 3's 8 possible references 8/8 verified (96.3 s; 36.8 s before), the 4 impossible tasks as shipped 4/4 failed (holes) |
| verification containers (`ContainerRunner`, lab gate) | Lab 1 dh4's reference verified; a scratch task form shipping `assume {:axiom} false;` delivered unchanged failed (2 `lab-audit`); Lab 3 c01's reference crate verified (`--mem-gb 16`) |
| `tests/wrappers/test_practice_tools_static.py`; `…_tool.py` | 39 OK (7 new); 12 OK (4 new) |
| `scripts/ci.sh --job wrappers --job harness` (study run, log `/tmp` scratch, archived) | `ci.sh: PASS — 2 passed, 0 failed, 0 skipped, 0 absent, in 2103 s`: `tests/wrappers` 512 OK (1 skipped), `tests/ci` 81 OK; `harness/tests/core` 549 passed, the adapter suite 50, `tests/sandbox` 171, `tests/bench` 57 (16 author-only steps skipped, as in every study run) |

## 4. DELTAS-ready text (for the integration lane to number)

### Δ2xx · The user's decisions D21–D24 (2026-10-13): the hidden-check spec kind and Q15's five prose specifications admitted, the oracles' glosses, a declared later-tier overlap, the lab gate's assumption audit — adopted (the user, 2026-10-13; applied by DV5e's decisions lane)
- **Status:** the user's answers to Δ224's four items (D21 item 1, D22 item 2, D23 item 3, D24
  item 4), each the recommended option. Δ224 is settled in full. Like Δ195–Δ225, it names no
  answer. Detail: `Solutions/plans/DV5e-decisions-notes.md`, the Q15 (§20) and Q18 (§17) code
  notes and the judging notes (§6).
- **Change:**
  - **D21, a third exception kind.** `[module.admissible]`'s `exception` accepts
    `"hidden-check spec: <why>"`: a prose specification below its band whose grade is its hidden
    check in the grader container, not a proof's lines. `scripts/check_course_map.py`
    (`HIDDEN_CHECK_KIND`, `hidden_check_problem`, `HIDDEN_CHECKS_HELD`, `sealed_labs`) accepts it
    only on an admitted H prose item of one of the module's exercise files that names no
    contractor, whose hidden check is recorded as holding (`HIDDEN_CHECKS_HELD`, each entry
    citing its DELTAS entry: Δ220's Q13.H3v, Q15.H3d–H5v, Q17.H3d) and whose module's sealed
    truth `sandbox/truth.toml` pins. **Q15.H3d, H4d, H5d, H3v and H5v admitted at 18 each**
    (pcount: 0, 0, 0, 7 and 0 proof lines). Q15's Lab 2 prose line carries 108 of 108 (design
    §7.5, QPLAN §25.7); the module's H items 225 of 240 (S12's H2 pair stays gated, Δ199).
  - **D22.** The `Verdict` docstring and its STRONG comment, the `Implication` docstring and
    H11's docstring (`harness/q/fvh_q/oracles.py` and its twin) say the reading as built: the
    two lemmas read a specification's requires and ensures together inside the reference's
    requires, so an added requires narrows it and counts as `STRONG`, and a dropped one is not
    seen. Text only: the tests, the formula and the freeze are unchanged. Q15's archive,
    re-sealed afterwards by the Lab 2 public-forms lane, carries the new twin; Q13's and
    Q17's sealed `judge/oracles.py` keep the old comment text (their code is the twin's).
  - **D23.** Q18.H1v's shipped `cast_out` states the domain of the invariant Q16.H2v asks for:
    a declared later-tier overlap (no answer line), recorded in the Q18 notes (§17) and beside
    the leak README's tier exemption (rule 2). The item does not change.
  - **D24, the lab gate's assumption audit.** `scripts/vcheck --gate --lab-task` runs, after
    the lever check and on a delivery still verified, `scripts/vaudit`'s audit of the delivery
    (learner mode, the default trust allowlist; `lab_audit`): each finding is a `lab-audit`
    finding and the verdict `failed`, so a delivery equal to a task form that ships `assume
    {:axiom}`, or a lever the lever check allows but the audit reports (an `{:axiom}` lemma),
    does not pass; an audit killed by memory is `killed(memory)` (137) and one stopped by the
    wall clock `inconclusive` (124), never a verdict. `specfreeze --lab` stays the static half.
    The container route stages `scripts/vaudit` already. Closes Δ221's probe finding for any
    later task source; the course's pools were already closed by the transform and the pool
    rule.
- **Why:** this lane's runs (16 GB scope, one job at a time; archive `dv5e/decisions/`):
  `check_course_map.py` and `--only vocab` OK; `test_course_map.py` 390 passed; `firsttry.sh
  Q15 --empty-body` 18/18; the oracles twin's frozen tests 26 passed; `specfreeze --check Q15`
  0; `pins.py --ci --module Q15` 0 problems after the `py-oracles` re-capture;
  `update_rubric_pins.sh --check` 111 current; `chapter_lint Q15` and `reference_lint --module
  Q15` 0; the leak verifier OK; the lab gate before and after on invented fixtures (two Dafny
  shipped-assumption forms pass before and fail after; clean deliveries pass in both
  languages; a Verus shipped `external_body` fails in both), on the course's 42 Lab 1–2 and 8
  Lab 3 reference deliveries (all verified after; Lab 3's 4 impossible forms fail) and in
  three verification containers; `scripts/ci.sh --job wrappers --job harness` PASS
  (`tests/wrappers` 512 OK with 1 skipped, `tests/ci` 81, `harness/tests/core` 549 passed).
- **Touches:** Δ173, Δ197, Δ199, Δ215, Δ218, Δ220–Δ225; QPLAN §25.2, §25.7–§25.8 (**As
  built**), §30 Q63; design §7.5 (no change: it already reads 108); `MODULES.toml` (Q15);
  `scripts/{check_course_map,test_course_map}.py`, `scripts/vcheck`;
  `harness/q/fvh_q/oracles.py` and its twin; `docs/Q15_PracticeIIC.md` (one pinned fence),
  `expected/Q15.chapter.toml`, `paper/rubrics/Q15_rubric.md` (a pin);
  `tests/instructor/leak_patterns/README.md`; `tests/wrappers/`; the Q15, Q18 and judging
  notes.
- **Owner:** the user; applied by DV5e's decisions lane.
- **Open** (owner, severity):
  - **The records lane (low).** QPLAN §25.2's prose-specs row and the §25 **As built** note
    (the five admitted at 18 under `hidden-check spec`), §30 Q63 (the lab gate's audit);
    `CLAUDE.md`'s **Armed** line ("the minutes of Q15's five below-band prose specifications
    await the user") and its `vcheck --gate` usage; `VERSIONS.md` §1.4's oracles row (it names
    `e168aaed…`: Q15's archive now carries `6cb4f036…`, Q13's and Q17's the old text); the STRATUM headers'
    lab-gate sentence (`bench/local/q/lab1/STRATUM.toml`, `lab2/STRATUM.toml`: "the done gate
    plus the lever check" now also runs the assumption audit); DV4-PLAN's lab-gate lines.
  - **The kits lane (low).** Bank Q15's K-probe insight on the two lemmas (it glosses
    `RefImpliesSpec`'s failure as "forbids an output the reference allows", which an added
    requires also fails, and says Q13's hidden check is "the same pair": the grader's prose
    check is the four-lemma refinement); the chapter's and the prose files' "pending" sentences
    (Δ225's item, unchanged).
  - **The judging owner (low).** At the next re-seal of `Hidden/labs/Q13/` and `Q17/`, copy the
    oracles twin again (`6cb4f036…a259`; Q15's archive already carries it).
