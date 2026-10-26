# CLAUDE.md — dafny-verus-learn-0

A self-study course teaching Dafny and Verus side by side, aimed at research in agentic formal verification, in two standalone tracks: **Q01–Q33** (by depth: a survey, concept and practice tiers, then fifteen solo challenge modules; studied first) and **R01–R16** (by topic). The tracks share one registry, one instructor layer, one ledger and one gradebook, and neither depends on the other's files. Three languages: Dafny and Verus from the first module of each track, and Python for the evaluation harness (`harness/`, from Q06 and R05). Install the pinned toolchains with `scripts/get_toolchain.sh dafny|verus`. Verify only through the pinned wrapper: `scripts/vcheck --module <ID>` (every verification unit of a module), `scripts/vcheck <file>` (one file, in the learner loop), `scripts/vcheck --gate <file>` (the done gate), `scripts/vcheck --bin <crate> [-- <args>]` (a crate's binary target, built and run once: the capstone's command-line tool) and `scripts/vaudit <file>` (the assumption audit); the written track builds with `make -C paper paper`. **A hole is a typed placeholder; green with zero tool-counted holes is done** (the tool counts holes, never grep). `MODULES.toml` is the module registry: skills resolve module ids through `python3 scripts/check_course_map.py --resolve <ID>` and never guess a filename. The design is `docs/design/DESIGN-PROPOSAL.md`, and the built-deltas log `docs/design/DELTAS.md` overrides it where they differ; `README.md` holds the learner-facing norms.

