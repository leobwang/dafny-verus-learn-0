# Q03 rubric — First syntax II: modes, logic, tooling, trust

> **Consumers:** `/grade-paper Q03` and `/grade-paper Q03 --post` (B1–B4), `/review-code Q03` (Gate, Code-review focus), and you, after you write contract v0 (the contract v0 review). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q03 --check` has recorded every Q03 prediction.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q03_solutions.tex  sha256 855e6cdc0d1129361eba0c8348d449951482f8d3d8a59d2f3f260ea98e0cd241 — the written track's reference (B1–B4)
paper/Q03_problems.tex  sha256 bde709566ac7c1149118ce0cbcd5e8d1de85adad91c4e4af66621aca2ee08dec — the problems these lines grade
Solutions/dafny/Q/Q03_FirstSyntaxII/core/Q03_FirstSyntaxII.dfy  sha256 b6fe44b2009942a6162df73e4da7404233ca872ae9b38b5345acfa66666a5a63 — the formal reference B3's blueprint precedes, and the Dafny half of the code review
Solutions/verus/q/q03_first_syntax_ii/src/lib.rs  sha256 c1f841e927f1ce1d9dc5e0e5d38d2fbf9c47aeaad4ba0da0a147ae2f794843cf — the Verus half of the code review

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. The program text below is the problems file's; the lines marked `<-` are where your own formulas go. A verified probe confirms a step (verdict kind 1). An error verdict alone refutes nothing: a flaw is exhibited by an executable check (a `@Test` method with `expect`, run with `scripts/vcheck --test`) or by a verified refutation.

- **Probe A** (B1, the wp). Write `instructor/scratch/probe.dfy`:

  ```dafny
  predicate Post(x: int, y: int) { x >= 4 }

  predicate LearnerWp(x: int, y: int)
  {
    true   // <- paste your wp(c, Q), over the start state
  }

  // Your formula is sufficient: every start state in it ends in Post.
  method Sufficient(x0: int, y0: int) returns (x: int, y: int)
    requires LearnerWp(x0, y0)
    ensures Post(x, y)
  {
    x, y := x0, y0;
    y := x + 3;
    if y > 10 { y := y - 10; } else { y := 2 * y; }
    x := y - 1;
  }

  // Your formula is necessary: every start state outside it ends outside Post.
  method Necessary(x0: int, y0: int) returns (x: int, y: int)
    requires !LearnerWp(x0, y0)
    ensures !Post(x, y)
  {
    x, y := x0, y0;
    y := x + 3;
    if y > 10 { y := y - 10; } else { y := 2 * y; }
    x := y - 1;
  }

  method Run(x0: int, y0: int) returns (x: int, y: int)
  {
    x, y := x0, y0;
    y := x + 3;
    if y > 10 { y := y - 10; } else { y := 2 * y; }
    x := y - 1;
  }

  // The executable check: your formula against the compiled program on a grid.
  @Test
  method WpAgreesOnGrid()
  {
    var x := -40;
    while x <= 40
      decreases 40 - x
    {
      var y := -2;
      while y <= 2
        decreases 2 - y
      {
        var x1, y1 := Run(x, y);
        expect LearnerWp(x, y) == Post(x1, y1), (x, y);   // a failure names the start state
        y := y + 1;
      }
      x := x + 1;
    }
  }
  ```

  Run `scripts/vcheck instructor/scratch/probe.dfy` (both triples verify exactly when the formula is the weakest precondition: it is sufficient, and the program is deterministic and total), then `scripts/vcheck --test instructor/scratch/probe.dfy`. A failed grid test names the first start state on which your formula and the program disagree, as the message of its error line: `error: (<x>, <y>)`. Keep `print` out of these tests: `vcheck --test` reads each test's verdict from its own output line.
- **Probe A′** (B1, one step). For a rewriting step of the trace, paste the formula before and after it:

  ```dafny
  lemma Step(x: int, y: int)
    ensures (true) <==> (true)   // <- (your formula at step k) <==> (your formula at step k + 1)
  {
  }
  ```

  It verifies when the step is an equivalence over the integers. When it does not, the flaw is exhibited by the integer values at which the two sides differ, evaluated in a `@Test` method.
- **Probe A″** (B1 (b), a counterexample state). In Probe A's file:

  ```dafny
  @Test
  method Counterexample()
  {
    var x0, y0 := 0, 0;            // <- your start state
    expect 0 <= x0 && x0 <= 8;     // it meets the precondition P of part (b)
    var x, y := Run(x0, y0);
    expect !Post(x, y);            // and the run ends outside Q
  }
  ```

  It passes exactly when the state is a counterexample to the verification condition.
- **Probe B** (B2 (a) and (b), one lemma per verification condition). Write each condition as a lemma, hypotheses as `requires`, conclusion as `ensures`, empty body:

  ```dafny
  lemma Entry(n: int)
    requires n >= 0                    // the method's requires
    ensures true                       // <- your wp(initialisation, invariant)
  {
  }

  lemma Maintenance(n: int, x: int, y: int)
    requires true                      // <- the invariant and the guard
    ensures true                       // <- your wp(body, invariant)
  {
  }

  lemma UseAtExit(n: int, x: int, y: int)
    requires true                      // <- the invariant and the negated guard
    ensures y == 0                     // the postcondition
  {
  }

  lemma Termination(n: int, x: int, y: int)
    requires true                      // <- the invariant and the guard
    ensures true                       // <- your bound and your decrease
  {
  }
  ```

  Run `scripts/vcheck instructor/scratch/probe.dfy`. A lemma that verifies confirms that condition as you wrote it; Probe B′ exhibits a failing one.
- **Probe B′** (B2 (b), the exhibited state):

  ```dafny
  @Test
  method WeakenedCounterexample()
  {
    var n, x, y := 0, 0, 0;            // <- your state
    expect true;                       // <- the hypotheses of the condition you say fails
    expect !(true);                    // <- its conclusion, negated
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`; it passes exactly when the state refutes that condition.
- **Probe B″** (B2 (c)). Copy the problem's Dafny `Countdown` into `instructor/scratch/probe.dfy` with the two changes part (c) names (the type of `y`, the invariant `x + y == n` alone) and run `scripts/vcheck --gate instructor/scratch/probe.dfy`; or copy the Verus `countdown` into `instructor/scratch/probe.rs` with the invariant line `x <= n,` deleted and run `scripts/vcheck --gate instructor/scratch/probe.rs`. The verdict is the answer key to "does the loop verify now?".
- **Probe C** (B3, splice template: is the blueprint formalizable as written?). In `instructor/scratch/probe.dfy`, one lemma per case of your blueprint, filled from the blueprint alone:

  ```dafny
  module ProbeC {
    import opened QG_L1_BigNat
    import opened QG_L2_BigNat

    lemma CaseK(s: seq<nat>, d: nat)          // one per case: Case1, Case2, ...
      requires Valid(s) && d < BASE
      requires true                           // <- your case condition
      requires true                           // <- your IH, at the instance this case uses (omit if none)
      ensures ToNat(AddLimb(s, d)) == ToNat(s) + d
    {
                                              // <- your helper facts, in your order, as lemma calls or asserts
    }

    lemma CaseKInstance(s: seq<nat>, d: nat)  // one per case that uses the IH
      requires Valid(s) && d < BASE
      requires true                           // <- the same case condition
      ensures true                            // <- your instance is smaller, and the lemma's requires hold there
    {
                                              // <- your helper facts
    }

    lemma Exhaustive(s: seq<nat>, d: nat)
      ensures true                            // <- your case conditions, joined by ||
    {
    }
  }
  ```

  Run `scripts/vcheck --module Q03 instructor/scratch/probe.dfy` (the module's given layers and unit options, so no induction happens for you). Every lemma verifying is the operational test of blueprint quality.
- **Probe D** (B4, the card pin). `sed -n '944,967p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B4 prints. Run it before grading any field.
- **Probe E** (Code-review focus C4–C6, a dead step). Copy the declaration under review, with the module's imports, into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, delete the one line in question, and run `scripts/vcheck --module Q03 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.

## B1 — The weakest precondition of loop-free code (hand-calculation; dimension: recomputation)

### recomputation
- **RC.a** — the trace runs backwards from Q, one statement per step, and each step names its rule (assignment, sequence, conditional). A missing rule name with a correct formula is a gap (3). A score ≤2 exhibits a step whose formula is not its rule applied to the previous formula: Probe A′ on that step fails, and the differing values are shown by an executable check.
- **RC.b** — the conditional step keeps a constraint for each branch (two implications, or an equivalent case split). A score ≤2 exhibits a start state that satisfies the learner's formula and ends outside Q, by Probe A's grid test or Probe A″.
- **RC.c** — every simplification is an equivalence over the integers, with its justification. A score ≤2 names the step and the integer at which its two sides differ (Probe A′ fails there, and the evaluation shows it).
- **RC.d** — the final formula of (a) mentions only the start value of x, and both triples of Probe A verify with it spliced in. If both verify and the grid test passes, (a) is correct: do not invent a flaw, whatever the formula's shape.
- **RC.e** — (b) states the verification condition as P ⟹ wp and decides it. A claim that it fails comes with a start state and its trace, and Probe A″ passes on that state. A claim that it holds scores ≤2 only with a start state in P that Probe A″ shows ending outside Q.
- **RC.f** — (c) agrees with the learner's own (a). A score ≤2 exhibits, by Probe A's `Run`, a start value that contradicts the claim (a value between two members of the set that is not in it, or a value in a claimed gap that is).

## B2 — Verification conditions of a loop (hand-calculation; dimension: recomputation)

### recomputation
- **RC.g** — (a) states four conditions as formulas (entry, maintenance, use at exit, termination), with the maintenance conclusion computed by substitution through the body, the last assignment first. A score ≤2 exhibits values of n, x, y at which the learner's maintenance conclusion and the substituted invariant differ.
- **RC.h** — each decision of (a) and (b) is consistent with Probe B. A condition decided valid whose lemma verifies is confirmed. A condition decided valid whose lemma does not verify scores ≤2 only with a state that passes Probe B′ for it. A condition decided to fail scores ≤2 when its lemma verifies (the pasted verified output refutes the claim).
- **RC.i** — (b) exhibits a state for each condition it says fails, and Probe B′ passes on it.
- **RC.j** — (b) answers whether a run reaches the exhibited state with an argument about runs, and says what the failure means for the program and for the weakened invariant as separate claims. A claim about the program is checked against the problem's own method with the original invariant (Probe B″'s recipe, unmodified, verifies or not); a claim about the invariant against Probe B.
- **RC.k** — (c) decides "verifies now?" in agreement with Probe B″'s verdict, and names a fact that the changed type supplies to the condition that failed in (b). A decision against a verified Probe B″ scores ≤2, the output pasted.

