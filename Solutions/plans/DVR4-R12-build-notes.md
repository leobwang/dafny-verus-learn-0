# DVR4 step 5 — R12 at the R module bar, non-Lab-α parts (author-only)

Lane P2 of the systemic passes (plan §5 step 5), on branch `sysb`, after R14 (Δ324), built on the Lab α lane's D63 change (Δ296: optional identifier lists, a `decreases` site kind) once it reached `authoring`. Scope: the native practice (T1, H1, H2 in both languages), the check unit, the specimens, the chapter outside §7, the bank (a full Q06 rebuild), the leak patterns, the written pair. Not in scope (the Lab α lane's): `harness/` (the Python holes H1py–H5py and their twins), `bench/local/r/labalpha/`, `tools/R12/`, `Hidden/labs/R12/` and chapter §7. Binding inputs: `Solutions/plans/DVR4-repair-plan.md` §2 (R12's row), §2.1, §2.2, §2.4, §4.2, §5 step 5; PLAN §3 R12 and §14; the exemplar `Solutions/plans/DVR4-R02-build-notes.md`. Scratch and run logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p2/r12/`.

## 1. Objective-to-exercise map (written before any change)

PLAN §3's objectives for R12 that this lane's files carry, where the learner meets each, the item that checks it and the evidence that keeps it real. Minutes are PLAN §14's (test-out 10 = 5 + 5; native holes 40 = 2 × (10 + 10)); the Python rows (H1py 40, H2py 40, H3py 20, H4py 90, H5py 60) are the Lab α lane's and are listed only for the map. Lines are plan §2.2's counter (proof lines) on the references before this pass; the learner writes only the hint sites, so the site content is given beside the whole body.

| objective (PLAN §3 R12) | chapter section | worked material | checked item | minutes D / V | proof lines before (D · V), sites | why not trivial (to be confirmed by the four results) |
|---|---|---|---|---|---|---|
| four doors, one verification subject; selected versus full scope | §1 | P3dv, the selection specimens | — | — | — | a green selected symbol over a failing file |
| hint sites: the object Lab α's engine fills | §2 | the blank/filled site probes | **T1d/T1v** `CatWitnessR12` (test-out, one `expr` site) | 5 / 5 | 1 · 1, site t1 | the split must be named; TRIV `true` at the site fails |
| obligations for the loop: induction calls and regrouping facts | §2, §3 | — | **H1d/H1v** `CopiesAppendR12` (one `calls` and one `expr` site) | 10 / 10 | 7 · 12, h1a, h1b | the induction call and the regrouping equation are both needed |
| — | §2, §3 | — | **H2d/H2v** `UpToMonoR12` (one `expr` and one `calls` site) | 10 / 10 | 7 · 17, h2a, h2b | the Alt branch and the lowered bounds are both needed |
| preserve results before localizing; spans are one-based | §3 | P1d (check unit), P2v, P4v | H1py/H2py (Lab α lane) | — | — | — |
| search proposes, execution observes; fields versus original binding | §4, §5 | P5dv | H3py–H5py (Lab α lane) | — | — | — |
| read a language-server trace | §6 | the captured LSP trace | — | — | — | — |
| the toolwright: a per-symbol profiler | §10 | `tools/R12/profiler.py` | A1py (Lab α lane's tools) | — | — | — |

**Line budget (criterion 2, §2.2).** The native items are hint-site forms (PLAN §14, Δ251): the learner writes only the sites, one boolean expression per `expr` site and one call per `calls` site, inside a frozen skeleton. T1 is one site (one line) for 5 minutes, H1 and H2 two sites each for 10 minutes; the whole reference bodies are 1, 7 and 7 proof lines in Dafny and 1, 12 and 17 in Verus. The §2.2 band was written for whole-body holes; the hint-site form is the object Lab α's engine fills, so the sites stay as designed. Reported, not changed.

## 2. Probes and changes (2026-10-21)

- **Twins.** The references carried "Reference:" doc comments in place of the learner prompts and hints; they now carry the learner's prompts and hints, so twin and learner differ only at the sites (and the `// did:` receipts above them). The hint-site layout and the `R12_HINT_SITES` manifests are unchanged (D63's optional identifier lists concern the Lab α forms and the engine, not these files).
- **Specimens and the check unit.** All eight specimens and `dafny/checks/R12_checks.dfy` re-laid out one statement per line (verdicts unchanged); the twins of P2v, P4v and the check unit follow.
- **Chapter (outside §7).** Each prediction subject's source is printed above its run (the selection, P4v, fields and bound specimens; the P1 and P2 observations, which ran from packed text in the pin entries, now run from a fence above the pin); each prediction is answered after its capture; numerals spaced outside §7 (Lab α's section is untouched).
- **T1's first-try record.** T1 had no commented check, so a first try made outside a shipped branch would record as "observed" (R09's finding; the first workflow run showed it for T1v). T1d/T1v now ship `CatWitnessCheckR12` / `cat_witness_check_r12` under `Uncomment as you go:` (the twins keep it enabled under the `reference-only: enabled shipped check` marker).
- **Use-site checks (bar criterion 10).** The native items are proof lemmas (no exec hole), so the criterion does not apply; the given-only check unit stays the P1 observation.

