# DVR4 step 5 — R13 at the R module bar (author-only)

Lane P2 of the systemic passes (plan §5 step 5), on branch `sysb`, after R11 (Δ322). Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2 (R13's row), §2.1, §2.2, §2.5 (the holes as fake deliveries on regex objects, Δ278), §4.2, §5 step 5; PLAN §3 R13 and PLAN §15 (minutes); the exemplar `Solutions/plans/DVR4-R02-build-notes.md`. Scratch and run logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p2/r13/`.

## 1. Objective-to-exercise map (written before any change)

PLAN §3's objectives for R13, where the learner meets each, the item that checks it and the evidence that keeps it real. Minutes are PLAN §15's (test-out 10 = 5 + 5; holes 60 = 3 × (10 + 10); stage attribution 30, forensics 60, `TRUST.md` R-v0 20 are lines of their own); none is narrowed. Lines are plan §2.2's counter (`scripts/pcount.py`, proof · exec) on the Δ278 references before this pass.

| objective (PLAN §3 R13) | chapter section | worked material | checked item | minutes D / V | proof · exec lines before (D · V) | why not trivial (to be confirmed by the four results) |
|---|---|---|---|---|---|---|
| the stages of each tool, and attributing a failure to its stage | §1–2 | P1d, P2v, P4d, P5v; the pipeline diagram | **T1d/T1v** (the fake: compiled code calls the ghost/spec matcher, stopped at resolution) | 5 / 5 | 0 · 1 · 0 · 1 | TRIV `false` fails the postcondition; the attribution is the point (test-out) |
| selected versus complete scope | §3 | P3dv, P6dv | stage attribution (30), the fake T1's `--symbol` run | — | — | a green selected run over a failing file |
| the trusted computing base without a small kernel | §4 | the TCB onion | **H1d/H1v** (the fake: a trusted axiom / `external_body` proof fn) | 10 / 10 | 6 · 0 · 6 · 0 | manual induction on `|u|` with the re-association stated |
| trusted executable helpers | §4, §8 | — | **H2d/H2v** (the fake: a bodiless method / `external_body` helper) | 10 / 10 | 2 · 6 · 4 · 6 | the invariant quantifies over the prefix; TRIV `false` fails |
| weakened statements and the statement freeze | §5, §8 | `specfreeze` | **H3d/H3v** (the fake: an added `requires` limiting it to the empty word) | 10 / 10 | 6 · 0 · 7 · 0 | both directions of `<==>` need the induction |
| forensics on the R half; two instruments, no false accusation | §5–6 | `fvh.corpus.load_half`, inventory | forensics (60), agent A1d/A1v (25) | — | — | UNKNOWN on grader-only classes |
| `research/TRUST.md` R-v0; card 12.3 | §7 | — | B1/B2 (paper 30), R-v0 (20) | — | — | rubric |

**Line budget (criterion 2, §2.2).** T1 is a one-line test-out (a call to A2's matcher); H1–H3 are 6–10 lines for 10 minutes, inside the 5–15 band.

**Constructs taught before the holes (criterion 11).** Tool stages and the wrapper's `stage` field (§1), compiled versus ghost code and `expect` (§2), selected versus full scope (§3), trusted declarations (`{:axiom}`, `external_body`, bodiless methods) and what `vaudit` lists (§4, §8), statement freezes (§5, §8); the holes use only constructs of earlier modules (induction under `{:induction false}`, prefix loop invariants, A1b/A2 facts).

**File order (criterion 9).** The header, the prediction block (the P3dv and P6dv switches), then the test-out T1 (with a commented check), the given `Derivs`, H1–H3, and a given compiled use-site test. T1 sits after the prediction block because one Dafny module (`R13_Repairs`, imported by `tools/R13/check_repairs.py`) holds every item.

## 2. Probes (2026-10-21)

- **Seed stability.** `vcheck --ref --brittleness` (Z3 4.12.1 and 4.14.1 for Dafny, seeds 1–3): every twin verified on every seed of the pinned solver; under the advisory 4.14.1 the Dafny runs are inconclusive on one declaration outside the targets' files (the same given-layer pattern as R10/R11; advisory, never gating); the Verus crate and agent twins are stable. `logs/brittle-*.log`.
- **The test-out record.** T1 had no commented check (R09's finding: a first try outside a shipped branch would record as "observed"). T1d/T1v now ship `AcceptsCheckR13` / `accepts_check_r13` under `Uncomment as you go:`; the twins keep it enabled under the `reference-only: enabled shipped check` marker.
- **Use-site checks (bar criterion 10).** The exec items T1 and H2 had no given client (only `tools/R13/check_repairs.py`'s compiled observations). Both files now end with a given compiled test (`R13_Clients.RepairSampleTest`, `repair_sample_test`) over two words and an A2 class range.
- **Twins.** The references carried "Reference:" doc comments in place of the learner prompts and no regions; the twins now carry the learner's prompts and hints with `@hole` regions (Dafny, Verus proofs) and `ref-begin`/`ref-end` (Verus exec), so the region gate runs. The agent files were packed and had no header: re-laid out, with a header that states the forensic task and the allowlist.
- **Specimens.** All eight re-laid out one statement per line (verdicts unchanged); the chapter now prints each above its run.

## 3. As built (2026-10-21)

**Files.** Both exercise files, both agent files, their twins and all eight specimens are one statement per line, in the order of §1, with the learner prompts and hints in the twins as well; `@hole` / `ref-begin` regions in every twin; T1's commented check; the given compiled tests. Module and symbol names the R13 tools import are unchanged (`R13_Repairs`, `accepts_r13`, `class_covers_r13`). `specfreeze --pin R13` (26 statements, 12 files), `vcheck --ref --pin-counts R13` re-pinned. No R13 specimen has a sealed sidecar (none existed before).

**Admission evidence (the four results).** (1) seeds as §2. (2)+(3) `firsttry.sh R13 --empty-body` 8/8 (`logs/empty-body-1.log`): every empty body fails in the shipped configuration and under maximal automation, every seed, and every item also fails with its twin region blanked (T1v and H2v by their `triv:` bodies). (4) TRIV: T1v and H2v declare `false`; T1d's and H2d's empty bodies leave the out-value open. `specfreeze --check R13` 0, `--lint-hollow` OK (10 files), `reference_lint --module R13` 0.

| item | minutes | lines after (proof · exec) | (1) seeds | (2) empty, shipped | (3) maximal automation | (4) TRIV | row |
|---|---|---|---|---|---|---|---|
| T1d | 5 | 0 · 1 | stable | fails | fails | unassigned out fails | admitted |
| T1v | 5 | 0 · 1 | stable | fails | fails | `false` fails | admitted |
| H1d | 10 | 6 · 0 | stable | fails | fails | n/a | admitted |
| H1v | 10 | 6 · 0 | stable | fails | fails | n/a | admitted |
| H2d | 10 | 2 · 6 | stable | fails | fails | unassigned out fails | admitted |
| H2v | 10 | 4 · 6 | stable | fails | fails | `false` fails | admitted |
| H3d | 10 | 6 · 0 | stable | fails | fails | n/a | admitted |
| H3v | 10 | 7 · 0 | stable | fails | fails | n/a | admitted |

Minutes reconcile: test-out 10 + holes 60 = PLAN §15; `[module.admissible]` keeps its 8 rows unchanged.

**Overlap checks.** No withheld line of an earlier R module in R13's files beyond structural lines. R13's own withheld lines appear in the Lab α forms `r06-backwards-*-d` (the sequence re-association `assert (u + v)[1..] == u[1..] + v;`, a generic idiom covered by the Lab α later-tier declaration) and in the chapter's H3 fake delivery (its base case, `lemma_nullable_correct(r)` and the empty-word extensionality, which the fake shows by design: Δ278). 0 public-answer windows (`pubwin`). Leak verifier: 8 patterns, T1v's re-cut to the body line, OK over 2,595 public files.

**Chapter.** Revised, not rewritten (it already had the fake deliveries' sources and captures inline): each prediction subject's source is now printed above its run (8 source blocks added: 16 Dafny/Rust blocks, from 8), each prediction's answer is stated after its capture, the files table and §8 name the given tests and T1's commented check, numerals spaced; 5,269 lint words (from 5,060), 23 pinned fences, PLAN §3's three diagrams, no appendix.

**Bank.** Rebuilt at the Q06 schema by a forked helper of this lane: 12 questions (2 reconstruct, 4 predict, 2 why, 2 connect, 2 transfer), 1,161 lines (from 220), 12 Reread lines naming the current headings, 8 backward edges (R01, R04, R06, R07, R08, R10, R11, R12), two disjoint draws with two live predicts each (A: K2, K7; B: K4, K10), two parallel problems (PP1 a band-membership loop parallel to H2, PP2 the sum of a concatenation parallel to H1) whose shipped, empty, trivial and reference runs were made on the course pins (bank/b/outputs.json in the scratch archive).

**Written pair and numerals.** Chapter, problems and rubric numerals spaced (the rubric's and problems' remaining digit runs are SHA-256 hashes); rubric pins refreshed; `make -C paper paper` builds.

**Study workflow** (`bin/check_workflow.py` with `r13/workflow.json`, a disposable detached worktree under this archive, removed after): 15/15 (`workflow/workflow-results.json`): `firsttry --check` records 8 first tries (6 predictions and both test-outs, each with its commented check enabled in a scratch copy), the strict report OK, freeze 0, both units' compiled tests, both units' and both agent files' gates and audits, `tools/R13/check_repairs.py` (50 compiled observations per language pass) and `tools/R13/inventory.py`.

**Focused author CI.** See Δ323 and the coordinator message (run after the commit, on a clean detached clone).

## 4. DECISION NEEDED

None for R13. (T1 is a one-line test-out, as in R11: its point is attributing the fake's stage, not the body.)
