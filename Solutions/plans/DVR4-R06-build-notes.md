# DVR4 step 5 — R06 at the R module bar (author-only)

**Binding inputs.**
- `Solutions/plans/DVR4-repair-plan.md` §2, R06's row: **keep**, plus a rewrite of P5v (a loop over `NodeCount` with a different invariant shape, re-captured).
- The same plan's §2.1, §2.2, §4.2, §5 step 5 and §7.
- PLAN §3 R06 and §6.6's 462-minute record.
- The course-wide rules now in force:
  - D64/D84: every hole's smallest proof is at least 3 one-fact lines, unless a recorded exception applies.
  - D82/D85: every WRITE tag names a step a smallest proof needs.
  - Twins stay mirrored.

Earlier R06 evidence is in `Solutions/plans/DVR1-R06-build-notes.md`. Scratch and logs: `~/.cache/dafny-verus-learn-0/author-probes/dvr4-step5/p1/r06/`.

## 1. Objective-to-exercise map (written before any change, 2026-10-24)

PLAN §3's objectives for R06: where the learner meets each, the item that checks it, its minutes (PLAN §6.6), and what keeps the item real. The minutes are as recorded and none is narrowed; the registry holds 14 admissible rows.

| objective (PLAN §3 R06) | chapter section (to be written) | items that use it | checked item | minutes D / V | why not trivial (to confirm by the four results and the D64 count) |
|---|---|---|---|---|---|
| loop invariants and loop `decreases`; the invariant as the induction hypothesis of an induction on the counter | the loop as an induction | W2, C2 | **T1d/T1v** `AllNullable` (closed book); **X2d/X2v** (checkpoint) | 5 / 5; 5.5 / 5.5 | the empty implementation fails its postcondition (exec: TRIV and implementation lines, D59's reading) |
| lemma recursion as induction, with a measure on the lemma | lemmas as induction | W1, C3 | **H1d/H1v** (the learner's measure); **X1d/X1v** | 60 / 68; 5.5 / 5.5 | an empty body fails; the measure is the learner's (to probe: is it needed in Dafny, where the default `decreases` may already be `r`?) |
| manual induction in Dafny (`{:induction false}`, Q-owned auto-induction stated) | manual induction | C4, C5 | **H1d**, **X1d** | — | the attribute is given, so the recursive calls are the learner's (to probe) |
| `calc` chains | calc | C1 | tagged on **H1** and **H4** | — | to probe: is `calc` a step the smallest proof needs, or a one-step wrapper? |
| the derivative and its correctness (the flagship, every constructor including `Star`) | the derivative; the flagship | W1, the paper problem | **H1d/H1v** `DerivCorrect` | 60 / 68 | an empty body fails; the `Cat` and `Star` cases need splits and recursive calls |
| the derivative matcher's loop invariant | the matcher loop | P4d, P5v | **H2d/H2v** `DerivMatch` (annotation hole: the loop, measure and proof call given) | 12 / 12 | the twin without its regions fails (RGN); to count its one-fact lines |
| refuting a plausible false statement about `Star` with a counterexample | refute | — | **H3d/H3v** `StarUnfoldRefuted` | 5 / 5 | an empty body fails; to count (a witness of two facts may be under the bar) |
| repairing it with the weakest hypothesis, then proving the repair | repair and prove | — | **H4d/H4v** `StarUnfold` (`requires` open) | 12 / 12 | an empty body fails; the weakest-hypothesis rule is reviewed by hand |
| hole-driven decomposition (green at every step) | the decomposer | — | **A1d/A1v** (agent) | agent 22 | the contract |

**File order (bar criterion 9).** The given `Deriv`; T1 (closed book); the prediction block; W1–W2; the WRITE cards C1–C4 and C5d; the holes H1–H4; the logs block; C6dv last.

**Prompts and hints (criteria 7–8).** Every H and X item gets a `**Hn.**` (`**Xn.**`) prompt with a guiding question, and `Hint(1)`/`Hint(2)`. The checkpoint's prompts stay closed-book and carry no hints.

**Chapter plan.** Rewritten to R02's standard with exactly PLAN §3's three diagrams:
- a string consumed one character at a time, with the derivative after each step;
- the invariant as the induction hypothesis on the loop counter;
- the flagship's decomposition tree.

Source and pinned output go inline, and every prediction is answered by a capture.

**Bank.** Rewritten at the Q06 schema: 12 questions, two draws with live predicts, backward edges to R01–R05, tags from `concepts.md`.

**Known item (repair plan):** P5v is to be rewritten so that it no longer nearly shows H2v's answer.

## 2. Measurements and early decisions (2026-10-24; probes in `r06/tags`, `r06/min`, `r06/d87`, `r06/p45`)

Smallest found proofs come from the greedy minimizer over whole files, with brace structure kept and both orders run. One-fact lines are counted as in D64: bindings don't count; `:|`/`choose` lines, calls, invariant clauses and conjuncts do.

| item | facts | note |
|---|---|---|
| H1d | about 25 | |
| H1v | ≥ 4 recursive calls plus splits | the harness could not parse its match arms; the reference makes 6 calls |
| H2d | 4 | |
| H2v | 6 | |
| H3d | **1** | |
| H3v | **2** | |
| H4d | 4–5 | plus the repaired `requires` |
| H4v | 4 | |
| X1d | 3 | plus the measure |
| X1v | 2 | plus the measure, once it is the learner's |
| X2d | 4 | |
| X2v | 5 | |
| T1 | exec | the empty implementation fails its postcondition |

Tag probes:
- **`calc`.** Removing H1's and H4's one-step wrappers verifies in both languages (`d-nocalc`, `v-nocalc`).
- **Measures.**
  - Dafny's default measure already serves H1d (`d-nodecr`).
  - X1d fails termination without its clause (`x1d-nodecr`).
  - Verus refuses H1v without one at resolve.
  - Both checkpoint items shipped their measure given.
- **P4d and P5v.** Each held its hole's bridge line verbatim:
  - P4d: `assert [s[i]]+s[i+1..] == s[i..];`, H2d's bridge;
  - P5v: H2v's `seq![s@[i]] + …` bridge.

Brought to the coordinator as decisions 1–4 on 2026-10-24.

## 3. D86–D89 (2026-10-24)

- **D86 (the user): `calc` is RECOGNISE in both languages.**
  - The cards C1d/C1v are `recognise:calc`, H1 and H4 lose `uses: calc`, and their one-step wrappers are removed.
  - Registry: `recognise_d = ["induction-auto", "calc"]`, `recognise_v = ["calc"]`; `calc` leaves both write lists.
  - The chapter's §4 presents `calc` as recognised.
- **D87 (the user): `lemma-decreases` is genuine in both languages, with no exception.**
  - The checkpoint's measures become the learner's in both languages: `decreases |u|` is stripped from the learner's X1d and `decreases u.len()` from X1v, and the prompts say "write the measure its recursion needs". Both are needed (`x1d-nodecr`; Verus requires the clause). X1v becomes 3 facts.
  - H1d's re-pose, so that Dafny's default measure fails: reordering the parameters to (c, s, r) makes the default fail at the prefix calls (`d87/csr`, `scr`, `src`), and `decreases r` restores it (`d87/csr-decr`).
  - The frozen A2 layer re-supplies `DerivCorrect(r, c, s)`, which R08, R11, R13 and the Lab α corpus call in that order.
  - **The coordinator's answer, (a):** H1 is reordered in R06 only, in both languages to keep the mirror: `DerivCorrect(c: char, s: seq<char>, r: Re)` and `lemma_deriv_correct(c: char, s: Seq<char>, r: Re)`. Every call site in R06 is reordered too (H1's recursive calls, H2's given call, the chapter's P6 stand-in).
  - Without its `decreases r`, the final twin fails termination at the four prefix calls (`d87/final-nodecr`). So Dafny has two genuine items (H1d, X1d), Verus has two (H1v, X1v), and there is no exception.
  - A2 stays byte-identical, with `(r, c, s)`. R06's chapter (§2.4) says that A2 re-supplies the same theorem with the regex first.
  - **Deferred:** the matching line in A2's header waits for A2's next planned change. Any edit to the A2 files would stale the recorded inputs of the chapter pins in R08–R14.
- **D88 (the user): H3d and H3v are refutation-witness exceptions** under D59's reading. They are 5 minutes each and judged by the empty-body gate: the counterexample is the empty word by nature, and H4 repairs exactly H3's claim.
- **D89 (the coordinator): P4d and P5v are rewritten as one pair** over `NodeCount`.
  - The invariant is one-directional, `n >= i`, with no derivative and no bridge line.
  - The labels: [a] on entry, [b] at the end of the body, [c] `n >= |rs|`, [d] `n == |rs|`.
  - The answer is `FAILS d` in both languages (captured); minutes unchanged.
- **induction-false (the coordinator): genuine.** The attribute is given, but the recursive calls it forces are the learner's.

## 4. As built (2026-10-24)

**Files.**
- Every R06 code file is one statement per line with spaced commas: core, checkpoint, agents, the check unit and every specimen, in both copies. Three layout passes did this (`bin/agentfmt.py`, `fmt2.py`, `fmt3.py`), with hand fixes after.
- T1, H1–H4 and X1–X2 have `**Tn.**`/`**Hn.**`/`**Xn.**` doc-comment prompts with a guiding question. H1–H4 have `Hint(1)`/`Hint(2)`. T1 and the checkpoint are closed book and carry no hints.
- The learner files are derived from the twins (`r06/derive.py`):
  - H1's measure, H4's `requires` and the checkpoint's measures are stripped;
  - H2/X2 keep the given loop with an `assume` at the top;
  - T1v and X2v keep their `external_body` holes.
- The specimen twins mirror the specimens; P2v, P4d and P5v differ only in their answered slots.

**Admission.**
- Seeds 1–3 are stable for all six twins: core d/v, exit d/v, agent d/v. The widest spreads are advisory: the Dafny agent's CV is 41.6 %, the others are ≤ 26 %.
- `firsttry.sh R06 --empty-body` gives 14/14; H4v runs as an open statement with its twin's clauses laid over.
- The registry's 14 rows are unchanged.
- Freeze re-pinned (86 statements, open specs StarUnfold/lemma_star_unfold); `--check` 0.
- Counts re-pinned; `--shipped` 0. `--lint-hollow` OK (21 files). `reference_lint` 0.
- Sealed sidecars refreshed (13); P2v, P4d and P5v are refused by design (H5).

**Chapter.**
- Rewritten to R02's standard: 5,195 lint words, 34 pins (from 19), and PLAN §3's three diagrams.
- Source is inline for every scratch scenario and every card or specimen it pins.
- Every prediction is answered by a capture. P1, P2 and P6 are new captures:
  - P6 is a stand-in attempt with the flagship's statement as a hole, so no proof of H1 appears, plus a separate counterexample lemma showing the shortcut false.
- `chapter_lint` 0. `pins.py --ci --module R06` 60 pins, 0 problems; `--ref` 6 checks, 0 problems.

**Bank.**
- Rewritten at the Q06 schema: 12 questions (2 reconstruct, 4 predict, 2 why, 2 connect, 2 transfer), all `viva: yes`.
- Draw A has live predicts K3 and K7; Draw B has K2 and K4.
- Nine backward edges (R01, R02, R04, R05). Every tag is in `concepts.md`, and every `**Reread**` resolves.
- Every probe ran on the pins (`r06/bank/out.json`).
- Two parallel problems, both verified as shipped, empty and reference: PP1 `SwapAlts`, structural induction with splits, for H1; PP2 refute/repair/prove, for H3/H4. PP1's function was renamed from `Mirror`, a curated `avoid.sh` name.

**Leak patterns.** 8. H1d is re-cut for D87's parameter order. H1d, H1v, H4d and H4v also match Lab α forms, which are declared (Δ294). The verifier gives 8 OK over 2,728 public files.

**Overlap.** Excluding Lab α:
- H1d shares 17 of 592 24-token windows with the chapter: W1's given `Chr` case, which H1's `Chr` case repeats.
- H3v shares 16 of 135 with its own learner file: the statement's expression, restated in the last assertion.
- No other answer shares more than 5 windows with any file.

**Rubric.** Six pins refreshed; all 194 current.

**Course map.** OK. Every remaining WRITE tag names a step a smallest proof needs:
- `invariant`: T1, H2 (and X2).
- `lemma-decreases`: H1d, X1d, H1v, X1v; each needed, probes `d87/final-nodecr`, `x1d-nodecr`, Verus resolve.
- `induction-false`: H1d, X1d.

## 5. Focused checks (2026-10-24)

Run one solver job at a time in `dvl0.slice` under an 8G outer scope. No exit 137 or 143.
- Empty-body 14/14. Seeds 1–3 stable for six twins.
- Pins: chapter 34; module 60 and `--ref` 6, 0 problems.
- `chapter_lint` 0. `check_course_map` OK. Leak verifier 8 OK. Rubric pins current.
- Study workflow 11/11 on `c66b353c` (`workflow.log`): firsttry, strict, freeze, the check unit's test, and the gate and audit of both core units and both agent files.
- The checkpoint twins gate (Dafny 16 verified, Verus 9, 0 holes) with clean audits in a scratch worktree. With the twins' measures in place, the freeze still reports 0 findings, so the measures the learner writes pass as added measures; `wf.py` does not cover the exits.

The focused author CI (static, harness, wrappers, rubric) needs the 16G slot and waits for the coordinator.