## 3. As built (2026-10-21/22)

**Admission evidence (the four results).** (1) `vcheck --ref --brittleness`: the Dafny unit twin and the check twin verified on seeds 1–3 under the pinned Z3 4.12.1 (the advisory Z3 4.14.1 runs inconclusive on a given-layer declaration only, as in R10–R14); the Verus crate twin stable. (2)+(3) `firsttry.sh R12 --empty-body` **11/11** (`logs/empty-body-1.log`): the six native hint-site items and the five Python items (the Lab α lane's, run read-only) fail with their sites empty in every setting, and every declared TRIV fails. `specfreeze --pin R12` (83 statements, 13 files), `vcheck --ref --pin-counts R12`, the three sealed sidecars (`bound-v`, `fields-v`, `selection-v`) re-pinned after the re-layout, `reference_lint --module R12` 0, `--lint-hollow` OK (12 files). `[module.admissible]`: 11 rows unchanged.

**Overlap checks.** The 8 leak patterns (2 native, 6 Lab α Python) verify unchanged, OK over 2,627 public files. The Python twin's generic lines (`except (TypeError, ValueError) as e:`) also occur in `harness/fvh/` (shared idioms; Lab α's files).

**Chapter.** Revised outside §7 (§7 byte-identical before and after): the selection, P4v, fields and bound specimens are printed above their runs, the P1 and P2 observations run from fences above their pins instead of packed text in the pin entries, the five predictions are answered after their captures, §9 names T1's commented check; 16 pins re-captured; 6,286 lint words; 11 source blocks (from 2); three diagrams.

**Bank.** Rebuilt at the Q06 schema by a forked helper of this lane: 12 questions (2 reconstruct, 4 predict, 2 why, 2 connect, 2 transfer), 1,018 lines (from 312), 12 Reread lines, 9 backward edges (R01, R02, R04, R05, R06, R07, R08, R09, R11), two disjoint draws with two live predicts each (A: K2, K7; B: K4, K10), two parallel problems (PP1 a `calls` and an `expr` site parallel to T1/H1, PP2 a `calls` site parallel to H2) with shipped, empty, trivial and reference runs on the course pins (`bank/b/outputs.json`); Lab α appears in one connect question as context, with no results; K4 probes D63's `decreases` site.

**Written pair and numerals.** Problems and rubric numerals spaced (the remaining digit runs are SHA-256 hashes); rubric pins refreshed; `make -C paper paper` builds.

**Study workflow** (`bin/check_workflow.py` with `r12/workflow.json`, a disposable detached worktree, removed after): 10/10 (`workflow/`): `firsttry --check` records 7 first tries (5 predictions and both test-outs), the strict report OK (with the Lab α Python twins copied in read-only so its acceptance gate can pass), freeze 0, the check unit's compiled test, both native gates and audits, the Python gate, `tools/R12/test_profiler.py`. The first run (`workflow-1/`) recorded T1v as observed and failed strict on the open Python holes; both fixed in the workflow configuration (T1v's file hollowed like Dafny's; the Python twins copied).

**Not run.** The focused author CI for R12 (and R14): waiting for the coordinator's go-ahead for a 16G Verus slot.

## 4. DECISION NEEDED

None for R12's native parts. (T1 is a one-site test-out; the hint-site line counts are reported in §1 and §2.)
