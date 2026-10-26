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
