# Q02 rubric — First syntax I

> **Consumers:** `/grade-paper Q02` and `/grade-paper Q02 --post` (B1–B3), `/review-code Q02` (Gate, Code-review focus), and you, after `/contract Q02` (the audit debrief). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q02 --check` has recorded every Q02 prediction.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q02_solutions.tex  sha256 3d8830d1f2355b622aa69602b6a64c5bf31331fd3d0d7e663300ef49fc678e9d — the written track's reference (B1–B3)
paper/Q02_problems.tex  sha256 8840f2e0972f924cba2291d97bfd32338c3332e5cdb748aac7a9fc39016ec8e2 — the problems these lines grade
Solutions/dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy  sha256 c48d5ffce2ff1bf5a075fffcd85c1cb47f1f0fa0575260a98ed6512611a464e9 — the formal reference B1 (a) precedes (H3d), and the Dafny half of the code review
Solutions/verus/q/q02_first_syntax_i/src/lib.rs  sha256 e6f8e29dd16f00e8c97f16e08a28421904cbaaf957a0255335b556440826b1a4 — the formal reference B1 (b) precedes (H2v), and the Verus half of the code review
Solutions/dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy  sha256 2ade24c2cc8900f5c784f9900931aedcde36d25b798f1abdc507513309cbbf38 — the reference delivery behind the audit debrief (Dafny)
Solutions/verus/q/q02_first_syntax_i/src/agent.rs  sha256 3ca8f849207a6286a4fe4ddaf780a27be22c270b28786d7ee8c0aad06491b6dd — the reference delivery behind the audit debrief (Verus)

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. The program text below is the problems file's or the exercise files'; the lines marked `<-` are where your own statements go. A verified probe confirms a step (verdict kind 1). An error verdict alone refutes nothing: a flaw is exhibited by an executable check (a `@Test` method with `expect`, run with `scripts/vcheck --test`) or by a verified refutation.

- **Probe A** (B1 (a), splice template: does the blueprint close as written?). In `instructor/scratch/probe.dfy`, filled from your blueprint alone:

  ```dafny
  module ProbeA {
    import opened QG_L1_BigNat
    import opened QG_L2_BigNat

    // One bodyless lemma per helper your blueprint names that is not a given lemma:
    // its statement only, exactly as you wrote it.
    lemma Helper1(s: seq<nat>)
      requires true          // <- your helper's hypotheses
      ensures true           // <- your helper's equation

    // The target under a probe name. Its body is your Base and Step, transcribed: one
    // branch per case you list, and only the calls and asserts you name, in your order.
    lemma Target(s: seq<nat>)
      ensures ToNat(Normalize(s)) == ToNat(s)
      decreases |s|
    {
                             // <- your cases, calls and asserts
    }
  }
  ```

  Run `scripts/vcheck --module Q02 instructor/scratch/probe.dfy` (the module's given layers and unit options). Verified, with one hole per pasted helper and no other: the decomposition closes, given those helpers. A resolve error on a helper exactly as written: that statement is not formalizable as written (paste the error). A verification error: a gap until Probe A″ exhibits a false step. With the reference blueprint spliced in, this template was verified on the pins (Dafny 4.11.0): `verified`, one hole.
- **Probe A′** (B1 (b), splice template: is the invariant enough?). In `instructor/scratch/probe.rs`, the problems file's loop under a probe name, with the helper the body calls pasted by its statement (H1v's, as the exercise file ships it) and your invariant spliced in:

  ```rust
  use vstd::prelude::*;
  use qg_bignat_l2::*;

  verus! {

  pub proof fn drop_top_zero_helper(s: Seq<u64>)
      requires
          s.len() > 0,
          s.last() == 0,
      ensures
          seq_to_nat(s.drop_last()) == seq_to_nat(s),
  {
      assume(false);  // the helper's statement only
  }

  pub fn blueprint_normalize(a: &mut BigNat)
      ensures
          final(a).wf(),
          final(a).to_nat() == old(a).to_nat(),
  {
      while a.limbs.len() > 0 && a.limbs[a.limbs.len() - 1] == 0
          invariant
              true,  // <- your invariant, over a and old(a)
          decreases a.limbs.len(),
      {
          proof {
              drop_top_zero_helper(a@);
          }
          a.limbs.pop();
      }
  }

  } // verus!
  ```

  Run `scripts/vcheck --module Q02 instructor/scratch/probe.rs`. Verified with exactly one hole (the helper): the invariant is enough, given the helper. With the reference invariant spliced in, this template was verified on the pins (Verus 0.2026.09.27.3cf1832): `verified`, one hole.
- **Probe A″** (B1, a step claimed false). A test file stands alone, so it carries copies of the problems file's definitions:

  ```dafny
  module ProbeStep {
    const BASE: nat := 18446744073709551616

    function ToNat(s: seq<nat>): nat
      decreases |s|
    {
      if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
    }

    function Normalize(s: seq<nat>): seq<nat>
      decreases |s|
    {
      if |s| == 0 then []
      else if s[|s| - 1] != 0 then s
      else Normalize(s[..|s| - 1])
    }

    @Test
    method StepOnExample()
    {
      var s: seq<nat> := [];          // <- the concrete sequence
      expect true, "the step fails";  // <- the step's equation, at s
    }
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. `FAILED` with the message: the step's equation is false at that sequence, a confirmed flaw. `PASSED`: the step holds there, and nothing is refuted.
- **Probe B** (B2 (b), the exhibited state). One pass of the learner's loop body from the learner's state:

  ```dafny
  @Test
  method OnePassFromState()
  {
    var x: int, y: int := 0, 0;   // <- your state before the pass (every variable)
    expect true;                  // <- your clause holds before the pass
    expect true;                  // <- the guard holds before the pass
    x, y := x, y;                 // <- the loop body, once
    expect !(true);               // <- your clause, negated: it fails after the pass
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. `PASSED` means the state shows the clause is not inductive on its own. Captured on the pins with a correct answer spliced in: `1 passed, 0 failed`.
- **Probe B′** (B2 (b), the clause holds wherever the loop goes). Copy the learner's loop into `instructor/scratch/probe.dfy` as a method, with the clause beside the invariant clauses the learner names in (c), and run `scripts/vcheck --module Q02 instructor/scratch/probe.dfy`. Verified confirms the clause in every reachable state. When it does not verify, the claim "holds in every reachable state" is refuted only by a reachable state that breaks the clause, shown by running the loop compiled from its start state with an `expect` of the clause after each pass (a `@Test` method, `scripts/vcheck --test`).
- **Probe C** (B3, the card pin). `sed -n '766,791p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B3 prints. Run it before grading any field.
- **Probe D** (Code-review focus C4, a dead step). Copy the declaration under review, with the module's imports, into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, delete the one line in question, and run `scripts/vcheck --module Q02 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.
- **Probe E** (Audit debrief D5, your adversarial checks). Each one is a lemma (Dafny) or a `by (compute_only)` proof fn (Verus) in the agent file's trailing block; `scripts/vcheck <agent file>` runs them. A Verus run reports one failing `compute_only` check at a time, the first in file order (the agent file's header and chapter §10): read the error's line, not the symbol line.

