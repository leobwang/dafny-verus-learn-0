# Q16 rubric — Practice III-A

> **Consumers:** `/grade-paper Q16` (B1, B2; then `--post` on B1) and `/review-code Q16` (Gate, Code-review focus). Q16 has no agentic file, so there is no audit debrief. Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **No prediction:** Q16 has no prediction item, so this file may be read at any time; it names no statement, invariant or lemma of the module's problems.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q16_solutions.tex  sha256 6a9ac455cbe4c5845592f2b357852018010e3ab9f5ff601c9df0a0f4f8446c0e — the written track's reference (B1, B2)
paper/Q16_problems.tex  sha256 29ed98d2ed9dc5f07f29b494b9efa6071b427cf8af2b50a52358dccf71a6b664 — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q16_PracticeIIIA/std/Q16_PracticeIIIA.dfy  sha256 a31183597fea59f6921eeac2a8c6201541a69070cb4f13888b0876283d9111d1 — the Dafny half of the code review
Solutions/verus/q/q16_practice_iiia/src/lib.rs  sha256 6805c806a78e87329a75811ef074b032790c219ab1f849f3e6e37d5dce0ad637 — the Verus half of the code review

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. A verified probe confirms a claim (verdict kind 1). An error verdict alone refutes nothing: a blueprint's formula is shown false only by a verified refutation at a concrete instance (Probes A and B) or by the learner's own verified proof contradicting it (`--post`).

