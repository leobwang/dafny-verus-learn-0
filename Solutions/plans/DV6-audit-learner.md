# DV6 audit lane: the learner's read of Q01–Q18 (author-side notes)

Lane: AUDIT (learner read). Memory share 2 GB: no solver job ran; every verdict cited is a
chapter pin or a CI log. Read-only except this file. Tree audited: the authoring worktree at
HEAD 83531a8 with the concurrent DV6 lanes' uncommitted edits as of 2026-10-14 (D26's README
step 3, firsttry.py, pins.py, vcheck, course_mode.sh, CLAUDE.md; D28's benchstrip.py; D31's
sandbox.py). No `docs/Q*.md` file was modified by any lane when this audit read them.
Scratch: `/tmp/dvl0-dv6-audit/` (removed). Checker scripts archived under
`~/.cache/dafny-verus-learn-0/author-probes/dv6/learner-audit/` (paths.py, flags.py,
xref.py, collapse.py).

Read in order: README.md, CLAUDE.md (learner sections: §Roles, Access matrix, §Contractor
contract, the learner-owned slot), design §7.1 (prework P0/P1), docs/Q01–Q18 in full (output
fences collapsed to their commands for Q04–Q18), and the headers of every exercise, exit,
agent, specimen-companion and Python file the chapters name.

## Findings (ranked; the StructuredOutput carries the same list)

### Major

1. **Solutions-last rule contradicts itself across the practice tiers.**
   Q10:456, Q11:387, Q13:421, Q14:515 ("after the exit"), Q16:342 ("after `--post`"),
   Q17:469 ("after the reviews") vs Q12:496, Q15:988, Q18:680 ("the `Solutions/` mirrors of
   Q10's, Q11's and Q12's files, only after the viva"; same for Q13–Q15, Q16–Q18). The
   concept tiers are consistent (Q02:862, Q04:1081, Q05:1142, Q07:928, Q08:1239: only after
   the tier viva, "which examines Q0n too"). A learner who follows Q10's line opens Q10's
   twins before `/viva Q12` examines Q10, which Q01:737 and README "Solutions last" call a
   taint. DECISION NEEDED (pedagogy rule): (a) every non-tier-end practice module says "only
   after `/viva Q12|Q15|Q18`, which examines Q1n too" (recommended: matches the concept
   tiers and the tier-end chapters); (b) per-module timing stays and the tier-end chapters
   name only their own module's twins; (c) state both: the module's twins after its exit,
   its tier's viva bank items excluded from the viva.

