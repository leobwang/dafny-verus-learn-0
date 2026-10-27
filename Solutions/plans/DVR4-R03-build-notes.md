# DVR4 step 8 — R03 kit build notes (author-only, lane P1)

Binding inputs:
- `Solutions/plans/DVR4-repair-plan.md` §1 (D48, the u32 design; §1.3 what R03's items become; §1.5 item 2, the re-verification) and §5 step 8 (the kit). The plan's §6 D-A1 (a) to D-A4 (a) were decided by the orchestrator (Δ274).
- PLAN §3 R03 and PLAN §6.3 (files, items, constructs, the agentic file, the 300 minutes).
- The R module bar of plan §4.2, as R02 met it (Δ283).
- The course-wide rules:
  - D64/D84: every hole's smallest proof has at least three one-fact lines, unless an exception is recorded;
  - D82/D85: every WRITE tag names a step that a smallest proof needs;
  - D90: the named-call gate, where it applies;
  - D92: `writes = "module"` only for learner-written modules;
  - twins mirrored.

Starting point: the parked draft `Solutions/plans/drafts/R03/`. Its API core twins were rebuilt on u32 in step 2 (Δ274). Everything else in it is still char-based: learner files, agent files with `CharPrev`/`CharNext`, `char_scalar.rs`, specimens, chapter, bank, paper and fixtures. Nothing of R03 is in the tree yet, and the registry row is `planned`.

Scratch: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step8/p1/r03/`.

Rules for every solver job: one at a time, a 6G outer scope (12G for CI), `free -g` ≥ 20G first, the pinned toolchain on PATH (D78), no model.

## 1. Objective-to-exercise map (written before any change, 2026-10-26)

PLAN §3's objectives for R03, the item that checks each, and the minutes (PLAN §6.3: holes 10 × 7 = 70).

| objective (PLAN §3 R03) | chapter section (to be written) | items | checked item | minutes D / V | to confirm by probe (the course-wide bar) |
|---|---|---|---|---|---|
| modules, `import`, export sets (`provides` vs `reveals`) / `mod`, `pub`, private fields | the module boundary | W1d/W1v (mini-API), C1d (WRITE export), C2d (recognise import), C5v (WRITE pub-visibility), P3dv/P4dv | **H2d** (adds `ClassRange` to the export set), **H4d/H4v** (a client of the API only) | 7 / 7 each | is the export edit needed by a smallest answer (D82)? is H4's client ≥ 3 one-fact lines (D64)? |
| `View` and `@`, `open` vs `closed spec fn` | the abstraction square | C3v (WRITE view), C4v (WRITE closed-spec), P4dv | H1v–H3v, H5v (view), H2v/H3v (closed-spec) | 7 each | does each tagged hole's smallest answer use the tagged step? |
| representation invariants (`ClassValid`) and abstraction (`InClass`, the view `ISet<char>`) on u32 code ranges | representation and validity on code points | W2d/W2v (worked `ClassInsert`: overlap and adjacency merge) | **H1** `ClassMember` / `member_from`, **H3** `ClassUnion` over `ClassInsert` | 7 / 7 | the function holes' "smallest proof": a definition plus its proof obligations; measure and record the reading |
| total functions (no partiality hidden in a `requires`) | totality | P1d/P2v (a strengthened `requires` and its four call sites) | **H2** `ClassRange(lo, hi)` (total; `Code` monotone/injective), **H5** `ClassOfString` | 7 / 7 | does H2 need a given `CodeOrder` lemma, or do both solvers know it? |
| what a client may assume | the client's view | C8dv (divergence), the API REVIEW block | H4 client `Union3` / `union3` | 7 / 7 | as above |
| opacity (recognise; WRITE in R08) | — | C6d/C7v | — | — | — |
| rung-2 API implementer + adversarial review | the agentic exercise | A1d/A1v `ClassIntersect`, `ClassDiff` (u32 splits under guards; no `CharPrev`/`CharNext`) | the contract (gate, specfreeze, vaudit) | agent 30 | the boundary probes: `0`, `u32::MAX`, adjacency, a range across the surrogate block |

**Constructs (registry, PLAN §6.3):**
- WRITE: `write_d = ["export"]`, `write_v = ["view", "closed-spec", "pub-visibility"]`.
- RECOGNISE: `recognise_d = ["import", "opaque"]`, `recognise_v = ["opaque"]`.
- Each WRITE tag needs ≥ 2 genuine uses per language (D82/D85). A tag that no smallest answer uses is a decision for the coordinator.

**Kit plan, in order (one solver job at a time):**
1. Port the learner files and twins from the draft onto u32. The core twins already exist. The learner files are derived from the twins: prompts, two hints, one statement per line. The agent files are rebuilt without `CharPrev`/`CharNext`, and `char_scalar.rs` is not carried over. Specimens and cards are ported (P1d/P2v wording per §1.3).
2. Registry row: `planned` → `authoring`, `admissible` rows, units, imports. Then gen_units and the course map.
3. Measurements: the smallest answers per hole (D64), and the WRITE tags (D82). Decisions go to the coordinator as found.
4. Admission: seeds 1–3, `--empty-body` with maximal automation and TRIV for the exec items, the agent pair (statements, specfreeze, vaudit), freeze, counts.
5. Chapter to the R02 bar: ≥ 5,000 words, source and pinned output inline, every prediction answered by a capture, PLAN's two diagrams. Then the bank at the Q06 schema, the paper card 03.2 with its gold and flawed fixtures, rubric pins, leak patterns and the A2 header line ("re-supplies R03's API").
6. Study workflow, then the focused CI. Ask before the CI.

## 2. The port onto u32 (2026-10-26)

Installed from the parked draft, onto the u32 core twins of step 2:
- **Twins and learner files.** One statement per line, with `**Hn.**` prompts (a guiding question and two hints per hole). The learner files are generated from the twins. Verus `uses: view` is dropped from H1v and H2v.
- **Agent files** rebuilt on u32. `CharPrev`/`CharNext` and `char_scalar.rs` are gone. `ClassDiff`/`class_diff` keeps `[lo, a - 1]` under `lo < a` and `[b + 1, hi]` under `b < hi`: no overflow, and no char built from a number. The reference helpers sit after the "clearly marked reference implementation" heading.
- **Specimens.**
  - P1d keeps its answer, `FAILS c d`. Its `ClassMember` is a ghost function whose body is `InClass`, called with `ghost var`, so the twin carries no hole form; a `planted:` marker is only for S10/S12 items.
  - P2v (rewritten 2026-10-27) is a small self-contained API whose invariant is only non-emptiness, with `class_single`, `class_span` and a proof-fn `member_contract`. It keeps `FAILS c d`, and no longer copies the given class code (that copy printed H6v's and H7v's definitions in a file opened before the holes).
  - P3/P4 (D/V): ported to u32 code ranges, still `D:fail V:fail`.
  - Card and demo names renamed for avoid.sh (`SingleHoldsItsCharR03`, `SevenR03`).
- **Lints:** `reference_lint` 0; `--lint-hollow` OK; avoid.sh OK; course map OK.

## 3. D93, D94, D95 (the user, 2026-10-27)

**D93: H2 and H4 re-posed to meet D64.**
- **H2** `ClassRange(lo, hi)` / `class_range` now also promises at most one range: `ClassRank(r) <= 1` in Dafny, and in Verus `r.rank() <= 1` with a new given `pub closed spec fn rank`.
  - The given Dafny `ClassInsert` is made `opaque`, so even inside `CharClasses` its body (which would show one range for an empty input) is hidden. The learner builds the representation and proves membership with the witness range 0. `class_insert` is exec, so its body is never visible anyway.
  - Probes, Dafny: the one-call answer `ClassInsert(ClassEmpty(), …)` fails; a missing witness assert fails; a missing proof block fails; an empty class fails.
  - Probes, Verus: the `class_empty` + `class_insert` answer fails; a missing witness fails; a missing proof fails.
  - `ClassInsert` opaque made the given `InsertRanges` run out of resources once (it was already the widest spread, CV 34.7 %); `{:isolate_assertions}` on it fixed that (88 verified).
- **H4** is the union of a sequence of classes.
  - Dafny: `method UnionOfClasses(cs: seq<CharClass>)`, a recursion. Smallest found: 5 one-fact lines (`ClassEmpty()`, the recursive call, `ClassUnion`, and two witness picks).
  - Verus: `pub fn union_of_classes(cs: &Vec<CharClass>)`, a loop. Smallest found: `class_empty`, four invariant clauses (each one's removal fails) and the `class_union` call.

**D94: `pub-visibility` written by the learner.**
- `class_range` (H2v) and `class_union` (H3v) ship without `pub`. Without it the client module is refused: "associated function `class_range` is private", "method `class_union` is private".
- Tooling: specfreeze and reference_lint gained open visibility (commit 82238a82). A Verus file marked `// specfreeze: open-visibility` may add `pub` to fns its twin declares `pub`; `--pin` lists them under `open_visibility`, and everything else on them stays frozen. Tests: `VerusOpenVisibility` in `tests/wrappers/test_practice_tools_static.py`.

**D95: `closed-spec` written by the learner (option A, approved 2026-10-27).**
- Probe: a `pub open spec fn` that reads a private field is refused at resolve ("disallowed: field expression for an opaque datatype"); `pub closed` verifies; a bare `pub spec fn` is a parse error.
- **H6v** `pub closed spec fn valid(&self) -> bool` and **H7v** `pub closed spec fn chars(&self) -> ISet<char>` (the view returns `self.chars()`) are Verus-only spec-definition holes, shipped `pub uninterp spec fn …;`.
- Probe: with them uninterp, the shipped file had 10 errors in `class_empty`, `copy_class`, `class_member` and W2v's `class_insert`.
- Those four ship `#[verifier::external_body]  // GATED until H6v and H7v: then delete this line`, in their own `impl` block so that the gates sit outside the definition items. Their bodies and proofs are complete, and W2v is still the worked proof to read. The learner loop counts the gates as holes (11 counted as shipped). `firsttry --strict` now fails on any GATED line anywhere in the file (commit 82238a82; test `test_strict_counts_a_gated_attribute_anywhere`).
- **Wrong-but-plausible answers** (probes, `r03/d95`):

| hole | wrong definition | what fails |
|---|---|---|
| H6v | adjacency allowed (`rs[i].1 < rs[j].0`) | W2v `class_insert`: "invariant not satisfied before loop" (its `separated(rs)` clause) |
| H6v | non-empty ranges only (no order) | the same invariant, in `class_insert` |
| H7v | half-open ranges (`c as u32 < hi`) | `class_member`'s postcondition; assertions in `class_insert` (two), `class_range` and `class_union` (5 errors) |
| H7v | only the first range | `class_member`'s postcondition; assertions in `class_insert` (two) and `class_union` (4 errors) |

- The H6v/H7v prompts say why the four functions are gated and that W2v is the worked proof to read. The hints point at `open` being refused rather than naming `closed`.

**Minutes (honest, D93–D95).**
- H1 7, H2 10, H3 7, H4 12 and H5 7 in each language, and H6v 5, H7v 5: Dafny 43, Verus 53, holes 96 (from 70).
- R03 326 min (from 300); band 1 2,168 (from 2,142); R 7,520 min / 125.3 h (from 7,494 / 124.9).
- The registry, PLAN §1.1, §3 R03, §6.3 and the band table are updated. DESIGN-PROPOSAL's 124.9 h is not edited, since it is the design record; PLAN supersedes it.

## 4. Measurements (D64, smallest found)

| item | Dafny | Verus |
|---|---|---|
| H1 | 3 (base, recursive call, the first range's test; a definition) | 4 (`false`, the range read, the code, the comparison with the recursive call) |
| H2 | 4 (construction, empty case, witness, proof block) | 4 (Vec, push, construction, witness) |
| H3 | 3 (base, `ClassInsert`, recursive call; a definition) | 13 (a loop with five invariant clauses and its step proof) |
| H4 | 5 | 6 (empty class, four invariant clauses, the union call) |
| H5 | 3 (base, recursive call, `ClassInsert`; a definition) | 10 (a loop with three invariant clauses and its step proof) |
| H6v, H7v | — | definitions (spec-definition holes, judged through their uses: the table above) |

The Dafny function holes (H1d, H3d, H5d) are definitions: their gate is the twin's cfree answers, each of which fails.

## 5. Admission (2026-10-26/27)

- Seeds 1–3 stable on the four twins: core D/V and agent D/V. Widest spreads: Dafny core 34.7 %, before `{:isolate_assertions}`; agent D 17.1 %, core V 10.1 %, agent V 5.9 %.
- `firsttry.sh R03 --empty-body` 12/12.
  - The function holes pass by cfree answers; the Verus exec holes by the empty body and TRIV; H4d by the empty body and the region gate.
  - H6v and H7v are skipped as spec-definition holes.
  - The region markers were removed from function and value-returning holes: blanking an expression body doesn't type-check.
- `specfreeze --pin`: 180 statements, with `open_visibility = ["class_range", "class_union"]`.
- Counts pinned. Chapter: 19 pins; 8,033 words.
- Leak patterns: 8 OK (H1d, H2d, H4d, H5d, H1v, H3v, H4v, H5v) over 2,802 public files. H6v and H7v are not cut: their prompts state the definitions in words, and the agent file copies the given class code (it carries a do-not-open-before-the-holes header, like A4's, Δ321).
- Paper builds; the card 03.2 source hash matches; rubric re-pinned (Probe C and the gate items for u32, GATED, open visibility and the D93 items).
- **Deferred:** the A2 header line "re-supplies R03's API: do not open before R03's holes are done". Changing A2's bytes would make the R07–R14 chapter pins that hash A2 stale; deferred as before (R06's D87 ripple decision).

## 6. Chapter, bank, paper, pins and workflow (2026-10-27)

- **Chapter** `docs/R03_Modules.md`: built from the draft and rewritten for u32 and D93–D95.
  - Structure: the three-ideas opening, a files table, §0–§10 with `---` separators, On paper before the exercise file, the agentic section with its CONTRACT blockquote, "What the instruments can and cannot see", Instructor touchpoints naming every skill, and "What R03 planted".
  - Captures: 19 pins, with sources inline above every specimen pin. Every prediction is answered after its capture (P1 and P2 `FAILS c d`, P3 and P4 `D:fail V:fail`). Three new demonstrations: `opaque-d`, an opaque contract hiding a body fact (D93); `open-private-v`, a `pub open spec fn` over a private field refused (D95); `private-call-v`, a client calling a non-`pub` fn refused (D94).
  - 8,033 words; `chapter_lint` 0.
- **Bank** `.claude/skills/instructor/banks/R03.md`, at the Q06 schema:
  - 12 questions (2 reconstruct, 3 predict, 3 why, 2 connect, 2 transfer), all viva-able, in two disjoint draws: A is K1, K2, K4, K6, K7, K10; B is K3, K5, K8, K9, K11, K12.
  - Live predicts K2, K3 and K9, each with its own toy probes in both languages and their captured outputs.
  - Seven backward edges, to R01 and R02 only.
  - PP1 parallels H2 and PP2 parallels H5, each author-verified (as shipped, a naive body, a reference body).
  - Tags all in concepts.md; no R03 leak pattern matches.
  - Written by a delegated agent from the R08 exemplar, then checked here.
- **Paper:** card 03.2, unchanged (source hash matches); rubric updated and re-pinned; fixtures installed; `make -C paper paper` builds.
- **Pins:** `pins.py --ci --module R03` 29/29; verdict pins written (`expected/R03.pins`); `--ref` 0.
- **Other checks:** counts and freeze re-pinned (170 statements; open visibility recorded); `reference_lint` 0 over 325 twins; avoid.sh OK (chapter excerpts no longer show `type V`); leak verifier OK over 2,804 public files.
- **Study workflow** 11/11 on a disposable clone of 82238a82 plus this diff: first tries, strict, freeze, gate and audit on both units and both agents.