## B1 — Normalizing keeps the value (informal-proof-first)

### statement-fidelity
- **SF.a** — (a) proves the stated equation for every limb sequence: no hypothesis added (no validity, no length bound) and none dropped, the same direction. A score ≤2 quotes the restated claim and exhibits a sequence on which it and the problem's equation differ.
- **SF.b** — (b) states an invariant about the loop as given (its variables are `a` and `old(a)`), not about a different loop. A rewritten loop is a gap (3) unless the rewrite changes what the invariant must say, shown by Probe A′ verifying on one loop and not the other.

### induction-soundness
- **IS.a** — the induction is named (on what, in which order) and the induction hypothesis is a formula with its quantifier explicit. An IH in words only is a gap (3).
- **IS.b** — every use of the IH is at an instance the stated IH provides: a strictly smaller instance by the named order. A score ≤2 names the use, the instance it needs, and exhibits a concrete sequence at which that instance is not covered.
- **IS.c** — every equation a step uses holds. A score ≤2 exhibits a concrete sequence at which the step's equation fails, by Probe A″ (`FAILED` with the step's message).
- **IS.d** — (b)'s invariant holds on entry and is kept by one pass, and with the negated guard gives both `ensures` clauses; Probe A′ verifies with it spliced in. When Probe A′ does not verify, the invariant scores ≤2 only with an exhibited state where it holds, the guard holds, and after one pass (the pop, with the helper's equation) it fails.

