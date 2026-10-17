# DV6 — the scan and grading decisions D31–D35 (lane notes, 2026-10-14)

Author-only (Solutions/). The DV6 scan-and-grading lane applied the user's decisions D31, D32,
D33 and confirmed D34 and D35 (Δ232 items 5, 6, 8, 7 and 9; each the recommended option).
Memory share 8 GB: no solver job ran in this lane (the scan is Python; every run below sat in
a `systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0` scope). No reference text,
reference statement or weakened statement appears here: the sealed references are named by
label, and every figure is a count. Archive: `~/.cache/dafny-verus-learn-0/author-probes/dv6/scangrade/`
(the measurement and re-scan logs, counts and labels only, the scripts, `attested.toml` before).

## 1. D31 — the sealed references are twins of the attestation scan

**Built** (`scripts/dvl/sandbox.py`, the section "the sealed references as twins"):

- `sealed_reference_twins(root)` → `([SealedTwin], "<n> twins, sha256 <16 hex>")`. Two sources:
  - **Lab 2** (`_lab2_twins`): every `[[lab]]` of `sandbox/truth.toml` that a local stratum
    without an archive names by its `lab` (today `lab2/` and `lab2pub/` name Q15; Lab 1's
    stratum names Q12, which has no truth lab: its references are the `Solutions/bench/local/`
    twins already). The archive is decrypted into memory (`_sealed_tree`: archive sha256, the
    pinned age binary's sha256, the key's location, the manifest's sha256, its file count and
    every file's digest checked; both manifest layouts, `labs/<lab>/…` and bare, are read).
    Per card two twins against the card's own task form (`task_form`, which must be a card path
    present in the tree): the reference program (`tasks/<card>/<card>.dfy|.rs`) and the
    reference statement (`reference.toml`'s `definitions`, `requires`, `ensures`, one per line,
    so D28's sealed definitions join it with no further change).
  - **Lab 3** (`_lab3_twins`): every stratum with an archive must have an entry in
    `SEALED_REFERENCE_DIRS` (today `bench/local/q/crate` → the Q18 lane's author archive
    `~/.cache/dafny-verus-learn-0/author-probes/dv5c/q18/crate-src/refs`, in the reference
    class). Its task forms are decrypted into memory; each `refs/<card>/<path>` is paired with
    `<card>/tasks/<path>`; a `possible` card with no reference refuses.
- **Never written.** Plaintext lives only in the process (`age --decrypt` to a pipe;
  `SealedTwin.twin`/`learner` and `Span.shingles`/`forms` are `repr=False`). Every failure is a
  `SealedRefsError` that names the source and the check, never its text; any other exception
  while the sealed twins are in memory (building the index, or a card's lookup in
  `author_scan`) is re-raised as `SealedRefsError("… (<type>); its message is withheld")` with
  its context suppressed.
- **Fail-closed.** A declared source that cannot be read (no key, a changed archive, a missing
  task form or reference) refuses the attestation and leaves `sandbox/attested.toml` byte for
  byte unchanged: no entry is added, rewritten or withdrawn. A throwaway root with no truth lab
  named by a stratum and no sealed stratum reads no sealed twin (the existing suites' roots).
- **One difference from the course's twins (an interface decision of this lane).** For a
  sealed twin's exact test the pool-common shingles are not set aside, only text a
  learner-visible course file shows (`Span.sealed`; `ScanIndex`'s docstring). Measured first
  under the course rule: 10 of the 68 sealed twins had no span that counted (the nine public
  cards' reference statements and dp3's program), because Lab 2's public cards are drawn from
  the installed upstream sets, which hold their statements; the pool rule set aside the very
  copy D31 exists to catch. The renamed test keeps every set-aside. This is D35's fail-closed
  reading carried to the new twins; it moved no entry (0 hits on all 88 files below).
- **`SCAN_RULE = "DV6"`; each entry records `refs`** (the sealed twins' digest) beside `scan`
  and `pools`. "Already attested" now needs the same rule and the same `refs`, so a re-seal of
  Q15 or a changed Lab 3 reference makes every entry current no more until it is re-scanned.
- **`rescan_attested(root)`** and **`scripts/mksandbox-run --author --attest-rescan`**: every
  entry re-scanned under the current rule, one line per entry (`re-attested`, `already`,
  `withdrawn`, `stale`, `refused`) and a tally; an entry of a sealed stratum takes its bytes from
  the archive decrypted into memory, at the path `fvh unseal` writes; exit 1 on any withdrawn,
  stale or refused entry, 3 when nothing could be scanned.

**Measured on the real archives (2026-10-14; counts only):**

| measure | result |
|---|---|
| sealed twins read | 68 (30 Lab 2 reference programs, 30 Lab 2 reference statements, 8 Lab 3 reference deliveries); `68 twins, sha256 7a896df3d3f1c4a4`; decryption under 1 s, the index 16.5 s |
| spans | 369 sealed of 5,524; 366 count for the exact test, 243 for the renamed test |
| twins with no counting span | course rule: 10; DV6 rule: 0 |
| twins with no span of 10 tokens | 1: Lab 3's c07 reference differs from its task form in two blocks of 6 and 7 tokens (a known limit, as DV5e's single short line; the task form's counted stub holes and the lab gate remain) |
| the 78 attested entries and the 10 public cards (88 files) | 0 hits, sealed or course |
| each sealed twin's own text as an invented card | caught 67 of 68 (c07 missed) |
| each twin's answer blocks planted into d01 or v01 by language | caught 67 of 68 (c07) |
| the same, every identifier renamed | caught 56 of 68 |
| the files this lane wrote (these notes included) and its scratch logs | 0 sealed-span hits (21 files) |

**Re-scan of every entry** (`mksandbox-run --author --attest-rescan`, 8 GB scope): 78 of 78
re-attested under DV6 (Lab 1's 22, Lab 2's 20 local cards, Lab 3's 36 sealed files from the
archive in memory); every sha256, path and `source` unchanged; each entry now carries
`scan = "DV6"`, `refs = "68 twins, sha256 7a896df3d3f1c4a4"`, `attested = "2026-10-14"`. The
file's header and `sandbox/README.md`'s attested row say so.

**Tests** (`tests/sandbox/test_sandbox.py`, `AttestSealedReferences`, 10 cases; decoys in
throwaway roots; a fake age that decodes a base64 "archive", so no plaintext sits on disk; a
canary word inside each sealed decoy): the twins and their labels; the cards themselves
attested with `refs` recorded; a planted Lab 2 reference statement and a planted Lab 3
reference delivery in invented cards refused, naming the sealed label; a sealed reference
still counts when two pool files show it; an unreadable source (the key removed) refuses and
changes nothing, the re-scan too; a changed archive refuses on its pin; a crash path while the
references are in memory (the index build, and a card's lookup) reports `withheld`, and the
canary is in no message, traceback, captured stream, repr or file; every entry re-scanned once
with a result each (`re-attested`, `re-attested`, `withdrawn`, `stale`; then `already`; then,
after the reference changes, `re-attested` again); the CLI's per-entry lines and tally.
`tests/sandbox` 182 OK (172 + 10); `harness/tests/core/test_batch.py` 53 passed.

## 2. D32 — a reported verdict anchors the finding at grade 2

`paper/rubrics/Q13_rubric.md` C5, `Q15_rubric.md` C4 (per specification) and `Q17_rubric.md` C6
(the statements reader, `VcSound`): a reported `strong`, `weak`, `vacuous` or `mismatch` from
the first run (A7) is a finding at grade 2, whatever Probe E shows, stated with the verdict
word and the outcome words as reported, then read for where the statement differs (never
guessing or stating the author's); `undecided` anchors nothing (the reader decides it);
`faithful`, `context` and `not run` leave the line to the reading. A grade-1 finding of another
kind stands (Q15's changed code line, Q17's specialized statement). "Do not invent a flaw" now
also needs no anchoring verdict. `.claude/skills/review-code/SKILL.md` gains one Hard rule: a
hidden check's verdict is the learner's report; where a rubric records it, its focus line says
what it anchors (grade 2; `undecided` the reader's call); never run the check, name its
archive or record it as passed or failed.

**Calibration fixtures:** none reads the changed rows. `tests/instructor/fixtures/Q1[357]_*`
are `/grade-paper`'s written answers (B1, B2, …) and `calibrate.py`'s cases are `flawed`,
`gold`, `empty` and `tutor`; no simulation case drives `/review-code`. So nothing was updated
here; `/review-code`'s calibration on Q13 and Q15 re-runs in the Simulate phase, as D32 says.

## 3. D33 — run the hidden check once, report the first run

- `docs/Q13_PracticeIIA.md` §2: "once your statement is final", and a paragraph **Run it once
  per item, and report the first run** (after the use site and the witness pass and a last
  read against the prose; the outcome words show side and direction, so a second run after a
  fix made from them measures the check's hints; a later run is reported beside the first, as
  later; what a reported word counts for in the review).
- `docs/Q15_PracticeIIC.md` §5: "once a specification is final", and the same rule per
  specification by reference to Q13's §2. §6.4 (a batch's re-judging) is unchanged.
- `docs/Q17_PracticeIIIB.md` §4's instrument row: the rule named beside Q13's §2.
- A7 in the three rubrics: the first run's word and its outcome words recorded, `not run`
  without one, a later run recorded as later and anchoring nothing (Q17's A7 gains the line;
  it had none).
- **Open (the image owner, next image rebuild):** `truthcheck`'s prose rows print the verdict
  and why only (D33 defers it): an image rebuild, `images_lock_sha256`, the chapters' glosses
  of the outcome words (Q13 §2, Q15 §5, Q17's row), A7's "with the outcome words they paste",
  the chapter pins and the leak verifier.

Checks: `chapter_lint` Q13, Q15, Q17 0 problems; every pinned fence byte-identical to HEAD (3,
26, 8), so no chapter pin was re-captured; `update_rubric_pins.sh --check` 111 current (no
rubric's pinned sources changed: nothing to re-capture). **Not run here:** `pins.py --ci
--module Q13/Q15/Q17` re-runs the chapters' pinned commands, Verus among them, outside this
lane's share (8 GB, no Verus job): the integration lane runs it (no pin input changed).

## 4. D34 and D35 — confirmed as built

- **D34:** `docs/Q17_PracticeIIIB.md` places the hidden check of `VcSound` only in §4's
  instrument row, "after the run and your AUDIT"; no other line of the chapter names it.
  Q17's A7 (new) says the same order. Matches.
- **D35:** `ScanIndex`'s exact test sets aside only course-visible text and pool-common
  shingles, never a span's shape; `test_an_exact_copy_of_a_pool_common_shape_still_counts`
  passes; the docstrings of `ScanIndex`, `author_scan` and `sandbox/attested.toml`'s header say
  so. Matches; `ScanIndex`'s docstring now cites D35.

## 5. Coordination

- **D28 (the Lab 2 public forms' rebuild and Q15's re-seal)** changes the sealed twins: after
  the re-seal, `refs` differs, so every entry is current no more until re-scanned. Run
  `scripts/mksandbox-run --author --attest-rescan` once after the final Q15 seal (about 20 s,
  no solver), then attest the ten public cards (`--author --attest`) through DV6: their
  reference statements and programs are then twins, so a card that kept a reference clause or
  a sealed definition is refused. This lane's re-scan stands for the current seal.
- **Seen while this lane ran:** the D28 lane rewrote the ten public forms in the tree (the
  sealed twins' learner side), so the digest moved from `7a896df3d3f1c4a4` (the 78 entries'
  `refs`) to `c3a734413939b836` with the Q15 seal unchanged. The rewritten forms scan clean
  against the current seal: `author_scan` refuses 0 of the 10 (labels-only log `pubcheck.txt`).
- `SEALED_REFERENCE_DIRS` names the Lab 3 references' author location; a Lab 3 re-seal or a
  moved archive updates it (a missing directory refuses every attestation, fail-closed).

## 6. DELTAS-ready text

### Δ2xx · The scan and grading decisions D31–D35 as built: the sealed references read as twins, every entry re-scanned under DV6; a reported hidden-check verdict anchors a finding at grade 2; run the hidden check once and report the first run — adopted (DV6, 2026-10-14; applies the user's decisions D31–D35)
- **Status:** applies the user's decisions D31, D32, D33 (Δ232 items 5, 6, 8; each option (a)/(b) as recommended) and records D34 and D35 (items 7, 9) as built. Like Δ195–Δ233, it names no answer, no reference statement and no weakened statement. Detail: `Solutions/plans/DV6-grading-notes.md`.
- **Change:**
  - **D31.** `scripts/dvl/sandbox.py`: `sealed_reference_twins` reads Lab 2's sealed reference programs and statements (the truth lab a local stratum's `lab` names; `reference.toml`'s definitions and clauses) and Lab 3's reference deliveries (`SEALED_REFERENCE_DIRS`, against the archive's task forms) into memory only (`_sealed_tree`: every pin checked; `SealedTwin` and `Span` keep their text out of `repr`; any failure a `SealedRefsError` naming the source, never its text; a crash while they are in memory reported by type, its message withheld). A declared source that cannot be read refuses the attestation and changes nothing. A sealed twin's exact copy counts even when the public pools show it (Lab 2's public cards come from those pools). `SCAN_RULE = "DV6"`; each entry records `refs`; `rescan_attested` and `mksandbox-run --author --attest-rescan`. All 78 entries re-scanned once: 78 re-attested, sha256 values unchanged.
  - **D32.** Rubrics Q13 C5, Q15 C4, Q17 C6: a reported `strong`, `weak`, `vacuous` or `mismatch` (the first run, A7) is a finding at grade 2; `undecided` the reader's call; `/review-code`'s SKILL gains the Hard rule.
  - **D33.** Q13 §2, Q15 §5, Q17 §4's row: one run per item, after the statement is final, the first run reported (as with `firsttry`); A7 of the three rubrics records it. Verdict-only output deferred to the next image rebuild (open).
  - **D34, D35:** confirmed as built (Q17 §4's row after the run and the AUDIT; the exact test fail-closed, its fixture green).
- **Why:** 68 sealed twins read (30 programs, 30 statements, 8 deliveries); under the course's pool rule 10 had no counting span, under DV6 0; the 78 entries and the 10 public cards 0 hits; each twin's own text as an invented card caught 67 of 68, its answer blocks planted into another card 67 of 68 (56 renamed), the miss one Lab 3 card whose reference differs from its task form only below the scan's span length (a known limit; the card and its sizes are in these notes' §2 table, never in DELTAS: DV6 fix round). `tests/sandbox` 182 OK (10 new: planted Lab 2 and Lab 3 references caught, fail-closed, a canary through the crash paths, the re-scan); `harness/tests/core/test_batch.py` 53 passed; `chapter_lint` Q13, Q15, Q17 0 problems with every pinned fence unchanged; `update_rubric_pins.sh --check` 111 current; the leak verifier, 18 modules over 1,633 public files, OK; `check_single_route.py` and `check_course_map.py` clean; 0 sealed-span hits over the files the lane wrote; the D28 lane's rewritten public forms 0 of 10 refused against the current seal. No solver job (8 GB scope). Archive `dv6/scangrade/`.
- **Touches:** Δ221, Δ228, Δ230–Δ232; `scripts/dvl/sandbox.py`, `scripts/mksandbox-run`, `sandbox/attested.toml`, `sandbox/README.md` (the attested row), `tests/sandbox/test_sandbox.py`; `paper/rubrics/{Q13,Q15,Q17}_rubric.md`; `.claude/skills/review-code/SKILL.md`; `docs/Q13_PracticeIIA.md`, `Q15_PracticeIIC.md`, `Q17_PracticeIIIB.md`; DV4-PLAN §5.4 items 3 and 5 and `Solutions/plans/DV4-author-notes.md` §13 (the records lane: the scan's DV6 rule).
- **Owner:** DV6's scan-and-grading lane; the open items' owners.
- **Open:** after Q15's re-seal (D28), `--attest-rescan` once more, then the ten public cards attested (the attestation owner); `pins.py --ci --module Q13/Q15/Q17` (a lane with a Verus share; no pin input changed); `/review-code`'s calibration on Q13 and Q15 (the Simulate phase); `truthcheck`'s verdict-only prose output at the next image rebuild (the image owner); `CLAUDE.md`'s Armed line and DV4-PLAN §5.4 name the DV6 rule (the integration and records lanes).
