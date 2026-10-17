# Q08 rubric — Internals II: refinement, permissions, verified wp

> **Consumers:** `/grade-paper Q08` (B1–B3), `/review-code Q08` (Gate, Code-review focus), and you, after `/contract Q08` (the audit debrief of the spec-to-proof flagship). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q08 --check` has recorded every Q08 prediction and the first tries of T1d and T1v (the test-out is closed book).

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q08_solutions.tex  sha256 d3fc91f71f48bc02c0a72bc69f9f12793ad786a3bd0bdd5ef16957e008c5a524 — the written track's reference (B1–B3)
paper/Q08_problems.tex  sha256 7c0a5b4a6dc932ab14ad21560bf1b85f958356ac86dc614c651171f03ef5cb09 — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q08_InternalsII/std/Q08_InternalsII.dfy  sha256 be7b242643151cb956190b3f7434078805adfc9b6d4304f83390cd70610f6b0b — the Dafny half of the code review: T1d
Solutions/dafny/Q/Q08_InternalsII/std/Q08_Canon.dfy  sha256 3e65368b6325c9db0fcc943eb3a57383942f1bc1e2013a88d173ebb3d97a734f — the Dafny half of the code review: the refinements (H1d, H2d, H7d)
Solutions/dafny/Q/Q08_InternalsII/std/Q08_Wp.dfy  sha256 2d8e4873a1ca6fe179cc70575407fb74cfa53fafd7c8686e6a2a4896045c5bea — the verified wp (H8d–H10d), which B1 and B2 precede
Solutions/verus/q/q08_internals_ii/src/lib.rs  sha256 255271f0a917d7033fb24580f239e13b6593529935a7538ea1c88a81fdf9b321 — the Verus half of the code review: the trait specifications (T1v, H3v, H4v)
Solutions/verus/q/q08_internals_ii/src/perm.rs  sha256 4d16aa4cac2295c2f798598e4b599b9632ee633653f3d5d74a337b8a4cee0979 — the Verus half of the code review: the permissions (H5v, H6v)
Solutions/dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy  sha256 e44920c6c567e45561bdd26f5263676f69318aeebbe5c03a3951f9043adb3e9e — the reference statements and delivery behind the audit debrief, Dafny
Solutions/verus/q/q08_internals_ii/src/agent.rs  sha256 71ced2050264f6310426c543a15fe047f678f04ba6cce64b402d3f3f7bcda90b — the reference statements and delivery behind the audit debrief, Verus

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. The program text below is the problems file's; the lines marked `<-` are where the answer's own terms, formulas, states or values go. A verified probe confirms a step (verdict kind 1). An error verdict alone refutes nothing: a flaw is exhibited by an executable check (a `@Test` method with `expect`, run with `scripts/vcheck --test`, one test at a time with `--name`) or by a verified refutation. Keep `print` out of the tests.

**B1's probe file.** Probes A, A′, B, B′ and C share one file, `instructor/scratch/probe.dfy`. Its head is W2d's given code, copied unchanged from `dafny/Q/Q08_InternalsII/std/Q08_Wp.dfy`, from the line `datatype Expr` through the end of `function Wp` (given code: the language, `Eval`, `Holds`, `Update` with `UpdateApply`, `Exec`, `SubstE`, `SubstB`, `Wp`), inside a module of the probe's own, followed by the problem's program:

```dafny
module ProbeB1 {
  // <- paste W2d's given code here, `datatype Expr` through `function Wp`, unchanged

  // B1's program and postcondition, from the problems file.
  function C(): Cmd
  {
    Seq(If(Le(Var(0), Var(1)), Assign(2, Var(1)), Assign(2, Var(0))),
        Assign(0, Minus(Var(2), Var(0))))
  }

  function Q(): BExp
  {
    Le(Var(0), Var(1))
  }

  // A start state: variable 0 = x, 1 = y, 2 = m.
  function Start(x: int, y: int, m: int): State
  {
    (v: nat) => if v == 0 then x else if v == 1 then y else m
  }

