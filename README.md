# dafny-verus-learn-0

**Release validation:** the Q core's local build and proof checks are recorded in [BASIC-RELEASE](docs/design/BASIC-RELEASE.md). Live Claude guard, coaching, grading and contractor validation is deferred because of the provider quota, under the author's explicit D45 instruction. Those sessions have not passed on the release tree; since the user's D47 the usage window has reset and they run now in a separate validation lane, and you may start studying. The initial Q core is released locally on `basic` (Δ250): full local author CI passed on the pre-release tree `5d9be4e` and full study CI on `40a9b5a`, and the release tree itself had a static CI run (BASIC-RELEASE §13).

A self-study course that teaches **Dafny and Verus side by side**, for an experienced developer heading into research on agentic formal verification. Three goals:

1. **Hand fluency in both verifiers**: read and write verified programs and proofs by hand, including the kinds of obligation that agents fail on (invariants, weak specs, arithmetic), with programming as a first-class outcome.
2. **The verifier as an environment**: program logic and verification conditions, the pipeline down to the SMT solver, verdict kinds, resource limits, brittleness, and the trusted computing base.
3. **Agentic verification as experimental science**: specify and audit an AI contractor's work with the verifier in the loop, and run pre-registered, reproducible experiments.

Design: [`docs/design/DESIGN-PROPOSAL.md`](docs/design/DESIGN-PROPOSAL.md), with [`docs/design/DELTAS.md`](docs/design/DELTAS.md) authoritative where they differ (read the warning under *Predictions first* before opening either). Role rules for Claude: [`CLAUDE.md`](CLAUDE.md).

## Status

Q01–Q18 form the initial Basic release: exercises, specimens, exits, agent files, chapters, written pairs, rubrics, banks, Labs 1–3 and the capstone are built, and the release registry marks those eighteen modules `shipped`. Full local author CI passed on the pre-release tree `5d9be4e` and full study CI on `40a9b5a`; the release tree had a static CI run and the final source-leak and history checks. After the review fixes (Δ275), basic's tip `148fa73` passed full local author CI (14/14) and full study CI (12 passed, 2 author-only skips) on 2026-10-18. The user deferred live Claude guard, coaching, grading and contractor validation under D45 because of the provider quota; these checks remain validation debt, never passing results, until the validation lane the user started under D47 records them. The [release checklist](docs/design/BASIC-RELEASE.md) records current evidence. The standalone R core is added to `basic` next; challenges follow on `challenge`, branched from Basic. Every later fix lands on Basic first and is merged forward. Actual learner labs still require completed learner oracles/policies, task draws and a graded pre-registration.

## Two tracks

The repo holds two complete, standalone courses over the same goals. They share one registry (`MODULES.toml`), one instructor layer, one error ledger and one gradebook, and both are comparative from the first module: most exercises pair the same obligation in a `.dfy` file and a `.rs` file, and where the two languages differ, the difference is the lesson.

- **Q (Q01–Q33), by depth: study this first.** A survey (Q01) that touches every strand; three concept tiers (Q02–Q09); three practice tiers (Q10–Q18), each ending in a module with a pre-registered lab (Q12, Q15, Q18); then fifteen solo challenge modules in five domain topics (algorithms, quant service, numerics, PL, agentic; Q19–Q33), in any topic order after Q18. Its running artifact is a big-number type carried through frozen given layers.
- **R (R01–R16), by topic.** Standalone and ungated: no R module needs a Q file, and no Q module needs an R file. Its running artifact is a regex engine grown into a verified compiler to a small virtual machine (`rexc`), with three labs of its own (R12, R15, R16). The design suggests starting R after Q09, and its labs after Q12, Q15 and Q18; in practice R ships after the Q core.

## How to start

1. Now: Setup steps 1–3 below (prerequisites, toolchains, your own branch).
2. On `basic`: open the Q01 chapter in `docs/` and read its `## 0` **before you run any verifier command**: it may ask for predictions first.
3. Work the Q track in order: Q01 → Q18, then the challenge topics in any order. Start R whenever you choose; it assumes nothing from Q.

