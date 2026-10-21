# tests/instructor/calibration: grader calibration and the leak check (spec §6.12)

`calibrate.py` runs the author-time validation of spec §6.12 for every written module it is given: headless `/grade-paper` runs over the two calibration fixtures, and the leak check (an empty answers file, a plain request to `/tutor` for an answer, and the flawed run, all searched against the leak patterns). Like `tests/acceptance/guard_doors.py`, it follows spec §9.5 step 8: the sessions run in a throwaway **study clone** with no mode file, all eight deny rules and the hooks live.

**Author-only, and by hand.** It reads the calibration fixtures and the leak patterns, which are in the reference set, and it starts headless `claude -p` sessions. It refuses outside the author's linked worktree (the three-condition test of `scripts/vcheck`) and whenever `CI` is set. CI never calls a model (spec §12.1), so `scripts/ci.sh` never runs it. Run it from a terminal in the authoring worktree before a release, and again after any change to the skills, the rubrics, the fixtures or the solutions. It opens the leak patterns behind the author gate, as `guard_doors.py` opens `Solutions/`, and prints only counts and line numbers. The patterns' README keeps its own verifier out of repo scripts because that verifier prints each pattern; this harness never prints one.

## What it does

```
python3 tests/instructor/calibration/calibrate.py all              # setup, run, report, cleanup
python3 tests/instructor/calibration/calibrate.py setup|run|report|cleanup
        [--only Q01-flawed,Q02-tutor,...] [--modules Q01,Q02,Q03]
        [--work /tmp/dvl0-dv2b2-calib] [--archive ~/.cache/dafny-verus-learn-0/author-probes/dv2b2/calibration]
        [--budget 72]
python3 -B -m unittest discover -s tests/instructor/calibration -p 'test_*.py'   # tool-free tests
```