2. **Binding decisions D27, D28, D30 and D33 are not yet in the learner-visible text**
   (at audit time no lane had touched docs/): 
   - D27 (public-card deliveries may add proof annotations): Q15:83–86 still says "One rule
     is not fixed yet, and the runs on the public strata wait on it"; README.md:13 "wait on
     one rule still to be fixed"; CLAUDE.md:5 "(the runs on the public strata wait on the
     user's rule …)"; bench/local/q/lab2pub/STRATUM.toml:7–8 "A delivery adds the `requires`
     and `ensures` and one witness call, and changes no executable code" (no annotations);
     Q15:630–631 S0/S1 rows (S1's kill must now mutate the delivery's annotated code).
   - D28 (spec-only non-recursive definitions removed and sealed): Q15:659–662 and
     lab2pub/STRATUM.toml:5–8 describe the form as "the specification and every proof
     removed … the code and an empty witness kept".
   - D30 (Lab 1's draw excludes Lab 2's five Verus tasks): Q12:273–282 and
     bench/local/q/lab1/STRATUM.toml:26–33 say nothing of the exclusion.
   - D33 (run the hidden check once per item, after the statement is final; report that first
     run): Q13:230–258 ("once your statement is written"), Q15:497–528, Q17:321, the
     headers of `Q15_Lab2Specs.dfy`:16–22 and `lab2_specs.rs` give no once-only rule.
   Integration: re-grep these lines after the decision lanes land.

3. **README's setup does not provide the services the chapters require; step 5's promise
   ("each chapter says what to install and when") is not kept.**
   - `uv` (pinned `required-version = "==0.12.4"`, harness/pyproject.toml): Q06:30 runs
     `uv sync --directory harness --frozen`; nowhere installed. README.md:61 says "Python
     3.11 or newer", harness/pyproject.toml:21 `requires-python = ">=3.12"`.
   - Docker and the `dvl-toolchain`/`dvl-agent` images (sandbox/build-images.sh, images.lock):
     Q07:843 replay, Q13:241 / Q15:517 / Q17:321 hidden check (grader container), Q15:595–614
     oracle runs, Q18:452 plant route; no chapter says how to get them.
   - Ollama with `qwen3.8:latest` (and the GPU calendar): Q07:843, Lab 1–3 Qwen arms.
   - The pinned `age` at `~/.local/bin/age` and the grader key at
     `~/.cache/dafny-verus-learn-0/keys/` (sandbox/truth.toml:24; harness/fvh/statements.py:55,
     234): needed by `python -m fvh unseal Q18` (Q18:78) and the hidden check.
   - rustup itself (README.md:64 runs `rustup toolchain install` but step 1 lists no rustup).
   On this host every piece is present (`uv` 0.12.4, Docker images dated 20261011/20261013,
   `ollama list` shows `qwen3.8:latest`, `~/.local/bin/age`, the key file), so the
   clean-clone dry run here passes; on any other host, or after a host rebuild, no file says
   how. Fix: a README Setup step 5 table (tool, pinned version, which module first needs it,
   the check command: `uv --version`, `scripts/contract_local.sh Q07 --available`,
   `sandbox/build-images.sh --check`, `ollama list`), and Python 3.12 as the floor.

4. **Editor/LSP setup is deferred ("Editor setup arrives with Release A", README.md:72),
   but chapters already use it.** Q01:698 asks for a "language-server lookup" door and
   Q01:712 admits the acceptance run had none; Q04:1034 (and Q10:346, Q07:643) make "IDE
   hover and go-to-definition" rung 1 of the search ladder; `.vscode/settings.json` pins
   `dafny.version` and a `verus-analyzer` binary path that no step installs. On this host
   Claude Code's init lists `LSP` with the user-level rust-analyzer-lsp plugin (VERSIONS.md
   §2.3 policy-mode row), so door 3 works here by accident. Fix: write the editor step now
   (VS Code Dafny extension at 4.11.0, verus-analyzer pointed at the pinned binary, or
   "skip rung 1"), and in Q01's THREE DOORS say what to record when the session has no LSP
   tool.

5. **Lab 1's public strata: no install step and no draw procedure.** The public sets are
   gitignored (`.gitignore`: `/bench/public/dafnybench/`, `/humaneval-verus/`,
   `/vericoding/` …), so a clean clone has none; Q12:65 names only `get_bench.sh --check`,
   and no chapter or README says to run `scripts/get_bench.sh` (fetch). The learner must
   pre-register "the draw seed, the pilot rule" (paper/Q12_answers.tex:29–30; Q12:276 "drawn
   by a pre-registered seed from validated pools"), but no command turns a seed and
   `bench/public/POOLS.toml`'s members into the plan's `tasks = [...]`
   (harness/fvh/batch.py:21 takes an explicit list) and the pilot (80 calls, Q12:285) has no
   procedure; Lab 2 has `scripts/dvl/lab2pub.py order` for the same job. Fix: a Q12 "run
   setup" paragraph: `scripts/get_bench.sh --all` (fetch on the pins, then `--check`), and a
   learner-runnable draw (e.g. a `lab1` mode of the seeded order, honouring D30's
   exclusion), with the pilot's plan form.

### Minor

6. Q12:47 "the lab's acceptance (§5.5)": Q12 has no §5.5; acceptance is §5.3 (Q12:319).
7. Q12:64 "`fvh report Q12 --reverify`": `python -m fvh report --help` shows
   `--reverify RUN` (an argument is required); Q18:543 writes `--reverify all`.
8. Q18:547 "**Then** (60 minutes in all): TRUST.md (15) … contract v2 (15) … proposal (60)":
   15 + 15 + 60 = 90, as §0's lines (Q18:38, `TRUST.md` and contract v2 30, proposal 60) say.
9. Q11:350–353's Done adds "`scripts/specfreeze --check Q11` reports no finding"; the
   headers' Done lines (dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy:23–26,
   verus/q/q11_practice_ib/src/lib.rs:16) omit it.
