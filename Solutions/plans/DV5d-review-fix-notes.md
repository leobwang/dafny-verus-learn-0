# DV5d review fix lane: the three reviews' findings (harness, admission, leakage and claims)

Author-only notes (reference class). The lane's brief: re-verify each finding of the three
DV5d reviews, fix every major and the cheap minors, re-run the affected checks, and give
DELTAS-ready text. Like Δ195–Δ217, nothing here names an answer, a reference statement or
an invariant. Memory share 32 GB (each solver job inside `systemd-run --user --scope -p
MemoryMax=32G -p MemorySwapMax=0`, under the wrappers' own caps, one job at a time;
`free -g` showed 97 GB available before each). Scratch `/tmp/dvl0-dv5d-reviewfix/`
(removed at the end); archive `~/.cache/dafny-verus-learn-0/author-probes/dv5d/reviewfix/`.

## 1. Outcomes, finding by finding

Review 1 (harness: the agent-mode route):

| # | sev | finding | reproduced | outcome |
|---|---|---|---|---|
| 1.1 | major | `Batch.live` turns False once `open()`'s preflight builds the live agent route: no calendar lock, no `--calendar-fd`, no server check, no state reap, no unload under `fvh run` | yes, by reading: `live` was `transports is None and agent is None`, and `_agent_route()` assigns `self.agent` | **fixed**: `self._live` is fixed in `__init__` from the injected routes; `live` returns it. New test `test_a_live_agent_batch_holds_the_calendar_lock_and_unloads` (LiveAgent, GpuCalendar, HostGate, `server_check` and `_reap_state` stubbed): after `open()` the batch is still live; one lock, one unlock, one server check, one reap, one unload; the session's `calendar_fd` is set; the run's apparatus carries `model_server_found` |
| 1.2 | major | a session that ends without `sandbox.json` reports 0 calls although its gate counted requests; the attempt is then re-issuable `infra-failed` after model output (Δ208) | yes (by reading `run_segment`'s early returns and `_agent_loop`'s `calls == 0` test) | **fixed**: `fvh.backends.agent._counted` fills calls, GPU-s, tokens, `capped`, `ctx_saturated` from `seg-<k>/gate-counts.json` on every early return (session timeout, self-test failed, sandbox refused or failed); an exit 137/143 or a signal (−9, −15) with no record is `ended_by = "killed-memory"`; `_agent_loop` decides "had output" by `calls > 0 or _had_output(rd)` and maps `killed-memory` after output to `truncated:host-memory`, any other non-zero exit after output to `truncated:container`. Tests: `test_the_live_routes_early_returns_carry_the_gates_counts` (fake `mksandbox-run`: timeout, −9, 137, exit 1 each give calls 5, GPU-s 40) and `test_a_session_ended_without_its_record_after_a_request_is_scored` (three cases: scored, the ledger's calls 3, nothing re-issuable) |
| 1.3 | minor | arm G's refused-stop brief in agent mode gives 20 reasons and no plain-gate verdict, unlike the harness-executed arm and the chapter | yes | **fixed**: the brief carries the gate's word, `reasons[:5]` and "The plain gate (`vcheck --gate`) on your files: <verdict>" (the refusal now carries `vcheck`); test `test_a_refused_stops_brief_carries_five_reasons_and_the_plain_verdict` |
| 1.4 | minor | an agent arm with `wall_s` < 120, or no room for a session, is scored `error` with no model call | yes | **fixed**: `load_plan` refuses an agent arm with `wall_s < AGENT_MIN_WALL_S` (120); `_agent_loop` sets outcome `deferred` (with the reason) when no session could start at all, which stops the batch between attempts. Tests: the `wall_s = 60` case in `test_an_agent_arm_is_checked`; `test_an_attempt_with_no_room_for_a_session_is_deferred` |
| 1.5 | minor | `fvh report --judge all` judges and counts runs of an excluded or unscored outcome | yes | **fixed**: `fvh.judging.judge` lists a run whose outcome is in `runlog.UNSCORED` or `EXCLUSIONS` as `Judged(..., excluded=True)` ("excluded outcome <x>: not judged") and stages nothing for it; the command's tally and exit count only the other runs and say how many were excluded. Test `test_runs_of_an_excluded_outcome_are_not_judged_or_counted` |
| 1.6 | minor | the recalibrated attestation scan does not catch a line a learner-visible file also shows, nor a single answer line under 10 tokens | not re-run (the review's planted sample; the limit is in the scan's design) | **no code change** (a tripwire, as the guard's threat model says); the limit goes into the DELTAS text (§3) |

Review 2 (admission and minutes):

| # | sev | finding | reproduced | outcome |
|---|---|---|---|---|
| 2.1 | major | an admitted H item with no hole and no `statement-item` exception gets no gate and `--empty-body` passes | yes, in process on a copy of Q18's record with H2d's exception removed: statement route items `['Q18.H2v']` only | **fixed**: `firsttry.ungated_items`; `mode_empty_body` prints `? <ID>  admitted with no hole and no statement-item exception: no gate` and fails. After the fix the same probe gives `ungated ['Q18.H2d']`; a sweep over every authoring module (Q01–Q18) finds no ungated admitted item on the tree. Tests: two new cases in `test_capstone_routes_static.py` |
| 2.2 | major | `statement-item` is accepted on any prose block, contractor or not (beyond D6) | yes (by reading `statement_item_problem`) | **fixed**: a prose block takes the kind only with one `// contractor: <ID>` line naming an A item of the same module in one of its agentic files; an item of an agentic file is accepted as before. Q17.H3d's block (learner file and twin) gains `// contractor: Q17.A1d`. `test_course_map.py`: the unit covers a prose block with a contractor, without one, with a non-A contractor and with a contractor outside the module; a new case refuses `statement-item` on Q15.H3d. The judging lane's DECISION NEEDED item 1 is reworded (option (a) now asks the user for a new kind) |
| 2.3 | minor | the DELTAS-ready Δ173 bullet in `DV5d-decisions-notes.md` states a general rule beyond D11 | yes | **fixed**: the bullet is scoped to Q15.H1d (8 minutes, rubric C1's reader), the clause on Δ214's forms dropped |
| 2.4 | minor | QPLAN's §27.2, §27 block, §25 block, §28.2, §28.8 disagree with the registry | yes | **fixed**: §27.2's H3d row and §28.2's H2d/H2v cells say admitted (35, 12, 13) and under which decision; **As built** notes after the §25, §27 and §28 registry blocks point to `MODULES.toml` and name the admissions (Q15.H4v 18 included) |

Review 3 (leakage and claims):

| # | sev | finding | reproduced | outcome |
|---|---|---|---|---|
| 3.1 | major | arm G and arm P are described only as they run harness-executed (chapter, rubric CA.d, template, solutions, gold fixture) | yes | **fixed**: chapter §5 gains the agent-mode paragraph (no `Verify` action; the stop is arm G's `Verify`; gate v2 outside the container at each stop; a refused stop continues in a new session with the gate's word, up to five reasons and the plain gate's verdict; the in-container `vcheck --gate` runs are tool calls; arm P judged once when the run ends); rubric CA.d, the template's Arms field ("what a `Verify` or, in agent mode, a stop runs"), the solutions' Arms and routes item and both Q18 fixtures (gold and flawed: the same Arms text, so the flawed fixture's planted flaws stay B1, B2, B4) match. Rubric pins refreshed. Calibrate's Q18 cases are not re-run here (they call a model): open |
| 3.2 | major | the Q18 chapter §0 says Qwen's agent-mode batches are not built | yes | **fixed**: the pending item removed; §0 says the Qwen arms run in agent mode on unsealed, attested task files; "Do the work in this order: …" |
| 3.3 | major | the template's `\texttt{plan-sha256:} <hex>` form does not parse | yes (the regex allowed only blanks after the colon) | **fixed** in the parser (no answers-file change, so no re-grade): `fvh.prereg._PLAN` accepts `}`, `~`, `\ ` and a second `\texttt{` between the colon and the digits, never a line break. `test_prereg.py` covers the six filled-in forms and a line-broken value (refused) |
| 3.4 | major | the Q18 rubric's gate_v2 twin pin is stale | yes: `update_rubric_pins.sh --check` STALE at `Q18_rubric.md:14` | **fixed**: `update_rubric_pins.sh` (3 pins: Q18's gate_v2 twin, Q18's solutions after 3.1, Q17's Vcgen twin after 2.2), then `--check`: all 111 current |
| 3.5 | minor | the agent brief says the in-container `vcheck --gate` checks the task "the way it is judged" | yes | **fixed**: "runs the course's gate on the task … It is not the judgement: your files are judged outside this container, by the lab gate, which also checks that the task's fixed parts are unchanged" (or "by the course's gate" for a plan without the lever check), ", and each stop by the acceptance gate" for a gated arm. The brief is already hashed into the run's `prompt_hashes` |
| 3.6 | minor | `test_pcount_static.py`'s Verus toy reproduces two twin answer lines | yes (the two lines were in the toy) | **fixed**: fields and locals renamed (`size`, `before`, a step of 2); the statement kinds and the asserted tags and counts unchanged; 12 OK |
| 3.7 | minor | the chapter does not say the plant's copy must keep the crate's course path at its end | yes (`runners.course_rel` raises `RunnerUnavailable`) | **fixed**: one clause in step 5 and in §4's live-check paragraph |
| 3.8 | minor | records contradict the build: `sandbox/README.md`'s attested row, QPLAN §28.2 and §28.6, `CLAUDE.md`'s Not-built line, chapter pending sentences | yes | **fixed in part**: `sandbox/README.md`'s row (78 entries: 22, 20, 36); QPLAN §28.2 (2.4) and §28.6 (D10's sentence and D8's agent mode); the Q12 chapter's pools sentence (`bench/public/POOLS.toml`, attested cards). **Left:** `CLAUDE.md`'s Not-built line (not this lane's file: text in §3); the Q13, Q15 and Q17 chapters' and the Lab 2 spec files' "hidden check pending" sentences, which the judging lane already gave to the kits and records lane (they need the learner's route to the prose items' hidden check worded, and the files' pins re-captured) |

## 2. Runs (archive `dv5d/reviewfix/`)

- `harness/tests/core`: 549 passed, sterile (`FVH_NO_MODEL=1 DVL_NO_DOCKER=1`) and plain;
  `tests/sandbox` 164 OK; `tests/harness_adapter` OK; `tests/bench` OK.
- `tests/wrappers` static files: capstone routes 14 OK (2 new), dafny, forms, pcount 12, practice
  tools, tools (1 skipped), verus: all OK.
- `check_course_map.py --root .`: OK (49 modules, 138 import files, 81 coverage rows).
  `scripts/test_course_map.py`: 382 passed, 0 failed (the new Q15.H3d case and the extended
  unit included).
- `firsttry.sh Q17 --empty-body` (32 GB scope): 3/3, exit 0 (H3d's prose gates pass with the
  contractor line in its block). `firsttry.sh Q18 --empty-body --eb-modes STMT`: statement
  items 2/2 (H2d 168 verified, 17 new statements; H2v 29 verified, 14), no ungated item; the
  run's exit 1 is H1v's "no gate run: --eb-modes names only RGN" line, which that mode always
  gives (unchanged by this lane). The full `firsttry.sh Q18 --empty-body` (32 GB scope): 7/7
  holes, statement items 2/2, no ungated item, exit 0.
- `pins.py --update --chapter Q17 --entry units` (32 GB scope): re-captured (the hole line of
  H3d moves from 194 to 195 in the fence; the input hash of `Q17_Vcgen.dfy`); a static check
  of every Q12, Q15, Q17 and Q18 chapter entry's input hashes: none stale.
- `specfreeze --check Q17` 0 findings; `reference_lint` 0 findings (141 twins);
  `chapter_lint Q12` and `Q18` 0 problems; `update_rubric_pins.sh --check` all 111 current;
  `make -C paper` 36 documents; the two Q18 fixtures compile against the preamble (scratch);
  `gen_units --check`, `gen_hook_fixtures --check`, `avoid.sh` OK; the leak README's verifier:
  18 modules, 1,613 public files, OK.

## 3. DELTAS-ready text (for the integration lane to number)

**Δ2xx · The DV5d review fix round: the agent route's live flag and killed sessions, the
refused stop's brief, the judging tally, the ungated-admission check, the statement-item
kind's contractor, the plan field's LaTeX forms, Lab 3's agent-mode text — adopted (DV5d,
2026-10-13)**
- **Status:** three reviews of the DV5d round (harness, admission, leakage and claims) raised
  18 findings (8 major, 10 minor); the fix lane reproduced 17 (one, the attestation scan's
  limit, is a property of its design and is recorded here), fixed all 8 majors and 8 minors in
  full, one minor in part (the records: the rest is listed below). Like Δ195–Δ217 it names no
  answer; the detail is in `Solutions/plans/DV5d-review-fix-notes.md`.
- **Change:**
  - **`fvh.batch`'s live flag** is fixed at construction (`Batch._live`: no test transport
    and no test agent route injected). Under `fvh run`, `open()`'s preflight builds the live
    agent route, and the batch now still takes the GPU calendar lock for the whole batch
    (its fd passed to every agent session), checks the model server (`model_server_found` in
    run.json), reaps stale per-call state and unloads the model at the end, as `fvh resume`
    already did.
  - **A killed agent session's spend:** `fvh.backends.agent` reads the session's
    `gate-counts.json` on every return without the sandbox's record (a timeout, a failed or
    refused sandbox, a failed self-test); exit 137/143 or a signal is `killed-memory`. The
    batch decides "had output" from the counts or the run directory (`_had_output`): after
    output a killed session is `truncated:host-memory` and another failure
    `truncated:container`, scored and never re-issued (Δ208); before output `infra-failed`.
  - **Agent-mode arm G's refused stop** gives the next session the gate's word, up to five
    reasons and the plain gate's verdict, as the harness-executed arm and the Q18 chapter do.
    The brief no longer says the in-container `vcheck --gate` checks the task "the way it is
    judged": it runs the course's gate, and the judgement is the lab gate's (with the lever
    check) outside the container, a gated arm's stops the acceptance gate's.
  - **An agent arm's wall clock:** `load_plan` refuses `wall_s` < 120 s (a session's minimum);
    an attempt with no room for any session is `deferred` (the batch stops), never a scored
    `error`.
  - **`fvh report --judge`** neither judges nor counts a run of an unscored or excluded
    outcome (`runlog.UNSCORED`, `EXCLUSIONS`): it is listed as excluded, and the tally and
    exit are over the other runs (stable interface: `Judged.excluded`, default false).
  - **`firsttry --empty-body` fails on an ungated admission:** an admitted H item that holds
    no hole and carries no `statement-item` exception prints `? <ID>  admitted with no hole and
    no statement-item exception: no gate` and fails the run (`ungated_items`); none exists on
    the tree (a sweep over Q01–Q18).
  - **The `statement-item` kind's contractor** (D6): `check_course_map.py` accepts the kind on
    an item of one of the module's agentic files, or on a prose item whose block names its
    contractor in one `// contractor: <ID>` line, an A item of the same module in an agentic
    file. Q17.H3d's block (learner file and twin) names `Q17.A1d`; a prose item with no
    contractor (Q15's Lab 2 specifications) cannot take the kind (a `test_course_map.py` case).
  - **The plan field's forms:** `fvh.prereg` reads `plan-sha256:` followed by blanks, `}`, `~`,
    `\ ` or a second `\texttt{` before the 64 hex digits (the template's own wording,
    `\texttt{plan-sha256:} <hex>`, now parses), never across a line break.
  - **Lab 3's agent-mode text:** the Q18 chapter §0 no longer lists Qwen's agent-mode batches
    as pending (the Qwen arms run in agent mode on unsealed, attested task files); §5 says how
    arms G and P run in agent mode (the agent's stop is arm G's `Verify`; gate v2 outside the
    container at each stop; the in-container `vcheck` runs are tool calls; arm P judged once
    when the run ends); rubric CA.d, the B2 template's Arms field, the solutions' Arms and
    routes item and the two Q18 fixtures say the same. The chapter's plant step and §4 say the
    copy keeps the crate's course path at its end (else `RunnerUnavailable`).
  - **Re-pins and text:** the rubric pins of Q17 (Vcgen twin) and Q18 (gate_v2 twin, the
    solutions); `expected/Q17.chapter.toml`'s `units` re-captured (H3d's hole line moves by
    one); `tests/wrappers/test_pcount_static.py`'s Verus toy renamed so it repeats no twin
    line; `sandbox/README.md`'s attested row; the Q12 chapter's pools sentence; QPLAN §27.2,
    §28.2, §28.6 and **As built** notes under the §25, §27 and §28 registry blocks.
  - **The attestation scan's limit, recorded** (no change; the scan is a tripwire): a line a
    learner-visible file also shows, or a single answer line under 10 tokens, is not caught
    alone; the leak patterns cover those cases.
