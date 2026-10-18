# dafny-verus-learn-0

**Release validation:** the Q core's local build and proof checks are recorded in [BASIC-RELEASE](docs/design/BASIC-RELEASE.md). Live Claude guard, coaching, grading and contractor validation is deferred because of the provider quota, under the author's explicit D45 instruction. Those sessions have not passed on the release tree; since the user's D47 the usage window has reset and they run now in a separate validation lane, and you may start studying. The initial Q core is released locally on `basic` (Δ250): full local author CI passed on the pre-release tree `5d9be4e` and full study CI on `40a9b5a`, and the release tree itself had a static CI run (BASIC-RELEASE §13).

A self-study course that teaches **Dafny and Verus side by side**, for an experienced developer heading into research on agentic formal verification. Three goals:

1. **Hand fluency in both verifiers**: read and write verified programs and proofs by hand, including the kinds of obligation that agents fail on (invariants, weak specs, arithmetic), with programming as a first-class outcome.
2. **The verifier as an environment**: program logic and verification conditions, the pipeline down to the SMT solver, verdict kinds, resource limits, brittleness, and the trusted computing base.
3. **Agentic verification as experimental science**: specify and audit an AI contractor's work with the verifier in the loop, and run pre-registered, reproducible experiments.

Design: [`docs/design/DESIGN-PROPOSAL.md`](docs/design/DESIGN-PROPOSAL.md), with [`docs/design/DELTAS.md`](docs/design/DELTAS.md) authoritative where they differ (read the warning under *Predictions first* before opening either). Role rules for Claude: [`CLAUDE.md`](CLAUDE.md).

## Status

Q01–Q18 form the initial Basic release: exercises, specimens, exits, agent files, chapters, written pairs, rubrics, banks, Labs 1–3 and the capstone are built, and the release registry marks those eighteen modules `shipped`. Full local author CI passed on the pre-release tree `5d9be4e` and full study CI on `40a9b5a`; the release tree had a static CI run and the final source-leak and history checks. The user deferred live Claude guard, coaching, grading and contractor validation under D45 because of the provider quota; these checks remain validation debt, never passing results, until the validation lane the user started under D47 records them. The [release checklist](docs/design/BASIC-RELEASE.md) records current evidence. The standalone R core is added to `basic` next; challenges follow on `challenge`, branched from Basic. Every later fix lands on Basic first and is merged forward. Actual learner labs still require completed learner oracles/policies, task draws and a graded pre-registration.

On this authoring line R01, R02 and R04–R14 are R-core candidates with registry status `authoring`: under the user's D46 the R core reaches Basic only as one reviewed release, so Basic holds the Q core alone and no R module is `shipped` yet. R03 is a draft rebuilt on `u32` code-point classes (D48), and R15–R16 and the challenges stay planned. Each module starts with predictions, so keep its specimens, expected outputs and later files closed until its chapter asks for them.

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

1. **Prerequisites.** git, bash, `curl`, `unzip`, `sha256sum`, Python 3.12 or newer (the course scripts read `MODULES.toml` with `tomllib`, and the harness's `pyproject.toml` asks for 3.12; this host has 3.12.3), rustup (for step 2's pinned Rust), and Claude Code, the `claude` command line. Every `/skill` in this course is typed into a `claude` session started in the repository root.
2. **Toolchains.** Each verifier is pinned to one release and installed into `.toolchain/` (gitignored); the install script checks the release tag, the commit, the asset's sha256 and a digest of the installed tree, and prints only the binary path:
   ```
   rustup set auto-self-update disable   # once: rustup must not replace itself (the sandbox's image lock pins its sha256)
   rustup toolchain install 1.98.1-x86_64-unknown-linux-gnu --profile minimal --no-self-update   # Verus needs exactly this Rust
   scripts/get_toolchain.sh dafny     # Dafny 4.11.0 (about 65 MB); no .NET needed
   scripts/get_toolchain.sh verus     # Verus 0.2026.09.27.3cf1832 (about 486 MB; 1.6 GB installed)
   scripts/get_toolchain.sh dafny --check   # re-verify offline at any time; the same for verus
   ```
   The course runs only these binaries, through `scripts/vcheck`; never put another `dafny`, `verus` or `z3` on your `PATH` for course work. `scripts/vcheck --selftest` confirms the install.
