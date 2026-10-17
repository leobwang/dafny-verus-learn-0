# DV6 audit lane: infrastructure and course level (author-side notes)

Scope: spec §12.1 "Infrastructure (Phase 0)" and "Course level", checked against the
authoring worktree at HEAD 83531a8 (branch `authoring`). Read-only except this file. Memory
share 2 GB, so this lane ran no solver jobs: solver evidence is cited from the green author
CI run `build/ci/20261014T004859Z-3125743/` (`summary.txt`: 14 passed, 0 failed, 16,918 s).
That run's header says "authoring @ db398e4, 68 uncommitted change(s)". No tracked file has
an mtime later than the run's start (2026-10-13 19:48:59 -0500; checked with
`git ls-files | find -newer`), so the run covers the tree committed as 83531a8. While this
audit ran, the D26 lane was editing `CLAUDE.md`, `README.md`, `scripts/{course_mode.sh,
firsttry.py,pins.py,vcheck,test_hooks.sh}`, `.claude/skills/review-code/SKILL.md` and
`expected/README.md`. Every finding below is about HEAD plus the CI run, not those edits.

Scratch: `/tmp/dvl0-dv6-audit-infra/` (removed at the end). Nothing was archived: the probes
are reproduced in full below.

## A. Lines verified as holding (for the release checklist)

### Infrastructure (Phase 0)

1. **Toolchain pinned, VERSIONS.md rows dated, CI asserts versions and sha256.** HOLDS.
   - `VERSIONS.md` §1.1 and §1.2 have dated rows for the Dafny 4.11.0 zip sha256, its tree
     digest, the binary sha256, the bundled Z3 4.12.1 and 4.14.1, the Verus release
     0.2026.09.27.3cf1832, Z3 4.16.0, Rust 1.98.1 and vstd `=0.0.0-2026-09-20-0158`.
   - All 25 `verus/**/Cargo.toml` vstd lines read `vstd = "=0.0.0-2026-09-20-0158"`.
   - `scripts/get_toolchain.sh --check` checks the tree digest, the pinned `--version`
     outputs (lines 271-284) and rustc (line 248).
   - CI: `verify-q-dafny.log:4-7` and `verify-q-verus.log:4-5` show
     `get_toolchain.sh … --check`, "verified", exit 0.
2. **Clean clone builds the default target green in minutes; `make -C paper paper` fails
   on an empty set.** PARTLY HOLDS.
   - `paper/Makefile` refuses an empty set and an unpaired file.
   - `paper.log`: "built 36 document(s)", exit 0. That run took 0 s: the PDFs were already
     up to date (they are gitignored), so it compiled nothing. The only include is
     `\input{preamble}`, which is a declared dependency, so make's up-to-date check is
     sound.
   - The clean-clone half is the dry-run lane's run.
3. **Default target is learner exercises only; reference built by name only; checker
   enforces the list.** HOLDS.
   - `static.log`: "gen_units: 37 unit(s) and verus/Cargo.toml match the registry".
   - The checker's `files` group forbids reference paths.
   - Reference builds happen only through `vcheck --ref <path>` in [A] steps.
4. **`MODULES.toml` + `check_course_map.py` (all groups) + regression tests run first in
   CI; the registry names no reference path.** HOLDS.
   - `static.log:8-15`: "course map OK: 49 modules (33 Q, 16 R; 0 shipped, 18 authoring,
     31 planned)", then "test_course_map: 396 passed, 0 failed".
   - `static` is the first job. Re-run by this lane on the live tree: the same OK line.
5. **Every skill's Step 0 resolves through the registry.** HOLDS.
   - Each of the 7 `SKILL.md` files (contract, discuss, grade-paper, review-code, tutor,
     viva; review on demand) has exactly one `check_course_map.py --resolve` step 0.
   - `--resolve Q01` returns the JSON record.
6. **`vcheck`, `vaudit`, `specfreeze`, `pins.py`, `firsttry.sh` exist; locations, not
   content.** HOLDS.
   - All five are present in `scripts/`.
   - The location-only rule is covered by `tests/wrappers/test_tools_{static,tool}.py` and
     `test_dafny_common.py`. `wrappers.log` passed.
7. **Guard: four layers.** HOLDS, except for the gap in B1.
   - The 4 canonical and 4 always-on deny rules are in `.claude/settings.json`.
   - The hook header lists rules 1/1b/1c/1d/1e/1f/2/2c/2s/2f/2g (lines 23-232).
   - `CORE.md:26-34` has MAY / MAY NOT.
   - Leak README verifier: "18 modules over 1,631 public files, OK". This comes from the
     DV5e integration draft (`~/.cache/…/author-probes/dv5e/integ-attempt1/d233.md`, line
     7), not yet in DELTAS.
