# DV5e learner-visible pending text and records lane (author-only notes)

The lane's brief: reword the learner-visible sentences that still called the hidden check or the
public pools pending to the route the learner actually takes, and write the record items Δ225
assigns the records lane, plus the records items this round's lanes (study root, decisions,
attestation, lab2pub) left for it. No answer, reference statement or weakened statement is
named here or in any file this lane changed. Memory share 16 GB: every solver job and container
inside `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, one at a time, `free -g`
97 GB available at each start. No model was called. Scratch `/tmp/dvl0-dv5e-pendtext/` (removed
at the end); archive `~/.cache/dafny-verus-learn-0/author-probes/dv5e/pendtext/`.

## 1. The learner's route, as built and checked

The hidden check of a prose item (Q13.H3v, Q15.H3d–H5v, Q17.H3d) runs only in the grader
container. Every command that reaches it names the sealed archive, so guard rule 1c refuses it in
a Claude session: the learner starts it from their own terminal.

- A prose item: a judging spec (TOML `[[candidate]]` tables, each an `id` and an `item`; the
  `file` defaults to the learner file), then `scripts/mksandbox-run --truth
  Hidden/labs/<ID>/verdicts.tar.age --truth-check judge --judge <spec>`, one language per run.
  It prints JSON with one verdict word per candidate (`faithful`, `strong`, `weak`, `vacuous`,
  `undecided`, `mismatch`, `context`; `sandbox/image/truthcheck.py`'s docstring defines them).
- A Lab 2 batch: `python -m fvh report Q15 --judge RUN|all --truth Hidden/labs/Q15/verdicts.tar.age`.

Checked by running the documented line exactly as the chapters give it, on the shipped learner
files (no learner work exists; host output archived under `judge/`):

| run | container | result |
|---|---|---|
| `Q15.H3d` (shipped: no specification) | Dafny, 11.5 GB, 13.1 s | exit 0, `"verdict": "weak"`, 72 files unsealed, manifest ok |
| `Q13.H3v` (shipped: no declaration) | Verus, `--mem-gb 16`, 0.4 s | exit 0, `mismatch` ("the file does not hold the declaration as one readable statement") |
| `Q17.H3d` (shipped: no `VcSound`) | Dafny, 0.4 s | exit 0, `mismatch` (the same reason) |

## 2. What changed

**Learner-visible text**

| file | change |
|---|---|
| `docs/Q13_PracticeIIA.md` | §2: the equivalence check's sentence names the sealed reference; a new paragraph *Running the hidden check* (the judging spec as a `toml` fence, the command, the seven verdict words with a gloss each, the report to `/review-code`); §6's row: what the check sees and that an `undecided` difference is a reader's |
| `docs/Q15_PracticeIIC.md` | §0: the judging step and the public strata are built; what is still open (the rule for what a public delivery may add); the order of work. §5: the diagram's grader node; the hidden check for the six (a three-candidate Dafny spec, the command, the verdict words by reference to Q13 §2). §6.2: the public strata as built (form, draw records, `lab2pub.py build --check`, NOTICE, no contamination control). §6.3: the B1 tasks-and-strata field states the recorded draw. §6.4: the acceptance's re-judging line (`fvh report Q15 --judge all --truth …`). §8's row |
| `docs/Q17_PracticeIIIB.md` | §4: a row for the hidden check of `VcSound` (from the learner's terminal, after the run and the AUDIT) |
| `dafny/Q/Q15_PracticeIIC/std/Q15_Lab2Specs.dfy`, `verus/q/q15_practice_iic/src/lab2_specs.rs` | the header's grading paragraph (same line count, so no hole line moved) |
| `paper/rubrics/Q13_rubric.md` | Probe E's parenthesis; A7: record the verdict word the learner reports from their own run, or `not run`; never run or name the archive in the session |
| `paper/rubrics/Q15_rubric.md` | Probe E's parenthesis; RP.c (the "while that container is missing" clause replaced by the learner's `fvh report Q15 --judge` lines); A7 as Q13's; the runs debrief's heading drops "pending"; D12 names the re-judging run |
| `bench/local/q/lab1/STRATUM.toml` | the lab gate's description gains the assumption audit (D24); the public strata's sentence drops "Pending" and names the stripping step and `POOLS.toml` |
| `bench/local/q/lab2/STRATUM.toml` | the composition comment names the built public strata (`lab2pub/`) and the `[[draw]]` records |

**Records**

| file | change |
|---|---|
| `CLAUDE.md` | line 3: `scripts/vcheck --bin <crate> [-- <args>]`; **Not built yet** drops Lab 2's public task forms; **Armed**: Q13–Q15 (the judging step's route, Q15's six prose specifications at 18 under D21, the lab gate's audit D24, Lab 2's public forms built; the open rule for public deliveries), Q16–Q18 (the 36 files re-attested under D25); the guard paragraph: rule 1's study root (D20), rule 1b's author-only steps (`get_bench.sh`/`dvl/bench.py` `--pin`/`--pin-pool`), 1c's `fvh unseal`, 2c's `dvl/bench.py` and `fvh unseal`; §Authoring mode item 2: the study root (D20) |
| `docs/design/DV4-PLAN.md` | §3.5: agent-mode batches as built; §5.4 item 3 (attestation: `attest_data`, `scan`, `pools`, re-attestation, the 78 entries, the ten public cards not yet attested) and item 5 (the scan as built: whole and renamed spans, the generic set, the limits); §5.10: agent sessions' lifecycle; §7.1: `transform`, the `POOLS.toml` and `lab2pub/` rows; §7.2: `--validate`'s rule and flags, `DVL_BENCH_TMP`, `--pin-pool`; §7.3: the pools as built and Lab 2's draw; §8's rule 2c row: 18 block and 10 allow template fixtures, itemized |
| `QPLAN.md` | §19.0's prose-item row; §22.6 (the lab gate as built; the pool rule; the stripping step keeps each loop's `decreases`; the public row); §23.5's As built (the hidden check holds); §25.2's prose-spec row (admitted 18 each, D21); §25.6 As built (the judging route, the public strata, the draw, the open rule); §25.8's As built; §28.8's registry block re-copied from `MODULES.toml`; §30 Q57 and Q63 |
| `harness/fvh/__init__.py` | the docstring names `fvh.backends.agent`, the batch's agent construct and `fvh.statements` (docstring only; `__all__` unchanged) |
| `sandbox/README.md` | the attested row (78 re-attested under `DV5e`; the ten public cards not yet) |
| `VERSIONS.md` | §1.4's judging row: Q15's re-seal (72 files, D22's twin) and the learner line's check |
| `expected/Q15.chapter.toml` | the `units` entry's two inputs re-pinned (`pins.py --update --chapter Q15 --entry units`; the body unchanged) |

## 3. Checks (final tree)

`chapter_lint --all` 18 chapters, 0 problems (before the re-capture: 1, Q15's `units` pin stale
on its two changed inputs); `pins.py --update --chapter Q15 --entry units` captured, body
unchanged; `pins.py --ci` 823 pins over 18 modules, 0 problems, and after the last prose edits
`--module Q13` 11, `Q15` 60, `Q17` 15, 0 problems; `update_rubric_pins.sh` 0 written of 111,
`--check` all current; the leak README's verifier, 18 modules over 1,631 public files, OK;
`check_course_map.py` OK and `--only vocab` OK; `specfreeze --check Q15` 0 findings;
`check_single_route.py` 0 outside the allowlist (a first docstring wording named the agent CLI
and was refused; reworded); `harness/tests/core` 549 passed; the two STRATUM files parse. The
documented Q15 spec of three Dafny candidates, run as written on the shipped file: exit 0,
three verdicts, 51 s.

## 4. Decisions for the user

1. **A learner-reported hidden-check verdict in the code review** (Q13 C5, Q15 C4, Q17's reader).
   As built: A7 records the verdict word the learner reports from their own run (or `not run`);
   no row's grade rests on it. Options: (a) as built; (b) a reported `weak`, `strong`,
   `vacuous` or `mismatch` is the anchor of a C5/C4 finding at grade 2 (an `undecided` stays the
   reader's), as D21's "graded by its hidden two-way check" suggests (recommended; the
   calibration of `/review-code` on Q13 and Q15 then re-runs); (c) the review asks for the
   verdict line first and caps C5/C4 at 3 without one.
2. **Where Q17's hidden check sits in the learner's sequence.** As built: §4's instrument row
   only, "after the run and your AUDIT", so the contract run and the audit stay the place a
   false statement is found (the chapter's §3 and §7). Options: (a) as built (recommended);
   (b) leave the chapter silent (the check stays an admission instrument only); (c) before the
   statements are committed (the contract run's lesson weakens).

## 5. Open items (owner, severity)

- **The user (medium):** §4's two items; lab2pub's four DECISION NEEDED items stand (the
  chapter's §0 and QPLAN §25.6 name the public-delivery rule as open).
- **The attestation owner (low–medium):** Lab 2's ten public cards are not in
  `sandbox/attested.toml`; any sandbox that stages them by `src` refuses them (DV4-PLAN §5.4
  item 3 and `sandbox/README.md` say so). If the lab2pub definitions decision rebuilds the
  forms, attest after it.
- **The kits lane (low):** the Q15 bank's K-probe gloss and "Q13's hidden check is the same
  pair" (the decisions lane's item) are unchanged; the Q13 and Q15 banks could name the
  learner's judging route.
- **The author (low):** the rubric text of Q13 A7 and Probe E and Q15 Probe E, RP.c, A7 and
  D12 changed, so `calibrate.py all` (already the author's) covers them.

## 6. DELTAS-ready text (for the integration lane to number)

### Δ2xx · The learner's route to the hidden check, worded; the public strata no longer pending; records for DV5d and DV5e — adopted (DV5e, 2026-10-13)
- **Status:** closes Δ225's kits-and-records item (the learner-visible sentences that called the hidden check or the pools pending) and its records-lane item, and the records items of this round's study-root, decisions, attestation and Lab 2 public-forms lanes that sit in the files below. Like Δ195–Δ225, it names no answer, no reference statement and no weakened statement. Detail: `Solutions/plans/DV5e-records-notes.md`.
- **Change:**
  - **The route, worded where the learner reads it.** The hidden check runs only in the grader container, and every line that reaches it names the sealed archive, so guard rule 1c refuses it in a Claude session: the learner starts it from their own terminal. A prose item: a judging spec of `[[candidate]]` tables (`id`, `item`; the `file` defaults to the learner file), then `scripts/mksandbox-run --truth Hidden/labs/<ID>/verdicts.tar.age --truth-check judge --judge <spec>`, one language per run, one verdict word per candidate (`faithful`, `strong`, `weak`, `vacuous`, `undecided`, `mismatch`, `context`, as `sandbox/image/truthcheck.py` defines them). A Lab 2 batch: `python -m fvh report Q15 --judge all --truth Hidden/labs/Q15/verdicts.tar.age`. `docs/Q13_PracticeIIA.md` §2 (a new paragraph, *Running the hidden check*) and §6's row; `docs/Q15_PracticeIIC.md` §0, §5 (the six, a Dafny spec of three candidates), §6.4 (the acceptance's re-judging line) and §8's row; `docs/Q17_PracticeIIIB.md` §4 (a row: `VcSound`'s check, after the run and the AUDIT); the headers of `Q15_Lab2Specs.dfy` and `lab2_specs.rs` (same line count); rubrics: Q13's Probe E and A7, Q15's Probe E, RP.c, A7, the runs debrief's heading and D12 (A7: the reviewer records the verdict word the learner reports from that run, or `not run`, never runs or names the archive, never records it as passed or failed itself).
  - **The public strata, as built, where the learner reads them.** `docs/Q15_PracticeIIC.md` §6.2 (the form, the draw's records in `bench/public/POOLS.toml`, `lab2pub.py build --check`, NOTICE; public, so no contamination control) and §6.3 (B1's tasks-and-strata field states the recorded draw; the template and rubric CT.c are unchanged, since the draw's seeds, commits and digests are recorded); §0 names the one open rule (what a public delivery may add besides its specification). `bench/local/q/lab1/STRATUM.toml` (the lab gate's assumption audit, D24; the stripping step and `POOLS.toml`) and `lab2/STRATUM.toml` (the public strata built in `lab2pub/`).
  - **Records.** `CLAUDE.md`: `vcheck --bin` in the tool line; the **Not built yet** line drops Lab 2's public task forms; the **Armed** line's Q13–Q15 and Q16–Q18 clauses (D21, D24, D25, the public forms, the open public-delivery rule); the guard paragraph (rule 1's study root, D20; rule 1b's `get_bench.sh` and `dvl/bench.py` `--pin`/`--pin-pool`; 1c's and 2c's `fvh unseal`; 2c's `dvl/bench.py`); §Authoring mode item 2 (the study root). DV4-PLAN §3.5 (agent-mode batches), §5.4 items 3 and 5 (the attestation and the scan as built), §5.10 (agent sessions), §7.1–§7.3 (`transform`, `POOLS.toml` and its `[[draw]]` records, `lab2pub/`, `--validate`'s rule and flags, `DVL_BENCH_TMP`, `--pin-pool`, the pools), and rule 2c's row (18 block, 10 allow template fixtures). QPLAN §19.0's prose-item row, §22.6, §23.5, §25.2's prose row, §25.6 and §25.8 (As built), §28.8's registry block (re-copied from `MODULES.toml`), §30 Q57 and Q63. `harness/fvh/__init__.py`'s docstring (`fvh.backends.agent`, the agent construct, `fvh.statements`). `sandbox/README.md`'s attested row. `VERSIONS.md` §1.4's judging row (Q15's 72-file re-seal; Q13's and Q17's archives keep the earlier oracles copy).
  - **Pins:** `expected/Q15.chapter.toml`'s `units` entry re-captured for its two changed inputs (the body unchanged).
- **Why:** the documented line, run as written on the shipped learner files (no learner work exists): `Q15.H3d` judged `weak` (Dafny container, 13.1 s, 72 files unsealed, manifest ok), `Q13.H3v` and `Q17.H3d` `mismatch` (no declaration yet); no model call. `chapter_lint --all` 18 chapters, 0 problems; `pins.py --ci` 823 pins, 0 problems; `update_rubric_pins.sh` 0 of 111 written and `--check` current; the leak verifier, 18 modules over 1,631 public files, OK; `check_course_map.py` and `--only vocab` OK; `specfreeze --check Q15` 0 findings. Archive `dv5e/pendtext/`.
- **Touches:** Δ173, Δ208, Δ215, Δ219–Δ225; the files above.
- **Owner:** DV5e's learner-visible text and records lane.
- **Open:** the user: whether a reported non-faithful verdict is a code-review finding, and where Q17's check sits (the notes §4); the attestation owner: Lab 2's ten public cards; the kits lane: the Q13 and Q15 banks; the author: `calibrate.py all` covers the changed rubric rows.