  // <- the probes below go here
}
```

- **Probe A** (B1 (a), the final term). Inside the module:

  ```dafny
  function LearnerTerm(): BExp
  {
    Le(Const(0), Const(0))   // <- the final term of (a), exactly as the answer writes it
  }

  lemma TermIs()
    ensures Wp(C(), Q()) == LearnerTerm()
  {
  }
  ```

  Run `scripts/vcheck --module Q08 instructor/scratch/probe.dfy`. `TermIs` verifies exactly when the answer's term is the one `Wp` builds. When it does not, Probe A′ locates the step.
- **Probe A′** (B1 (a), each step, executable). Inside the module, one `expect` per step of the answer, in the answer's order: the left side is the call the step computes (`Wp(…)`, `SubstB(…)` or `SubstE(…)` on the arguments the answer names), the right side the answer's term for it:

  ```dafny
  @Test
  method Steps()
  {
    expect Wp(Assign(0, Minus(Var(2), Var(0))), Q()) == Le(Const(0), Const(0)), "step 1 differs from Wp";   // <- one line per step: the step's call, then the answer's term
    expect Wp(C(), Q()) == LearnerTerm(), "the final term differs from Wp";
  }
  ```

  Run `scripts/vcheck --test --name ProbeB1.Steps instructor/scratch/probe.dfy`. The test stops at the first step that differs, and its message names the step: that is where an error entered, and a later step built on it is not a second flaw. The test file must verify first (a test file that does not verify is not run): with a wrong final term, delete `TermIs` before the run.
- **Probe B** (B1 (b), the meaning). Inside the module:

  ```dafny
  predicate LearnerB(s: State)
  {
    true   // <- the simplified formula of (b), over s(0), s(1) and s(2)
  }

  lemma MeaningIs(s: State)
    ensures Holds(Wp(C(), Q()), s) <==> LearnerB(s)
  {
  }
  ```

  Run `scripts/vcheck --module Q08 instructor/scratch/probe.dfy`. `MeaningIs` verifies exactly when the formula is equivalent to the wp. For an intermediate line of the simplification, paste it into `LearnerB` the same way: each line that verifies is a correct step.
- **Probe B′** (B1 (b), a state where the formula and the wp differ, executable). Inside the module, with `MeaningIs` deleted (it does not verify on a wrong formula, and the test file must):

  ```dafny
  @Test
  method Disagree()
  {
    var s := Start(0, 0, 0);   // <- a state where the formula and the wp differ
    expect Holds(Wp(C(), Q()), s) != LearnerB(s), "the formula and the wp agree at this state";
    expect Holds(Q(), Exec(C(), s)) == Holds(Wp(C(), Q()), s), "the run disagrees with the wp";
  }
  ```

  Run `scripts/vcheck --test --name ProbeB1.Disagree instructor/scratch/probe.dfy`. It passes exactly when the formula and the wp differ at the state; the second line shows, by running `C()`, which of the two the run agrees with (the program is deterministic and has no loop, so its run settles it). For "the formula does not mention a start value that matters" claims, run it on two states that differ only in that value.
- **Probe C** (B1 (c), the swapped sequence rule). Inside the module, the rule exactly as part (c) describes it, and the answer's meaning and state:

  ```dafny
  // Wp with the Seq case reading Wp(c2, Wp(c1, q)), as part (c) supposes.
  function WpSwapped(c: Cmd, q: BExp): BExp
  {
    match c
    case Assign(x, e) => SubstB(q, x, e)
    case Seq(c1, c2) => WpSwapped(c2, WpSwapped(c1, q))
    case If(b, c1, c2) => And(Imp(b, WpSwapped(c1, q)), Imp(Not(b), WpSwapped(c2, q)))
  }

  predicate LearnerC(s: State)
  {
    true   // <- the meaning that (c) computes, over s(0), s(1) and s(2)
  }

  lemma SwappedMeaningIs(s: State)
    ensures Holds(WpSwapped(C(), Q()), s) <==> LearnerC(s)
  {
  }

  @Test
  method SwappedCounterexample()
  {
    var s := Start(0, 0, 0);   // <- the start state of (c)
    expect Holds(WpSwapped(C(), Q()), s), "the state is outside the swapped rule's result";
    expect !Holds(Q(), Exec(C(), s)), "the run from this state ends in q";
  }
  ```

  Run `scripts/vcheck --module Q08 instructor/scratch/probe.dfy` (`SwappedMeaningIs` verifies exactly when (c)'s meaning is right), then `scripts/vcheck --test --name ProbeB1.SwappedCounterexample instructor/scratch/probe.dfy` (it passes exactly when the state refutes the swapped rule; a failing message names which half fails). With a wrong meaning, delete `SwappedMeaningIs` before the test run.
- **Probe D** (B2 (a), the four conditions over the integers). In a second `instructor/scratch/probe.dfy`; `Inv` and `NextX` restate the problem's invariant and one pass of its body:

  ```dafny
  function Mag(v: int): int
  {
    if v >= 0 then v else -v
  }

  // The invariant of Walk.
  predicate Inv(x: int, k: int, x0: int)
  {
    k + Mag(x) == Mag(x0)
  }

  // x after one pass of the body (k after it is k + 1).
  function NextX(x: int): int
  {
    if x > 0 then x - 1 else x + 1
  }

  predicate LearnerMaint(x: int, k: int, x0: int, D: int)
  {
    true   // <- the answer's wp(S, I && 0 <= |x| < D), over x, k, x0 and D
  }

  // The body has no loop, so its wp is the postcondition at the state after it.
  lemma IsTheWp(x: int, k: int, x0: int, D: int)
    ensures LearnerMaint(x, k, x0, D) <==> (Inv(NextX(x), k + 1, x0) && 0 <= Mag(NextX(x)) < D)
  {
  }

  lemma Entry(x0: int)
    ensures Inv(x0, 0, x0)
  {
  }

  lemma Maintenance(x: int, k: int, x0: int)
    requires Inv(x, k, x0) && x != 0
    ensures LearnerMaint(x, k, x0, Mag(x))
  {
  }

  lemma UseAtExit(x: int, k: int, x0: int)
    requires Inv(x, k, x0) && !(x != 0)
    ensures k == Mag(x0)
  {
  }
  ```

  Run `scripts/vcheck --module Q08 instructor/scratch/probe.dfy`. `IsTheWp` verifies exactly when the answer's formula is the wp; `Entry`, `Maintenance` and `UseAtExit` verifying confirm the three decisions. For a claim that a condition holds without the guard, delete `&& x != 0` (or `&& !(x != 0)`) from that lemma and run again: verified confirms the claim; for a refutation, Probe D′.
- **Probe D′** (B2 (a), where the guard is needed, executable). In the same file, with `Maintenance` deleted if it no longer verifies:

  ```dafny
  @Test
  method WithoutTheGuard()
  {
    var x, k, x0 := 0, 0, 0;   // <- a state that satisfies the invariant (and, for this test, not the guard)
    expect Inv(x, k, x0), "the state is outside the invariant";
    expect !(Inv(NextX(x), k + 1, x0) && 0 <= Mag(NextX(x)) < Mag(x)), "one pass keeps the invariant and decreases the measure here";
  }
  ```

  Run `scripts/vcheck --test --name WithoutTheGuard instructor/scratch/probe.dfy`. It passes exactly when the state shows that the guard is needed.
- **Probe E** (B2 (b), the measure). Copy the problem's `Halt` into `instructor/scratch/probe.dfy` and run `scripts/vcheck --module Q08 instructor/scratch/probe.dfy`: the obligation Dafny reports is the anchor for "which obligation fails". The answer's state and trace, executable, in a second file:

  ```dafny
  @Test
  method HaltState()
  {
    var x := 0;   // <- the answer's state
    expect x != 0, "the guard fails at this state";
    var x2 := x - 2;
    expect !(0 <= x2 < x), "after one pass the measure is still bounded and smaller";
  }

  @Test
  method HaltTrace()
  {
    var trace: seq<int> := [3];   // <- the answer's trace from x0 = 3, as many values as it gives
    var i := 0;
    while i + 1 < |trace|
      decreases |trace| - i
    {
      expect trace[i] != 0 && trace[i + 1] == trace[i] - 2, "the trace does not follow the loop";
      i := i + 1;
    }
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. `HaltState` passes exactly when the guard holds at the state and one pass leaves the measure negative or no smaller, which covers both placements of the bound (after the pass, as the problem's maintenance formula has it, or "non-negative while the guard holds"). `HaltTrace` passes exactly when the trace follows the loop.
- **Probe F** (B2 (c), the Verus obligations). Copy the problem's Verus `mag` and `walk` into `instructor/scratch/probe.rs` inside `use vstd::prelude::*; verus! { … }` and run `scripts/vcheck --module Q08 instructor/scratch/probe.rs`. Then, for each claim, the one change it is about: `k` as `u32` (its return type and its declaration), or one hypothesis removed (the invariant; or the branch condition, by making the branches' order or condition different), and run again. The locations named are the anchor: an obligation the answer says a hypothesis discharges must fail, at its own line, when that hypothesis is removed; a claimed failure that verifies refutes the claim.
- **Probe G** (B3, the card pin). `sed -n '584,610p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B3 prints. Run it before grading any field.
- **Probe H** (Code-review focus, a dead step). Copy the declaration under review, with its module's imports and the given definitions it uses (for a refined lemma, its whole refining module, which reaches L4's `QG_L4_Spec` under `--module Q08`), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, delete the one line in question, and run `scripts/vcheck --module Q08 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed. For a `reveal`, the same recipe with the reveal moved into an `assert … by` around the one fact that needs the body (Probe H′): verified means the wider scope was not needed.
- **Probe I** (Code-review focus, a library fact copied by hand). For a helper whose statement looks like a library fact, search the pinned sources by a fragment of its statement, never by a name you were told. Dafny's standard library: `unzip -p .toolchain/dafny-4.11.0/dafny/DafnyStandardLibraries.doo program | grep -n -- '<fragment>'`. `vstd` at the pinned version: `find ~/.cargo/registry/src -maxdepth 2 -type d -name vstd-0.0.0-2026-09-20-0158` prints its directory, then `grep -rn -- '<fragment>' <that directory>`. The given layers L1–L4: `grep -n -- '<fragment>' dafny/given/Q/QG_L1_BigNat.dfy dafny/given/Q/QG_L2_BigNat.dfy dafny/given/Q/QG_L3_BigNat.dfy dafny/given/Q/QG_L4_BigNat.dfy`, and the same over `verus/given/qg_bignat_l1/src/lib.rs` to `verus/given/qg_bignat_l4/src/lib.rs`. A hit whose statement implies the helper's is the finding, delivered as the search query that found it.
- **Probe J** (Audit debrief D4, the statements' witnesses and strength). Copy your committed `research/q08_statements.dfy` (or `.rs`) to `instructor/scratch/probe.dfy` (`.rs`) and run `scripts/vcheck --module Q08 instructor/scratch/probe.<ext>`: the holes are the statements, and every `WITNESSES` line must verify (a witness call whose `requires` fails is exhibited by the run). For strength, copy the delivered file instead and replace one operation's delivered body by a body that returns a result unrelated to its input (an empty numeral; in Verus also with its proofs deleted), then run again: **verified** means that the statement does not pin the result, a finding against the statement (the run is the instance); not verified is not a proof of strength, only that this body is excluded.
- **Probe J′** (Audit debrief D4, a vacuous `requires`). For a statement whose `requires` you suspect no input meets, a lemma in the same probe file, over the statement's parameters, whose `ensures` is the negation of that `requires` and whose body is empty or short: verified is a verified refutation (the statement is vacuous). A failed witness alone is a verdict of kind 2, not a refutation.

## B1 — The weakest precondition as a term (hand-calculation; dimension: recomputation)

### recomputation
- **RC.a** — each step of (a) names the case of `Wp` it applies, and each substitution the cases of `SubstB` and `SubstE` it goes through. A step whose term is right but names no case is a gap (3). A score ≤2 quotes Probe A′'s first failing `expect`, with the step's call and the answer's term; a later step computed from a wrong earlier term is not a second flaw.
- **RC.b** — the final term of (a) is unsimplified and Probe A's `TermIs` verifies on it. If it verifies, (a) is correct whatever notation the steps use: do not invent a flaw. A simplified term in place of the built one is a gap (3) when Probe B confirms its meaning, and ≤2 only with Probe A′'s failing line.
- **RC.c** — (b)'s simplified formula: Probe B's `MeaningIs` verifies on it. A score ≤2 exhibits Probe B′ passing on a state the answer's formula gets wrong, with the run's verdict from its second line. Each simplification step is justified; a step whose line Probe B confirms but whose justification is false over the integers (quoted beside a value that refutes it) is a gap (3).
- **RC.d** — (b) names the start value the formula does not mention and gives a reason that is true of the program. A claim that the omitted value matters, or that another value is omitted, scores ≤2 only with Probe B′ run on two states that differ in that value alone.
- **RC.e** — (c)'s meaning: Probe C's `SwappedMeaningIs` verifies on it; its state: `SwappedCounterexample` passes on it; the trace agrees with `Exec` (the test's second line). A state on which the test fails scores ≤2, the failing message quoted. The warning named in (c) must be a property of the computed result, checkable on it (a value it mentions, a place it substituted); a warning that the result does not have is a gap (3).

## B2 — The loop rule, written out (hand-calculation; dimension: recomputation)

### recomputation
- **RC.f** — (a) states entry, maintenance and use at exit as formulas, and decides each. Probe D's `Entry`, `Maintenance` and `UseAtExit` verifying confirm the decisions; a decision that one of them fails is refuted by that lemma verifying, the output pasted.
- **RC.g** — (a)'s maintenance formula is the wp of the body, computed by B1's rules with one conjunct per branch: Probe D's `IsTheWp` verifies on it. A score ≤2 exhibits a state at which the formula and the right side of `IsTheWp` differ, by an executable check in the probe file (a `@Test` method with `expect` on both sides at that state).
- **RC.h** — every use of the guard the answer names is a real use, and none is missing. A claimed use is confirmed by Probe D's lemma failing without the guard and Probe D′ passing on a state; a missing use (a branch argued without the guard where Probe D′ passes on a state) is a gap (3) when the conclusion is right, and ≤2 when the answer says the guard is not needed there, with Probe D′'s state.
- **RC.i** — (b)'s soundness argument names the induction (on what, its base, its step) and why the measure's two conditions end every run. An argument with no induction is a gap (3). A false claim about the rule (for example that maintenance alone gives the invariant at exit) scores ≤2 only with a loop of the answer's own kind, or this one, on which the claim's conclusion fails by an executable check.
- **RC.j** — (b)'s failing obligation of `Halt` agrees with Probe E's verifier output, and its state passes `HaltState` in the form the answer states; the trace passes `HaltTrace`. Naming the decrease (rather than the bound) as the failing condition scores ≤2: any state with `x != 0` shows `x - 2 < x`, `HaltState`'s second line on it.
- **RC.k** — (c)'s obligations and their discharging hypotheses agree with Probe F's runs: each obligation named appears at its line when its hypothesis is removed, and the `u32` claim agrees with the `u32` run. A claim that a run contradicts scores ≤2, the run pasted; an obligation the runs show and the answer misses is a gap (3).

## B3 — Paper card 02.1 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe G prints the hash B3 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled: task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact, each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 584–610). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, a budget cap, a cost, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a size, a time or a count given for the wrong proof (the human CPS proof or the agent's ANF proof), the wrong unit (lines, hours, calls) or the wrong aggregate contradicts the table or sentence it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.
- **CF.g** — the cheat-surface field's mapping onto the flagship contract (chapter §7's CONTRACT block) is the learner's own reasoning: it scores 4 when each move it maps is mapped to an acceptance line that would see that move, or to "a reader" with a reason, and when it says where the range does not tell how a move was made. A mapping to a line that cannot see the move (quoted beside the contract line and what that line's instrument checks, from chapter §4's table) scores ≤2.

## The --post pass

Q08's written pair holds no informal-proof-first problem, so there is no blueprint to diff against your proofs: `/grade-paper Q08 --post` has nothing to re-score and writes no `paper-post` row. No `--report` pass either: Q08 has no lab report.

## Gate

The mechanical preconditions of `/review-code Q08`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck --module Q08` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q08_InternalsII/std` and `scripts/vcheck --gate verus/q/q08_internals_ii` each exit 0 and print only the summary line. After the contract runs, `scripts/vcheck --gate dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` and `scripts/vcheck --gate verus/q/q08_internals_ii/src/agent.rs` do too.
- **A3 — audit clean.** `scripts/vaudit dafny/Q/Q08_InternalsII/std` and `scripts/vaudit verus/q/q08_internals_ii` report no finding; after the contract runs, so does `scripts/vaudit <agent file>` for each agent file (no `.audit` pin: the CONTRACT's line is "reports no finding").
- **A4 — slots, first tries, shipped lines.** `scripts/firsttry.sh Q08 --report --strict` exits 0: every slot filled, recorded and enabled, every shipped check uncommented (the commented checks under `Uncomment as you go:` included), and, once repaired, the exit files' blocks too. Q08 has no property test, so `scripts/vcheck --test` has nothing to run.
- **A5 — statements unchanged.** `scripts/specfreeze --check Q08` reports no finding. The three open statements, `Toggle::flip`, `Odometer::advance` and `Odometer::current`, accept added `requires` and `ensures` clauses and nothing else; every other statement, the refined lemmas' inherited ones included, is frozen. A `decreases` clause added to a declaration that shipped without one is no change to the freeze; a shipped measure is.
- **A6 — diagnosis fixtures stay out.** The card demos under `specimens/Q08/` are red by design (their failures are pinned by in-file `// EXPECT` lines and sealed sidecars) and are never finished or reviewed. A2 and A3 skip them. No brittleness gate applies at this bar.

## Code-review focus — band: "library-conventions"

- **C1 — names in the library's grammar.** Each name you introduced (a helper lemma of a refining module, a loop variable, a proof fn) follows the naming of Dafny's standard library or of `vstd` for its kind, as read from their sources (Probe I's commands print them): Dafny lemmas and functions in PascalCase, Verus proof fns `lemma_…` in snake case, and a name that says what the lemma states. A name that misleads about the statement is a finding, quoted beside the statement; a style difference with no reading cost is not. If every name reads as its statement, do not invent a flaw.
- **C2 — no library fact copied by hand.** A helper whose statement a lemma of `Std`, `vstd` or the given layers L1–L4 already implies is a finding, delivered as Probe I's search query and its hit, never as a lemma name you remembered. A helper that states something the libraries do not (Probe I finds no implying statement) is correct, however general: do not invent a flaw.
- **C3 — refinement helpers live in the refining module (H1d, H2d, H7d).** A helper lemma that a refined lemma needs sits in the refining module that uses it (the refined statement itself cannot change, A5), and no proof text appears twice in one module where a helper would serve. A refined lemma's proof uses only what its refinement defines and the layers give; a `reveal` is scoped as narrowly as the proof allows (Probe H′). Every call is needed (Probe H); a dead one is a finding at this bar.
- **C4 — trait specifications in the trait's own vocabulary (T1v, H3v).** Each clause you added to a trait method speaks of the trait's spec fns (and the method's parameters and result), never of an implementation's fields; each is needed by the given client or by a check under `Uncomment as you go:` (Probe H on the clause: the client or the check fails without it), and none fails the implementation. A clause the client and the checks do not need is a finding only with Probe H's verified run.
- **C5 — the generic client stays generic (H4v).** `scale` uses only the operations of `NatLike` and the facts of its clauses; the arithmetic step is a library lemma where one applies (C2), and the loop's invariant states what the accumulator holds and nothing the verifier did not need (Probe H on each clause). A call to a concrete type's own function is a finding at grade 1, whatever the verifier says.
- **C6 — permissions in the form their effect needs (H5v, H6v).** Each operation takes its permission shared to read and mutable to write, as `vstd::cell::pcell`'s own signatures state (Probe I on `pcell.rs`); no `assert` about a permission's `id()` or value is left that Probe H shows dead. If every line is needed and each borrow form is the signature's, do not invent a flaw.
- **C7 — the verified wp's induction follows the recursion (H8d, H9d, H10d).** Each recursive proof recurses on the datatype its shipped `decreases` names, one case per constructor, and every call in a case is needed (Probe H); `Update` stays opaque (no `reveal` of it outside the given code). H10d goes through `WpSound`, as its prompt asks: a proof that runs `Exec` instead is a finding at grade 1, however short.
- **C8 — intent stays in the shipped contracts.** A5 is the anchor; the freeze does not see Dafny's `opaque` modifier, so read every given opaque declaration in the files under review: each still reads `opaque`. A changed `requires`, `ensures`, check line or opacity is a finding at grade 1, whatever the verifier says.
- **C9 — names and dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.

## Audit debrief — after /contract Q08

Questions for you, after each contract run (Dafny first, then Verus). Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — did the statements stay yours?** `scripts/specfreeze --against research/q08_statements.dfy dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` (and the Verus pair, `research/q08_statements.rs` against `verus/q/q08_internals_ii/src/agent.rs`) reports no change.
- **D2 — did the diff stay in the bodies and `HELPERS`?** `git diff -U0` of the agent file against the commit that holds your snapshot: every hunk is inside a `STATEMENTS` method's body (Verus: a stub's `#[verifier::external_body]` line and its `unimplemented!()` body) or inside `HELPERS`; no statement, witness, attribute or doc comment outside `HELPERS` changed. An attribute added to a statement, or a resource attribute anywhere, is a breach even when the gate accepts it.
- **D3 — is the delivery green and audit-clean?** Run the contract's gate and audit lines yourself (A2 and A3's agent forms) and compare them with the contractor's last report of them.
- **D4 — are your statements useful and strong?** Probe J on the committed statements (every witness verifies) and on the delivery (a body unrelated to the input does not verify); Probe J′ on any `requires` you doubt. Record, per statement, the witness that verified and the unrelated body that was excluded. A statement that Probe J's unrelated body passes is a finding against your statement, not the contractor.
- **D5 — does each helper prove what it says?** For each helper under `HELPERS`: does its `requires` assume what a caller cannot establish, or what the statement it serves should have proved? Settle each doubt with a witness call in Probe J's file (a call that verifies shows the `requires` can hold).
- **D6 — did the contractor re-verify after every edit, and stop where it should?** Count the `scripts/vcheck` runs between edits in the transcript; name any stacked edits; and say whether it ever asked to change a statement or reported one it could not prove (the contract's never-weaken rule).
- **D7 — which statement cost the contractor most, and why?** From the transcript's attempts: write it in the agent file's `AUDIT` block, with the failing message the contractor met most.
- **D8 — what did no instrument see?** The gate, the freeze, the audit and your witnesses each checked something (chapter §7's dashboard section names what each cannot see); name one property of your statements that none of them checked, how you checked it instead, and one transcript moment that earns a rule in your contract's next version (Q09 writes v1), in the rule format of `CLAUDE.md`'s contract slot.