8. **`test_hooks.sh`: must-block/must-allow with rule attribution and every §7.2 side
   channel, in the study, jq-free, stand-down and still-armed passes.** HOLDS, with the
   minor gap in B7.
   - `hook-test.log`: the sections "study mode", "jq-free parser", "authoring mode stands
     down in a linked worktree", "ignored outside git / in a primary worktree / on a
     leobwang-* branch", "course_mode.sh", "review-due.sh", "settings.json and the IDE
     pins". Result: "6806 passed, 0 failed".
9. **`course_mode.sh` refuses authoring outside a linked, non-learner worktree, moves both
   layers; CI fails on a shipped mode file or a missing canonical rule.** HOLDS.
   - `scripts/course_mode.sh:24-28,105-120`.
   - `static.log:5`: "study mode shipped: yes (0 problem(s); checked the working tree and
     HEAD, 4 canonical and 4 always-on rules)".
   - `scripts/course_mode.sh status` on the worktree today reports "mode: STUDY" with all
     8 deny rules.
10. **A fresh study session is demonstrably denied …; refusal texts captured for module 1.**
    HELD ONLY AT AN OLD HOOK (B2).
    - The last `guard_doors.py` run was 2026-10-04, hook `a2883993…`, CLI 2.1.289, 10/10
      (`tests/acceptance/README.md:48-50`). The hook is now `0a1c2b63…`.
    - The Q01 chapter's quoted rule 1b text (`docs/Q01_Hello.md:709`) still equals the hook
      message at `spoiler-guard.sh:2245`.
11. **SessionStart banner: due reviews, stale allowlist, authoring mode.** HOLDS.
    - `.claude/hooks/review-due.sh:18-36` prints the three banners.
    - The `review-due.sh (SessionStart)` section of `test_hooks.sh` passes.
    - The ledger path and `due:` format match `CORE.md:125-130`.

### Course level

12. **Role ladder end to end; artifact-based acceptance; one known-good transcript.**
    - Artifact-based acceptance HOLDS. Each of the 22 agentic files (20 A items, plus
      `tools/Q12/holecount.py` and `tools/Q15/toolsmith.py`) opens with the CONTRACT block
      on line 1 and machine-checkable `acceptance:` lines.
    - The agent twins pass the [A] reference gate and audit (`verify-q-dafny.log:85-88`,
      `verify-q-verus.log:85-88` and the following lines).
    - The ladder's rungs are all in the registry: Q01, Q02, Q04-Q09, Q12, Q15, Q17 and Q18
      have `contract`. Q03 has `agentic = []`, so `/contract Q03` refuses by design
      (simulation case f, `tests/instructor/simulations/README.md:54`).
    - Contract v0/v1/v2 are written by hand: `docs/Q03_FirstSyntaxII.md:959`,
      `docs/Q09_InternalsIII.md:828`, `docs/Q18_PracticeIIIC.md:548`.
    - Known-good transcripts: see B3. Only Q07.A2d has one.
13. **Contract v0/v1/v2 slots in CLAUDE.md below the learner marker, fallback rules
    above.** HOLDS.
    - The fallback rules are at `CLAUDE.md:87-96` and the marker at line 98.
    - The slots Q-v0/v1/v2 and R-v0/v1/v2 are at lines 106-116.
14. **Continuity pass.** NO ARTIFACT (B6).
15. **Clean-clone dry run.** Not run yet: it is the dry-run lane's job.
16. **Brittleness (CV gate).** NOT RUN course-wide (B4).
17. **CI never calls a model, never runs on the learner branch, never prints reference
    content.** HOLDS.
    - `ci.sh:150-152` excludes `guard_doors.py`.
    - `harness.log`: sterile env with `-u CLAUDE_CODE_OAUTH_TOKEN -u ANTHROPIC_API_KEY`,
      tripwire shims, "549 passed".
    - `check_single_route.py`: 34/34 allowlisted.
    - `--author` refuses on `leobwang-*` (`ci.sh:296-298`). This follows Δ67's reading of
      the learner-branch rule ("ci.sh is never run on the learner branch by an authoring
      session").
    - Every [A] step's output is redirected: `verify-q-dafny.log` has 102 reference
      commands and 102 "(output: ~/.cache/…)" lines; `verify-q-verus.log` 84/84; the
      empty-body, harness, pins, paper, rubric and static [A] steps likewise.

### Readiness probe for the freeze (not a checklist line)

- The registry keeps Q01-Q18 at `status = "authoring"`. The shipped-only checks only run
  for `shipped`: every path exists, a statement pin of PENDING is an error, bank sizes, a
  tier viva's banks.
- Probe: a scratch root of symlinks with MODULES.toml copied and Q01-Q18 flipped to
  `shipped`. Results: `check_course_map.py --root …` gives "course map OK: 49 modules (33
  Q, 16 R; 18 shipped, 0 authoring, 31 planned)", and `gen_units.py --check` gives "37
  unit(s) … match". The flip is safe for the checker.
