# DVR4 step 5 — R14 at the R module bar (author-only)

Lane P2 of the systemic passes (plan §5 step 5), on branch `sysb`, after R13 (Δ323). Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2 (R14's row), §2.1, §2.2, §2.6 (the rebuild on R14's own `MatchesV`, Δ279), §4.2, §5 step 5; the user's **D57** (fuel and bit-vector are RECOGNISE; WRITE covers triggers and nonlinear facts; Δ282); PLAN §3 R14 and PLAN §16; the exemplar `Solutions/plans/DVR4-R02-build-notes.md`. Scratch and run logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p2/r14/`.

## 1. Objective-to-exercise map (written before any change)

PLAN §3's objectives for R14, where the learner meets each, the item that checks it and the evidence that keeps it real. Minutes are PLAN §16's (holes 70 = 2 × (10 + 10 + 15); battery 60, CV sweeps 40, toolsmith 30 are lines of their own); none is narrowed. Lines are plan §2.2's counter (`scripts/pcount.py`, proof lines) on the Δ279 references before this pass; a hole's reference-only helper counts with it (H3's `SquareGrowth` / `lemma_square_growth`).

| objective (PLAN §3 R14) | chapter section | worked material and cards | checked item | minutes D / V | proof lines before (D · V) | WRITE / RECOGNISE (D57) | why not trivial (to be confirmed by the four results) |
|---|---|---|---|---|---|---|---|
| triggers on split existentials | §1 | `MatchesV`'s stated triggers, C1, C4dv, P1dv | **H1d/H1v** `CatIntroV` / `lemma_cat_intro_v` | 10 / 10 | 3 · 3 | WRITE: trigger | the instantiation term is absent from the goal; facts without it do not help |
| matching loops | §3 | the loop/repair cells of the battery | battery (60) | — | — | WRITE: trigger | — |
| fuel is unfolding depth, not induction | §4 | C2 (concrete `n = 3` by fuel), P5dv | **H2d/H2v** `StarPowV` / `lemma_star_pow_v` (induction) | 10 / 10 | 5 · 6 | RECOGNISE: fuel (read on the card; the hole is an induction) | default induction is disabled by the printed lever; fuel covers one `n` |
| nonlinear facts | §5 | P2dv, C5dv divergence | **H3d/H3v** `DerivSizeV` / `lemma_deriv_size_v` | 15 / 15 | 18 · 16 | WRITE: nonlinear-arith | induction plus a product inequality per case |
| bit-vector facts | §5 | C3 (`bv32` / `by (bit_vector)`) | battery cells | — | — | RECOGNISE: bit-vector | — |
| resource limits, seeds, stability | §6 | CV sweeps | CV sweeps (40) | — | — | — | — |
| the toolsmith: `trigscan` | §8, §11 | `tools/R14/trigscan.py` | the battery (60) and toolsmith (30) | — | — | — | the learner audits all 12 cells |

**Line budget (criterion 2, §2.2).** H1 is 3 proof lines for 10 minutes and H2 5–6: H1 sits under the 5–15 band (at the "under 3 is redesigned" line, not below it); H3 is inside the 15–30 band. Reported (DECISION NEEDED), not narrowed.

**Constructs taught before the holes (criterion 11).** Triggers and their terms (§1, C1, C4dv), the SMT log route (§2), matching loops (§3), fuel and its limits (§4, C2: RECOGNISE), nonlinear queries and the D/V divergence (§5, C5dv: WRITE), bit-vector facts (§5, C3: RECOGNISE), resource limits and seeds (§6).

**File order (criterion 9).** The header, the prediction block, `MatchesV` and `PowerWord`, then H1 (trigger), H2 (trigger plus induction), the given size lemma (Verus), H3 (nonlinear). The cards are specimens read in §1–§5 before the holes.

## 2. Probes (2026-10-21)

- **D57 and H3v's fuel step.** H3v's reference needed `reveal_with_fuel(node_count, 3)` in the Cat case, and its prompt and Hint(2) asked for it: a learner-written fuel lever, which D57 makes a RECOGNISE construct. The Verus file now gives that unfolding as a lemma, `lemma_deriv_cat_count_v` (its body is the one `reveal_with_fuel`, with its `// did:` receipt), and H3v's Cat case calls it; H3v's `uses:` drops `fuel`, its prompt and Hint(2) name the lemma. The statement of H3v and its minutes are unchanged. Dafny's H3d never needed fuel (Dafny opens `NodeCount` twice by default).
- **D57 in the registry.** Moving `nonlinear-arith` from RECOGNISE to WRITE fails `check_course_map`'s rule that a WRITE slug is tagged by at least two H/X/T items per language: only H3 uses it. Not applied: DECISION NEEDED (§4). The cards, prompts and chapter already treat nonlinear facts as written work (H3) and fuel and bit-vectors as read (C2, C3).
- **Twins.** The references carried "Reference:" doc comments in place of the learner prompts and no regions; the twins now carry the learner's prompts and hints with `@hole` regions, so the region gate runs; the learner files are regenerated from them (unchanged apart from the Verus given lemma and H3v's prompt).

