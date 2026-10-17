# Q05 rubric — Frames, ownership, modes, wp→VC

> **Consumers:** `/grade-paper Q05` and `/grade-paper Q05 --post` (B1–B4), `/review-code Q05` (Gate, Code-review focus), and you, after `/contract Q05` (the audit debrief). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q05 --check` has recorded every Q05 prediction and T1's first try (the test-out is closed book).

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q05_solutions.tex  sha256 857b41b6d40c9e6cca3b414f7151c4e6efbc4be20a1715fd56fd02a62bde9f81 — the written track's reference (B1–B4)
paper/Q05_problems.tex  sha256 09dc97721b1780e3e9febbf62ea5c263b6d89338b2c7ae4183a208310a7f41cc — the problems these lines grade
Solutions/dafny/Q/Q05_Frames/std/Q05_Frames.dfy  sha256 d23fd3a55a8da5b7e2fa4a5632bb016e491279fe362cd7f352634e96ad5755e4 — the formal reference B3's blueprint precedes (H4d), and the Dafny half of the code review
Solutions/verus/q/q05_frames/src/lib.rs  sha256 5d3c6ebcb33a6cc36daeb5a69579929d27ee339aef61828241d70208f2a3ab63 — the formal reference of H4v, which B3 also precedes, and the Verus half of the code review

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. The program text below is the problems file's; the lines marked `<-` are where your own formulas or values go. A verified probe confirms a step (verdict kind 1). An error verdict alone refutes nothing: a flaw is exhibited by an executable check (a `@Test` method with `expect`, run with `scripts/vcheck --test`, one test at a time with `--name`) or by a verified refutation. In the B1 and B2 probes, `L` is the array's length, `s` its contents at the start of the method, and `c`, `c2` contents at later points, as sequences.

- **Probe A** (B1 (a), sufficiency). Write `instructor/scratch/probe.dfy`:

  ```dafny
  predicate LearnerWp(L: nat, s: seq<nat>)
  {
    true   // <- paste your wp(body, R), over L and s (guard each s[k] with |s|, as your formula does)
  }

  method Drain(a: array<nat>, i: nat) returns (x: nat)
    requires i < a.Length
    modifies a
    ensures x == old(a[i]) && a[i] == 0
    ensures forall j | 0 <= j < a.Length && j != i :: a[j] == old(a[j])
  {
    x := a[i];
    a[i] := 0;
  }

  // Your formula is sufficient: from every start state in it, both calls'
  // preconditions hold and the run ends in R.
  method Sufficient(a: array<nat>) returns (t: nat)
    requires LearnerWp(a.Length, a[..])
    modifies a
    ensures t == old(a[0]) + old(a[1]) && a[0] == 0 && a[1] == 0
  {
    var x := Drain(a, 0);
    var y := Drain(a, 1);
    t := x + y;
  }
  ```

  Run `scripts/vcheck instructor/scratch/probe.dfy`. `Sufficient` verifies exactly when your formula implies the weakest precondition. When it does not, Probe A″'s `Included` exhibits the state.
- **Probe A′** (B1 (a), one step). For a rewriting step of the trace, paste the formula before and after it, over the variables it mentions, one direction per lemma:

  ```dafny
  lemma StepDown(L: nat, s: seq<nat>, c: seq<nat>, x: nat)
    requires |s| == L && |c| == L   // s and c: contents of a, whose length is L
    requires true                   // <- your formula at step k
    ensures true                    // <- your formula at step k + 1
  {
  }

  lemma StepUp(L: nat, s: seq<nat>, c: seq<nat>, x: nat)
    requires |s| == L && |c| == L
    requires true                   // <- your formula at step k + 1
    ensures true                    // <- your formula at step k
  {
  }
  ```

  Run `scripts/vcheck instructor/scratch/probe.dfy`. Both lemmas verifying confirm the step as an equivalence. When a step removes a quantifier over a call's outcomes, the direction that starts from the quantified formula needs one outcome named in its body: bind the contents and result that the callee's contract allows from the values at hand (`var c1 := …;`) and `assert` the call's hypotheses at them; the verifier does not build a sequence by itself. A lemma that does not verify refutes nothing: the flaw is exhibited by values at which the two sides differ (RC.c).
- **Probe A″** (B1 (a), runs from chosen start states). In a second `instructor/scratch/probe.dfy`, `LearnerWp` and `Drain` as in Probe A, then:

  ```dafny
  // Drain with its requires checked at run time instead, for the tests below.
  method DrainChecked(a: array<nat>, i: nat) returns (x: nat)
    modifies a
    ensures i < a.Length && x == old(a[i]) && a[i] == 0
    ensures forall j | 0 <= j < a.Length && j != i :: a[j] == old(a[j])
  {
    expect i < a.Length, "Drain's requires fails";
    x := Drain(a, i);
  }

  // A start state inside your formula. The test fails at "Drain's requires
  // fails" or at "the run ends outside R" exactly when the state refutes
  // sufficiency.
  @Test
  method Included()
  {
    var a := new nat[2];         // <- a start state inside your formula: its length
    a[0], a[1] := 0, 0;          // <- and its contents
    expect LearnerWp(a.Length, a[..]), "the state is outside your formula";
    var s := a[..];
    var x := DrainChecked(a, 0);
    var y := DrainChecked(a, 1);
    var t := x + y;
    expect t == s[0] + s[1] && a[0] == 0 && a[1] == 0, "the run ends outside R";
  }

  // A start state outside your formula. The test passes exactly when the state
  // refutes necessity: every precondition holds on the run, and it ends in R.
  @Test
  method Excluded()
  {
    var a := new nat[2];         // <- a start state outside your formula: its length
    a[0], a[1] := 0, 0;          // <- and its contents
    expect !LearnerWp(a.Length, a[..]), "the state is inside your formula";
    var s := a[..];
    var x := DrainChecked(a, 0);
    var y := DrainChecked(a, 1);
    var t := x + y;
    expect t == s[0] + s[1] && a[0] == 0 && a[1] == 0, "the run ends outside R";
  }
  ```

  Run `scripts/vcheck --test --name Included instructor/scratch/probe.dfy`, then the same with `--name Excluded`. The failing `expect`'s message names what happened. Keep `print` out of these tests.
- **Probe A‴** (B1 (b), an outcome of the weakened contract). In `instructor/scratch/probe.dfy`:

  ```dafny
  @Test
  method WeakenedRun()
  {
    var s: seq<nat> := [0, 0];                 // <- your start contents
    var x: nat, c: seq<nat> := 0, [0, 0];      // <- the first call's result, and the contents after it
    var y: nat, c2: seq<nat> := 0, [0, 0];     // <- the second call's result, and the contents after it
    expect true, "the first call's outcome is not allowed";    // <- the weakened contract of Drain(a, 0), over s, x and c
    expect true, "the second call's outcome is not allowed";   // <- the weakened contract of Drain(a, 1), over c, y and c2
    var t := x + y;
    expect !(true), "that conjunct of R holds";   // <- the conjunct of R you say fails, over t, s and c2
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. It passes exactly when the outcome is one the weakened contract allows and the named conjunct fails on it. One run per conjunct you say fails.
- **Probe B** (B2 (a) and (b), one lemma per verification condition). Write each condition as a lemma, hypotheses as `requires`, conclusion as `ensures`, empty body; the call's outcome is the pair `c2`, `x`:

  ```dafny
  lemma Entry(L: nat, c: seq<nat>)
    requires |c| == L
    ensures true      // <- your wp(i := 0, I), over L and c
  {
  }

  lemma Maintenance(L: nat, i: int, c: seq<nat>, c2: seq<nat>, x: nat)
    requires |c| == L && |c2| == L   // c and c2: contents of a, whose length is L
    requires true     // <- I and b, over i and c
    requires true     // <- the call's postcondition: the outcome c2, x of Drain(a, i) from c
    ensures true      // <- I after the body, over i + 1 and c2
  {
  }

  lemma UseAtExit(L: nat, i: int, c: seq<nat>)
    requires |c| == L
    requires true     // <- I and the negated guard
    ensures forall j | 0 <= j < L :: c[j] == 0   // the postcondition
  {
  }

  lemma Termination(L: nat, i: int, c: seq<nat>, c2: seq<nat>, x: nat)
    requires |c| == L && |c2| == L
    requires true     // <- I and b
    requires true     // <- the call's postcondition
    ensures true      // <- your bound, and the measure after the body below the measure before it
  {
  }
  ```

  Run `scripts/vcheck instructor/scratch/probe.dfy`. A lemma that verifies confirms that condition as you wrote it. For (b), write the weakened contract in the call's `requires` lines; Probe B′ exhibits a failing condition.
- **Probe B′** (B2 (b), the exhibited state and call outcome):

  ```dafny
  @Test
  method WeakenedMaintenance()
  {
    var L, i := 0, 0;                          // <- your state: the length and the index
    var c: seq<nat> := [];                     // <- the contents at the start of the iteration
    var x: nat, c2: seq<nat> := 0, [];         // <- the call's result, and the contents after it
    expect |c| == L && |c2| == L, "c and c2 are not contents of a";
    expect true, "the hypotheses fail";        // <- I and b over i and c, and the weakened outcome of Drain(a, i)
    expect !(true), "the conclusion holds";    // <- the conclusion of the condition you say fails, negated
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`; it passes exactly when the state and outcome refute that condition.
- **Probe B″** (B1 (b)–(c) and B2 (b)–(c), the verifier on the programs). Copy the problem's Dafny program (B1: `Drain` and `Collect`; B2: `Drain` and `DrainAll`) into `instructor/scratch/probe.dfy`, or the Verus one (B1: `drain` and `collect`; B2: B1's `drain` and `drain_all`) into `instructor/scratch/probe.rs` inside `use vstd::prelude::*; verus! { … }`, as given and then with the one clause the part deletes, and run `scripts/vcheck instructor/scratch/probe.<ext>`. The verdict and the locations it names are the anchor for "which obligations fail": compare them with the learner's list. A verified run of a claimed failure refutes the claim; a reported failure the learner did not list is a finding only with Probe A‴ or B′ passing on an instance of it.
- **Probe C** (B3, splice template: is the blueprint formalizable as written?). Copy B3's code (`BitCount`, `Ones`, `CountOnes`) into `instructor/scratch/probe.dfy` and replace the comment line in the loop header with the blueprint's invariants and measure, written from the blueprint alone:

  ```dafny
      invariant true      // <- each clause of your invariant, one line each
      decreases 0         // <- your measure, its components in your order
  ```

  Run `scripts/vcheck --module Q05 instructor/scratch/probe.dfy` (the module's unit options). Verified is the operational test of blueprint quality for H4d.
- **Probe C′** (B3, one pass of the body, executable). In a second `instructor/scratch/probe.dfy`, B3's `BitCount` and `Ones` (leave `CountOnes` out: an invariant that fails to verify there would stop the test from compiling), then:

  ```dafny
  @Test
  method OnePass()
  {
    var s: seq<nat> := [];        // <- your sequence
    var i, x, c := 0, 0, 0;       // <- a state
    expect true, "the state is outside your invariant or the guard";   // <- your invariant and the guard, over s, i, x, c
    var i0, x0, c0 := i, x, c;
    if x > 0 { c := c + x % 2; x := x / 2; } else { x := s[i]; i := i + 1; }   // one pass of the body
    expect !(true), "the claim holds after the pass";   // <- the claim you test after the pass (your invariant, or your measure below its value at i0, x0), negated
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy` (the code needs no given layer; `--test` takes a file, not a module probe). It passes exactly when the state satisfies the invariant and the guard and the claim fails after one pass: a confirmed failing instance.
- **Probe C″** (B3, the overflow paragraph for H4v). Below `BitCount`:

  ```dafny
  lemma NoOverflow(c: nat, x: nat, total: nat)
    requires x > 0                       // the branch that adds x % 2
    requires true                        // <- the facts your paragraph uses (add a parameter for each further quantity it names)
    ensures c + x % 2 <= 18446744073709551615
  {
  }
  ```

  Run `scripts/vcheck --module Q05 instructor/scratch/probe.dfy`. It verifies when the paragraph's facts suffice. `total` stands for `ones(v@)`.
- **Probe D** (B4, the card pin). `sed -n '1366,1386p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B4 prints. Run it before grading any field.
- **Probe E** (Code-review focus C1–C5, a dead step). Copy the declaration under review, with the module's imports, into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, delete the one line in question, and run `scripts/vcheck --module Q05 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.

## B1 — The verification condition of two calls (hand-calculation; dimension: recomputation)

### recomputation
- **RC.a** — the trace runs backwards from R, one statement per step, and each step names its rule (assignment, call, sequence). A missing rule name with a correct formula is a gap (3). A score ≤2 exhibits a step whose formula is not its rule applied to the previous formula: Probe A′ on that step fails, and the differing values are shown by an executable check.
- **RC.b** — each call step applies the call rule as chapter §3 writes it: the callee's precondition at the call's arguments, a fresh outcome (the contents after the call and the result) quantified, the postcondition assumed of it, and the formula continued over the outcome. A call step that reads `Drain`'s body instead of its contract is a flaw only when it changes the result; then Probe A‴ (for the weakened contract) or Probe A″ exhibits the state.
- **RC.c** — every simplification after a call says which hypothesis fixes which value and is an equivalence (Probe A′'s two lemmas). A score ≤2 names the step and exhibits values at which its two sides differ, by an executable check: when the step's result is too weak, values and a call outcome that the call rule's hypotheses allow on which the step's conclusion fails (a `@Test` in Probe A‴'s form); when it is too strong, a start state on which Probe A″'s `Excluded` passes.
- **RC.d** — the result of (a) is a formula over L and s alone; Probe A's `Sufficient` verifies with it spliced in, and Probe A″'s `Excluded`, on any state the learner or grader proposes, does not pass. If `Sufficient` verifies and no `Excluded` run passes, (a) is correct: do not invent a flaw, whatever the formula's shape. A formula that still names an intermediate state is a gap (3) unless it is false at an exhibited start state.
- **RC.e** — (b) states the verification condition as the precondition implies the wp, and decides it. A decision against Probe A's verdict on the problem's `Collect` (Probe B″, as given) scores ≤2, the output pasted.
- **RC.f** — (b), the weakened contract: each conjunct the answer says fails comes with an outcome on which Probe A‴ passes; each conjunct it says still holds has no such outcome. A claim that the weakened verification condition still holds scores ≤2 with an outcome on which Probe A‴ passes. The answers to "can a run end that way?" and "what does the failure say?" keep the program and the contract apart, and are checked against Probe B″ (the program with `Drain`'s body is unchanged; its verdict changes with the contract).
- **RC.g** — (c) names what plays the role of the frame in Verus, the obligation the Verus caller has that the Dafny caller has not, and what in the two contracts discharges it; the list of failing obligations agrees with Probe B″'s Verus run with the named clause deleted. A claim against that verdict scores ≤2, the output pasted.

## B2 — Verification conditions of a loop whose body makes the call (hand-calculation; dimension: recomputation)

### recomputation
- **RC.h** — (a) states four conditions as formulas (entry, maintenance, use at exit, termination), with the maintenance conclusion computed through the body, the last statement first and the call by the call rule. A score ≤2 exhibits values of L, i, c and a call outcome at which the learner's maintenance conclusion and the computed one differ.
- **RC.i** — each decision of (a) and (b) is consistent with Probe B. A condition decided valid whose lemma verifies is confirmed. A condition decided valid whose lemma does not verify scores ≤2 only with a state that passes Probe B′ for it. A condition decided to fail scores ≤2 when its lemma verifies (the pasted verified output refutes the claim).
- **RC.j** — (b) exhibits a state and a call outcome for each condition it says fails, and Probe B′ passes on them.
- **RC.k** — (b) answers reachability with an argument about runs, says whether a stronger invariant could repair the loop with an argument about what the weakened contract allows, and names which annotation is too weak, as separate claims. A claim that an invariant repairs it is checked by Probe B with that invariant; a claim that none can is checked against an outcome of the weakened contract (Probe B′) that breaks every candidate the grader proposes.
- **RC.l** — (c) lists the conditions that fail in agreement with Probe B″'s Verus run with the named clause deleted, and says why the Dafny contract needs no such clause. A list against that verdict scores ≤2, the output pasted.

## B3 — A blueprint for H4d and H4v (informal-proof-first)

### statement-fidelity
- **SF.a** — the statement proved is the method's: the loop ends with the count equal to `Ones(s)` for every `s` (and, for H4v, under its `requires`), with no hypothesis added or dropped. A score ≤2 quotes the restated claim and exhibits an input on which it and the method's `ensures` disagree.

### induction-soundness
- **IS.a** — the invariant is written as a formula with its quantities explicit, and the measure as an ordered tuple (or a single quantity). An invariant in words only is a gap (3).
- **IS.b** — each branch's maintenance argument uses only the invariant, the guard and the branch condition, and concludes the invariant at the updated values. A score ≤2 exhibits a state satisfying the stated invariant and the guard on which one pass breaks it: Probe C′ passes on it.
- **IS.c** — the measure goes down in each branch, in the stated order, and is bounded below. A score ≤2 exhibits a state on which one pass does not lower the stated measure in its stated order: Probe C′, with the decrease as its claim, passes on it.

### case-exhaustiveness
- **CE.a** — the blueprint covers entry, both branches of the body, the exit (where the negated guard is used) and termination for each branch. A missing case whose argument is true is a gap (3); a score ≤2 exhibits a state in a case the blueprint covers whose stated argument fails on it.

### blueprint-quality
- **BQ.a** — every helper fact is named by its statement: an unfolding of a definition, the assertion the code gives, or a new lemma with its full `requires` and `ensures`. The operational test is Probe C filled from the blueprint alone, with nothing invented: if it verifies, do not invent a flaw. A failing Probe C is a gap (3) unless Probe C′ exhibits an instance.
- **BQ.b** — the H4v paragraph names the facts that bound `c + x % 2`, and Probe C″ verifies with them. A paragraph whose facts do not suffice is a gap (3); a score ≤2 needs values at which its stated facts hold and the bound fails, evaluated in a `@Test` method.

### gap-accounting
- **GA.a** — declared gaps score 3. An undeclared step that is false at an exhibited input is a flaw (≤2). An undeclared step that is true but unjustified is recorded as a gap (3), never as a flaw.

## The --post pass

Runs once `scripts/vcheck --gate dafny/Q/Q05_Frames/std` exits 0 (H4d is in that unit), and again for the Verus half once `scripts/vcheck --gate verus/q/q05_frames` exits 0 (H4v). Re-score `blueprint-quality` of B3 only, with your verified `CountOnes` and `count_ones` as the oracle:
- **BQ.c** — diff the blueprint against the proofs: the invariant clauses it stated against those the loops carry; the measure against the `decreases` lines; the helper facts it named against the assertions and proof blocks the proofs needed. Record each clause or fact a proof needed that the blueprint did not name (in Verus, any clause a loop needs because it sees only its invariants), and each named one no proof used.
- **BQ.d** — record whether formalizing forced a change the paper missed (another clause, another order, an extra fact). A blueprint whose invariant and measure survived formalization scores 4; each missed clause or fact is a finding at 3, never lower unless the blueprint's step was false at an exhibited input.

The gradebook gets a `paper-post` row with the new `blueprint-quality` score.

## B4 — Paper card 03.12 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe D prints the hash B4 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact). An empty field scores 1 for that field.
- **CF.c** — each field agrees with the pinned range. A field scores ≤2 only by quoting the pinned line it contradicts, with its line number.
- **CF.d** — a field for which the range is silent is correct when it says so (and what would be needed); silence in the range is never a contradiction.
- **CF.e** — a figure stays attached to the benchmark, model, time limit and baseline that the range gives it; a figure moved to another (a baseline's time limit read as the method's, a range read as a single run) is a contradiction, quoted as in CF.c.
- **CF.f** — wording is free: a field in the learner's own words that agrees with the range scores 4. The card's grade is the minimum over its fields.

## Gate

The mechanical preconditions of `/review-code Q05`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck --module Q05` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q05_Frames/std`, `scripts/vcheck --gate verus/q/q05_frames` and `scripts/vcheck --gate dafny/checks/Q05_checks.dfy` each exit 0 and print only the summary line. After both contract runs, `scripts/vcheck --gate dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` and `scripts/vcheck --gate verus/q/q05_frames/src/agent.rs` do too.
- **A3 — audit, pinned.** `scripts/vaudit dafny/Q/Q05_Frames/std`, `scripts/vaudit verus/q/q05_frames` and `scripts/vaudit dafny/checks/Q05_checks.dfy` report no finding; `scripts/vaudit --compare expected/Q05_AgentInfra.audit dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` and `scripts/vaudit --compare expected/q05_frames_agent.audit verus/q/q05_frames/src/agent.rs` report no difference.
- **A4 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q05 --report --strict` exits 0 (every prediction filled, recorded and enabled; the test-out blocks written and their checks uncommented; every shipped "Uncomment as you go" check uncommented; and, after the exit's scored run, the exit files repaired).
- **A5 — statements unchanged.** `scripts/specfreeze --check Q05` reports no finding. It accepts added `modifies` and `ensures` clauses in `Pop`'s header and nowhere else.
- **A6 — diagnosis fixtures stay out.** The card demos under `specimens/Q05/card-*` are red by design (their failures are pinned) and are never finished or reviewed; the obligation specimens `specimens/Q05/P4d.dfy.specimen`, `P5v.rs.specimen` and `P6d.dfy.specimen` are predictions, covered by A4 alone. A2 and A3 skip all of them. The agent files are the contractor's work and the debrief's, not the code review's. No brittleness gate applies at this bar.

## Code-review focus — band: "proof-shape"

Q05's bar: invariants say what the loop has established; the `decreases` follows the recursion or the loop; frames say what the code writes and what a caller needs; `assert … by` and lemma calls scope their facts; no dead scaffolding. You wrote annotations into given code (H1d–H4d), code under given annotations (H5d) and whole exec bodies (H1v, H2v, H4v, H5v): only your own lines are reviewed.

- **C1 — invariants say what the loop has established (H1d, H3d, H4d, H4v, H5v).** Each invariant clause states a fact about the part of the data the loop has processed, or a bound the next pass needs, in the loop's own variables. A clause Probe E shows dead is a finding at this bar; a clause that restates what the guard or a type already gives is a reading note, not a finding. If every clause is needed, do not invent a flaw.
- **C2 — measures follow the loop or the recursion (T1d, T1v, H4d, H4v).** Each `decreases` names the quantities that go down, in the order in which the passes lower them; the verifier checks that it does. A component Probe E shows removable is a finding; a measure the verifier accepts with every component needed is correct: do not invent a flaw.
- **C3 — frames say what the code writes (H1d, H2d).** The frame clauses you wrote name what the body writes, and the frame postcondition says what a caller needs (the shipped client checks are the anchor: they verify). A wider frame that the client checks still accept is a reading note, never a finding at this bar; a narrower one cannot pass them. If the checks verify and A5 passes, do not invent a flaw.
- **C4 — facts scoped where they are used (H3d, H4v, H5d, H5v, H1v).** Each assertion, lemma call or `proof` block sits next to the step that needs it, and is needed (Probe E). One Probe E shows dead is a finding; one that is needed but placed far from its use is a reading note.
- **C5 — the method clauses no instrument sees.** H4v is one loop with no nested loop and an explicit lexicographic `decreases`; H5v is one loop using `?` on the given `digit` and `mul10_add`; H5d takes each digit with `:-` as its prompt says. Read the bodies, and cite `file:line` for a clause that is not met. If every clause is met, do not invent a flaw.
- **C6 — intent stays in the shipped contracts.** Q05's statements ship frozen; A5 is the anchor. A changed `requires`, `ensures`, `reads` or check line is a finding at grade 1, whatever the verifier says; added `modifies` and `ensures` clauses in `Pop`'s header are the hole itself, not a change.
- **C7 — no dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.

## Audit debrief — after /contract Q05

Questions for you, after each contract run (one agent file per run). Each is settled by the transcript (`claude --resume` on that session), the artifact or a command, and none has a secret answer.
- **D1 — were the receipts verbatim?** Put the agent file back as it was when you filled its `RECEIPTS` block (commit the block before the run; then `git stash push -- <agent file>` restores that commit's file and `git stash pop` brings the delivery back), re-run the two commands the `RECEIPTS` block names, and compare: every command, exit code and diagnostic or finding line matches the block character for character, scratch paths aside (they change on every run), and the layer chain matches `MODULES.toml`. A rephrased or missing line is a finding against the receipts, not against the contractor; a receipt line the contractor changed is a finding against the run (D4).
- **D2 — does each DIAGNOSIS line rest on a receipt?** For each line, find the receipt line it cites and check that it says what the diagnosis claims: the instrument, the location, the message. A cause with no receipt line behind it is a guess, even when the repair worked.
- **D3 — was the DIAGNOSIS written before any other edit?** In the transcript, the first edit of the agent file fills the `DIAGNOSIS` block; no other line changed before it.
- **D4 — did the diff stay outside every declaration?** `git diff -U0 -- dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` (Verus: `verus/q/q05_frames/src/agent.rs`). Every changed line lies outside every lemma, function, method, predicate or fn (its signature, contract and body) or in the `DIAGNOSIS` block; no declaration was added or removed, and no `RECEIPTS` line changed.
- **D5 — were both instruments re-run after every edit?** Count the edits in the transcript and the `scripts/vcheck --json` and `scripts/vaudit` runs between them: both after each edit, never two edits between runs.
- **D6 — did it stop at a green gate?** Find the last `scripts/vaudit --compare` of the transcript, then run it yourself, with A2's gate line for the file. A delivery reported when the gate was green and the audit was not is a breach of the acceptance, whatever the final state.
- **D7 — did it reach for a wiring file?** Search the transcript for an attempted edit of a `dfyconfig.toml`, a `Cargo.toml`, `MODULES.toml` or anything under `scripts/`, and for the guard's refusal; and for a proposal to change one "instead". Record each attempt and what the contractor did next.
- **D8 — who decided, the proposer or the checker?** Card 03.12's boundary, applied to the run: for each `DIAGNOSIS` line, which instrument's output confirmed it after the repair, and which line, if any, only the contractor's reading supports. Name one moment that earns a rule in your contract, and write it in the rule format `CLAUDE.md`'s contract slot shows.