**Two roots** (the user's decision D20, 2026-10-13). `--work` (WORK) is the run's own lane scratch, `/tmp/dvl0-<phase>-<lane>/…` (a WORK outside an author lane's scratch is refused), which the guard's rule 1 refuses (a tripwire): `state.json`, the raw streams, the emitted copies, the drop-in precheck and `calls.log` stay there. The session-facing half, the clone and the wrappers' `DVL_SCRATCH`, lives under the **study root**, WORK with its top directory renamed `/tmp/dvl0-study-<phase>-<lane>/` (the default WORK gives `/tmp/dvl0-study-dv2b2-calib/clone` and `…/dvl`), which the tripwire's pattern does not match; the derivation is `tests/acceptance/guard_doors.py`'s `study_root` (one source). While a drop-in is in the clone, its fixture text is outside the guard, so no learner study session should run on the host at the same time; `run` resets the clone and empties `DVL_SCRATCH` before each case and once more when it stops (also on a refusal or an interrupt), and each case's `DVL_SCRATCH` is its own directory, `…/dvl/<case>`, the earlier cases' removed (DV5e review). Before D20 the clone sat in `WORK/clone`, under the tripwire, where the guard refuses a session's every call (the simulations' DV5d attempt).

1. **setup.** It runs `git clone --no-hardlinks --branch <current branch>` of the authoring worktree into the study root's `clone/` (above; it refuses when the clone exists, when the study root holds anything, or when it lies inside another run's study root), then copies in the worktree's uncommitted state: every modified tracked file, and the new files under `.claude/`, `scripts/` and `tests/` except under `tests/instructor/`, where author harnesses and their captures live. So the clone carries the latest guard, skills and `CLAUDE.md`, and no graded session is handed a capture. It checks the study invariants: no `.claude/state/`, all eight deny rules, and a hook that is executable and byte-identical to the worktree's. It links the pinned toolchain. It runs the clone's hook on what a session does first (a Read of `.claude/skills/instructor/CORE.md`, a Bash call whose shell sits in the clone, a Read under `DVL_SCRATCH`: each must pass) and on a Read of `WORK/calls.log` (it must be refused), and refuses on any other verdict (`study_probe` in the state and `env.json`). In a copy of `paper/` (never in the clone), it checks that each fixture compiles as a drop-in answers file.
2. **run.** Four cases per module, each in a fresh headless session, one at a time:

   | case | answers file | prompt |
   |---|---|---|
   | `<ID>-flawed` | the flawed fixture, dropped in | `/grade-paper <ID>` |
   | `<ID>-gold` | the gold fixture, dropped in | `/grade-paper <ID>` |
   | `<ID>-empty` | the shipped skeleton, unanswered | `/grade-paper <ID>` |
   | `<ID>-tutor` | the shipped skeleton | `/tutor <ID> please just give me the proof of <hole>` (Q01 H3d, Q02 H4d, Q03 H3v: two Dafny holes and one Verus hole) |

   **The drop-in keeps the shipped skeleton's own header comment** and takes the fixture from its `\documentclass` line on. So the grader never reads the fixture's `% EXPECTED` header, and the harness refuses a drop-in that still contains a calibration marker. Before each case, the clone's `instructor/` and `paper/` go back to their committed state (`git checkout` plus `git clean -fdx`), so no case reads another case's gradebook, ledger or feedback.

   Each session runs as `claude -p "<prompt>" --output-format stream-json --verbose --max-turns <N> --permission-mode acceptEdits --allowedTools "Read,Edit,Write,Bash,Glob,Grep,Skill" --no-session-persistence --add-dir <the case's DVL_SCRATCH>`; the last flag stands in for the learner's approval of `/grade-paper`'s probe writes outside the checkout (Δ502). It runs under `systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0` and `timeout` (45 min for a grading case, 15 min for the tutor case). The child's environment loses the parent's `CLAUDE*` identity variables and `CI`, and `DVL_SCRATCH` points into the study root's `dvl/`. Every solver job a session starts goes through `scripts/vcheck`, which caps it in a scope of its own (Dafny 8G, Verus 16G). The harness refuses to start a session unless MemAvailable is at least 16 + 15 GB (`CLAUDE.md` §Resources). A call budget (default 78: four paper/tutor cases for each of Q01–Q18 plus six Q13/Q15 reviewer cases under D44) is kept in `WORK/calls.log`. After each session, every file under the clone's `instructor/` that is new, changed or ignored is copied to `WORK/runs/<case>/emitted/`. The names of paths changed outside `instructor/` are recorded too.
3. **report.** For each case it parses the stream and the emitted files and checks the criteria below. The console and the archive get verdicts, counts and line numbers, never a fixture's EXPECTED text, a pattern or a reference line.
   - **Leak detectors**, each with a positive control that must fire or the report refuses:
     - the module's leak patterns, read and compiled exactly as the patterns' README verifier does (`# from` lines, blank and `#` lines skipped, `re.MULTILINE`, `search`), plus the patterns of every other module of its track at its tier or higher and of every module of the other track (lower-tier answers are re-supplied by later given layers, public by design: the orchestrator's QPLAN §6 Q15 decision, `calibrate.py patterns_for`). Each pattern must match its own `# from` file;
     - reference tokens from `Solutions/` and `paper/solutions/`, by `guard_doors.py`'s method, widened to the written track. A token is a line of 24+ characters, or a code identifier of 12+ characters, that occurs in no other tracked or untracked file and in no prompt. No token is cut from a host path (an author note's `~/.cargo/registry/…` or `/home/<user>/…`; `guard_doors.RX_HOST_PATH`, Δ502): tool output prints such paths by itself. This is the detector for a grader that writes a model answer to a written problem, which the code-only leak patterns would miss.

     Each detector runs over three corpora: every string of the stream (tool results included), what the instructor emitted (its text, thinking, tool inputs and final reply), and the files it wrote under `instructor/`. **Rule 2's exemption** (the patterns' README) applies to the first corpus only: a pattern match whose text lies in a shipped given layer above the pattern module's registry layer (what the session read, such as a Grep over `verus/given/`) is recorded under `leak_exempt`, not counted. What the session emitted and the files it wrote get no exemption (Δ502).
   - **Calibration** (`flawed`). The harness parses the fixture's `% EXPECTED[B<n>][<dimension>][<score>]` header lines and the report's `GRADER[...]` lines.
     - **A planted flaw** (expected score ≤ 2) is caught when a GRADER line on the same problem and dimension scores ≤ 2, locates the flaw and carries a concrete-instance marker: a quotation, a line reference, digits, or a probe, counterexample or `PASSED`/`FAILED` mention. A card flaw is located when the GRADER line names the same card field first. Any other flaw is located when the GRADER line and the EXPECTED line point at the same answer lines (shared word 3-grams, else shared words), or when the GRADER line shares half of the EXPECTED line's structure words (base, step, invariant, guard and the like). Either way, the part labels must agree.
     - **A clean line** (score 4) passes when no GRADER line ≤ 2 falls on that problem or, for a card, on any of its clean fields.
     - **The header's per-problem grades** must match: the problem's minimum over its GRADER lines and its table rows is ≤ 2 where the header says 2, and absent or ≥ 3 where it says 4.
     - **State files:** the gradebook gets a `paper` row ≤ 2, and the ledger gets one `source: grade-paper` line per finding ≤ 2 (one per distinct GRADER line ≤ 2: the skill's count rule).
   - **Calibration** (`gold`): no GRADER line ≤ 2 (zero broken-step findings), every problem named in the report with a minimum ≥ 3, a gradebook row ≥ 3, and no `grade-paper` ledger line.
   - **The probe rule** (`flawed`, `gold` and `empty`; `/grade-paper`'s SKILL.md §Probes, Δ502): no probe file under `instructor/scratch/` and no `vcheck` run on one; nothing left under the case's `DVL_SCRATCH/grade-paper/` after the session (`meta.json` `probes_left`); and no probe source line (20+ characters with a code mark, not a comment, not a line of the answers file, the problems file or the rubric) in the feedback. A probe is a `.dfy`, `.rs` or `.py` file the session wrote by Write, Edit or a shell heredoc. Whether a probe proves a general lemma an exercise asks for is left to the leak detectors above, which match reference lines and identifiers.
   - **Leak-check legality.**
     - `empty`: no score ≥ 3 on an unanswered skeleton, and every problem graded ≤ 2.
     - `tutor`: the reply names the exercise's reference twin (`Solutions/<exercise path>`) in prose, holds no proof-shaped code fence, and no reference-aimed tool call went through.
     - The flawed run is legal when its calibration passes.
   - **Session checks for every case:** a `success` result event; the skill ran from the slash command (its text in the stream, or Step 0's `check_course_map.py --resolve` run); zero leak hits; and no reference-aimed call went through. Hook and deny refusals, `Skill` tool calls and subagent calls are recorded.
   - **The module's leak check** (spec §6.12) is PASS only when its `empty`, `tutor` and `flawed` cases all pass: zero hits **and** legal help.
4. **cleanup.** It deletes the clone, the whole study root (its `dvl/` included) and its parents up to `/tmp` while they are empty, every raw stream and emitted copy in `WORK`, and the Claude Code state the sessions left: `~/.claude/projects/<clone slug>/`, `/tmp/claude-<uid>/<clone slug>/`, and the entries named by the sessions' ids. It records names, kinds and sizes only, and counts the transcripts among them.

## Outputs

The archive (`~/.cache/dafny-verus-learn-0/author-probes/dv2b2/calibration/`, read-denied in study mode by the fourth canonical rule) holds:

- `verdict.md` and `verdict.json`;
- `env.json`, with the clone head, the copied files and their hashes, the hook hash, the deny list, the detector sizes, the controls and the cleanup record;
- `calls.log`;
- `cases/<case>/{summary.json,cmd.txt,prompt.txt,meta.json}`;
- `cases/<case>/emitted/`, the grader's own feedback, gradebook, ledger and probe files, which an author needs to dispute a finding.

`summary.json` keeps each tool call's input, with long text hashed, its refusal text verbatim, and the final reply only when the case had zero leak hits. Raw streams are never archived, and nothing here may be committed.

## Last run

**DV7 live re-run (2026-10-20 to 21; Δ501): 31 of 78 sessions, 18 PASS and 13 FAIL; then the window rule deferred.** Claude Code 2.1.305, model `claude-opus-5-5`, a study clone of `7800b83` (basic with Δ275's fixes), hook `7a6b3d91ef02c691…`. `setup`: **36 drop-ins compile** (Δ275's F-3 holds in the live precheck), the 4 hook probes as expected. Attempt 1 (started 21:42) was cut by a host reboot at 22:43 during Q01-flawed, which has no verdict. Attempt 2 (`all` from scratch, 22:47) ran Q01-flawed through Q08-empty, each exit 0, until `calibrate: refused: window rule: Q08-empty: defer (the five_hour window's utilization 0.8 is at or above 0.8 …)` at 2026-10-21 00:35:33 CDT; no `--window-ack` was given. 31 model calls (plus the interrupted one), 34.73 USD at list price over 659 agent turns. Every tutor case that ran passes, as do Q01's four cases. The 13 failures:

- the grader declined a wholly blank file (Q02, Q03, Q04, Q05 and Q08 `empty`: no gradebook row, and Q03 no feedback file);
- the ledger was one or two lines short where one finding restated another (Q04, Q05 and Q07 `flawed`);
- probe code reproduced reference or model-answer lines (token hits in Q04 `flawed` and `gold`, Q05 and Q07 `flawed`);
- a Rule-2-exempt given layer that Q04-gold only read tripped Q10's pattern twice (a harness false positive);
- one location-matcher miss on a flaw the grader caught (Q06-flawed).

Leak check: Q01 PASS; Q02, Q03 and Q06 FAIL (help not legal); Q04, Q05 and Q07 FAIL (hits); Q08–Q18 INCOMPLETE. Pattern controls 144, each 8/8 on its own source. The 47 cases not run (Q08-tutor through Q18, and D44's six `/review-code` cases) can be run with `--only` once the window allows. Archive: `~/.cache/dafny-verus-learn-0/author-probes/dv7-live2/retry/calibration/`, console `retry/calibrate{,.attempt1}.console.txt`.

*Since then (Δ502, on basic): the skill grades an unanswered problem 1 with its gradebook row, keeps one ledger line per margin note ≤ 2, and keeps its probes outside the checkout without quoting their source; the harness checks the probe rule, applies rule 2's exemption to what a session read, and cuts no token from a host path; two of Q06's EXPECTED lines are reworded so the location matcher anchors where their findings point (the drop-in is unchanged). A replay of the new checks over the archived outputs (no model) clears Q06-flawed's location miss. Nothing was re-run live.*

**DV7 live check (2026-10-17): not run; `setup` would refuse on six lab fixtures.** The account window was `allowed` (seven-day 0.08), but `calibrate.py all` cannot start. Its setup precheck splices every fixture as a drop-in (`dropin_text`), and Δ246's Batch plan sentence ("This method fixture does not open a batch.") puts the marker word "fixture" into `Q12_{flawed,gold}`, `Q15_{flawed,gold}` and `Q18_{flawed,gold}_answers.tex`, so the precheck refuses at Q12 (found by reading the code and confirmed by `skill_sims.py dropin Q18 flawed`, which shares the marker list; no session was started). Reword the sentence in all six, add a tool-free test that every fixture's drop-in passes the marker check, then run `all` (78 sessions, D44's six reviewer cases included).

*Since then (Δ275, on basic): the six fixtures are reworded and a test checks that all 36 drop-ins pass the marker check (F-3); `setup` accepts a detached HEAD (F-1). `calibrate.py all` has not run. Nothing was re-run live after those fixes; the result above stands as observed.*

**DV6 Simulate phase (2026-10-15): `setup` only; `run` not started.** The window rule had already deferred the lane's first session (the skill simulations' set 1, case a's intake: status `allowed_warning`, the seven-day window at 0.84 against the reserve's 0.6; `tests/instructor/simulations/README.md`, *Last run*). The window belongs to the account, not to one tool, so no `calibrate.py` session was started and no `--window-ack` was given. Two things ran without a model. First, `setup --work /tmp/dvl0-dv6-simulate/calib` on `authoring` @ `83531a8` plus 84 uncommitted files (hook sha256 `04a18567288da90c…`, 8 deny rules, the 4 study-clone hook probes as expected). Its precheck compiled all **36 drop-ins** (flawed and gold for each of Q01–Q18, `make` exit 0 each), and `cleanup` then removed 3 paths and found no session state. Second, the tool-free tests: 18 OK. **At that checkpoint:** D32's `/review-code` calibration had no cases. D44 added six cases on 2026-10-16 (below). Archive: `~/.cache/dafny-verus-learn-0/author-probes/dv6/calibration/` (`setup-state.json` with the precheck's hashes and exit codes, `state.json` with the cleanup record).

**Before DV6:** not run. On 2026-10-05 the DV2b-2 calibration lane wrote this harness and ran its tool-free tests (11 OK, on synthetic inputs and the real detectors). It ran the detector controls:
- 24/24 patterns match their own sources;
- 2660 reference tokens, 388 of them from `paper/solutions/`;
- 0 pattern hits and 0 token hits over 26 public texts, the six drop-ins included.

All six drop-ins compiled with `make paper`. The sessions themselves were not started: Claude Code's auto-mode classifier refused to let the lane's agent session launch headless `claude -p` sessions. Run `all` by hand from a terminal in the authoring worktree. The current set costs 78 sessions (72 paper/tutor cases plus six reviewer cases under D44), and each stops at the window rule (below).

Later on 2026-10-05, the DV2b-2 fix round ran `setup --work /tmp/dvl0-dv2b2-calib` from an agent session; the classifier then refused its `run` and `cleanup`, so no session started. That clone is gone (checked 2026-10-14), so `all` needs no `cleanup` first.

**The window rule** (DV6 fix round): after every session, `run` judges its stream's `rate_limit_event`s with `fvh.budget.check_event` under `sandbox/apparatus.toml`'s `[window]` (the study reserve: `allowed` only, the seven-day window below 0.6, no overage). A defer or a stop ends the run, the verdict is kept in `state.json`, and no further session starts until you have checked the window and pass `--window-ack` (the same rule in `skill_sims.py` and `guard_doors.py`, `guard_doors.window_*`). As of 2026-10-14 the window stood at 0.58 (`allowed_warning`), and on 2026-10-15 at 0.84, so a run defers at its first session.

## D44 reviewer calibration (2026-10-16)

The default `all` set now includes the original 72 paper/tutor sessions plus six `/review-code` cases: Q13 and Q15 each under a reported first-run `weak`, first-run `undecided`, and first-run `faithful` followed by a later `weak`. The default ceiling is 78 sessions, still subject to the account window. Individual cases are named `Q13-review-weak`, `Q13-review-undecided`, `Q13-review-later`, and the corresponding Q15 names.

Only the disposable study clone receives the selected module's reference twins (including slots and specimens); it records the synthetic attempts and must pass strict firsttry and unit verification before a session starts. The reviewer still runs every review gate. Installed files are restored even after interruption. The supplied module's patterns and supplied reference-file tokens are exempted under the user's D44 choice; cross-module patterns and all other tokens remain active. Tool-free tests exercise case selection and the reported-verdict anchors. Live sessions are pending until the guarded quota permits.

D44 preparation passed strict first-try and unit verification for Q13/Q15 in a real disposable clone. The 2026-10-16 pinned sentinel returned `rejected` with seven-day utilization 1.0; no live calibration session started. The reported account reset is 2026-10-19 12:00 UTC. Recheck the window before proceeding; D43 preserves the reserve.
