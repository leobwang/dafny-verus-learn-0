# DVR4 step 5 — R10 at the R module bar (author-only)

Lane P2 of the systemic passes (plan §5 step 5), on branch `sysb`, after R09 (Δ320). Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2 (R10's row: **keep** + systemic: appendix outputs, packed twins), §2.1, §2.2, §4.2, §5 step 5; PLAN §3 R10 (Why, Core payload, Diagrams, Written track, Exercises, Agentic role, Hours) and PLAN §12 (the band-2 item plan: items and minutes); the exemplar `Solutions/plans/DVR4-R02-build-notes.md`. Scratch and run logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p2/r10/`.

## 1. Objective-to-exercise map (written before any change)

PLAN §3's objectives for R10, where the learner meets each, the item that checks it and the evidence that keeps it real. Minutes are PLAN §12's (holes 110 = 55 + 55; no test-out); none is narrowed. Lines are plan §2.2's counter (`scripts/pcount.py`) on the step-3 references as shipped (packed layout).

| objective (PLAN §3 R10) | chapter section | worked material and cards | checked item | minutes D/V | proof · exec lines before (D · V) | why not trivial (to be confirmed by the four results) |
|---|---|---|---|---|---|---|
| the enforcement spectrum (runtime check, Option, precondition, type) | §1.3, §4 | W2d/W2v (runtime predicate), P3dv | the spectrum lab (30) and **H1d/H1v** (the Option end) | 8 / 10 | 1 + 5 · 2 + 3 | H1's rejection clause (`None ==> !is_norm`, the function body in Dafny) rejects an always-reject body; TRIV `None` fails |
| subset types and `function by method` (D); `#[verifier::type_invariant]` with `Ghost`/`Tracked` (V) | §1.1–1.2, §2, §3.1, §5.1 | W1d/W1v (the packet), C1d/C1v, C2d, C2v/C3v, C3d, P4v | **H1**, **H2d/H2v** (rebuild the erased count) | 12 / 12 | 1 + 5 · 5 + 5 | the subset predicate / type invariant is checked at construction; H2 must follow `MkCat`'s four branches from the operands' facts |
| normal forms (`NormRe`) and the normalizer's termination | §3.2 (the rewrite lattice), §7 | A4's `Norm`, `MkAlt`/`MkCat`/`MkStar` | **H3d/H3v** (normal regexes are fixed points; idempotence given) | 15 / 15 | 5 · 6 | structural induction with each child's hypothesis; Dafny ships `{:induction false}` |
| erasure: what reaches compiled code | §2.3, §3.2 | the erasure diagram; `tools/R10/check_normalizer.py` | **H4d/H4v** (the compiled normalizer equals the ghost model) | 20 / 18 | 2 + 14 · 5 + 18 | the function body `Norm(r)` rules out a constant valid packet; the method cannot call the ghost model |
| learner-written language-preservation statements (rung 8, spec-to-proof flagship) | §6, §11 | `tools/R10/check_statements.py` | A1d/A1v (statements 40 + audit 20) | — | — | the consumer over an arbitrary result (§6.2) fails for shape-only statements |

**Constructs taught before the holes (criterion 11).** Subset types and their construction obligation (§1.2, C1d, C3d), type invariants and `use_type_invariant` (§1.2, §5.1, C1v), ghost fields and erasure (§2.1), `Ghost`/`Tracked` (§2.2, C2v, C3v), `function … by method` (§3.1, C2d), why a ghost model cannot be called (§3.2), structural induction under `{:induction false}` (R02/R06, recalled in the H3 prompt).

**File order (criterion 9).** The prediction block; the worked examples W1 (packet types), W2 (runtime check), W3 (a language fact); the holes H1–H4 with the given idempotence corollary after H3; the given compiled use-site test. The cards are specimens read in §1–§3.

**Line budget (criterion 2, §2.2).** H3 is a 15-minute proof hole whose shipped reference is a 5–6-line structural induction: below §2.2's 15–30-line band for a 15–20-minute hole. Measured after the re-layout and reported (DECISION NEEDED), not narrowed or re-posed in this pass.

## 2. Probes (2026-10-20)

- **TRIV for the Dafny by-method items** (`probes/triv-*.dfy`): `return NoPacketR10;` (H1d), `return a;` (H2d) and `return CountPacketR10(Empty, 1);` (H4d) each fail the by-method agreement at the method's return. The Verus TRIV body of H1v (`None`) is the twin's `// triv:` line, run by the gate; H2v and H4v return a struct whose trivial body is not a literal (no TRIV line; their empty bodies fail).
- **The by-method region gate.** Blanking a by-method body leaves the out-value unassigned; the region gate reports it as failing, as required (the empty-body log).
- **H3d's lever.** With Dafny's default induction the empty body of `NormalFixedR10` verifies; with the shipped `{:induction false}` it fails. The registry row now names the lever ("printed induction-disabled levers"), as R02's H2d/H3d rows do.
- **A4's header.** A4 imports A1b and A2, which re-supply R02's, R03's, R05's and R06's answers, and carried no "do not open before" line (bar criterion 16). Both A4 files now say so, in the same number of lines (so no captured diagnostic that points into A4 moves; R11–R14's chapter pins need a hash refresh only).