- Whether the freeze flips the status is the orchestrator's call (Δ123-era note: "moving
  them to shipped is a Release A decision").

## B. Gaps (ranked)

B1 **(blocker) The `Monitor` tool runs shell commands and the guard never sees it.**
- Where:
  - `.claude/settings.json:17`: the PreToolUse matcher lists Bash and PowerShell but not
    Monitor.
  - `.claude/hooks/spoiler-guard.sh:476-480`: `IS_SHELL` is set only for
    `Bash|PowerShell`, and any other tool name hits `*) exit 0`.
  - `scripts/test_hooks.sh:494-498`: Monitor is in neither the `covered` nor the
    `left_alone` list.
- Evidence:
  - The installed CLI is 2.1.299. Monitor was already in the session tool list at 2.1.289
    (`author-probes/dv1a/e2e-guard-wiring/out.jsonl`, init `tools`: "…Bash, …, LSP,
    Monitor, NotebookEdit…").
  - Its schema takes `command` ("Shell command or script").
  - Hook probe in this worktree (study mode):
    - Bash `cat Solutions/plans/DV5e-decisions-notes.md`: exit 2, "spoiler-guard: blocked
      (rule 1)".
    - Monitor with the same `command`: exit 0, nothing printed.
  - Layer 1's `Read(...)` deny rules are not shown to apply to a shell command. So a study
    or examiner session that uses Monitor for a recursive search or a file read reaches
    the reference with no tripwire. `grep -rn` through Monitor bypasses rule 1d too.
- Fix:
  - Add `Monitor` to the matcher.
  - In the hook, `Bash|PowerShell|Monitor) IS_SHELL=1` (its field is `command`, the same as
    Bash's). A `ws` input has no command but opens a network socket, so treat it like
    WebFetch: refuse it under rule 2c.
  - Add Monitor must-block fixtures mirroring the Bash rule 1/1b/1d/2c rows, and add
    Monitor to `covered`.
  - Make `guard_doors.py report` fail on any tool in the session init `tools` list that is
    in neither the covered nor the left-alone list. This is the mechanical check that
    would have caught Monitor.
  - Re-run the doors (B2).

B2 **(major) The guard's acceptance test has not run since the hook changed.**
- Checklist line: "A fresh study session is demonstrably denied …". The freeze bar names
  `guard_doors.py all`.
- Evidence: the last run was 2026-10-04 on hook `a2883993…` with CLI 2.1.289
  (`tests/acceptance/README.md:50`). `sha256sum .claude/hooks/spoiler-guard.sh` now gives
  `0a1c2b63…` (changed in Δ227 and later). The host CLI is 2.1.299
  (`~/.local/bin/claude -> versions/2.1.299`).
- Fix: after B1, run `python3 tests/acceptance/guard_doors.py all` (8 GB share, budget 10).
  Record the CLI version and the init tool list in `tests/acceptance/README.md`'s Last run,
  and add a Monitor door.

B3 **(major) Known-good transcripts are missing for 21 of 22 agentic exercises.**
- Checklist line: "Each agentic exercise has … one recorded known-good transcript".
- Exists: **Q07.A2d** (the Qwen replay through `contract_local.sh`).
  - Archive: `author-probes/dv5b/dv4s3/3b-q07-replay/`.
  - Its `replay-output.txt` ends "verdict: verified; every checked acceptance line met
    (4)".
  - The agent file is unchanged since 5e5d3ee.
- Missing (no archived full delivery):
  - Q01.A1d, Q01.A1v, Q02.A1d, Q02.A1v, Q04.A1d, Q04.A1v, Q05.A1d, Q05.A1v, Q06.A1d,
    Q07.A1d, Q07.A1v, Q08.A1d, Q08.A1v, Q09.A1d, Q09.A1v.
  - Q12's toolwright (`tools/Q12/holecount.py`).
  - Q15.A1d, Q15.A1v, and Q15's toolsmith (`tools/Q15/toolsmith.py`).
  - Q17.A1d, Q18.A1dv, Q18.A2dv.
- The simulations' case f covers only dry runs: restate the contract, then stop
  (`tests/instructor/simulations/README.md:54,66,78,90,102,116`).
- Fix: the dry-run lane runs one `/contract` delivery per file on an invented learner
  state in a study clone. That state is the author's reference fill of the prerequisites
  (frozen snapshots, interface blocks). These are never lab tasks.
- Archive each run under `author-probes/dv6/<lane>/transcripts/<item>/`: transcript, gate
  output, acceptance checklist. Record the list in a DELTAS entry.

B4 **(major) The CV gate (brittleness) has never run course-wide.**
- Checklist line: "Brittleness: the reference re-verifies under N seeds within the pinned
  resource limit".
- Evidence:
  - No `build/ci/*/summary.txt` mentions the `brittleness` job, and there is no
    `brittleness.log`.
  - Per-lane `--brittleness` runs exist only for some modules: L7 and Q16 (Δ209, Δ210),
    Q17 (Δ211), and the DV5c tools lane (Δ207).
- Fix: at the frozen tree, run
  `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 scripts/ci.sh --author --brittleness --job brittleness`,
  with `free -g` ≥ 31 first. Record the summary line beside the CI pass.

B5 **(major) The study-mode CI run is missing for this tree.**
- Freeze bar: "CI green in both modes".
- Evidence: the last full study run is `build/ci/20261013T102615Z-1957673` (authoring @
  e43077c, 98 uncommitted). The last study run on db398e4 (`20261013T213838Z-104589`) ran
  only `static`.
- Fix: run `scripts/ci.sh` (no `--author`) at the frozen tree, under a 16 GB scope.

B6 **(major) The continuity pass has no artifact, and threshold concepts are not tracked in
the Q chapters.**
- Checklist line: "Continuity pass: every whisper or threshold-concept step pays off".
- Evidence:
  - No DELTAS, QPLAN or notes record of a continuity pass.
  - `grep -o 'TC[0-9]+' docs/Q[01][0-9]_*.md` finds nothing, and QPLAN has no TC1-TC14
    table. The schedule exists only as a design sentence (`DESIGN-PROPOSAL.md:131`).
  - A mechanical probe of the 18 "What Qnn planted" tables (237 harvest references) found
    every target among Q01-Q18. The exceptions are forward pointers to the challenges:
    Q05→Q32, and Q18→Q31-Q33. On `basic`, those pay off only once `challenge` exists.
- Fix:
  - A read-only continuity lane checks each harvest row against the target chapter's
    section and records a pass/fail table in its notes.
  - Add a TC table to QPLAN, mapping each TC to the Q chapter section where it is
    glimpsed, operated and explained.
  - Reword the two Q05 and Q18 rows to say the payoff is on the `challenge` branch, or
    accept them as declared forward pointers.

B7 **(minor) A §7.2 side channel without a must-block fixture: `include_bytes!`.**
- Evidence: the hook handles it (`spoiler-guard.sh:45-46`), but
  `grep -c include_bytes tests/hooks/must_block.jsonl tests/hooks/templates/*` returns 0.
  `include_str` has one.
- Fix: add one template (a Write of a learner `.rs` with
  `include_bytes!("…/Solutions/…")`, rule 1). Regenerate the fixtures with
  `gen_hook_fixtures.py`.

B8 **(minor) D26 residue outside D26's touch list.**
- `scripts/ci.sh:4` says "before every merge into main".
- Fix: have the D26 lane reword it to "before every merge into a shipped branch (basic,
  then challenge)", along with the files it already edits.

## C. DELTAS-ready text for the integration lane

> **Δ2xx · DV6 audit, infrastructure and course level (spec §12.1).**
> - **Status:** a read-only audit of HEAD 83531a8 with the author CI run
>   20261014T004859Z-3125743 (14/14). It names no answer.
> - **Holds:** the toolchain pins and CI's sha and version checks; the default-target rule;
>   the registry and checker first in CI; Step 0 through the registry; the tool set; the
>   four guard layers; the hook-test passes (6,806/0); `course_mode.sh` and the
>   shipped-mode check; the SessionStart banners; artifact-based acceptance on all 22
>   agentic files; the contract slots; CI's no-model, no-learner-branch and
>   location-only rules.
> - **Gaps:**
>   - (B1) Claude Code's `Monitor` tool takes a shell command and the hook never sees it
>     (the matcher and `IS_SHELL`). Fix it, add fixtures, and make `guard_doors` compare
>     the session tool list with the matcher.
>   - (B2) `guard_doors.py all` was last run on the 2026-10-04 hook.
>   - (B3) Only Q07.A2d has a recorded known-good transcript; the other 21 go to the
>     dry-run lane.
>   - (B4) No course-wide brittleness run.
>   - (B5) No study-mode CI on this tree.
>   - (B6) No continuity artifact and no TC table.
>   - (B7) No `include_bytes!` fixture.
>   - (B8) `ci.sh`'s header still names `main`.