10. Q01's Verus done line omits the audit: verus/q/q01_hello/src/lib.rs header step 4
    ("Done = gate … AND firsttry") and Q01:655 (vaudit on the Dafny unit only), against
    README.md:47 (done = gate, `vaudit`, firsttry) and Q02:733+ (vaudit on unit and crate).
11. Q01 has no Setup step: §0's table budgets "setup 15" (Q01:21–23, CALIBRATION block
    line 452) but, unlike Q02–Q18, no paragraph says what it is (design §7.1: P0's
    `vcheck --selftest`; start `/tutor Q01`; `make -C paper paper`).
12. README stale lines: README.md:47 "All three commands arrive in phase DV1b, before Release
    A", :53 "(arriving in phase DV1b)", :69 "At Release A, `scripts/vcheck --selftest`",
    :76 "Both arrive in phase DV1b" (the tools exist: `scripts/vcheck --help` lists
    `--selftest`); :78 "`--quick` … (about three minutes)" against build/ci/20261014T004859Z-3125743
    (static 419 s + hook-test 181 s) and build/ci/20261013T213838Z-104589 (static 446 s); :78
    "the gate for changes to `main`" (D26: shipped branches are basic/challenge).
13. README.md:13 sends the learner to "prework P1 in the design" (the paper list is
    DESIGN-PROPOSAL.md:182), while README.md:54 keeps `docs/design/` closed until a module's
    predictions are committed (none are, before Q01). Fix: list the nine card ids
    (05.10, 06.1, 04.8, 04.6, 04.7, 03.8, 07.2, 02.6, 02.4) in the README.
14. Q07:713 and verus/q/q07_internals_i/src/port.rs:116 "in a scratch copy of the crate, does
    `scripts/vcheck` still verify your contract?": the crate's Cargo.toml depends on
    `../../given/qg_bignat_l*` by path, so a copy elsewhere does not resolve, and rule 1b's
    message lists only "a registry unit or a scratch file". Name the route (a probe file run
    with `scripts/vcheck --module Q07`, or edit in place and `git restore`).
15. Q11:286 (vstd's `cell/pcell.rs`) and Q14:410 (`simple_pptr.rs`) and the grep rung of
    Q04:1034 do not say where vstd's source is; Q04:1034 gives Dafny's (`DafnyStandardLibraries.doo`).
    On this host it is `~/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/vstd-0.0.0-2026-09-20-0158/`
    (the version pinned in every generated Cargo.toml: `vstd = "=0.0.0-2026-09-20-0158"`).
16. Q04's agent line (15 minutes, Q04:17–19, design §7.5) covers racing six goals (three per
    agent file, `SEARCH LOG` rows ScaleStrict, HighLimbOfShift, ProductMod and three Verus)
    down a five-rung ladder with timings, two contract-run audits and COMPARISON: under 1.5
    minutes per goal before any audit. Either say the race is one goal per file or move
    minutes.