## 3. As built (2026-10-21)

**Files.** Twins rebuilt from the learner files with `@hole` regions and the reference bodies (the learner prompts and hints now appear in both); the reference-only `SquareGrowth` / `lemma_square_growth` carries the bare `// reference-only` marker, so the learner files are regenerated from the twins byte for byte (apart from the Verus given lemma and H3v's prompt and Hint(2)). `specfreeze --pin R14` (50 statements, 19 files), `vcheck --ref --pin-counts R14` re-pinned, `reference_lint` 0 (the first install left `// SLOT: CHECK` in the twins and the helper marker one line too high: both fixed before any admission run).

**Admission evidence (the four results).** (1) `vcheck --ref --brittleness`: both twins verified on seeds 1–3 under the pinned Z3 4.12.1; under the advisory 4.14.1 the Dafny runs are inconclusive on one declaration outside the target's files (the given-layer pattern of R10–R13; advisory, never gating); the Verus crate stable (CV 1.2%). (2)+(3) `firsttry.sh R14 --empty-body` 6/6 (`logs/empty-body-1.log`): every empty body fails in the shipped configuration and under maximal automation (H3d's maximal-automation run ran out of resources at the pinned limit, counted as failing under QPLAN §30 Q66), every seed, and every item also fails with its twin region blanked. (4) TRIV: proof lemmas only (no exec item), so no TRIV body; a probe without the given size lemma shows H3v's reference fails without it (`probes/h3v-nocount.rs`). `specfreeze --check R14` 0 (50 statements), `--lint-hollow` OK (18 files), `reference_lint` 0. Bar criterion 10 does not apply (no exec hole).

| item | minutes | proof lines after | (1) seeds | (2) empty, shipped | (3) maximal automation | (4) TRIV | row |
|---|---|---|---|---|---|---|---|
| H1d | 10 | 3 | stable | fails | fails | n/a | admitted |
| H1v | 10 | 3 | stable | fails | fails | n/a | admitted |
| H2d | 10 | 5 | stable | fails | fails | n/a | admitted, lever named |
| H2v | 10 | 6 | stable | fails | fails | n/a | admitted |
| H3d | 15 | 15 + 3 helper | stable | fails | inconclusive (counted failing) | n/a | admitted |
| H3v | 15 | 14 + 2 helper | stable | fails | fails | n/a | admitted |

Minutes reconcile: 35 + 35 = 70 = PLAN §16's holes; `[module.admissible]` keeps its 6 rows unchanged.

**Overlap checks.** The 7 leak patterns still match the regioned twins (verifier OK over 2,595 public files); 0 public-answer windows. R05's two extensionality lines in `card-c4dv-v` and the R14 card-c1v twin's two concrete slice lines in R04's chapter are generic sequence idioms of earlier modules.

**Chapter.** `docs/R14_Smt.md` revised (every run already had its source above its capture, and every prediction its answer): §0 states D57's WRITE/RECOGNISE split, §5's Verus paragraph points at the given size lemma, §10 names H1 correctly (`CatIntroV`, not the stale `CatStarIntroV`) and H3v's Cat-case lemma; 17 pins re-captured; 5,276 lint words, four diagrams, no appendix.