## What a module looks like

- **Chapter** `docs/<ID>_<Name>.md`. A Q chapter opens with `## 0`: the minute budget, the pretest, and what a correct pretest lets you skip.
- **Exercise files** with typed holes, in both languages (`dafny/Q/…`, `verus/q/…`, and the R equivalents), plus specimen and slot files for predictions. From Q06 and R05, Python harness code under `harness/` as well.
- **Exit file** (Q01–Q15, and the R06 and R11 checkpoints): closed book, scored once on its first complete run.
- **Written track** (every Q01–Q18 and R module, paper cards at least; the other problem kinds where they pay): `paper/<ID>_problems.tex` → your `paper/<ID>_answers.tex`, built by `make -C paper paper`. It holds hand calculations (weakest preconditions, verification conditions), informal proofs that become the blueprint an agent formalizes, concept questions, paper cards, and, in lab modules, the pre-registration and the lab report.
- **Agentic exercise**: `/contract <ID>` starts an AI contractor whose role escalates module by module (repairer → implementer → audited prover → … → co-developer). **You** do the exercise: you specify, then audit the transcript, the diff and the artifacts.
- **Instructor layer**: Claude as tutor, Socratic discussant, examiner, paper grader, code reviewer and review scheduler (`/tutor`, `/discuss`, `/viva`, `/grade-paper`, `/review-code`, `/review`). It asks, probes and grades; it never writes course code and never opens reference solutions. Its grades are advisory: a verifier check always outranks them.
- **Reference twins** under `Solutions/`: yours to open, last.

## The module loop

```
chapter (→ optional /discuss) → paper problems → make -C paper paper green → /grade-paper (fresh session)
→ revise → exercise files (/tutor after 20 minutes stuck) → done → /grade-paper --post
→ agentic exercise via /contract (fresh session) → /review-code (fresh) → /viva (fresh)
→ self-compare with Solutions/ LAST → /review whenever the session banner shows due items
```

- **Done** for code means `scripts/vcheck --gate <file>` exits 0 with zero holes **counted by the tool** (never by grep), `scripts/vaudit <file>` reports no finding, and `scripts/firsttry.sh <ID> --report --strict` exits 0 (every prediction filled and its first try recorded, no check left commented). A hole is a typed placeholder; green with zero tool-counted holes is done.
- On the Q track only the tier-end modules have a viva (`/viva Q03` examines Q02 and Q03 together; then Q06, Q09, Q12, Q15, Q18), and each challenge ends in a defense. Every R module has its own viva.
- A Q module's own loop, with its pretest and exit, is in its chapter's `## 0` and its "Instructor touchpoints" section.

## Study norms (read once; they carry the course)

- **Attempt for 20 minutes before `/tutor`.** The tutor needs to see your attempt before it hints, gives one hint-ladder rung per turn, and logs your hint depth: leaning on it buys future review load.
- **Predictions first.** Write each prediction into its slot and record the first try with `scripts/firsttry.sh <ID> --check` **before** you run anything it is about. Until a module's predictions are committed, do not open `docs/design/`, `VERSIONS.md`, `MODULES.toml`, `PLAN.md`/`QPLAN.md`, `expected/`, the output of `scripts/ci.sh`, the module's bank or rubric, later modules' files, or the git history of any of them (`git log -p`, `git show <rev>:<file>`): they record verified tool behaviour, and a description can give a prediction away. The `fvh` harness core and the author's acceptance tests (`harness/fvh/`, `harness/tests/`) are on it from Q06: they state the estimators that Q06's Python predictions ask about. The cheat corpus (`tests/corpus/`) and the recorded gate fixtures (`harness/tests/q/fixtures/`) are on it from Q09: they hold the labels and the tool results that Q09's forensic predictions and gate core ask about. The grader calibration fixtures in `tests/instructor/fixtures/` are on this list too, for longer: a gold fixture is a correct answer set, so leave a module's fixtures closed until the module is done.
- **Solutions are yours to open, and only yours.** Nothing stops *you* from reading `Solutions/` or `paper/solutions/`; opening them before the loop's last step just taints every later grading step for that module. Claude, in every role, is kept out of them by committed deny rules and a hook; ask it outright for an answer and it names the reference path and stops.
- **Sessions have roles.** A `/tutor` session is long-lived, one per module (resume it with `claude --resume`). Grader, reviewer, viva and contractor sessions are fresh every time (a new `claude` run, or `/clear`). Every skill refuses, in one line, a session that already holds work it may not share: a coach skill refuses examiner or contractor work, and a fresh-session skill refuses any earlier skill run, its own included.
- **Disputes go to the verifier.** Any disagreement about what Dafny or Verus does is settled by a probe whose output is pasted verbatim, and you interpret it first. The verifier is asymmetric: "verified" is trustworthy, but "could not be proved" is not a refutation, and a time-out or resource-limit hit is no verdict at all.

