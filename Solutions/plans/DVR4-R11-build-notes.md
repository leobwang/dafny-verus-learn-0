# DVR4 step 5 — R11 at the R module bar (author-only)

Lane P2 of the systemic passes (plan §5 step 5), on branch `sysb`, after R10 (Δ321). Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2 (R11's row: **keep** + systemic: appendix outputs), §2.1, §2.2, §4.2, §5 step 5; PLAN §3 R11 (Why, Core payload, Diagrams, Written track, Exercises, Agentic role, Hours) and PLAN §13 (the band-2 item plan: items and minutes, Δ267); the exemplar `Solutions/plans/DVR4-R02-build-notes.md`. Scratch and run logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p2/r11/`.

## 1. Objective-to-exercise map (written before any change)

PLAN §3's objectives for R11, where the learner meets each, the item that checks it and the evidence that keeps it real. Minutes are PLAN §13's (test-out 10; core holes 125 = 70 D + 55 V; certifying search 50 = 30 D + 20 V; Vec arena 45; checkpoint 22); none is narrowed. Lines are plan §2.2's counter (`scripts/pcount.py`, proof · exec) on the Δ267 references before this pass; a hole's reference-only helpers count with it (H2v's `sound_word_r11`, H3v's `complete_word_r11`).

| objective (PLAN §3 R11) | chapter section | worked material and cards | checked item | minutes D / V | proof · exec lines before (D · V) | why not trivial (to be confirmed by the four results) |
|---|---|---|---|---|---|---|
| wp and VCs by hand | §3.1–3.2 | the wp probes, P4v | **T1d/T1v** (test-out) | 5 / 5 | 0 · 1 · 0 · 1 | the postcondition pair rejects a constant; TRIV `0` (V) fails `next == i + 1` |
| a loop invariant is a relation to the input (R06's invariant-as-IH harvested) | §3.3–3.4 | W1/W3 residual facts, the loop probes | **H4d/H4v** (streaming prefix matcher) | 15 / 10 | 7 · 7 · 7 · 6 | the trace clause quantifies over every consumed prefix; bounds alone fail the postcondition |
| `Derivation` trees (A4) and a verified checker | §1.1–1.3, §2 | W2 (evidence), W1v (slice split), P1d, P2v | **H1d/H1v** (checker agreement) | 18 / 15 | 0 · 20 · 4 · 18 | equality with `CheckDeriv` in both directions; TRIV `false` (V) fails |
| soundness (certificate ⇒ match) | §1.2, §4 | W2v tracked evidence, C1v | **H2d/H2v** | 17 / 15 | 14 · 0 · 16 · 0 | induction on the tree; Dafny ships `{:induction false}` (PLAN §13: lever-needed) |
| direct completeness (match ⇒ certificate) | §1.2, §4 | `:|` / `choose` | **H3d/H3v** | 20 / 15 | 25 · 0 · 36 · 0 | the witness must be constructed per constructor; V states `|s| <= usize::MAX` |
| the certifying matcher: complete search, not an always-absent producer | §5.1–5.2 | P5dv | **H5d/H5v**, **H6d/H6v**, **H7d/H7v** | 30 / 20 | 4 · 27 · 27 · 42 | the no-match clause rejects always-`None` (TRIV); H6/H7 need the exclusion invariant |
| the arena (V; `PointsTo` gated, Vec fallback) | §5.3 | the arena excerpt and picture | **H8v/H9v** | — / 45 | — · 4 + 2, 2 + 2 | frame clauses (old nodes, the other edge, the length) |
| the second checkpoint (2 D + 2 V) | §10 | — | **X1d/X1v**, **X2d/X2v** | 11 / 11 | 12 · 0, 4 · 5 · 14 · 0, 7 · 6 | fresh statements, disjoint from the hand files; X1d lever-needed |
| a plausible but wrong rule verifies (rung 13, metatheory contractor) | §6, §11 | P3dv, `tools/R11/check_rule_binding.py` | A1d/A1v (agent 25) | — | — | the transport theorem proves over the changed rule too |
| Lean4Lean card; derivations by hand | §8 | — | B1/B2 (paper 40) | — | — | rubric `card-fidelity`, `invariant-rigour` |

Minutes reconcile: test-out 10 + holes 100 D + 120 V (core 125 + search 50 + arena 45) + checkpoint 22 = 252 = the 22 admitted rows; the module total stays 540.

**Constructs taught before the holes (criterion 11).** The derivation datatype and the rule relation (§1.1), relative splits and the slice identity (§2), wp of an assignment and machine representability (§3.1–3.2), invariants as relations to the input and opaque predicates (§3.3–3.4), ghost records and Verus `tracked` with move semantics (§4, C1v), the exclusion invariant and uniform measures (§5.2), the Vec arena's index invariants and frames (§5.3).

**File order (criterion 9).** The test-out first (T1, closed book, with a commented check), then the prediction block, the certificate kernel (W2 the evidence, then H1–H3), the streaming matcher (W1 and W3 the residual facts, then H4), complete search (H5–H7), in Verus the arena (H8–H9), and the given compiled use-site test last. Every hole follows the worked material its `uses:` names.

**Line budget (criterion 2, §2.2).** T1 is a one-line test-out (`i + 1`), H8v and H9v are 6 and 4 lines for 20 and 25 minutes, and H4v–H7v run 27–42 lines for 5–10 minutes. Measured after the re-layout and reported (DECISION NEEDED), not narrowed or re-posed in this pass.

## 2. Probes (2026-10-20)

- **Seed stability.** `vcheck --ref --brittleness` (Z3 4.12.1 and 4.14.1 for Dafny, seeds 1–3): every twin verified on every seed of the pinned solver. Under the advisory 4.14.1 every Dafny run is inconclusive on one declaration outside the targets' files (a given layer: the same pattern as R10's; advisory, never gating); the Verus crate, exit and agent twins are stable (widest spread 9.5%, `lib.rs:158`). `logs/brittle-*.log`.
- **The induction levers.** `firsttry.sh R11 --empty-body` reports H2d (`CheckSoundR11`) and X1d (`CertificateLengthR11`) lever-needed: with Dafny's default induction their empty bodies verify; with the shipped `{:induction false}` they fail. Both registry rows now name the lever ("printed induction-disabled levers"), as R02 and R10 do. H3d also ships the attribute but is not lever-needed (its empty body fails either way).
- **The test-out record.** T1 had no commented check, so a first try made outside a shipped branch would record as "observed" (R09's finding). T1d/T1v now ship `WpIndexStepCheck` / `wp_index_step_check` under `Uncomment as you go:` (the twins keep it enabled under the `reference-only: enabled shipped check` marker).
- **Use-site checks (bar criterion 10).** No exec hole had a given client: the exec items were exercised only by `tools/R11/check_runtime.py`. Both exercise files now end with a given compiled test (`R11_Clients.CertificateSampleTest`, `certificate_sample_test`: T1, H1 accept and reject, H4's trace, H5–H7 through a found and a missing certificate, and in Verus H8/H9 on a two-node arena), and both checkpoint files with a given client that asserts X2's certificate through its contract (`RepeatCertificateClientR11`, `repeat_certificate_client_r11`).
- **The chapter's P1 answer** needed a specimen that runs alone: `specimens/R11/chapter-p1-d.dfy.specimen` defines its own derivation type (`// after: R11.P1d`).

## 3. As built (2026-10-20)

**Files.** Both exercise files, both checkpoint files, both agent files and their twins re-laid out one statement per line (Dafny 2-space, Verus rustfmt-like) and ordered as §1. Every item has a `**Tn.**` / `**Hn.**` / `**Xn.**` prompt with a guiding question and `Hint(1)`/`Hint(2)`; the checkpoint prompts carry no hints (closed book). `// did:` receipts sit directly above every `reveal_with_fuel` inside the proof blocks. The specimens and the check unit are re-laid out (verdicts unchanged; P1's answer is `expect middle == 6;`); the sealed sidecars are re-pinned. Module and symbol names the R11 tools import are unchanged. `specfreeze --pin R11` (87 statements, 19 files), `vcheck --ref --pin-counts R11` re-pinned.

**Admission evidence (the four results).** (1) seeds as §2. (2)+(3) `firsttry.sh R11 --empty-body` 22/22 (`logs/empty-body-1.log`): every empty body fails in the shipped configuration and under maximal automation except the two named levers, and every Dafny item and H2v/H3v/X1v also fail with their twin region blanked. (4) TRIV: the Verus exec items run their declared `// triv:` bodies (T1v `0`, H1v `false`, H4v an empty report, H5v–H7v `None`, H8v `0`, H9v `{ }`, X2v `DStarNil`); the Dafny items' empty bodies leave the out-value unassigned or the postcondition open. `specfreeze --check R11` 0, `--lint-hollow` OK (17 files), `reference_lint --module R11` 0.

| item | minutes | lines after (proof · exec) | (1) seeds | (2) empty, shipped | (3) maximal automation | (4) TRIV | row |
|---|---|---|---|---|---|---|---|
| T1d | 5 | 0 · 1 | stable | fails | fails | unassigned out fails | admitted |
| T1v | 5 | 0 · 1 | stable | fails | fails | `0` fails | admitted |
| H1d | 18 | 0 · 31 | stable | fails | fails | unassigned out fails | admitted |
| H1v | 15 | 4 · 23 | stable | fails | fails | `false` fails | admitted |
| H2d | 17 | 14 · 0 | stable | fails | verifies: lever-needed, named | n/a | admitted, lever named |
| H2v | 15 | 19 · 0 | stable | fails | fails | n/a | admitted |
| H3d | 20 | 25 · 0 | stable | fails | fails | n/a | admitted |
| H3v | 15 | 46 · 0 | stable | fails | fails | n/a | admitted |
| H4d | 15 | 11 · 10 | stable | fails | fails | unassigned out fails | admitted |
| H4v | 10 | 16 · 11 | stable | fails | fails | an empty report fails | admitted |
| H5d | 15 | 0 · 19 | stable | fails | fails | unassigned out fails | admitted |
| H5v | 10 | 2 · 25 | stable | fails | fails | `None` fails | admitted |
| H6d | 10 | 3 · 11 | stable | fails | fails | unassigned out fails | admitted |
| H6v | 5 | 15 · 14 | stable | fails | fails | `None` fails | admitted |
| H7d | 5 | 3 · 11 | stable | fails | fails | unassigned out fails | admitted |
| H7v | 5 | 16 · 15 | stable | fails | fails | `None` fails | admitted |
| H8v | 20 | 4 · 3 | stable | fails | fails | `0` fails | admitted (Vec fallback) |
| H9v | 25 | 2 · 3 | stable | fails | fails | `{ }` fails | admitted (Vec fallback) |
| X1d | 6 | 12 · 0 | stable | fails | verifies: lever-needed, named | n/a | admitted, lever named |
| X1v | 6 | 14 · 0 | stable | fails | fails | n/a | admitted |
| X2d | 5 | 4 · 5 | stable | fails | fails | unassigned out fails | admitted |
| X2v | 5 | 7 · 6 | stable | fails | fails | `DStarNil` fails | admitted |

`[module.admissible]` keeps its 22 rows and minutes; only the two lever names change.

**Overlap checks.** No withheld line of an earlier R module in R11's files beyond structural lines (`ensures`, `requires Matches(r, s)`). R11's own withheld lines appear in the Lab α forms `r11-rename-transport-{d,v}` and `r06-backwards-*-v` (constructor case lines and one `choose` line), which the Lab α lane's later-tier overlap declaration and headers cover (labalpha `c9a659a`); in A4 and in the chapter only as constructor case lines, `reveal_with_fuel(valid_word_r10, 2)` and P2's own answer after its box. 0 public-answer windows (`pubwin`). Leak verifier: 8 patterns re-cut (H1d, H3d, H4d, H6d, H2v, H5v, H7v, H9v), OK over 2,596 public files.

**Chapter.** Rewritten (5,329 lint words, from 5,341 with an output appendix; 12 Dafny and 11 Rust source blocks, from 0 and 0; 32 pinned fences, from 14; four diagrams: a derivation tree for one match, the checker's trust story, the streaming loop's obligations, the Vec arena; no appendix). Answers after their boxes: P1 and P2 §2.2, P4 §3.2, P5 §5.1, P3 §6.

**Bank.** Rebuilt at the Q06 schema by a forked helper of this lane: 12 questions (2 reconstruct, 4 predict, 2 why, 2 connect, 2 transfer), 1,780 lines (from 242), 12 Reread lines, 7 backward edges (R01, R02, R04, R06, R08, R09, R10), two disjoint draws with two live predicts each (A: K3, K7; B: K2, K4), two parallel problems (PP1 a certificate checker parallel to H1, PP2 a split search parallel to H6) whose shipped, empty, trivial and reference runs were made on the course pins (bank/b/pp/outputs.json in the scratch archive).

**Written pair and numerals.** Problems, rubric and `tools/R11/README.md` numerals spaced; rubric pins refreshed; `make -C paper paper` builds.

**Study workflow** (`bin/check_workflow.py` with `r11/workflow.json`, a disposable detached worktree under this archive, removed after): 19/19 (`workflow/workflow-results.json`): `firsttry --check` records 7 first tries (5 predictions and both test-outs, each with its commented check enabled in a scratch copy), the strict report OK, `firsttry --exit` 4/4 PASS (threshold 3, per language 2/2), freeze 0, the check unit's and both units' compiled tests, both units', both checkpoint files' and both agent files' gates and audits, and `tools/R11/check_runtime.py` and `check_rule_binding.py` on the completed files (both pass in both languages). The first run (before the given tests and T1v's hollowing) failed the two unit `--test` steps ("no test ran") and recorded T1v as observed; both are fixed above. Final `firsttry.sh R11 --empty-body`: 22/22 (`logs/empty-body-final.log`).

**Focused author CI.** See Δ322 and the coordinator message (run after the commit, on a clean detached clone).

## 4. DECISION NEEDED

**1 · Line budget outliers.** All four results pass for every item; the line counts sit outside §2.2's bands in two directions. (i) T1 (5 + 5) is a one-line test-out: its difficulty is the closed-book wp argument, which the count does not see; R09's T1 was 4 lines. (ii) H8v (20 min, 7 lines) and H9v (25 min, 5 lines): the arena's work is reading and stating the frames of `push` and `set`, not writing many lines. (iii) H4v (10, 27), H5v (10, 27), H6v (5, 29), H7v (5, 31) and H3v (15, 46) are above the band for their minutes. Options: (a) keep the Δ267 minutes and record the outliers as R11 exceptions; (b) re-balance inside the 252 without changing any total: H8v 20 → 10 and H9v 25 → 15, moving 10 minutes each to H6v (5 → 15) and H7v (5 → 15), with T1 kept as a test-out exception; (c) re-pose T1 as a two-step update (`i + 2` under `i + 1 < len`) so it reaches 3 lines. **Recommend (b)** (with T1 kept): the Verus search loops are the longest references and carry the exclusion invariant; the arena's frames are shorter than their minutes.