No blocker found: nothing stops a learner who has this host's services, and no learner-visible
line read here quotes a reference answer (the final leak audit is another lane's).

## Lines verified as holding (for the release checklist)

- **Skills named exist**: every `/skill` in README and Q01–Q18 is one of contract, discuss,
  grade-paper, review, review-code, tutor, viva (`.claude/skills/`); `/grade-paper` supports
  `--post`, `--report`, `--fixture <path>` (SKILL.md line 3).
- **Script flags exist**: every `scripts/<x> --flag` in README, Q01–Q18 and the exercise
  headers occurs in its script or the dvl/fvh sources (flags.py, 0 misses); checked by hand
  against `--help`: vcheck (`--gate --json --symbol --module --lang --seed --isolate
  --brittleness --solver --solvers --selftest --test --bin --lab-task`), vaudit (`--compare
  --json --mode`), firsttry.sh (`--check --report --strict --record --exit`), specfreeze
  (`--check --against --lab`), check_course_map.py (`--only import-tiers`, `--resolve`),
  pins.py (`ID`, `--ci`, `--chapter`), mksandbox-run (`--truth --truth-check judge --judge`),
  contract_local.sh (`--file --available`), get_bench.sh (`--check`), lab2pub.py (`build
  --check`), `python -m fvh` (`run --plan`, `resume`, `report --judge --truth --reverify RUN`,
  `unseal`), `fvh_q.gate.core --half`, `fvh_q.gate.gate_v2 --set`, `fvh_q.lsp_client`.
- **fvh names the chapters use exist**: `fvh.records.load_calib`, `calib_records`;
  `fvh.stats.wilson_interval`, `pass_at_k`, `mcnemar`, `mde_two_proportions`;
  `fvh.tools.run`, `fvh.tools.command` (exported, tools/__init__.py:49).
- **Paths**: every backticked repo path in README and Q01–Q18 exists, except files the
  learner creates (research/q06_skeleton.dfy, q07_frozen.*, q08_statements.*, q09_bank.*,
  q17_statements.dfy, research/runs/…, tools/Q12/test_holecount.py,
  .claude/state/contract-allowlist) and tool-made directories (bench/local/q/lab2/oracle/tasks/);
  `Solutions/decoy/Q15/` exists (DECOY.md, answers.txt).
- **Minutes**: every chapter's §0 line sums to design §7.5's total (Q01 227, Q02 234, Q03 251,
  Q04 251, Q05 253, Q06 281, Q07 270, Q08 270, Q09 295, Q10 182, Q11 177, Q12 576 = 100 + 476,
  Q13 200, Q14 210, Q15 628 = 165 + 463, Q16 225, Q17 225, Q18 575 = 245 + 330), and the
  in-section splits add up (Q12 hand 8 × 12 = 96; Q15 prose 6 × 18 = 108; Q18 H2 110, H3 85,
  gate v2 60, adversarial 25) except finding 8.
- **Hole counts**: each header's "ships with exactly N holes" equals the chapter's file table
  and the §"exercise file" total (Q01 3+3, Q02 6+6, Q03 5+5, Q04 3+2 / 2+4, Q05 5+4, Q06 5+5+3py,
  Q07 4 / 4+3, Q08 1+3+3 / 3+2, Q09 1+1 / 2 + 4py, Q10 5+7, Q11 5+1 / 3+1, Q12 1+4 / 1+4 + 8py,
  Q13 3+3, Q14 2+1 / 4+2, Q15 2+3 / 2+3 + 7py, Q16 2+2, Q17 3+1 / 2, Q18 1+1 + 5py).
- **Slots**: `slots/Q*.slots` unfilled counts equal each chapter's verdict-item count (Q01 15 =
  7 + 8 exit, Q02 5, Q03 11, Q04 5, Q05 4, Q06 7, Q07 7, Q08 6, Q09 15, Q10 2, Q11 2, Q12 6,
  Q13 1, Q14 1, Q15 11, Q18 4; Q16 and Q17 none, as their chapters say).
- **Order of work**: Q02–Q03 pretest before predictions, Q04+ predictions before pretest, in
  chapter and header alike (firsttry.py docstring: from Q04 a T item's first try is refused
  while a P item is unrecorded).
- **In-chapter § references** resolve, except Q12:47 (xref.py over Q01–Q18).
- **Exit thresholds** match firsttry.py's EXIT_TIERS docstring: survey 10/13, intro 5/6,
  moderate and detailed 3/4 with ≥1 per language, Q10–Q12 1/2, Q13–Q15 1/1, Q16–Q18 none.
- **CI at the audited base**: build/ci/20261014T004859Z-3125743 (author run, db398e4 + 68
  changes, the tree committed as 83531a8): 14 passed, 0 failed (static, hook-test, verify-q-*,
  pins, empty-body, corpus, wrappers, coexist, paper, rubric, harness). Not re-run (2 GB share).
- **Host services present** (finding 3's evidence): `uv` at ~/.local/bin/uv; docker images
  `dvl-agent`/`dvl-toolchain` :20261011 and :20261013; `ollama list` includes `qwen3.8:latest`;
  `~/.local/bin/age`; the pinned Claude version file `~/.local/share/claude/versions/2.1.296`
  (sandbox/apparatus.toml) still present while the CLI link is 2.1.299.

## Runs this audit did not do (need a solver share)

None of the findings rests on a run. A clean-clone dry run (the freeze bar's) should confirm
findings 3 and 5 on a fresh clone: `uv sync --directory harness --frozen`,
`scripts/contract_local.sh Q07 --available`, `ls bench/public/`.
