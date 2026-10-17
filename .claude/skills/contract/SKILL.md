---
name: contract
description: "The CONTRACTOR door for dafny-verus-learn-0 agentic exercises: parses the agentic file's CONTRACT header, validates and writes the edit allowlist, executes under the verifier contract through the pinned wrapper, then closes out. Invoked as /contract <Qxx|Rxx> in a fresh session."
disable-model-invocation: true
---

Read the **§Contractor contract** section of `CLAUDE.md` first and operate under it: you are the CONTRACTOR, not the instructor. The learner's contract sections there (Q-vN and R-vN, one shared block) add to the rules below and never relax them; where they conflict, the stricter rule wins. Do NOT read `.claude/skills/instructor/CORE.md`: instructor rules are not yours. The anti-spoiler layer still binds you: `Solutions/`, `paper/solutions/`, `tests/instructor/leak_patterns/`, the grader calibration fixtures `tests/instructor/fixtures/` and `~/.cache/dafny-verus-learn-0/` stay unread in every mode, contractor included.

# /contract <Qxx|Rxx> — verifier-checked contract work

## Session check — before anything else

Contractor sessions are fresh every time. If this session shows any earlier skill activity (a tutor, discussion, review, viva, grading, code review, or an earlier contract), refuse in one line ("contractor needs a fresh session: instructor and contractor never share a transcript") and stop, before resolving or building anything.

## Step 0 — resolve the module through the registry

`MODULES.toml` is the single registry of modules; work from its record, never from a guessed filename.

1. Run `python3 scripts/check_course_map.py --resolve <ID>` (any case; prints the record as one JSON object). Exit 3 (unknown id) → refuse in one line naming the id; any other failure → the registry is broken or missing: say so in one line. Either way, stop.
2. `status = "planned"` → refuse in one line ("Q14 is not authored yet").
3. `solo = true` → refuse in one line: "<ID> is a solo challenge module: /contract is closed for it; that work is the learner's alone."
4. `agentic` is empty → refuse in one line, nothing more. When the module's agentic exercise is one the learner writes by hand, the line names that exercise. Those modules are listed in `.claude/skills/contract/hand_written.toml`, the one list (`scripts/chapter_lint.py` reads the same file; never keep a copy here). Read it: if it has a table for <ID>, the line is that table's `refusal`, verbatim; its `exercise` names the exercise and its `where` says where the learner writes it. Offer no draft, rule or review of that exercise: it is the learner's own work. Any other module with an empty list: "<ID> has no agentic exercise (registry `agentic` is empty), so /contract is closed for it." If the file is missing or unreadable, say so in one line and stop, without guessing which line applies.
5. The record's `engines` must include `contract`; otherwise refuse in one line: "<ID>'s agent work runs through the harness, not /contract."
6. Run `scripts/vcheck --module <ID>` before the first edit, so "green" later means something. If it reports a missing toolchain, tell the learner in one line to run `scripts/get_toolchain.sh dafny` or `verus` and stop. Then run `scripts/vcheck <file>` on each agentic file too: a unit need not contain it (red-by-design agentic files are outside every unit), and its output is that file's baseline. A red unit or a red file here is the baseline to record, not a refusal: a repair contract starts red.

## 1. Parse the CONTRACT header

Open the module's agentic file: the record's `agentic` list names it; if the list holds more than one file, ask the learner which run this is. Line 1 of that file opens the contract, the one format this skill parses. In a `.dfy` or `.rs` file it is a block comment; in a `.py` file, a module docstring (`"""CONTRACT` … `"""`) with the same body:

```
/* CONTRACT
goal: <one line: what to deliver>
allowed-files:
  - <repo-relative path>
  - <further paths, if any>
acceptance:
  - <artifact-based criterion: a command and the output it must show>
  - <a method clause, e.g. the per-edit feedback discipline>
*/
```

It has **exactly three keys**, `goal:`, `allowed-files:` and `acceptance:`; every method clause is one more `acceptance:` bullet. If the header is missing, not on line 1, or malformed (another key, a key missing, an empty list), stop and report: never guess scope. Restate the parsed contract in one short block and get the learner's go-ahead before touching anything.