## B3 — A blueprint for H1d (informal-proof-first)

### statement-fidelity
- **SF.a** — the statement proved is the lemma's: the same hypotheses on `s` and `d`, the same equation, no hypothesis added or dropped. A score ≤2 quotes the restated claim and exhibits an input on which it and the lemma disagree.

### induction-soundness
- **IS.a** — the induction is named (on what, with which order), and the induction hypothesis is written as a formula with its quantifiers explicit. An IH in words only is a gap (3).
- **IS.b** — every use of the IH is at an instance the stated IH provides: a smaller sequence, and every other argument one the IH quantifies over. A score ≤2 names the use, the instance it needs and the instances the stated IH covers, and exhibits concrete `s` and `d` at which the needed instance is not covered, evaluated in a `@Test` method over the quoted definitions.
- **IS.c** — the lemma's `requires` are established at each instance where the IH is used (Probe C's instance lemma verifies). A requirement that holds but is not argued is a gap (3); one that fails at an exhibited input is a flaw.

### case-exhaustiveness
- **CE.a** — the cases cover every input (Probe C's `Exhaustive` verifies), each case states its condition, and each case's argument applies to every input in it. A score ≤2 exhibits `s` and `d` that fall in no case, or in a case whose argument fails on them, with `AddLimb` evaluated in a `@Test` method.

### blueprint-quality
- **BQ.a** — every helper fact is named by its statement: a lemma of L2 by its name and statement, or a new lemma with its full `requires` and `ensures`. The operational test is Probe C filled from the blueprint alone, with nothing invented: if every lemma verifies, do not invent a flaw. A case lemma that does not verify is a gap (3) unless an exhibited input makes the claimed step false.
- **BQ.b** — within each case, facts come before the step that uses them, in an order a formalizer can follow.

### gap-accounting
- **GA.a** — declared gaps score 3. An undeclared step that is false at an exhibited input is a flaw (≤2). An undeclared step that is true but unjustified is recorded as a gap (3), never as a flaw.

## The --post pass

Runs once `scripts/vcheck --gate dafny/Q/Q03_FirstSyntaxII/core` exits 0 (H1d is in that unit). Re-score `blueprint-quality` of B3 only, with your verified `AddLimbToNat` as the oracle:
- **BQ.c** — diff the blueprint against the proof: the helpers it named against the calls and asserts the proof makes; the IH instance against the recursive call's arguments; the case order against the branches. Record each helper the proof needed that the blueprint did not name, and each named helper the proof never used.
- **BQ.d** — record whether formalizing forced a change the paper missed (a different instance, an extra fact, a reordered case). A blueprint whose decomposition survived formalization scores 4; each missed helper is a finding at 3, never lower unless the blueprint's step was false at an exhibited input.

The gradebook gets a `paper-post` row with the new `blueprint-quality` score.

## B4 — Paper card 02.13 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe D prints the hash B4 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact). An empty field scores 1 for that field.
- **CF.c** — each field agrees with the pinned range. A field scores ≤2 only by quoting the pinned line it contradicts, with its line number.
- **CF.d** — a field for which the range is silent is correct when it says so (and what would be needed); silence in the range is never a contradiction.
- **CF.e** — wording is free: a field in the learner's own words that agrees with the range scores 4. The card's grade is the minimum over its fields.

## Gate

The mechanical preconditions of `/review-code Q03`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck --module Q03` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q03_FirstSyntaxII/core`, `scripts/vcheck --gate verus/q/q03_first_syntax_ii` and `scripts/vcheck --gate dafny/checks/Q03_checks.dfy` each exit 0 and print only the summary line.
- **A3 — audit, pinned.** `scripts/vaudit dafny/Q/Q03_FirstSyntaxII/core`, `scripts/vaudit verus/q/q03_first_syntax_ii` and `scripts/vaudit dafny/checks/Q03_checks.dfy` report no finding.
- **A4 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q03 --report --strict` exits 0.
- **A5 — statements unchanged.** `scripts/specfreeze --check Q03` reports no finding.
- **A6 — diagnosis fixtures stay out.** `specimens/Q03/P11d.dfy.specimen`, `specimens/Q03/P12d.dfy.specimen`, `specimens/Q03/P13v.rs.specimen` and `specimens/Q03/P14v.rs.specimen` are fake-green deliveries you diagnose (P11–P14), never finish: A2 and A3 skip them, and nothing in them is a code-review finding. The card demos under `specimens/Q03/card-*` are red by design and are not reviewed either. No brittleness gate applies at this bar.

## Code-review focus — band: "it-reads"

- **C1 — names say what things are.** Any name you introduced (a loop index, a ghost variable, a helper) says what it holds. If you introduced none beyond the shipped ones, there is nothing to review here: do not invent a flaw.
- **C2 — ghost and executable code separated on purpose.** The witness index of T1d and T1v is ghost, as their method clause asks; no exec variable exists only to be read by specifications or proofs; a ghost value reaches exec code only where the language allows it. The verifier enforces the mode rules, so a finding here is about intent, cited at `file:line`. If no exec variable is read only by ghost code, do not invent a flaw.
- **C3 — intent stays in the shipped contracts.** Q03's statements ship frozen; A5 is the anchor. A changed `requires` or `ensures` is a finding at grade 1, whatever the verifier says.
- **C4 — exec checks test the fact the result needs (H4d, H4v).** The runtime test in exec code uses exec values only and is what makes the returned value fit its type; an extra test or an `assert` that Probe E shows dead is a finding. If Probe E shows every line needed, do not invent a flaw.
- **C5 — induction proofs follow the recursion (H1d, H2d).** Each recursive call is on an argument the shipped `decreases` covers (the verifier checks this), and each helper call or `assert` is used: Probe E shows it needed. A call Probe E shows dead is a finding at this bar; without that evidence, do not invent a flaw.
- **C6 — witnesses named once (H3d, H3v).** The witness appears where the solver needs it; extra assertions are findings only with Probe E's evidence.
- **C7 — no dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.

## Contract v0 review — after you write Q-v0

No Claude session reviews, drafts or edits contract v0: `/contract Q03` refuses, and no tool or skill grades `CLAUDE.md` (chapter §11). These questions are for you, at the end of the module; each is settled by the artifact (the `### Q-v0 — Q03` section of `CLAUDE.md`), your transcripts or a command, and none has a secret answer.
- **D1 — is the slot format kept?** Read the section against the slot comment above it in `CLAUDE.md`: the dated heading, three to six numbered rules of the form `<rule> — earned by: <source run> — <one-line transcript moment>`, and one `Done means (re-checkable by a third party):` line.
- **D2 — can every cited moment be found again?** Open each cited transcript (`claude --resume`), your Q01 tally or the `LATENCY LOG` block of Q02's agent file, and find the moment. A rule whose moment you cannot find is a guess: move it to your v1 notes.
- **D3 — does each rule carry its class, and does each verifier-class rule name its command?** For every rule marked as checked by the verifier, run its command on your finished Q03 files now and compare the output with what the rule says it must show.
- **D4 — can a stranger re-run the done clause?** Every command in it is a course tool or a `git` command, run from a fresh checkout, and each names the output it must show. Run each one.
- **D5 — does v0 only add to the fallback rules?** Compare each rule with the four fallback bullets in `CLAUDE.md` §Contractor contract. A rule that permits what a fallback forbids is void, because the stricter rule wins.
- **D6 — does any rule open a door the guard keeps shut?** Check v0 against the access matrix in `CLAUDE.md`: no rule may let a contractor edit a statement, a check, a slot, a frozen file or solo work, or widen an allowlist beyond the module's `agentic` list.
- **D7 — which rule do you expect to fire first?** Write it down now. After Q04's contract run, the first live test of v0, check the transcript to see whether it did.