- **Probe A** (B1, a claimed equation about L7's `MulAcc` or `Times`, Dafny). Instantiate the claimed equation where the definition unfolds in one step (an empty `b`), negate it, and ask the verifier to prove the negation:

  ```dafny
  module ProbeA {
    import opened QG_L1_BigNat
    import opened QG_L7_BigNat

    // A claimed equation about MulAcc, negated, at an instance where the
    // definition unfolds in one step (b empty).
    lemma AtEmptyRow(a: seq<nat>, k: nat)
      requires Valid(a)
      ensures !(ToNat(MulAcc(a, [], [1], k)) == 0)   // <- the claimed equation at b = [], acc = [1]
    {
    }
  }
  ```

  Save it as `instructor/scratch/probe.dfy` and run `scripts/vcheck --module Q16 instructor/scratch/probe.dfy`. **Verified**: the claim is false at that instance, a verified refutation (an exhibited failing instance). **An error**: the instance does not refute it; that is not a confirmation either. As shipped (the placeholder claim `== 0`) it verifies; with the true value `== 1` in its place it fails at the postcondition. Choose the instance the claim is about (other `acc`, `k` or `a`), never one of the module's items.
- **Probe B** (B1, a claimed invariant or lemma of H2 or H3, Verus). The claimed equation, negated, at one concrete state written with literal limbs:

  ```rust
  use vstd::prelude::*;
  use qg_bignat_l7::*;

  verus! {

  // A claimed invariant or lemma, negated, at one concrete state (limbs as literals).
  proof fn at_state()
      ensures
          !(seq_to_nat(seq![2u64, 1u64]) == 3),   // <- the claimed equation at the state
  {
      reveal_with_fuel(seq_to_nat, 3);
  }

  } // verus!
  ```

  Save it as `instructor/scratch/probe.rs` and run `scripts/vcheck --module Q16 instructor/scratch/probe.rs`. Verified: a verified refutation at that state. As shipped (the placeholder `== 3`) it verifies; with the true value `== 2 + BASE` it fails (`postcondition not satisfied`). The fuel is one more than the longest literal sequence; `weight(n)` is opaque, so a state that needs it adds `lemma_weight_zero()` and `lemma_weight_succ(..)` calls for the powers it uses.
- **Probe C** (B2, the card pin). `sed -n '458,481p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B2 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review, with its file's `module` line and imports (for the crate, its `use` lines) and every helper it calls, into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, renaming the module (Dafny) so it does not clash with the exercise's; delete the one line in question; run `scripts/vcheck --module Q16 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.
- **Probe E** (Gate A6, stability). `scripts/vcheck --brittleness dafny/Q/Q16_PracticeIIIA/std` and `scripts/vcheck --brittleness verus/q/q16_practice_iiia`: the summary line ends with `stable`. A `differs` line names each symbol whose verdict varies.
- **Probe F** (Gate A5, the speed test). `scripts/vcheck --test verus/q/q16_practice_iiia` prints `2 passed, 0 failed` once the suite after `verus!` is uncommented. A test that does not finish within the wrapper's wall clock is a failing test, never a pass.

## B1 — The blueprint of H1, H2 and H3 (informal proof first; dimensions: statement-fidelity, induction-soundness, case-exhaustiveness, blueprint-quality, gap-accounting)

The grade is the minimum over the five dimensions; at least 3 on every one unlocks formal work. A blueprint that differs from any other correct one is correct: grade its own statements and steps.

### statement-fidelity
- **SF.a** — each problem's top statement is the shipped one: H1 proves `MulCorrect`'s two conjuncts, H2 `div_limb`'s three `ensures` under its two `requires`, H3 `mul`'s two and `MulLoop`'s three (the exact sequence `Times(a, b)` among them). A blueprint that proves only the value of `MulLoop`'s result, or only `wf` of `mul`'s, scores ≤2, quoting the missing conjunct beside the shipped `ensures`.
- **SF.b** — a generalized statement has the shipped statement as an instance, named in (c) with the values it is instantiated at. A generalization whose instance does not give the shipped statement (a missing conjunct, a free variable fixed wrongly) scores ≤2 with the instance written out.
- **SF.c** — every invented lemma's statement is true. A false one scores ≤2 only with Probe A's or B's verified refutation pasted; one that cannot be refuted at small instances stands.

### induction-soundness
- **IS.a** — every induction names its measure, and every recursive use in (c) is at an instance strictly smaller in it. H1's answer states why the shipped statement fails as its own hypothesis (part (d)): an answer that inducts on the shipped statement alone, with no generalization, scores ≤2, citing the chapter's pinned plain attempt.
- **IS.b** — every loop invariant is stated as a formula (each conjunct, bounds included), and (c) shows its three duties: true on entry, kept by one iteration (with the step's arithmetic named), and with the negated guard giving the `ensures`. An invariant in words only scores ≤2 on this dimension, quoting the words.
- **IS.c** — the hypothesis or invariant is used only at an instance it provides: a step that uses the generalization at the shipped instance in the middle of its own proof, or an invariant at a state the loop never reaches, scores ≤2 with the step quoted.
- **IS.d** — H2's loop runs from the top limb with a counter that steps down, H3d's from the low limb up, and H3v's rows are added in place with no whole-number addition per row (the forms of the exercise files): a blueprint whose loop runs the other way, or that adds each row by a whole-number addition, scores ≤2, quoting the form line it contradicts.

### case-exhaustiveness
- **CE.a** — every base case is covered (an empty `b`, an empty `a`, `k = 0`, a zero limb, the last carry), and none is vacuous. A missing base case is a gap (3) when declared, ≤2 when the blueprint claims completeness without it, with the case named.
- **CE.b** — every bound the machine code needs is in the plan: the 128-bit sums of H2 and H3 fit, each quotient limb and carry is below `BASE`, each index is in range. A missing bound is a gap (3) unless declared.

### blueprint-quality
- **BQ.a** — the operational test: someone could formalize the blueprint without inventing a statement. Each invented lemma has a name and an exact `requires`/`ensures`; each step names the lemma or fact it uses. A step that says "by arithmetic" with no named facts and no identity written out scores ≤2, quoting it.
- **BQ.b** — two to four invented lemmas per problem, or one invariant for a loop problem's main loop, each used in (c). A lemma no step uses is a reading note; a lemma that restates the problem's own statement is a finding at 2, quoted beside the shipped statement.
- **BQ.c** — every library or layer fact is named by its declaration (`Std.Arithmetic.Mul`, `vstd::arithmetic::mul`, `vstd::arithmetic::div_mod`, L1–L7). A fact named wrongly is a gap (3) when the intended identity is written out, ≤2 when neither the name nor the identity is there.

### gap-accounting
- **GA.a** — declared gaps are honest and specific (score-3 territory, never lower for being declared). An undeclared gap confirmed by Probe A or B, or by the plan's own contradiction quoted, scores ≤2.
- **GA.b** — `--post` re-scores blueprint-quality only, against the learner's verified files: where a proof needed a lemma, a stronger invariant or another measure the blueprint lacks, record it in the diff table; it lowers the post score only where the blueprint claimed completeness at that step.

## B2 — Paper card 01.13 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B2 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 458–481). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a seed count, an interval, a cost) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a rate given to the wrong split (validation, test), the wrong source of drafts or the wrong ablation contradicts the table it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q16`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q16` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q16_PracticeIIIA/std` and `scripts/vcheck --gate verus/q/q16_practice_iiia` each exit 0 and print only the summary line.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q16_PracticeIIIA/std` and `scripts/vaudit verus/q/q16_practice_iiia` report no finding.
- **A4 — statements unchanged.** `scripts/specfreeze --check Q16` reports no finding: every shipped signature, `requires`, `ensures` and `decreases` is as shipped, and the module's nonlinear attribute is still on its `module` line (a deleted one is `freeze-lever-removed`). The lemmas you invented are new, so the freeze does not see them (C2 reads them).
- **A5 — forms, the speed test and shipped lines.** `scripts/firsttry.sh Q16 --report --strict` exits 0: every shipped commented check uncommented (`div_limb_check`, `mul_check`, `MulCorrectCheck`, `MulLoopCheck`, the speed test); H2v's `form: loop-dir:i:down`, H3v's `form: no-call:big_add, no-call:plus, no-adder` and H3d's `form: loop-dir:up` lines met; the speed test passing (Probe F); no `lever:` line.
- **A6 — stable under seeds.** Probe E: both sweeps end `stable` (gate 6 of `/review-code`). The spread of resource counts is reported, not graded: this rubric pins no threshold.
- **A7 — what is not reviewed.** The `CALIBRATION` block is your prose, read by no tool. B1's grade is `/grade-paper`'s, not this review's.

## Code-review focus — band: "library-pr"

At this bar, the conventions of the earlier bars bind (the proof reads, the induction follows the recursion it unfolds, library and layer facts are called by name, an invariant or measure is named where it is used, where each fact lives is defended, the proof is stable under seeds), plus the library pull request's: documentation on every lemma and function you wrote, helper factoring, trigger hygiene, no needless automation, golf only where it clarifies.
- **C1 — documented.** Every lemma, proof fn and helper you added in a `HELPERS` area carries a doc comment (`///` in Verus; `//` or `/** */` above it in Dafny) that says what it states, in words, in one or two lines. A missing or wrong comment (one that says something the statement does not) is a finding, cited at `file:line`, the comment quoted beside the statement.
- **C2 — factored.** Each invented lemma is called by the item it serves and states a fact the item's proof cannot get in one line; none restates the item's own statement; none is dead (Probe D on its call). Two to four per problem is the tier's range: more is a reading note, not a finding, when each earns its place. A lemma used by two items lives once.
- **C3 — the generalization (H1d).** The induction is on a statement whose recursive instance is what `MulAcc`'s recursion calls, and `MulCorrect` is proved as its instance, with the instance's arithmetic named. If A2 is green the proof is sound: a finding here is about reading, cited at `file:line`.
- **C4 — invariants as value equations (H2v, H3v, H3d).** Each loop's invariant is one statement about every step, from which the `ensures` follows at the exit; bounds and lengths it needs are stated, not left to luck. H2v's loop counts `i` down and H3d's counts up: A5's form lines check the counters, the indices each loop reads (each adds its counter) and that the loop computes the result, so the anchor of a wrong direction is A5's `form … not met` line, a finding at grade 1. The forms cannot follow an index through a helper or another sequence: a loop that reads the limbs the other way by such a route is the same finding, cited at `file:line`.
- **C5 — in place (H3v).** One result vector, written row by row at each limb's offset, with a carry of the row's own. A5's `no-call:` lines refuse L4's `big_add` and `NatLike::plus`, and its `no-adder` line a helper whose `ensures` states a whole-number sum (an adder copied under another name); a whole-number addition per row that the forms cannot see (inlined in `mul`, or a helper whose sum is stated another way) is the same finding at grade 1, cited at `file:line`. If A2, A5 and A6 hold and the rows are added in place, do not invent a flaw in the algorithm.
- **C6 — automation used on purpose.** A `broadcast use`, a `reveal`, a `reveal_with_fuel` or a scoped `nonlinear_arith` step is scoped to the body that needs it and carries a short reason; one that Probe D shows unneeded is a reading note. Triggers you write are on terms the proof instantiates. The Dafny module's `{:disableNonlinearArithmetic}` attribute stays as shipped: the anchor is A4 with no `freeze-lever-removed` finding; a removed attribute is a finding at grade 1, whatever the verifier says.
- **C7 — golf only where it clarifies.** A shorter proof that hides which fact a step uses (one wide `nonlinear_arith` over a whole loop step, a chain of calls with no comment) is a reading note with the step quoted; a longer one that names each fact is never a finding.
- **C8 — no dead code.** No commented-out experiments and no unused helpers in your own lines; the speed test stays uncommented.