**Bank.** Already at the Q06 schema (12 questions, 13 Reread lines, two disjoint draws, two parallel problems with runs). Fixed: three Reread lines named wrong section numbers (the battery is §8, the paper §9, the instruments table sits in §10); K6's backward edge named the parked R03 (now R09's code-point classes); K6's follow-up asked the learner to write a `by (bit_vector)` repair (now: read it and say what it asks of the solver, D57).

**Written pair and numerals.** No glued numerals in learner prose (the remaining digit runs are SHA-256 hashes); the rubric's H3 line follows the given lemma; rubric pins refreshed; `make -C paper paper` builds.

**Study workflow** (`bin/check_workflow.py` with `r14/workflow.json`, a disposable detached worktree, removed after): 9/9: `firsttry --check` records the 5 predictions, strict OK, freeze 0, both gates and audits, `tools/R14/test_trigscan.py` OK on the completed `trigscan.py`, `tools/R14/battery.py` 12/12 cells closed and audited.

**Focused author CI.** See Δ324 and the coordinator message (run after the commit, on a clean detached clone).

## 4. DECISION NEEDED

**1 · D57 in the registry.** D57 makes `nonlinear-arith` a WRITE construct, but `check_course_map` requires every WRITE slug to be tagged `uses:` by at least two H/X/T items in each language, and only H3 uses it (2 errors when the lists are moved). The registry keeps `nonlinear-arith` under RECOGNISE for now; everything else follows D57 (fuel and bit-vector RECOGNISE: H3v's fuel step is now a given lemma; the chapter states the WRITE/RECOGNISE split). Options: (a) split H3 into H3a, the product-inequality helper as its own item (5 minutes, `uses: nonlinear-arith`), and H3b, the induction that calls it (10 minutes, `uses: nonlinear-arith`), per language: H3's 15 minutes and the 70-minute total unchanged; (b) keep `nonlinear-arith` RECOGNISE in the registry until R15 adds a second written use, and record D57's WRITE reading in the chapter and cards only; (c) relax the rule to one tagged item for R14. **Recommend (a)**: the helper is exactly the written nonlinear work (`by (nonlinear_arith)` in Verus, the expanded square in Dafny), so it is an honest second use.

**2 · H1 under the line band.** H1 (10 minutes per language) is 3 proof lines in each language: under §2.2's 5–15 band for a 10-minute hole, at the "under 3 is redesigned" line. All four results pass; the work is finding the trigger term, which the line count does not show. Options: (a) keep 10 / 10 as an R14 exception; (b) move 5 minutes per language from H1 to H3 (H1 5, H3 20; total unchanged); (c) extend H1 to `Cat(a, Star(a))` (the chapter's old `CatStarIntroV` text: two trigger terms, about 6 lines). **Recommend (a).**

(§3 and §4 above record the first pass, committed as `2948c89`. The coordinator settled §4 the same day; §5 records what was applied and the re-admission.)

## 5. Settled (the coordinator, 2026-10-21) and applied