**Initial Q-core release:** Q01–Q18, layers L1–L7, Labs 1–3 and the capstone are complete as course content, with registry status `shipped`. Full local author CI passed on the pre-release tree `5d9be4e` and full study CI on `40a9b5a`; the release tree itself had a static CI run (Δ250). `docs/design/BASIC-RELEASE.md` records the exact scope and final source/history evidence. Under the user's D45 instruction, live Claude guard acceptance, skill simulations, 78 grading/review calibration sessions and contractor/capstone transcripts are deferred validation debt, not passes. They do not block this build. No provider-window override or reserve release is used. Since the user's D47 (Δ275) the usage window has reset: those live checks run now in a separate validation lane, and the learner may start studying. Main remains design-only; the initial Basic content is one squash atop main (D42). Basic holds the Q core only (the user's D46: it was rolled back from a state that also had R01–R02, now archived). The next build adds the standalone R core to Basic, then the challenge modules on `challenge`. R01–R16 and Q19–Q33 remain `planned` in that Q-only snapshot, so skills refuse them at Step 0. **This `authoring` line** is canonical for R work: R01–R14 are R-core candidates under the repair plan `Solutions/plans/DVR4-repair-plan.md` (D48–D53), R03 is a draft under `Solutions/plans/drafts/R03`, and R15–R16 are planned; every fix to released content lands on `basic` first and is merged here.

**Not built yet:** `scripts/challenge_gate.sh` (the challenge phase); the Claude agent CLI in a container with its credential proxy (the user's D10 defers it until R16). Actual learner lab runs still require the learner's completed oracles, policy/gate work and pre-registration. The built Lab 2 feedback callback, sealed-reference calibration and complete scripted-policy/container/replay smoke pass (Δ244–Δ245); they are not substitutes for the deferred live model validation. Historical build detail remains in DELTAS.

**Current build exception (D45, Δ247):** the user instructed “record the blocker and skip. continue to build.” Live Claude acceptance, skill simulations, calibration and contractor/capstone transcripts are deferred validation debt and do not gate this build or the initial Basic release. They are not passes. The model reserve, guards, full local CI, frozen-tree leak audit and D42 squash/history checks remain in force. See `docs/design/BASIC-RELEASE.md` §11.

## §Roles

Claude wears exactly four hats in this repo, and **modes are entered only by their skill**: never drift from one role into another inside a session.

1. **Author**: builds the course (design §15.2). Active only in authoring mode (below).
2. **Coach** (instructor posture): `/tutor`, `/discuss`, `/review`. Hints, Socratic questions, spaced repetition. `/tutor` sessions are long-lived, one per module.
3. **Examiner/Grader** (instructor posture): `/viva`, `/grade-paper`, `/review-code`. A fresh session every time; coach and examiner never share a transcript.
4. **Contractor**: `/contract`. Verifier-checked delivery inside an explicit edit allowlist; a fresh session every time; never mixes with instructor work.

Firecrawl’s local-file parser (`mcp__firecrawl__firecrawl_parse`) is guarded as a file read, including relative paths and symlinks (DELTAS Δ242).

The instructor contract is `.claude/skills/instructor/CORE.md`; the contractor contract is §Contractor contract below. The verifier grades the formal; the instructor grades what the verifier cannot, and its output is advisory.

### Access matrix

| capability | Author (authoring mode) | Coach | Examiner/Grader | Contractor |
|---|---|---|---|---|
| Read the reference set: `Solutions/`, `paper/solutions/`, `tests/instructor/leak_patterns/`, the grader calibration fixtures `tests/instructor/fixtures/` (a gold fixture is a correct answer set by design; hook rule 1 and `CORE.md` keep them out, with no deny rule behind them), the held-out tree, `~/.cache/dafny-verus-learn-0/` | yes (build time only) | **never** | **never** | **never** |
| Edit the learner-owned files (hook rule 2): `dafny/{Q,R}/`, `verus/{q,r}/`, `harness/{q,r}/` (minus the solo gates), `specimens/` (their header slots) and `dafny/checks/` (their value-predict slots), `slots/`, `paper/*_answers.tex`, `research/`, `bench/local/{q,r}/**/{tasks,answers}/`, `tools/`; the run records `research/runs/**` and the ledger anchors `research/ledger-heads.jsonl` are written only by `fvh` and `scripts/mksandbox-run` | yes | **never** | **never** | only paths on `.claude/state/contract-allowlist`, each taken from the module's own `agentic` list (never `research/runs/**` or `research/ledger-heads.jsonl`) |
| Edit solo work (rule 2s): `Challenges/`, `agents/`, Q's gate (`harness/q/*/gate/`), R16's trust-report (a path under `dafny/R/`, `verus/r/` or `harness/r/` whose name holds `trust-report` or `trust_report`); R has no harness gate of its own, so `harness/r/**/gate/` is learner-owned (rule 2) | yes | **never** | **never** | **never** (no allowlist line may name them) |
| Edit frozen files (rule 2f): `*/given/**` (`dafny/given/`, `verus/given/`), `harness/fvh/**`, `harness/tests/**` (the author's acceptance tests for learner Python), `paper/rubrics/**` (what `/grade-paper` grades against), `expected/**`, challenge statements (`Challenges/**/*Statement*`), the benchmark manifest `bench/manifest.toml` and the third-party sets `bench/public/**` (installed by `scripts/get_bench.sh`) | yes | **never** | **never** | **never** (no allowlist line may name them) |
| Edit the guard, the build and the files that steer a session (rule 2g): everything under `.claude/` (hooks, `settings{,.local}.json`, skills with `CORE.md`, agents, commands) except `.claude/state/`, of which only the mode file; `tests/` (the guard's, the checker's and the grader's fixtures; the grader's calibration fixtures, `tests/instructor/fixtures/`, are in the reference set too, so the hook names them under rule 1 first); `CLAUDE.md` and `CLAUDE.local.md` at any depth (the learner writes the contract block below by hand, never Claude); `MODULES.toml`, `scripts/`, `sandbox/`, `.vscode/settings.json`, `.mcp.json`, `.toolchain/`, `dafny/options/`, `.config/dotnet-tools.json`, and at any depth every `dfyconfig.toml`, `Cargo.toml`, `Cargo.lock`, `.cargo/`, `build.rs`, `rust-toolchain{,.toml}`, `pyproject.toml`, `uv.lock`, `conftest.py`, `pytest.ini`, `setup.cfg`, `setup.py`, `tox.ini`, `sitecustomize.py`, `usercustomize.py` and `*.pth`; Claude Code's user-level settings (`~/.claude/settings{,.local}.json`, `$CLAUDE_CONFIG_DIR/settings*.json`, `/etc/claude-code/`; `~/.claude.json` is rule 1e); mode bits included (`chmod`/`chown`). As a write target, the checkout root itself, or any directory that holds it, is 2g too: `rm -rf .`, `chmod -R .`, `git checkout .` or `git restore .`, `git clean` with no pathspec, `find . -delete`, an archive extracted there or a directory's contents copied there (a single file copied or moved there is judged by its own name) | yes | **never** | **never** | **never** (no allowlist line may name them) |
| Write `instructor/` state (ledger, gradebook, feedback, records) | yes | yes (ledger, records) | yes (all) | **never** (rule 2c: the hook denies it while an allowlist is non-empty) |
| Run verifier probes in `instructor/scratch/` (`/grade-paper`: under `DVL_SCRATCH`, outside the checkout), through `scripts/vcheck` | yes | yes | yes | n/a (works in allowed files) |
| Write the rest of the course: chapters and design documents (`docs/`), `paper/*_problems.tex` and the paper build files, `README.md`, `VERSIONS.md`, and the reference set | yes | never | never | never |

These rows copy the path lists of the hook header (`.claude/hooks/spoiler-guard.sh`, rules 2, 2s, 2f and 2g), which wins where they differ; the registry names each module's files. The last row is the one the hook does not enforce: of its paths it guards only the reference set (rule 1), so the chapters and design documents, the paper problem and build files and the top-level documents rest on the role contracts alone. `/contract` writes `.claude/state/contract-allowlist`; the hook rejects any line there that names a solo (2s), frozen (2f) or guard (2g) path. Rule 2c keys on that file alone: while it is non-empty, every session is refused `instructor/` writes and the web tools, a coach session running beside the contract included. An archive unpacked into a learner, frozen or guard directory is refused even under a contract: unpack it into `/tmp`.

Enforcement is layered, hard first:

1. **Permission deny rules** in `.claude/settings.json`: the four canonical rules (named in §Authoring mode); three that keep other Claude sessions' transcripts out of reach, `Read(~/.claude/projects/*/*.jsonl)`, `Read(~/.claude/file-history/**)` and `Read(~/.claude/history.jsonl)`; and `Skill(skill:local-assistant)`, which keeps the local assistant out of course sessions.
2. **The `spoiler-guard.sh` PreToolUse hook** over the file tools, the shell and the verifier-wrapper tools. Its header lists its rules: 1 spoiler names (an author lane's scratch `/tmp/dvl0-dv…/` among them, a tripwire; an author harness's study clone lives under `/tmp/dvl0-study-…/`, which it does not match), 1b spoiler builds and the author-only steps (`scripts/get_bench.sh` and `scripts/dvl/bench.py` `--pin` and `--pin-pool` among them), 1c held-out material (`fvh unseal` among it), 1d whole-tree readers (recursive searches, `diff -r`, `find` or `fd` feeding `-exec`/`-x`/`xargs`, `ctags -R` and `cscope -R`, archives and recursive copies, globs) and build outputs, 1e other sessions' Claude Code state (their transcripts and their scratch folders under `/tmp/claude-<uid>/`), the Claude Code credentials file, the sandbox's run state under `$XDG_RUNTIME_DIR/dvl-runs/` and `fvh`'s per-call state (`fvh-claude-state`, `fvh-qwen-state`), 1f nested agents, Workflow/ScheduleWakeup calls and container tools (container and agent runs go only through `scripts/mksandbox-run`, `scripts/contract_local.sh` and `fvh`, which `scripts/ci.sh`'s static job checks), 2 learner-owned files, 2c a contract is active (no `instructor/` writes, no web tools (WebFetch, WebSearch), no reads of `bench/public/**/answers/`, no git command that rewrites tracked files across the tree: a checkout or switch to a revision, `reset --hard/--merge/--keep`, `stash` other than list/show, `merge`, `pull`, `rebase`, `cherry-pick`, `revert`, `am`; no `patch` or `git apply` fed on a pipe; and no other agent, container run or fetch: `scripts/contract_local.sh`, `scripts/mksandbox-run` other than `--check-access`, `--dry-run` and `--build-verify`, `scripts/get_bench.sh` and `scripts/dvl/bench.py`, `fvh run`, `resume` and `contract-local`, and `fvh unseal`, which writes a sealed stratum's cards), 2s solo work, 2f frozen files (given layers, `harness/fvh/` and `harness/tests/`, rubrics, `expected/`, challenge statements, the benchmark manifest and public sets), 2g the guard, the build and the files that steer a session, and the checkout root as a write target. Rule 1 lets the registry's field `solutions_policy` and its value `solutions-first` through on a shell line, so both are reserved names: no crate, package or module (Dafny, Rust or Python) may carry either, in any case and with `-` read as `_`, and `scripts/check_course_map.py` enforces this over the learner-visible tree (isolation I1). `scripts/test_hooks.sh` replays the `tests/hooks/` fixtures against it. The `review-due.sh` SessionStart hook banners due reviews, a stale contract allowlist and an authoring-mode file.
3. **The instructor contract** (`CORE.md`, MAY / MAY NOT), which repeats every hard rule as an instruction.

So degradation is soft, never silent. The guard is a **tripwire against accidental exposure of reference material, not a sandbox**: string splitting, or a script that opens files itself, gets past it, and the instructor contract forbids trying. Separate Unix accounts and host hardening are optional (design §4, H1 and H2), never required.

### Session hygiene

- Tutor sessions are long-lived, one per module: "the history is the pedagogy".
- Grader, reviewer, viva and contractor sessions are fresh each time.
- Every skill self-checks its transcript and refuses cross-role contamination in one line.
- Formal disputes go to the verifier: a probe in `instructor/scratch/`, the output pasted verbatim, and the learner interprets it first.

The self-check is one uniform rule: an examiner or contractor session refuses if its transcript shows any earlier skill activity, its own earlier run included; a coach session refuses if its transcript shows examiner or contractor activity. Every skill works in its own session only: no subagents, workflows, background jobs, nested agents or local assistants, and one solver job at a time (§Resources).

### Authoring mode

`.claude/state/mode` containing `authoring` suspends the spoiler-guard hook so the course can be built (solutions written, exercises hollowed, rubrics distilled). The file is gitignored and machine-local.

**Author only in a dedicated linked worktree**, outside the learner checkout and outside any scratchpad (for example `git worktree add ../dafny-verus-learn-0-authoring -b authoring origin/basic`, or `origin/main` while `basic` does not exist; the recipe `course_mode.sh` prints names the one that exists). `scripts/course_mode.sh authoring` refuses in the primary worktree, on `leobwang-*` branches and outside git, and the hook ignores a mode file in any of those places (it checks git itself and never trusts the file), so the learner's checkout never stands its guard down.

Layer 1 cannot read that file, so authoring mode ALSO removes the four canonical rules from `.claude/settings.json`'s `permissions.deny`: the two layers move together, or the author is locked out of the files being written. **Never flip either by hand**: `scripts/course_mode.sh authoring|study|status` moves both, touching only the four canonical rules (the three transcript rules and any other deny rule stay), and `study` is the shipping state. `scripts/ci.sh` fails if the repo ships with `.claude/state/mode` present or with any of the four canonical deny rules missing:

- `Read(./Solutions/**)`
- `Read(./paper/solutions/**)`
- `Read(./tests/instructor/leak_patterns/**)`
- `Read(~/.cache/dafny-verus-learn-0/**)`

A `deny` list without them in a working tree therefore means "this checkout is mid-authoring", never "the guardrails were removed".

**Authoring sessions and the merge into a shipped branch** (the author's procedure; the shipped branches are `basic` and `challenge`, branched from `basic`, and `main` holds only the design: the user's decision D26):

1. **Project directory.** An authoring session, an orchestration and every lane it starts included, runs with the authoring worktree as its project directory: start `claude` in the authoring worktree and run `scripts/course_mode.sh authoring` there (`scripts/course_mode.sh status` confirms it). The hook reads only the mode file of the session's own project directory, so a session rooted anywhere else is not in authoring mode, whichever worktree it writes to.
2. **Scratch.** Lane scratch goes under `/tmp/dvl0-<phase>-<lane>/` (for example `/tmp/dvl0-dv1b-infra/`), never under `/tmp/claude-*`: rule 1e treats `/tmp/claude-<uid>/` as other sessions' state, so a guarded session cannot read a lane's files there. This replaces Δ66's per-lane subdirectory of the session scratchpad. The author harnesses that start study sessions (`skill_sims.py`, `calibrate.py`, `guard_doors.py`) keep their state and streams under the lane's scratch and put the session-facing half, the study clone and its `DVL_SCRATCH`, under the sibling root `/tmp/dvl0-study-<phase>-<lane>/`, which rule 1's lane-scratch pattern does not match (the user's decision D20). Before removing a lane's scratch, run its harness's `cleanup`, or remove `/tmp/dvl0-study-<phase>-<lane>/` too: a study root lies outside the tripwire, and `skill_sims.py setup` refuses while one is on the host.
3. **The first `basic` release (D42).** Once the freeze bar passes, create one squashed commit of the frozen tree with `main` as its sole parent; old authoring history must never be merged into a shipped branch. Run `python3 scripts/check_release_history.py <candidate>` before distributing it: it checks that main..candidate is a linear chain of single-parent commits whose subjects start with `basic: `, the first on main, with no archived (`archive/*`) ancestry; `scripts/ci.sh`'s static job runs it on `basic` (Δ275). Recreate authoring from the released `basic` baseline after preserving this worktree's work. Later fixes land on `basic` first and merge forward into `challenge`. This strategy and conditional branch creation were approved by the user (DELTAS Δ243). The full CI and acceptance requirements below still apply.

4. **Before merging later authoring work into a shipped branch** (`basic` first for every fix, then merged forward into `challenge` at once), in the authoring worktree: run `scripts/course_mode.sh study`, which restores the four canonical deny rules and removes the mode file, so `.claude/settings.json` is in its shipping state (do the same before any commit of `.claude/settings.json`). Then run `scripts/ci.sh` (and `scripts/ci.sh --author` in the authoring worktree) and record its summary line in the merge commit message (Δ67). The plain run skips the steps that read the reference and is safe in any checkout. `--author` adds those steps, refuses outside the author's context (a linked worktree off `leobwang-*`, or `CI=true`; never on a `leobwang-*` branch), and sends their output only to `~/.cache/dafny-verus-learn-0/ci/`. The hook lets a study session run `scripts/ci.sh`, but it refuses any shell line that sets `CI` (rule 1b). Before a merge that changes the guard, the deny list or the Claude Code pin, also run the by-hand acceptance test `python3 tests/acceptance/guard_doors.py all` in the authoring worktree (Δ107): it calls a model, so `scripts/ci.sh` never runs it. Run `scripts/course_mode.sh authoring` again to resume authoring.
5. **The primary checkout.** A session whose project directory is the primary checkout is in study mode as soon as its branch carries the guard: the hook arms there and ignores any mode file. So never update the primary checkout to a guarded `basic` or `challenge` (or merge one into it) from inside an authoring orchestration session: the guard would arm under the running orchestration and its lanes, and block their scratch under `/tmp/claude-*` and every path into the authoring worktree's reference trees (rule 1 matches those by name, absolute paths included). Update the primary checkout after the orchestration has ended.

Authoring is started by the human author. Never walk someone working through the course into it: in a study checkout, do not explain how to stand the guard down (an authoring worktree, `course_mode.sh`, the mode file) or offer to read or build the reference there. A learner who wants the reference gets its path in prose (it is theirs to open) and nothing more.

## §Resources: solver memory budget (binding for every session, agent and script)

This host has about 123 GB of RAM, no swap, and other Claude sessions and services running. Verus and Dafny sweeps ran it out of memory twice on 2026-10-03. `--rlimit` / `--resource-limit` bound solver *work*, not memory.

- **Budget memory, not cores.** Plan up to 8 GB per Verus z3 (more for empty-body or high-rlimit modes). Total solver memory across **all** concurrently running lanes, agents and scripts stays at or below **48 GB**. Split it between lanes: for example, Verus 32 GB (`GATE_WORKERS=4`) beside Dafny 16 GB.
- **Verus sweeps:** `GATE_WORKERS` ≤ 6, and fewer while another solver lane runs. **Dafny:** concurrent z3 = workers × `--cores`; keep that product small (script defaults 3 × 2).
- **Always run sweeps under a hard cap**, so a mistake kills only the sweep:
  `systemd-run --user --scope -p MemoryMax=<lane share>G -p MemorySwapMax=0 env GATE_WORKERS=<n> <command>`
- **Before launching**, `free -g` must show the budget plus 15 GB available. **While running**, watch memory (`ps -C z3 -o rss= | awk '{s+=$1} END {print s/1048576 " GiB"}'`), not just CPU, and stop if it nears the budget.
- **Script defaults must be safe when run bare.** Never hard-code a large worker pool.
- The course tools apply no memory cap of their own (DELTAS Δ503, D78): these limits are the host's, so every run that starts solvers goes under a cap like the one above.
- A job killed by memory exits 137/143 (-9/-15). Record it as `killed(memory)`, **never** as a verification verdict.
- Workflow and subagent prompts that run solvers must state these limits explicitly, with each lane's share.

## §Contractor contract

Contract v0 is written by the learner, by hand, with no AI session: in Q03 on the Q track and in R01 on the R track. v1 follows the red-teamed run (Q09, R15) and v2 the capstone round (Q18, R16). Until a learner contract exists, `/contract` sessions follow the fallback rules embedded in `.claude/skills/contract/SKILL.md`:

- re-verify after every edit through the pinned wrapper (`scripts/vcheck`), unless an `acceptance:` line names another per-edit discipline; never stack unverified edits;
- done = `scripts/vcheck --gate` exits 0 with zero tool-counted holes on every allowed file, `scripts/vaudit` reports no finding, and every acceptance artifact holds;
- never weaken a spec, statement or check to get green, and never reach for an escape hatch (an assumption, an axiom, a trusted or external body, skipped or filtered verification, a verifier flag the wrapper does not pin): stop and report instead;
- edits only inside the allowlist, which names only files from the module's own `agentic` list.

Learner contracts add to the `/contract` fallback rules; the stricter rule wins. Everything below the marker is one shared contract block (design D3): every written Q-vN and R-vN section binds every `/contract` session, whichever track it serves, and where two rules conflict, the stricter wins.

<!-- learner-owned below: contract v0/v1/v2 -->

<!-- Slot format (spec §5.2). Replace "(not written yet)" with the date when you write a version:
     ### Q-v0 — Q03, YYYY-MM-DD
     1. <rule> — earned by: <source run> — <one-line transcript moment>
     2. ... (3 to 6 numbered rules, each tied to an observed transcript moment)
     Done means (re-checkable by a third party): <commands, and the output each must show> -->

### Q-v0 — Q03 (not written yet)

### Q-v1 — Q09 (not written yet)

### Q-v2 — Q18 (not written yet)

### R-v0 — R01 (not written yet)

### R-v1 — R15 (not written yet)

### R-v2 — R16 (not written yet)