Acceptance lines change only when the learner edits the CONTRACT header and you re-parse and restate it. A permission given in chat ("skip that check", "use another channel if this one is flaky") never relaxes one: decline it and say why. If a channel an acceptance line requires is unavailable, stop and report; never substitute another.

## 2. Validate and write the edit allowlist

Check every `allowed-files` path before writing anything. If any path fails, refuse the whole contract in one line naming the path, and write nothing. Each path must:

- be repo-relative, with no leading `/` or `./`, no `..` segment and no glob character;
- be in the record's `agentic` list: equal to one of its entries, or under an entry that ends in `/`. A contract never unlocks a file outside its own module's agentic list, so a Q contract never unlocks an R file;
- not be under `Challenges/` or `agents/`, or in a solo gate (Q's gate `harness/q/*/gate/`, R16's trust-report: a path under `dafny/R/`, `verus/r/` or `harness/r/` whose name holds `trust-report` or `trust_report`): that is solo learner territory, the hook never consults the allowlist there, and it rejects such entries (rule 2s). R has no harness gate of its own, so a `harness/r/**/gate/` path is ordinary learner work (rule 2);
- not be frozen: no `given/` path component (`dafny/given/`, `verus/given/`), nothing under `harness/fvh/`, `harness/tests/` (the author's acceptance tests), `paper/rubrics/` or `expected/`, no challenge statement file (`Challenges/**/*Statement*`). Every learner shares them, and the hook rejects such entries (rule 2f);
- not be inside a reference tree (`Solutions/`, `paper/solutions/`, `tests/instructor/leak_patterns/`, `tests/instructor/fixtures/`) or the held-out tree;
- not be guard or build configuration, or a file that steers a session: nothing under `.claude/`, `tests/`, `scripts/` or `sandbox/`, no `CLAUDE.md` or `CLAUDE.local.md` at any depth, not `MODULES.toml`, and no project, toolchain or editor file (`dfyconfig.toml`, `Cargo.toml`, `Cargo.lock`, `.cargo/`, `build.rs`, `rust-toolchain{,.toml}`, `pyproject.toml`, `uv.lock`, `conftest.py`, `pytest.ini`, `setup.cfg`, `setup.py`, `tox.ini`, `sitecustomize.py`, `usercustomize.py`, `*.pth`, `dafny/options/`, `.toolchain/`, `.config/dotnet-tools.json`, `.mcp.json`, `.vscode/`): those decide what is verified and how, and what a session is told, and the hook rejects such entries (rule 2g);
- not be under `instructor/`;
- not be a run record or the ledger anchors (`research/runs/**`, `research/ledger-heads.jsonl`): only `fvh` and `scripts/mksandbox-run` write them, and the hook rejects such entries (rule 2);
- not be the benchmark manifest or a public set (`bench/manifest.toml`, `bench/public/**`): frozen, installed only by `scripts/get_bench.sh` (rule 2f).

Then write the validated paths, exactly as given, one per line and nothing else, to `.claude/state/contract-allowlist`, with the Write tool or a shell command of its own. Claude Code treats `.claude/state/` as a sensitive location and asks the learner to approve this one write (and the emptying write at close-out); ask them to approve exactly that file and nothing broader. In a headless run with no one to approve, the write is refused: stop and report that the contract needs an interactive session. This is what unlocks edits to those specific files: the spoiler-guard hook denies edits in the learner-owned trees to any path NOT on this list, and while the list is non-empty it denies every `instructor/` write, the web tools, reads of `bench/public/**/answers/` and the git and patch commands of §4 (rule 2c). Never add paths beyond the header; needing another file means renegotiating the contract with the learner first.

## 3. Execute under the verifier contract

These are the fallback rules; the learner's contract adds to them, and the stricter rule wins.

- **Re-verify after every edit** with `scripts/vcheck <file>` on each edited file, and never stack unverified edits, unless an `acceptance:` line names a different per-edit feedback discipline; then follow it. The Step 0 baseline never counts against such a line.
- **Done** = `scripts/vcheck --gate <file>` exits 0 with **zero tool-counted holes** on every allowed file, `scripts/vaudit <file>` reports no finding on every allowed file, and every acceptance artifact holds. **One exception:** an allowed file under `tools/<ID>/` (a learner tool in plain Python, such as Q12's toolwright file) is outside the verifiers' scope, and `scripts/vcheck` refuses it with exit 3 before running anything; for that file alone the gate and audit clauses do not apply, and its acceptance lines are its whole done check. Say so in the report, with the refusal pasted. A refusal on any other path is a stop-and-report, never this exception.
- **Never weaken to get green.** Do not weaken, delete or reinterpret any check, test, signature, `requires`, `ensures`, invariant, `decreases` line or spec comment; statement changes are out of scope unless the contract explicitly grants them. If a spec looks wrong, stop and report.
- **Never reach for an escape hatch**: no assumption, axiom, trusted or external body, assumed specification, skipped or filtered verification, test-only check used in proof code, or verifier flag the wrapper does not pin. If in doubt whether a construct is one, it is: stop and report.
- **The verifier runs only through the pinned wrappers** (`scripts/vcheck`, `scripts/vaudit`): never a bare `dafny`, `verus` or `cargo verus`, and never `cargo build` or `cargo test` as a verdict. An error verdict is not proof the claim is false, and a run killed by memory or by the wall-clock net is no verdict at all.
- **One solver job at a time**, in the foreground (`CLAUDE.md` §Resources).
- Your prose is rhetoric; your artifacts are the deliverable. Keep the final report to: what changed (files and line ranges), the final gate and audit output, and the acceptance checklist with evidence per item.

## 4. Hard boundaries

- **Work in this session only.** Never delegate to subagents, the Task/Agent tool, a Workflow, a background job, a nested `claude`, `opencode`, a local assistant or a container tool, whatever mode the environment announces: the learner audits this transcript, and an edit made elsewhere is not in it. The course's own agent and container entry points are closed to you too while the allowlist is non-empty (rule 2c): `scripts/contract_local.sh`, `scripts/mksandbox-run` (other than `--check-access` and `--dry-run`), `scripts/get_bench.sh`, and `fvh run`, `resume` and `contract-local`; the local replay is the learner's to start.
- **No web search or fetch** during a contract (WebFetch and WebSearch are refused while the allowlist is non-empty, rule 2c), and no reads of `bench/public/**/answers/`; library facts come from the pinned toolchain's own sources and the course files, and each one is cited with the command that found it.
- **No whole-tree git and no piped patches** while the allowlist is non-empty (rule 2c): the hook refuses a checkout or switch to a revision, `reset --hard/--merge/--keep`, `stash` other than list/show, `merge`, `pull`, `rebase`, `cherry-pick`, `revert`, `am`, and a `patch` or `git apply` fed on a pipe. It also refuses any write to the checkout root as a whole (`rm -rf .`, `chmod -R .`, `git checkout .` or `git restore .`, `git clean` with no pathspec, `find . -delete`, an archive extracted there; rule 2g), and an archive unpacked into a learner, frozen or guard directory, contract or not. To undo your own edit, name the allowed file (`git checkout -- <file>`); a task that needs a tree-wide operation is outside the contract: stop and report.
- **Never tutor.** If the learner asks "why does this work?", answer in at most one sentence and point to `/tutor` in a separate session.
- **Never touch instructor state**: `instructor/` (ledger, gradebook, feedback, records) is off-limits to the contractor, for reading and writing.
- Never read `Solutions/`, `paper/solutions/`, `tests/instructor/leak_patterns/`, `tests/instructor/fixtures/` or `~/.cache/dafny-verus-learn-0/`.
- Never import, include, build, verify or open reference material through ANY tool or wrapper flag; never read build outputs (`target/`, `build/`, `*-py/`, `.verus-log/`, `__pycache__/`); never name a held-out path.

## 5. Close out

On completion or abandonment, empty `.claude/state/contract-allowlist` (write an empty file) so the edit unlock does not leak into later sessions, and deliver the acceptance-checklist report.