### case-exhaustiveness
- **CE.a** — the cases cover every sequence (the branches of `Normalize` as defined, or a split shown equivalent), each case states its condition, and each case's argument applies to every sequence in it. A score ≤2 exhibits a sequence that falls in no case, or in a case whose argument fails on it (Probe A″).

### blueprint-quality
- **BQ.a** — every helper fact is named by its statement (an equation between values of named sequences, with its hypotheses) and attributed: a given lemma by its name, another hole of this module by its item, or a declared gap. The operational test is Probe A filled from the blueprint alone, with nothing invented: if it verifies with one hole per pasted helper, do not invent a flaw. A Probe A that does not verify is a gap (3) unless Probe A″ exhibits a false step.
- **BQ.b** — every fact a step relies on is named, the facts a reader might take for granted included. A missing one is a gap (3), recorded for the `--post` diff, never a flaw by itself.
- **BQ.c** — (b) says which fact keeps the invariant across a pass and what gives each `ensures` clause at the exit, and names the measure's decrease.

### gap-accounting
- **GA.a** — declared gaps score 3. An undeclared step that is false at an exhibited input is a flaw (≤2). An undeclared step that is true but unjustified is recorded as a gap (3), never as a flaw.

## The --post pass

Runs once `scripts/vcheck --gate dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy` and `scripts/vcheck --gate verus/q/q02_first_syntax_i` both exit 0 (H3d and H2v are in them). Re-score `blueprint-quality` of B1 only, with your verified `NormalizeToNat` and `normalize` as the oracle:
- **BQ.d** — diff the blueprint against the proofs: the helpers it named against the calls and asserts `NormalizeToNat` makes; the IH instance against the recursive call's argument; the cases against the branches; (b)'s invariant against the invariant clause you wrote. Record each fact the proof needed that the blueprint did not name, and each named helper the proof never used.
- **BQ.e** — record whether formalizing forced a change the paper missed (an extra fact, a different instance, an extra clause). A blueprint whose decomposition survived formalization scores 4; each missed fact is a finding at 3, never lower unless the blueprint's step was false at an exhibited input.

The gradebook gets a `paper-post` row with the new `blueprint-quality` score.

## B2 — True is not inductive (concept; dimension: correctness)