- **Why:** each finding reproduced before its fix, by probe or by reading (archive
  `dv5d/reviewfix/`); afterwards the runs in the notes' §2: `harness/tests/core` 549
  (sterile and plain), `tests/sandbox` 164, the wrappers' static files, the course map and its
  suite, `firsttry --empty-body` Q17 3/3 and Q18, the Q17 chapter pin, the rubric pins, the
  paper, the leak verifier.
- **Touches:** Δ173, Δ182, Δ208, Δ212, Δ215, Δ216 (items 11–12, superseded by D8, D10, D17)
  and this round's agent-mode, judging, decisions and pools entries; `harness/fvh/{batch,
  judging,prereg,__main__}.py`, `harness/fvh/backends/agent.py`, `harness/tests/core/
  {test_batch,test_judging,test_prereg}.py`; `scripts/firsttry.py`,
  `scripts/check_course_map.py`, `scripts/test_course_map.py`;
  `tests/wrappers/{test_capstone_routes_static,test_pcount_static}.py`; `dafny/Q/Q17_PracticeIIIB/std/Q17_Vcgen.dfy` and its twin;
  `docs/Q12_PracticeIC.md`, `docs/Q17_PracticeIIIB.md` (the pinned fence), `docs/Q18_PracticeIIIC.md`;
  `paper/Q18_answers.tex`, `paper/solutions/Q18_solutions.tex`, `paper/rubrics/{Q17,Q18}_rubric.md`;
  `tests/instructor/fixtures/Q18_{gold,flawed}_answers.tex`; `expected/Q17.chapter.toml`;
  `sandbox/README.md`; `QPLAN.md`; `Solutions/plans/DV5d-{decisions,judge}-notes.md`.
- **Owner:** DV5d's review fix lane.
- **Open** (owner, severity):
  - **The author (high: before Lab 3 runs; it calls a model).** `calibrate.py`'s Q18 cases
    (the rubric's CA.d and both Q18 fixtures changed), and simulation case g.
  - **The integration lane (medium).** `CLAUDE.md`'s **Not built yet** line: drop the
    agent-mode lab batches, the grader's judging step, the capstone CLI's binary target, the
    public pools and the cards' attestation (built this round); keep step 4c (for R16).
  - **The kits and records lane (medium; the judging lane's item).** The "hidden check is
    recorded as pending" sentences of the Q13, Q15 and Q17 chapters, the headers of
    `Q15_Lab2Specs.dfy` and `lab2_specs.rs`, Q13's rubric A7/C5, and the Q15 chapter's §0 and
    Lab 2 pools sentence; their chapter pins re-captured and the leak verifier re-run.
  - **The user (medium).** The five below-band Q15 prose specifications: `statement-item`
    no longer covers them (a new kind, a shortfall, or a short-format reading; the judging
    notes' §6 item 1, reworded).
