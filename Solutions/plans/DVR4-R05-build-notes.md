# DVR4 step 5 — R05 at the R module bar (author-only)

Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2 (R05's row: **keep**, systemic only), §2.1, §2.2, §4.2, §5 step 5, §7 (D58–D60); PLAN §3 R05 and §6.5's 402-minute record; the exemplar R02 and its notes. Earlier R05 evidence: `Solutions/plans/DVR1-R05-build-notes.md`, `Solutions/plans/R-author-notes.md` §6. Scratch and logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p1/r05/` (never `/tmp/dvl0-dv*`).

## 1. Objective-to-exercise map (written before any change, 2026-10-19)

PLAN §3's objectives for R05, where the learner meets each, the item that checks it, and the evidence that keeps it real. Minutes are PLAN §6.5's (holes 72 = 6 × 8 + 2 × 12; Python 24 = 2 × 12, of the line's 35); none is narrowed; the registry already holds the 10 rows (Δ255).

| objective (PLAN §3 R05) | chapter section | items that use it | checked item | minutes | reference lines (D · V) | why not trivial (four results to confirm) |
|---|---|---|---|---|---|---|
| obligations and their labels; reading a failure without a goal state | §1.1 (a fresh two-split witness, its related lines), §1.2 (P1/P2) | W1 | P1d, P2v | — | — | — |
| assertion bisection | §2.1 (a pinned four-step bisection, Dafny; the end state, Verus), §2.2 (facts per line, W1) | W1 | **H4d/H4v** `StarConcat` (bisect and repair: an annotation hole, the skeleton given) | 12 / 12 | 3 annotation lines · 3 | the twin without its regions fails (RGN); the given skeleton is frozen |
| `assert … by` scoping | §3.1 (C1 demos; a reveal that stays in its block) | W2, C1 | **H1–H2** use it | — | — | — |
| per-assertion and per-function isolation; `--isolate` | §3.2 (C2, C3 demos; W2) | W2, C2, C3 | **H1d/H1v** `CatAssocLR` | 8 / 8 | 9 · 13 | empty body fails (two existentials to take, one to build) |
| `Cat` associativity, the other direction | §1.2's slice chain | — | **H2d/H2v** `CatAssocRL` | 8 / 8 | 9 · 13 | empty body fails |
| one match is a star match | §1.2 | — | **H3d/H3v** `StarOne` | 8 / 8 | 2 · 4 (minimal to measure) | empty body fails |
| the fast channel against the gate; latency | §4.1 (P4), §4.2 (the latency ladder) | — | P4dv; the LATENCY block | — | — | — |
| resource limits and verdict kinds | §5 (C4 Rosetta; pinned inconclusive pair) | C4dv | — | — | — | — |
| repeated runs, CV, a bootstrap interval (`fvh.stats`) | §6.1 (P3; a recorded ten-run log per language), §6.2, §6.3 | C5dv | **H1py** `runs_from_log`, **H2py** `variance_summary` | 12, 12 | Python | TRIV (`# triv:` bodies) fails the frozen tests |
| rung 6 obligation prover: fast channel only, one final gate | §10 | — | A1d/A1v | agent 25 | — | — |

**Constructs a reference needs, and where each is taught before its hole (criterion 11).** `:|` / `choose` and slice facts (R02, R04; §1.2's chain of slices of slices); `assert … by` (§3.1); `@IsolateAssertions` / `spinoff_prover` (§3.2); bisection by asserted intermediate facts (§2.1); `fvh.stats.bootstrap_ci`, `statistics.fmean`, `statistics.stdev` (§6.2, the docstrings).

**File order (criterion 9).** The prediction block; W1–W2; the cards C1, C2 (Dafny) / C1, C3 (Verus) and C4; the holes H1–H4; the logs block; C5dv last. The Python file: the docstring contract, the dataclasses, H1py, H2py.

**Hole prompts and hints (criteria 7–8).** Each H item, the Python ones included, gets `**Hn.**` (`**Hnpy.**`) with a guiding question and `Hint(1)`, `Hint(2)`.

**Chapter plan.** Rewritten to R02's standard with exactly PLAN §3's three diagrams (a proof to its obligations to the failing labels; the bisection tree; the latency ladder); every prediction answered by a capture (P3's ten runs as a recorded quote of the author's runs, both fields per run, since a fence cannot re-run ten timings).

**Bank.** Rewritten at the Q06 schema by the bank sub-lane: 12 questions, both draws with live predicts, backward edges to R01, R02, R04, tags from the controlled vocabulary.

## 2. Probes (2026-10-19 to 2026-10-22; `probes/`, `chapter/`, `bank/`, `min/`, `tags/`, `records/`)

The chapter's scratch sources (`chapter/`: the bisection steps `bis-0`…`bis-4`, `by-local`, `rlimit`, both languages) were probed before they were written into the chapter, and the chapter pins now re-run them. The bank sub-lane's probes (`bank/`, 37 files, and `bank/pp/`, 12 parallel-problem files) were re-run on 2026-10-22 against the installed files: every verdict and output line matches `bank/outputs.json` and `bank/pp/outputs.json`. P3's ten runs per language are in `records/runs10-d.txt` and `records/runs10-v.txt`, made by `records/runs10.py`. The timing specimen waits for P3dv (H5), so the script runs a byte copy under `instructor/scratch/` with `--module R05`.

## 3. As built (2026-10-22)

**Files.** Both exercise files are in the file order of §1: the prediction block, W1–W2, the cards, a `Holes` banner, H1–H4 with `**Hn.**` prompts, guiding questions and `Hint(1)`/`Hint(2)`, the logs block, and C5dv last. `variance.py` (both copies) has the docstring contract, the dataclasses, and H1py/H2py with prompts and two hints each. Twins, learner files, agent files and every specimen are one statement per line with spaced commas. The learner files are derived from the twins by `derive.py`:
- H1–H3 become bodyless (Dafny) or `proof_note` assumes (Verus).
- H4's first region becomes the shipped `assume`, and its second region is emptied, so H4's given skeleton stays.
The specimen twins mirror the learner specimens (10). P1d and P2v differ only in their answered slots.

**Admission evidence (plan §2.1).**
- References are stable on seeds 1–3: the core twins (Dafny CV 13.5 %, Verus 20.2 %) and both agent twins (Dafny CV 39.7 %, Verus 2.4 %; advisory, never gating). Logs: `logs/brittle-*.log`.
- `firsttry.sh R05 --empty-body` gives 10/10 (`logs/empty-body-1.log`). Every empty body and region gate fails in every run, maximal automation included, and the Python holes' TRIV bodies fail the frozen tests.
- Freeze `--check` 0 (the statements are unchanged; the edits are whitespace, prompts and hints). Counts: `--shipped` 0. `--lint-hollow` OK (15 files). `reference_lint` 0. `avoid.sh` OK. The sealed sidecars are refreshed (10; P1d and P2v refused by design, H5).

Smallest proofs were found by the greedy minimizer (`bin/minimize_multi.py`, every region at once, both orders; `min/`). One-fact lines are counted as in D64: a `var`/`let` binding is not a fact, a `:|`/`choose` line is, and facts packed into a conjunction count separately.

| item | minutes | reference lines | smallest found (one-fact lines) | (1) seeds 1–3 | (2) empty body, shipped | (3) maximal automation | (4) TRIV | row |
|---|---|---|---|---|---|---|---|---|
| H1d | 8 | 9 | 4: two `:|`, `u[..k] == s[..k]`, `v[..i - k] == s[k..i]` | stable | fails | fails | n/a | admitted |
| H1v | 8 | 13 | 6: two `choose`, four subrange or match facts | stable | fails | fails | n/a | admitted |
| H2d | 8 | 9 | 4 forward, 5 reverse | stable | fails | fails | n/a | admitted |
| H2v | 8 | 13 | 6 | stable | fails | fails | n/a | admitted |
| H3d | 8 | 2 (one packed conjunction inside `if`) | **1**: `assert u[..|u|] == u;` | stable | fails | fails | n/a | admitted at 8; DECISION 1 |
| H3v | 8 | 4 | 3: whole subrange, empty tail, the star's empty match | stable | fails | fails | n/a | admitted |
| H4d | 12 | 3 annotation lines (two regions) | 3 | stable | region gate fails | fails | n/a | admitted |
| H4v | 12 | 4 (two regions) | **2**: the two `=~=` facts about `t` (the empty-case block is not needed) | stable | region gate fails | fails | n/a | admitted at 12; DECISION 1 |
| H1py | 12 | Python | TRIV fails the frozen tests | — | 38 tests fail as shipped | — | fails | admitted |
| H2py | 12 | Python | as H1py | — | as H1py | — | fails | admitted |

Minutes reconcile: holes 72 (6 × 8 + 2 × 12) and Python 24 = PLAN §6.5's lines; `[module.admissible]` holds the 10 rows, unchanged.

**Overlap.**
- `bin/overlap.py R05` at 24-token windows. Every large overlap is with Lab α's forms (`r09-copies-split-*`, `r09-rep-range-correct-*`, `r06-backwards-sound-*`, `a1b-cat-assoc-v`), which restate A1b's `Cat` associativity and star lemmas. Lab α is the declared later-tier overlap (Δ294, "DO NOT OPEN BEFORE R11 IS DONE").
- Without Lab α, no R05 answer shares more than one window with any R05 learner-visible file.
- Finding, not this lane's file: R05.H3v shares 38 of 79 windows with R14's `specimens/R14/card-c4dv-v.rs.specimen`. That specimen's `lemma_cat_eps_r` states the same two subrange facts (the whole subrange and the empty tail). R14 is a later module, and the overlap is the generic split-at-the-end idiom; reported to the R14 lane, not changed.

**Leak patterns.** 8 (H1d, H2d, H4d, H1v, H2v, A1d, H1py, H2py). H4d and A1d were re-cut for the one-statement-per-line twins; their old patterns matched nothing. H1v and H2v also match three Lab α forms, which the verifier lists as declared (Δ294). The verifier (README's current copy) gives 8 OK over 2,727 public files.

**Chapter.**
- Rewritten to R02's standard: 5,156 lint words, 37 pinned fences (from 19), and exactly PLAN §3's three diagrams (a proof to its obligations to the failing labels; the bisection tree; the latency ladder).
- Source is inline for every scratch scenario: a four-step Dafny bisection (`bis-0`…`bis-4`) and Verus's start and end states, `by-local` in both languages, and an `rlimit` pair that is `inconclusive` in both.
- Gate, audit and freeze are captured. Every prediction is answered by a capture.
- P3's answer (`D:same,varies V:same,varies`) is quoted from the two recorded ten-run logs (`kind = "recorded"`, both fields per run). Dafny's resource count is 136,772 in all ten runs and Verus's is 38,681; the wall times spread over 0.918–1.024 s and 1.686–1.783 s.
- `python-shipped` is an excerpt of four output lines, which the chapter says.
- `chapter_lint` 0 problems. `pins.py --ci --module R05` 58 pins, 0 problems; `--ref` 4 checks, 0 problems.

**Bank.**
- Rewritten by the bank sub-lane at the Q06 schema: 12 questions, 12 `**Reread**` lines that all resolve in the new chapter's headings, and tags all in `concepts.md`.
- Two disjoint draws with live predicts.
- Backward edges to R01, R02 and R04. No generic branch lines.
- Probes are re-run and match (§2). The glued-numeral scan is clean (its one hit is a commit hash).

**Written pair.** The problems are unchanged; the 5 rubric pins are refreshed.

## 4. DECISION NEEDED

**1 · Two holes are under D64's three-fact bar (non-blocking).** R05 is a **keep** module (plan §2: systemic only), and D64 was the user's rule for R04. The rule's measure finds:
- H3d `StarOne`: one fact (`u[..|u|] == u`).
- H4v `lemma_star_concat`: two facts (the two `=~=` facts about `t`). H4d needs three.

The objectives ("one match is a star match"; "bisect and repair") and minutes are unchanged. Options:
- (a) Record both as R05 exceptions under the reading D59 gave R02's H5 and R01's H1/H3: H3 as the module's short warm-up, H4 as an annotation hole measured by its region gate.
- (b) Re-pose them on the D64 bar: H3d, for example, as `StarOne` over a two-chunk star or `Matches(a, u) && Matches(a, w) ==> Matches(Star(a), u + w)` (this overlaps H4); H4v by a skeleton that leaves more facts to the learner. This changes the items.

**Recommend (a).** **Resolved by the user's D84 (2026-10-23): re-pose both to the D64 bar; see §6.**

**2 · WRITE tags that no smallest proof needs (non-blocking).** Probes in `tags/`:
- **Dafny.**
  - The minimal proofs of H1d, H2d and H4d verify with each `assert … by { }` written as a plain `assert` (`*-min-plain`).
  - The full reference twin with all four empty `by` blocks removed runs out of resource in `CatAssocRL` (H2d) at the pinned limit (`d-noby`). So the by-block keeps the 5-fact reference within budget; a measured instance of §3.1's lesson, not a step of the smallest proof.
  - Removing `@IsolateAssertions` from H1d and H4d still verifies (`d-noiso`). The attribute is part of the given statement, frozen as a lever, and the learner does not write it.
- **Verus.** No `by` block (`v-noby`, `v-flat`) and no `spinoff_prover` (`v-nospin`) is needed.

So under the rule R04 now follows ("every tag names a step the smallest proof needs"), `assert-by`, `isolate-assertions` and `spinoff-prover` have no genuine hole instance in R05. Only the cards C1–C3 use them. Options:
- (a) Keep them WRITE under R05's own reading: R05's skill is diagnosis and cost, and the holes ask the learner to use scope and isolation while bisecting, whether or not the final proof needs them.
- (b) Move `isolate-assertions` and `spinoff-prover` to RECOGNISE, and keep `assert-by` WRITE with H2d tagged for the budget reason recorded above.
- (c) Re-pose one hole per language so that a by-block is needed (for example, a local `reveal` of an opaque helper, as `by-local` shows). That changes objectives.

**Recommend (b)** if R04's rule applies course-wide; otherwise (a). **Resolved by the user's D85 (2026-10-23), the coordinator's option (a): isolation is RECOGNISE in both languages; `assert-by` stays WRITE in Dafny on H2d, under a registry exception; see §6.**

## 5. Focused checks (2026-10-22)

Run one solver job at a time in `dvl0.slice` under an 8G outer scope (`systemd-run --user --scope --slice=dvl0.slice -p MemoryMax=8G -p MemorySwapMax=0`). No exit 137 or 143.
- Empty-body 10/10.
- Pins (chapter 37, module 58) 0 problems.
- `chapter_lint` 0.
- `check_course_map` OK.
- Leak verifier 8 OK.
- Rubric pins current.
- Study workflow 11/11 on `236c4f23` (`workflow.log`: firsttry, strict, freeze, and the gate and audit of both core units and both agent files). The Python twin gates in a scratch worktree (38 passed, 0 holes) with a clean audit; `wf.py` does not cover Python.

The focused author CI (static, harness, wrappers, rubric) needs the 16G slot and waits for the coordinator.

## 6. D84 and D85 (the user, 2026-10-23; built 2026-10-23)

**D84: the short holes re-posed to the D64 bar.** The objectives ("one match is a star match"; "bisect and repair") and minutes (8, 12) are kept, the mirrors are kept, and every proper subset of each smallest found body fails. Probes are in `d84/`; the minimizer ran in both orders.

| item | before | after | smallest found (one-fact lines) | subsets | reference · seeds 1–3 |
|---|---|---|---|---|---|
| H3d | `StarOne`: `Matches(a, u) ==> Matches(Star(a), u)` · 1 | `StarThrice`: `Matches(a, u) ==> Matches(Star(a), u + u + u)` | 4 forward (`t[..\|u\|] == u`, `t[\|u\|..] == r`, `u[..\|u\|] == u`, the star match of `r[\|u\|..]`), 5 reverse | all 63 proper subsets of the 6-line set (bindings included) fail | 10 lines · stable |
| H3v | `lemma_star_one` · 3 | `lemma_star_thrice`, the same claim (mirror) | 8 (5 `=~=` facts, 3 `matches` mentions; 4 `let` bindings not counted), both orders | greedy: each one-line deletion fails | 15 lines · stable |
| H4d | the given skeleton held the recursive call · 3 | the call is the learner's: the skeleton keeps the case split, the choice of the first chunk and the measure | 4: the empty-case fact, the call, two slice facts | all 15 proper subsets fail | 4 lines · stable |
| H4v | the given skeleton held the call · 2 | the same skeleton change (mirror) | 3: the call and the two `=~=` facts about `t` | all 7 proper subsets fail | 4 lines · stable |

Other shapes tried for H3d:
- `Matches(Star(Star(a)), u)`: 2 facts.
- `Matches(Star(a), u + u)`: 2.
- `Matches(Star(Star(a)), u + u)`: 3.
- `Matches(Star(Alt(a, b)), u + w)`: 3, but it changes the objective.

StarThrice is a special case of H4's claim, but its proof is direct (three splits, no induction), and H3 precedes H4 in the file.

The bank's PP2 (parallel to H4) now also leaves the recursive call to the learner. It was re-verified: shipped with one hole; with the hole line deleted, it fails; the reference, now 3 lines in Dafny and 7 in Verus, verifies.

The chapter (§7, §9), the prompts and hints, the file headers, the rubric and PLAN name the new statements and skeleton.

**D85: honest WRITE tags (the coordinator's option (a), which the user chose).**
- `isolate-assertions` and `spinoff-prover` are RECOGNISE. `assert-by` is WRITE in Dafny only, and RECOGNISE in Verus, where no hole needs it (`v-noby`, `v-flat`).
- Registry: `write_d = ["assert-by"]`, `write_v = []`, `recognise_d = ["rlimit", "isolate-assertions"]`, `recognise_v = ["rlimit", "assert-by", "spinoff-prover"]`.
- Cards and tags: C1v is `recognise:assert-by`, and C2d and C3v are `recognise:`. Only H2d keeps `uses: assert-by`; every other R05 `uses:` line is removed.
- The empty `by` blocks of H1d, H1v and H2v are plain assertions now, so no reference line pretends to need scope. H4's references are plain too.
- **The user's answer named Dafny H2 only.** The course map's "≥ 2 tagged items" rule therefore needs an exception, and this exception is the decision's consequence:
  - `MODULES.toml` declares one top-level `[[write_exception]]` (R05, `d`, `assert-by`, R05.H2d, reason naming D85).
  - `check_course_map.py` accepts that declaration only through its `WRITE_USES_EXCEPTIONS` table, and only when the slug's one tagged item is the declared item.
  - `scripts/test_course_map.py` gains six cases. Without the declaration, the 1-item slug fails. A declaration for an undecided slug, for the other language or for another item is refused, and so is a reason that does not name D85. A second slug with fewer than two items still fails.
  - The existing Q04 case still shows an unlisted 1-item slug failing. The suite gives 411 passed, 0 failed.
  - The coordinator will tell the user. If they prefer option (b), `assert-by` becomes RECOGNISE in Dafny too and the exception goes.
- **The `d-noby` evidence, re-run on the D84 twin** (`tags/d84-noby`): writing H2d's one `by` block as a plain `assert` makes `CatAssocRL` run out of resource at the pinned limit (`inconclusive`, 77 verified). H2d's smallest found proof needs no `by` block (`tags/H2d-min-plain`); the block is what keeps the readable reference within budget.

**Evidence (2026-10-23).**
- Freeze re-pinned (34 statements), `--check` 0. Counts re-pinned, `--shipped` 0.
- Both core twins stable on seeds 1–3 (Dafny CV 14.7 %, Verus 10.7 %). `firsttry.sh R05 --empty-body` 10/10.
- Chapter re-captured (37 pins; `chapter_lint` 0, 5,287 words). `pins.py --ci --module R05` 58 pins, 0 problems; `--ref` 0.
- `--lint-hollow` OK. Rubric pins refreshed (2). `check_course_map` OK.
- Leak patterns: H1d and H4d re-cut, 8 OK over 2,728 public files.
- The study workflow is recorded below.

The finding for the R14 lane (§3, Overlap) goes to the coordinator's notes for P2.