### correctness
- **CO.a** — (a) names, for each of the three obligations, whether it bears on inductiveness. A score ≤2 quotes the claim and exhibits a loop and clause that contradict it, shown with Probe B and Probe B′ (an executable state, or a verified loop).
- **CO.b** — (b)'s clause holds in every reachable state (Probe B′ verifies with the companions the answer names), and (b)'s state passes Probe B. A score ≤2 exhibits a reachable state that breaks the clause (compiled run, Probe B′'s fallback), or a Probe B run on the answer's own state that fails, output pasted. A state left unchecked by the answer but passing Probe B is correct: do not invent a flaw.
- **CO.c** — (c) says what pruning does with the clause in each of the two settings, consistently with the card's own description of pruning (its pinned range) and with (b)'s probes. A claim that Probe B or Probe B′ contradicts on the answer's own loop scores ≤2, with that probe's output pasted.

## B3 — Paper card 02.7 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B3 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact). An empty field scores 1 for that field.
- **CF.c** — each field agrees with the pinned range. A field scores ≤2 only by quoting the pinned line it contradicts, with its line number.
- **CF.d** — a field for which the range is silent is correct when it says so (and what would be needed); silence in the range is never a contradiction.
- **CF.e** — wording is free: a field in the learner's own words that agrees with the range scores 4. The card's grade is the minimum over its fields.

## Gate

The mechanical preconditions of `/review-code Q02`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck --module Q02` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy`, `scripts/vcheck --gate verus/q/q02_first_syntax_i` and `scripts/vcheck --gate dafny/checks/Q02_checks.dfy` each exit 0 and print only the summary line. After both contract runs, `scripts/vcheck --gate dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy` and `scripts/vcheck --gate verus/q/q02_first_syntax_i/src/agent.rs` do too.
- **A3 — audit, pinned.** `scripts/vaudit dafny/Q/Q02_FirstSyntaxI/core`, `scripts/vaudit verus/q/q02_first_syntax_i` and `scripts/vaudit dafny/checks/Q02_checks.dfy` report no finding; `scripts/vaudit --compare expected/Q02_AgentImplement.audit dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy` and `scripts/vaudit --compare expected/q02_first_syntax_i_agent.audit verus/q/q02_first_syntax_i/src/agent.rs` report no difference.
- **A4 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q02 --report --strict` exits 0 (the test-out blocks written and their checks uncommented, every slot filled and recorded, and, after the exit's scored run, the exit files repaired).
- **A5 — statements unchanged.** `scripts/specfreeze --check Q02` reports no finding.
- **A6 — diagnosis fixtures stay out.** The card demos under `specimens/Q02/card-*` are red by design (their failures are pinned) and are never finished or reviewed; the obligation specimens `specimens/Q02/P1d.dfy.specimen`, `P2v.rs.specimen`, `P5d.dfy.specimen` and `P6v.rs.specimen` are predictions, covered by A4 alone. A2 and A3 skip all of them. No brittleness gate applies at this bar.

## Code-review focus — band: "it-reads"

- **C1 — the method clauses no instrument sees.** H1d and H1v each use one `assert … by`; H5d and H6d build their result with a `while` loop that states its `decreases`; X1d (once its exit block is repaired) recurses counting `i` up, as its prompt asks. Read the file, and cite `file:line` for a clause that is not met. If every clause is met, do not invent a flaw.
- **C2 — names say what things are.** Any name you introduced (a loop index, a local sequence, an adversarial check) says what it holds or tests. If you introduced none beyond the shipped ones, there is nothing to review here: do not invent a flaw.
- **C3 — intent stays in the shipped contracts.** Q02's statements ship frozen; A5 is the anchor. A changed `requires`, `ensures`, `modifies` or check line is a finding at grade 1, whatever the verifier says.
- **C4 — no dead steps.** Each `assert`, lemma call and invariant clause you wrote is needed: Probe D shows it. A line Probe D shows dead is a finding at this bar; without that evidence, do not invent a flaw.
- **C5 — measures written out.** Every recursion and loop you wrote states its `decreases`, in both languages, as the course does everywhere. A missing one that the verifier still accepted is a finding at this bar (it reads less clearly), cited at `file:line`.
- **C6 — adversarial checks read as cases of the prose contract.** Each check in the agent files' trailing blocks states one concrete input and the value the prose contract (the doc comment) gives it. A check that holds for the delivered body is not a defect: it documents a case. If every check states its case plainly, do not invent a flaw.
- **C7 — no dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.

## Audit debrief — after /contract Q02

Questions for you, after each contract run (Dafny, then Verus). Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — was every per-edit check the fast channel?** Count the `scripts/vcheck` commands in the transcript: each one between edits should be `--symbol` on the definition just edited or on a check that uses it. Any other verifier command before the last is a breach of the contract's first acceptance line; name it.
- **D2 — was there exactly one full gate, last?** Find every `scripts/vcheck --gate` in the transcript: exactly one, after the last edit, exit 0, printing only its summary line. Run it yourself and compare.
- **D3 — did the diff stay in the bodies?** `git diff -U0 -- dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy` (Verus: `verus/q/q02_first_syntax_i/src/agent.rs`). Every hunk is inside a definition's body (Verus: also the `uninterp` → `open` change on each definition line and the bound lemmas' proofs); no signature, `ensures`, doc comment or check line changed, no declaration added or removed.
- **D4 — is the audit clean?** `scripts/vaudit --compare expected/Q02_AgentImplement.audit dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy` (Verus: `--compare expected/q02_first_syntax_i_agent.audit verus/q/q02_first_syntax_i/src/agent.rs`) reports no difference.
- **D5 — does the delivery meet the prose, not only the checks?** Your adversarial checks (Probe E): inputs the six shipped checks never tried, each with the value the doc comment gives. A failing one is a contract breach the shipped suite missed; quote the doc comment it contradicts.
- **D6 — did a red symbol line mislead the Verus run?** In the Verus transcript, for each `symbol <fn>: failed`, read the error's line: was it the named fn's own check, or the first failing check above it? Note any edit the contractor made in response to a failure that was not its own.
- **D7 — what did the fast channel cost and save?** Fill the `LATENCY LOG` from the transcript's timings: the number of fast-channel runs and their typical wall time, and the gate's wall time.
- **D8 — which moment earns a rule?** Name one transcript moment (a skipped check, a stacked edit, a misread symbol line, an escape hatch tried) that deserves a rule in your Q03 contract v0, and write it in the rule format `CLAUDE.md`'s contract slot shows.