## 3. As built (2026-10-20)

**Files.** Both exercise files and twins re-laid out one statement per line and reordered: the prediction block (moved from the file's end to the top), W1 the packet types, W2 the runtime check, W3 the congruence fact, then H1–H4 with the given idempotence corollary after H3, then a given compiled use-site test (`PacketSampleTest`, `packet_sample_test`: bar criterion 10, the exec holes are function-by-method or exec items whose only live check is compiled). Every hole has a `**Hn.**` prompt with a guiding question and `Hint(1)`/`Hint(2)`; H4 gains `uses:` lines. The module and symbol names the R10 tools import are unchanged (one module `R10_TypeInvariants`). Specimens, the check unit and both agent files re-laid out (verdicts unchanged; sealed sidecars re-pinned); the agent learner files say where the human's statements go; the twins' H3v carries a `// did:` receipt on its `reveal_with_fuel`. New specimen `chapter-p1-d.dfy.specimen` (self-contained: a specimen runs alone).

**Admission evidence (the four results).** (1) `vcheck --ref --brittleness`: every twin verified on seeds 1–3 under the pinned Z3 4.12.1 (unit twins, agent twins, check twin); under the bundled Z3 4.14.1 the Dafny runs are inconclusive on a declaration outside the targets' files (a given layer; advisory, never gating), the Verus twins stable. (2)+(3) `firsttry.sh R10 --empty-body` 8/8 (`logs/empty-body-1.log`), H3d lever-needed and named. (4) TRIV as §2. `specfreeze --check R10` 0 (68 statements), `--lint-hollow` OK (20 files), `reference_lint` 0.

| item | minutes | reference lines (proof · exec) | (1) seeds | (2) empty, shipped | (3) maximal automation | (4) TRIV | row |
|---|---|---|---|---|---|---|---|
| H1d | 8 | 1 · 6 | stable | fails | fails | `NoPacketR10` fails | admitted |
| H1v | 10 | 2 · 4 | stable | fails | fails | `None` fails | admitted |
| H2d | 12 | 1 · 7 | stable | fails | fails | `return a` fails | admitted |
| H2v | 12 | 10 · 12 | stable | fails | fails | n/a (struct result) | admitted |
| H3d | 15 | 10 · 0 | stable | fails | verifies: lever-needed, `{:induction false}` named | n/a | admitted, lever named |
| H3v | 15 | 11 · 0 | stable | fails | fails | n/a | admitted |
| H4d | 20 | 5 · 25 | stable | fails | fails | a constant packet fails | admitted |
| H4v | 18 | 5 · 23 | stable | fails | fails | n/a | admitted |

Minutes reconcile: 55 + 55 = 110 = PLAN §12's hole line; `[module.admissible]` keeps its 8 rows.

**Overlap checks.** 0 public-answer windows for every R10 file; no withheld line of an earlier R module in R10's files. R10's own withheld lines appear in the Lab α forms `r10-mk-cat-correct-{d,v}` and `r10-star-star-{d,v}` (the flagship's reference helpers), which the Lab α lane's later-tier overlap declaration and headers cover (labalpha `c9a659a`, the coordinator, 2026-10-20). The chapter's consumer probe and the bank's K8 were changed so that neither prints a flagship statement verbatim (the statement checker's source still shows the consumer relation, as before: the flagship is a guided design exercise). Leak verifier: 8 patterns re-cut, OK over 2,594 public files.

**Chapter.** Rewritten (5,260 lint words, from 5,279 with an appendix; 20 Dafny and 11 Rust source blocks, from 0 and 0; 39 pinned fences, from 19; PLAN §3's three diagrams: the enforcement spectrum, erasure of one function, the rewrite lattice; no output appendix). Answers after their boxes: P3 §4.2, P1 and P2 §4.3, P4 §5.2, P5 §6.1.

**Bank.** Rebuilt at the Q06 schema by a forked helper of this lane: 12 questions (2 reconstruct, 4 predict, 2 why, 2 connect, 2 transfer), 1,499 lines, 12 Reread lines, 7 backward edges (R01, R02 twice, R04, R06, R08, R09), two disjoint draws with two live predicts each (A: K3, K7; B: K2, K4), two parallel problems (PP1 a nullable-flag packet parallel to H1/H2, PP2 normalization keeps nullability parallel to H3) with author-verified runs.

**Written pair and numerals.** Problems, rubric and `tools/R10/README.md` numerals spaced; rubric pins refreshed; `make -C paper paper` builds.

**Focused author CI.** Run `20261021T040214Z-1955924` on `41bc3b0` (a detached clone with the R10 commit and the A1b hash refresh; the earlier run on `fc6ef39` was interrupted by the 22:43 CDT reboot and counts as not run): verify-r-dafny PASS 488 s, verify-r-verus PASS 347 s; static FAIL 850 s at `check_single_route.py` (the pre-existing Lab α files `bench/local/r/labalpha/pub-hev-075/tasks/pub-hev-075.rs`, `harness/fvh/report.py`) and `chapter_lint --all` (11 stale pins in `docs/R08_Abstraction.md`, inputs `RG_A1b_Facts.dfy`: P1's A1b header change, R08 is P1's module); pins FAIL 2,627 s on the same 11 R08 pins only (1,463 pins over 31 modules checked; `pins --ref` 192 checks, 0 problems). Every R10 check passed.

## 4. DECISION NEEDED

**1 · H3 under the line band.** H3 (15 minutes per language) is a structural induction whose references are 10 (Dafny) and 11 (Verus) proof lines by the counter, one statement per line: below §2.2's 15–30-line band for a 15–20-minute hole. All four results pass. Options: (a) keep 15 / 15 as an R10 exception: the item's difficulty is reading why each smart constructor returns its plain node on normal children (three `Normal` cases), which the line count does not show; (b) move 5 minutes per language from H3 to H4 (H3 10, H4 25 / 23; the 110 total is unchanged; H4's references are the longest, 30 and 28 lines); (c) extend H3 to the idempotence corollary as part of the hole (adds 2–4 lines; the corollary is given today). **Recommend (b).**

**Settled (the coordinator, 2026-10-21): (b).** 5 minutes per language move from H3 to H4: H3 10 / 10, H4 25 / 23 (Dafny / Verus); the hole total stays 110 (55 + 55). Measured reference lengths (pcount, proof · exec): H3d 10 · 0, H3v 11 · 0; H4d 5 · 25, H4v 5 · 23. Applied in `MODULES.toml` (`[module.admissible]`) and the chapter's minutes line and item table; no hole, statement or reference changed.