## Setup

1. **Prerequisites** (Linux x86-64 or macOS on Apple silicon; see [Platforms](#platforms)):
   - git, bash (bash 4 or newer for `scripts/ci.sh` and `scripts/test_hooks.sh`; macOS ships 3.2, so `brew install bash`), `curl` and `unzip`;
   - [uv](https://docs.astral.sh/uv/) 0.11.0 or newer;
   - Python 3.12 or newer: Ubuntu's `python3.12`, or uv's own (`uv python install 3.12`; the system Python of macOS is 3.9);
   - rustup, for Verus's Rust 1.98.1;
   - Claude Code, the `claude` command line. Every `/skill` in this course is typed into a `claude` session started in the repository root.

   Run the course scripts through uv from the repository root: `uv sync` once, then `uv run scripts/vcheck …`. Or `source .venv/bin/activate` once per shell and run them bare, as this README writes them.
2. **Toolchains on your PATH** (DELTAS Δ503, D78). You provide the pinned verifiers on `PATH`, and the course calls them as plain processes:
   - **`dafny` 4.11.0** (`dafny --version` prints `4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2`). Use the release zip, which bundles the Z3 solvers 4.12.1 (the course's pin) and 4.14.1. If you install with `dotnet tool install --global dafny --version 4.11.0` (on .NET 8) instead, also put a Z3 4.12.1 on `PATH` as `z3-4.12.1`.
   - **`verus` 0.2026.09.27.3cf1832**, the weekly release zip. It bundles Z3 4.16.0 and needs Rust `1.98.1`.

   On Linux x86-64:
   ```
   curl -LO https://github.com/dafny-lang/dafny/releases/download/v4.11.0/dafny-4.11.0-x64-ubuntu-22.04.zip
   curl -LO https://github.com/verus-lang/verus/releases/download/release/0.2026.09.27.3cf1832/verus-0.2026.09.27.3cf1832-x86-linux.zip
   unzip -q dafny-4.11.0-x64-ubuntu-22.04.zip -d ~/opt && unzip -q verus-0.2026.09.27.3cf1832-x86-linux.zip -d ~/opt
   export PATH="$HOME/opt/dafny:$HOME/opt/verus-x86-linux:$PATH"     # in your shell's startup file
   rustup toolchain install 1.98.1-x86_64-unknown-linux-gnu --profile minimal --no-self-update
   ```
   On macOS (Apple silicon): use the same release pages' `dafny-4.11.0-arm64-macos-13.zip` and `verus-0.2026.09.27.3cf1832-arm64-macos.zip`. The directories are `dafny` and `verus-arm64-macos`, and the Rust toolchain is `1.98.1-aarch64-apple-darwin`.

   Then run `scripts/vcheck --versions`, which checks each tool and its Z3 against the pins, and `scripts/vcheck --selftest`. A different version is not refused. Every command warns (expected against found) and continues, but it marks everything whose meaning depends on the exact toolchain as **UNTRUSTED**, in its output and its JSON (D79): the done gate's verdict, pins, first tries and brittleness figures. `scripts/vcheck --fingerprint` is an optional diagnostic: it checks that your solvers count resources exactly as the reference builds do. On Linux x86-64, `scripts/get_toolchain.sh dafny|verus` still installs the pinned vendor releases into `.toolchain/`, which the sandbox images use; put its `dafny` and `verus-x86-linux` directories on `PATH` if you like. Never put another `dafny`, `verus` or `z3` on `PATH` for course work.
3. **Your own branch.** Once, before your first module: `git switch -c leobwang-<name> basic`, from the local branch `basic` (the learner branch prefix is `leobwang-`; once `basic` is pushed, `git fetch origin` and `git switch -c leobwang-<name> origin/basic` do the same). `basic` is the course as shipped (the Q core now; the R track is added to it next) and `challenge` adds the challenges to it; `main` holds only the design. Commit course work on your branch, never on `basic` or `challenge`: they keep every file as shipped, and `scripts/firsttry.sh` and the rubrics compare your files with the newer of the two that your branch contains. To take a course update, merge the newest of `basic` and `challenge` into your branch (`challenge` once it exists: it holds `basic` and every fix to it; once they are pushed, `git fetch origin` first and merge `origin/basic` or `origin/challenge`); changes never flow back.
4. **TeX** (for the written track): TeX Live with `latexmk`, `pdflatex`, and the `mathpartir`, `listings`, `xcolor` and `stmaryrd` packages (on Ubuntu 24.04 they come from the `latexmk`, `texlive-latex-recommended` and `texlive-science` packages, or with `texlive-full`). `make -C paper paper` builds every problems/answers pair of both tracks and fails loudly while there is none, or when a file lacks its partner. Reference solutions have their own author-only target, `paper-solutions`, so your build never compiles one.
5. **Later**, each when its first module needs it (the module's chapter points back here):

   | tool | pin | first module | install | check |
   |---|---|---|---|---|
   | uv and the harness environment | uv ≥ 0.11.0, a minimum (`required-version` in `pyproject.toml` and `harness/pyproject.toml`); the sandbox images carry their own pinned uv 0.12.4 (`sandbox/images.lock`) | Q06, R05 | install uv, then `uv sync --directory harness --frozen` | `uv --version`; `uv run --directory harness python3 -c 'import fvh'` |
   | Docker and the course images (`dvl-toolchain`, `dvl-agent`) | `sandbox/images.lock` | Q07 (the local agent replay) | Docker Engine, then `sandbox/build-images.sh` | `sandbox/build-images.sh --check` |
   | Ollama and the local model | `qwen3.8:latest` (`sandbox/apparatus.toml`) | Q07, the labs | Ollama, then `ollama pull qwen3.8:latest` | `ollama list`; `scripts/contract_local.sh Q07 --available` |
   | the course's copy of Claude Code's version file | Claude Code 2.1.306, `[backend.claude]` in `sandbox/apparatus.toml` | Q12 (Lab 1: every `fvh` batch checks it, a Qwen-only one too) | `scripts/get_toolchain.sh claude`, while that version is still in `~/.local/share/claude/versions/` (see below) | `scripts/get_toolchain.sh claude --check` |
   | age and the grader's key | age v1.3.2 at `~/.local/bin/age` (`sandbox/truth.toml`) | Q13 (the hidden checks) | the pinned release binary for your platform (linux-amd64 or darwin-arm64), and the key where `sandbox/truth.toml` names it | `sha256sum ~/.local/bin/age` (macOS: `shasum -a 256`) against this platform's `age_sha256` |
   | the public benchmark sets | `bench/manifest.toml`, `bench/public/POOLS.toml` | Q12 (Lab 1) | `scripts/get_bench.sh --all` | `scripts/get_bench.sh --check` |
   | the editor | the Dafny extension at 4.11.0 and verus-analyzer on the pinned `verus` (`.vscode/settings.json`) | Q01 (its language-server door), Q04 (the IDE rung) | VS Code with both extensions; open the repository root | hover a symbol in `dafny/Q/Q01_Hello/core/Q01_Hello.dfy` |

   Claude Code updates itself and deletes old version files, so `fvh` never runs the `claude` link or the updater's files: it runs the course's own copy of the pinned version, `~/.local/share/dafny-verus-learn-0/claude/versions/<version>`, which `scripts/get_toolchain.sh claude` makes once (it checks the pinned sha256) and which survives every later update. Your Claude Code and its auto-updater stay as they are. When a course update moves the pin, run `scripts/get_toolchain.sh claude` again; if your CLI has already deleted that version, it says so and how to put it back (`VERSIONS.md` §1.3).

## Platforms

The course runs on Linux x86-64 and on macOS on Apple silicon (D77). `PYTHONPATH=scripts python3 -m dvl.host id` names the host.

| | Linux x86-64 | macOS on Apple silicon |
|---|---|---|
| **T1** the verification loop: `vcheck`, `vaudit`, `specfreeze`, `pins.py`, `firsttry.sh`, chapters, skills, the guard, the written track | yes | yes |
| **T2** the labs without containers: Ollama and the local model through `harness/fvh` | yes | yes, except `fvh` batches (below) |
| **T3** containers: `scripts/mksandbox-run`, `scripts/contract_local.sh`, the sealed hidden checks, agent replays in Docker | yes | not yet |

**`fvh` batches on macOS: not yet.** `sandbox/apparatus.toml` pins this course host's Claude Code and opencode binaries by path and sha256 (`[backend.*]`), so `fvh apparatus --check`, which every batch runs, refuses on a Mac. A Mac needs its own host-specific `[backend.*]` pins, which the course does not support yet.

**Memory is yours.** The course tools apply no memory management (D78): no cap, no preflight. A verifier job can take several GB. Run long sweeps and `scripts/ci.sh` under a limit of your own, for example on Linux `systemd-run --user --scope -p MemoryMax=32G -p MemorySwapMax=0 scripts/ci.sh`. A job killed by a signal (exit 137 or 143) is recorded as `killed(memory)`, never as a verdict.

**The same results on both.** Every build of one Z3 version that was measured gives the identical rlimit count and verdict on every query of `tests/fingerprint/z3/`: vendor x64 and arm64, Dafny's own build, and macOS. The macOS arm64 builds of 4.12.1, 4.14.1 and 4.16.0 matched the x86 baselines on all 129 queries. So one set of pins holds on both platforms, including the 17 that depend on resource counts. `scripts/vcheck --fingerprint` checks your solvers.

**macOS setup.**
```
brew install bash jq uv               # or uv's own installer; any uv >= 0.11.0
uv python install 3.12
curl --proto '=https' -sSf https://sh.rustup.rs | sh -s -- --default-toolchain stable --profile minimal
rustup toolchain install 1.98.1-aarch64-apple-darwin --profile minimal --no-self-update
# unzip the arm64 Dafny and Verus release zips (step 2) and put dafny/ and verus-arm64-macos/ on PATH
uv sync && uv run scripts/vcheck --versions && uv run scripts/port_selftest.sh
```
macOS needs no GNU coreutils. The guard runs under the system bash 3.2, and `ci.sh` and `test_hooks.sh` re-run themselves under Homebrew's bash. The editor setting `verus-analyzer.verus.verusBinary` is `verus`, resolved on `PATH`.

**Hosted CI (advisory).** `.github/workflows/portability.yml` runs on `ubuntu-24.04` and `macos-14`, with no model and no container. It unzips the pinned releases onto `PATH`, then runs `vcheck --versions`, the fingerprint, the toolchain-contract tests and `scripts/ci.sh --job static --job hook-test --job verify-q-dafny`. The merge gate stays the local `scripts/ci.sh` run.

## Verifying, memory, and the local CI

- **`scripts/vcheck`** is the only way the course runs Dafny and Verus: it pins the binary, the solver, a deterministic resource limit (never a wall-clock limit), the thread count and the flags, and it refuses flags that would weaken a gate. `scripts/vaudit` is the assumption audit.
- **Memory.** A single verifier job can take several GB. The course applies no memory cap (D78): memory is yours, so run one verifier job at a time (the default) and long runs under a limit of your own. A job killed by a signal is recorded as `killed(memory)`, never as a verdict.
- **Local CI.** The merge gate is local (the advisory hosted matrix is under [Platforms](#platforms)). `scripts/ci.sh` runs every course check on this machine: the registry and its checker, the guard's hook tests, verification of both tracks in both languages (hole counts taken from the tools), golden pins, the cheat corpus, the tool suites, the two tracks resolving together, and the written track. `scripts/ci.sh --quick` runs only the first two jobs (about ten minutes), `--list` names the jobs and `--job NAME` runs one of them. It runs one verifier job at a time under the memory caps and checks free memory before it starts one. Each job prints one `PASS`, `FAIL`, `SKIP` or `ABSENT` line, the logs go to `build/ci/<run>/` with only their locations on the console, and any failure gives a non-zero exit. The steps that read reference material run only in the course author's run (`--author`), which refuses in your checkout, so your run reports them as skipped. It runs before every merge into a shipped branch (`basic` first, then merged forward into `challenge`); you do not need it to study, and its output (the console and `build/ci/`) is on the *Predictions first* list.

## Agents and models: no usage-billed API

All agent work uses the Claude subscription CLI and local models only: interactive `/contract` sessions; tool-less `claude -p` policy runs and sandboxed agent runs driven by the course harness (`fvh`); and opencode with local Qwen models through Ollama. No API keys, no SDK, no usage-billed API, and never `claude --bare` (it uses an API key). `scripts/ci.sh` never calls a model. Budgets are counted in calls, tokens, wall-clock and GPU time, with checkpoint-and-resume so a rate limit never turns into best-of-n.

## Study mode and authoring mode

The checkout you study in is in **study mode**, the shipping state: committed deny rules and the spoiler-guard hook keep every Claude session out of the reference material, and each skill's contract repeats those rules as instructions. The course author builds the course in a separate linked worktree, where the guard stands down; `scripts/course_mode.sh` refuses to stand it down in your checkout or on a `leobwang-*` branch, and the hook ignores a mode file there. You never need authoring mode to study. The guard is a tripwire against *accidental* exposure, not a sandbox: it keeps Claude from stumbling into answers; it does not stop you, and when you open the references is your call.

## Repo map (as planned)

- `docs/` — chapters (and `docs/design/`, the design documents)
- `dafny/`, `verus/`, `harness/` — your exercise trees per track (`Q`/`q`, `R`/`r`), the frozen given layers (`given/`), and the Python harness
- `specimens/`, `slots/`, `expected/` — prediction specimens, your slot files, and the author's pinned expectations
- `paper/` — the written track (`make -C paper paper`); `paper/rubrics/` — the module rubrics
- `research/` — your `EVAL.md` and `TRUST.md` (one shared file each, with Q-vN and R-vN sections) and run logs
- `instructor/` — your ledger, gradebook, feedback and exam records ([`instructor/README.md`](instructor/README.md))
- `Challenges/`, `agents/` — solo work, yours alone
- `Solutions/` — reference twins: open LAST
- `.claude/` — the skills, hooks and committed guard settings
- `MODULES.toml` — the module registry for both tracks; every skill resolves its module id through `python3 scripts/check_course_map.py --resolve <ID>`
- `scripts/` — `get_toolchain.sh`, `vcheck`, `vaudit`, `firsttry.sh`, `ci.sh` and the course checkers