3. **Your own branch.** Once, before your first module: `git switch -c leobwang-<name> basic`, from the local branch `basic` (the learner branch prefix is `leobwang-`; once `basic` is pushed, `git fetch origin` and `git switch -c leobwang-<name> origin/basic` do the same). `basic` is the course as shipped (the Q core now; the R track is added to it next) and `challenge` adds the challenges to it; `main` holds only the design. Commit course work on your branch, never on `basic` or `challenge`: they keep every file as shipped, and `scripts/firsttry.sh` and the rubrics compare your files with the newer of the two that your branch contains. To take a course update, merge the newest of `basic` and `challenge` into your branch (`challenge` once it exists: it holds `basic` and every fix to it; once they are pushed, `git fetch origin` first and merge `origin/basic` or `origin/challenge`); changes never flow back.
4. **TeX** (for the written track): TeX Live with `latexmk`, `pdflatex`, and the `mathpartir`, `listings`, `xcolor` and `stmaryrd` packages (on Ubuntu 24.04 they come from the `latexmk`, `texlive-latex-recommended` and `texlive-science` packages, or with `texlive-full`). `make -C paper paper` builds every problems/answers pair of both tracks and fails loudly while there is none, or when a file lacks its partner. Reference solutions have their own author-only target, `paper-solutions`, so your build never compiles one.
5. **Later**, each when its first module needs it (the module's chapter points back here):

   | tool | pin | first module | install | check |
   |---|---|---|---|---|
   | uv and the harness environment | uv 0.12.4 (`sandbox/images.lock`) | Q06, R05 | install uv, then `uv sync --directory harness --frozen` | `uv --version`; `uv run --directory harness python3 -c 'import fvh'` |
   | Docker and the course images (`dvl-toolchain`, `dvl-agent`) | `sandbox/images.lock` | Q07 (the local agent replay) | Docker Engine, then `sandbox/build-images.sh` | `sandbox/build-images.sh --check` |
   | Ollama and the local model | `qwen3.8:latest` (`sandbox/apparatus.toml`) | Q07, the labs | Ollama, then `ollama pull qwen3.8:latest` | `ollama list`; `scripts/contract_local.sh Q07 --available` |
   | age and the grader's key | age v1.3.2 at `~/.local/bin/age` (`sandbox/truth.toml`) | Q13 (the hidden checks) | the pinned release binary, and the key where `sandbox/truth.toml` names it | `sha256sum ~/.local/bin/age` against `age_sha256` |
   | the public benchmark sets | `bench/manifest.toml`, `bench/public/POOLS.toml` | Q12 (Lab 1) | `scripts/get_bench.sh --all` | `scripts/get_bench.sh --check` |
   | the editor | the Dafny extension at 4.11.0 and verus-analyzer on the pinned `verus` (`.vscode/settings.json`) | Q01 (its language-server door), Q04 (the IDE rung) | VS Code with both extensions; open the repository root | hover a symbol in `dafny/Q/Q01_Hello/core/Q01_Hello.dfy` |

## Verifying, memory, and the local CI

- **`scripts/vcheck`** is the only way the course runs Dafny and Verus: it pins the binary, the solver, a deterministic resource limit (never a wall-clock limit), the thread count and the flags, and it refuses flags that would weaken a gate. `scripts/vaudit` is the assumption audit. For R14, `scripts/vcheck --smt-log DIR <Verus file>` also keeps the SMT queries Verus sends to Z3 (the learner loop or fast channel only, never the gate; `DIR` new or empty); the run is otherwise the same run, with the same verdict and hole count.
- **Memory.** A single verifier job can take several GB; `CLAUDE.md` §Resources sets the host's solver memory budget and binds every session, agent and script. Run one verifier job at a time; the wrapper applies a memory cap, and a job killed by memory is recorded as `killed(memory)`, never as a verdict.
- **Local CI.** There is no hosted CI. `scripts/ci.sh` runs every course check on this machine: the registry and its checker, the guard's hook tests, verification of both tracks in both languages (hole counts taken from the tools), golden pins, the cheat corpus, the tool suites, the two tracks resolving together, and the written track. `scripts/ci.sh --quick` runs only the first two jobs (about ten minutes), `--list` names the jobs and `--job NAME` runs one of them. It runs one verifier job at a time under the memory caps and checks free memory before it starts one. Each job prints one `PASS`, `FAIL`, `SKIP` or `ABSENT` line, the logs go to `build/ci/<run>/` with only their locations on the console, and any failure gives a non-zero exit. The steps that read reference material run only in the course author's run (`--author`), which refuses in your checkout, so your run reports them as skipped. It runs before every merge into a shipped branch (`basic` first, then merged forward into `challenge`); you do not need it to study, and its output (the console and `build/ci/`) is on the *Predictions first* list.

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