**1 · nonlinear-arith: option (a), with one change forced by the gate.** The split is H3 (5 minutes per language, `uses: nonlinear-arith`) and H4, the induction `DerivSizeV` / `lemma_deriv_size_v` (10 minutes, `uses: nonlinear-arith`); item ids follow the registry's `H<n>` grammar (no "H3a"). The registry moves `nonlinear-arith` to WRITE in both languages (`write_d`/`write_v` = trigger, nonlinear-arith; `recognise` = fuel, bit-vector); `check_course_map` passes for R14 (its 2 remaining errors are R04's, P1's). **The product-inequality helper as H3 failed admission:** `firsttry.sh R14 --empty-body` reported H3v "FALLS TO AUTOMATION" (its empty body verifies under the E2, EM and NL maximal-automation modes, seeds 1–3: a pure arithmetic fact is closed by the nonlinear mode; `logs-v2/empty-body-1.log`), and in Dafny its empty body only runs out of resources. H3 is therefore H4's **Cat case** on its own, `CatCaseV` / `lemma_cat_case_v`: from the two bounds on the operands' derivatives, the bound on the Cat's derivative. Its proof is the product inequality (the learner's own helper over two naturals: the squares expanded, asserted in Dafny, `by (nonlinear_arith)` in Verus) plus, in Verus, the given size lemma; no automation mode can make that call (`probes2/cc-*.rs`: empty and helper-only bodies fail; reference verifies; Dafny `cc-*.dfy`: empty body out of resources on seeds 1–2, reference verifies). H4 calls H3 in its Cat case and needs inequalities of the same shape in the Alt and Star cases, so both items write nonlinear facts. The helper is reference-only (`SquareGrowth` / `lemma_square_growth`), shared by H3 and H4 in the references. Minutes: H3 5 + H4 10 = the old H3's 15.

**2 · H1: option (c), re-posed.** H1 is now `TwoChunksV` / `lemma_two_chunks_v`: two non-empty words of `a`, one after the other, match `Star(a)`. The trigger objective is kept at two levels of the same existential: `v` as a one-chunk word of `Star(a)` (its split at `|v|` and the empty rest), then the split of `u + v` at `|u|`. Reference: 8 proof lines in each language (in band). Probes (`probes2/h1-*.dfy`, `h1v-*.rs`): the empty body fails in both languages; the old two-equation proof (the outer split only) fails; dropping single lines shows the two-level structure is needed. The old H1 (`CatIntroV` / `lemma_cat_intro_v`) stays in the files as the given worked example W1, because `tools/R14/battery.json` calls it in two cells and the chapter's §1 explains it. Minutes: H1 10, H2 10, H3 5, H4 10 per language = 70, PLAN §16's holes.

**Not mine, reported.** The Lab α lane's sealed tasks `r14-cat-intro-v-{d,v}` and `r14-deriv-size-v-{d,v}` were cut from R14's old H1 and H3 references; their statements are still course objects (W1 and H4), but their provenance names change.

**Re-admission (after §5).** (1) `vcheck --ref --brittleness`: both twins verified on seeds 1–3 under the pinned Z3 4.12.1 (Dafny's advisory Z3 4.14.1 runs inconclusive on a given-layer declaration only, as before; Verus stable, widest spread `lemma_square_growth`, CV 15.0%). (2)+(3) `firsttry.sh R14 --empty-body` **8/8** (`logs/empty-body-1.log`; the run with the helper as H3 is `logs-v2/`, the first pass `logs-v1/`): every empty body fails in the shipped configuration and under maximal automation, every seed, and with its twin region blanked; H3d's shipped and maximal-automation empty bodies and H4d's maximal-automation one run out of resources at the pin and are counted as failing (QPLAN §30 Q66). `specfreeze --pin R14` (54 statements), `vcheck --ref --pin-counts R14`, `reference_lint` 0, `--lint-hollow` OK, `check_course_map` clean for R14, rubric pins current, the paper builds. Chapter re-captured (17 pins, 5,416 lint words; §0, §1, §5, §10 name W1 and the new H1, H3, H4). Leak patterns re-cut (8: H1d–H4d, H1v–H4v; H3's by the helper's expansions), verifier OK. Study workflow 9/9 on a disposable worktree (`workflow/`: 5 first tries, strict, freeze, both gates and audits, `test_trigscan.py`, the battery 12/12 with W1 still serving its two cells).

| item | minutes D / V | proof lines (D · V) | (1) seeds | (2) empty, shipped | (3) maximal automation | row |
|---|---|---|---|---|---|---|
| H1 `TwoChunksV` | 10 / 10 | 8 · 8 | stable | fails | fails | admitted |
| H2 `StarPowV` | 10 / 10 | 5 · 6 | stable | fails | fails | admitted, lever named (D) |
| H3 `CatCaseV` | 5 / 5 | 1 + 3 helper · 2 + 3 helper | stable | fails (D: out of resources, counted failing) | fails (D: as (2)) | admitted |
| H4 `DerivSizeV` | 10 / 10 | 15 · 14 | stable | fails | fails (D: out of resources, counted failing) | admitted |
