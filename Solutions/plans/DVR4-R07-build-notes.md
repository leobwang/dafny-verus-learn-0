# DVR4 step 5 — R07 at the R module bar (author-only)

**Binding inputs.**
- `Solutions/plans/DVR4-repair-plan.md` §2, R07's row: **revise**, with the `u32` port (§1.4, done in step 2, Δ274) and "check each hole's reference size against its band". The same plan's §2.1, §2.2, §4.2 and §5 step 5 (R07's admission rerun after the `u32` migration).
- PLAN §3 R07 (360 minutes).
- The course-wide rules:
  - D64/D84: three one-fact lines, unless an exception is recorded;
  - D82/D85: every WRITE tag names a step a smallest proof needs;
  - twins stay mirrored.

Earlier evidence: `Solutions/plans/DVR2-R07-build-notes.md`. Scratch: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p1/r07/`.

## 1. Objective-to-exercise map (written before any change, 2026-10-24)

PLAN §3's objectives for R07: where the learner meets each, the item that checks it, and the minutes (the registry's ten rows; holes 72 minutes).

| objective (PLAN §3 R07) | chapter section (to be written) | items | checked item | minutes D / V | why not trivial (to confirm) |
|---|---|---|---|---|---|
| Dafny `Std` and `vstd` lemmas called by name: search, then name (the search ladder) | the library as contracts; the search ladder | W1, W2 (Dafny) / W1–W4 (Verus), the WRITE cards C1–C3 | **T1d/T1v** `ObservedAlphabetBound` (closed book); **H1** `FilteredSamplePrefix`, **H2** `FilteredAlphabetExact`, **H3** `SampleBatchBound` | 5 / 5; 8 / 6; 11 / 7; 12 / 8 | the empty body fails; to count: one or two named calls each |
| `broadcast use` after explicit calls (hand-first rule) | scoping automation | W3v/W4v, a card | **H4v** `filter_map_origin_scoped`, **H5v** `filter_map_step_scoped` | — / 5, 5 | the empty body fails; to probe: is a broadcast needed, or does a named call do (W3v/W4v)? |
| import tiers checked transitively | the import graph | C-cards on `std`/`all` | — (the course map's tier check) | — | — |
| the toolchain-mismatch lab | toolchain mismatch | C5dv (RECOGNISE) | the lab activity (prose) | 20 | — |
| the library's trusted base | the trust surface | — | the trust audit (prose) | 20 | — |
| unbiased pass@k by hand; `EVAL.md` R-v0 | pass@k | — | the pass@k calculation; `EVAL.md` R-v0 | 15, 15 | — |
| the retriever race (rung 4) | the agentic exercise | — | **A1d/A2d**, **A1v/A2v** (agent) | agent 25 | the contract |

**Constructs.** Registry: `write_d = ["library-call"]`, `write_v = ["library-call", "broadcast-use"]`, `recognise_d = recognise_v = ["toolchain-mismatch"]`.

**Chapter plan.** Rewritten to R02's standard, with source and pinned output inline. The current chapter has no source block. It will carry PLAN §3's three diagrams: the trust surface, the search ladder, the import-tier lattice.

**Bank.** Rewritten at the Q06 schema.

## 2. Measurements and early decisions (2026-10-24; probes in `r07/min`, `r07/d91`)

Every R07 reference body is one or two named library calls. Every proper subset fails: the empty body of every hole, either call of H1d, H2d, H3d, H2v and H3v removed, and the single call of T1d, T1v and H1v removed.

| item | calls |
|---|---|
| T1d | 1 |
| T1v | 1 |
| H1d | 2 (an `assert` of the split, then `LemmaFilterDistributesOverConcat`) |
| H1v | 1 |
| H2d, H2v | 2 (one per direction) |
| H3d, H3v | 2 (the bound, and the bridge between the two flattenings) |
| H4v, H5v | 1 `broadcast use` |

W3v and W4v prove H4v's and H5v's exact statements with one named call each, so no H4v/H5v proof needed a broadcast. Brought to the coordinator as decisions 1 and 2 on 2026-10-24.

## 3. D90 and D91 (the user, 2026-10-25)

**D90: a module-wide reading for library-call holes, checked mechanically.** Each such hole is judged by the **named-call gate**:
1. the empty body fails;
2. removing any one call fails;
3. every call keeps its found-by note.

Items and minutes are unchanged. The gate is mechanical and recorded per item:
- An item opts in with a `// gate: named-calls` line, in the learner file and the twin.
- In the twin, every call of the hole carries `// found-by: <rung>`, and the block carries one `// cfree: { … }` answer per call: the hole body with exactly that call removed.
- `scripts/firsttry.sh R07 --empty-body` runs every `cfree:` answer in place of the body and requires it to fail (the forms gate), so check 2 is a solver run.
- Check 1 is the empty-body gate itself.
- `scripts/named_call_gate.py` checks, from the twins alone, that every gated item has found-by notes on all its calls and one removal answer per call.
- `tests/ci/test_named_call_gate.py` runs it on the committed twins, requiring all ten R07 hole items to be gated and recorded, and on invented fixtures:
  - a recorded item passes;
  - a missing removal answer, a call without found-by, an answer that removes nothing, and a gated item with no hole region are each refused;
  - an ungated item is not checked.

**D91: H4v and H5v re-posed so that `broadcast use` is the smallest proof.** Each now states W3's or W4's fact for every element at once, so the lemma is needed at every index of a quantified goal. The objectives (scoped automation after named calls) and minutes (5, 5) are kept, and broadcast-use stays WRITE in Verus. Evidence is in §4.
