# Q11 rubric — Practice I-B

> **Consumers:** `/grade-paper Q11` (B1, B2) and `/review-code Q11` (Gate, Code-review focus). Q11 has no agentic file, so there is no audit debrief. Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q11 --check` has recorded both Q11 predictions.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q11_solutions.tex  sha256 9de6a3bca0c7039ac7fd626448e5314899b37454204d7e0d18828d74cd0f9495 — the written track's reference (B1, B2)
paper/Q11_problems.tex  sha256 18e636f08aa40c5ef4dbc46f75e7ed2a7f4cc0b2d76162edf6a487c02cae73e9 — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy  sha256 35bf6d621fd959a53aa204d1a3e417bd3d95b8d24699f1831b4e244a79e009d4 — the main Dafny half of the code review
Solutions/dafny/Q/Q11_PracticeIB/std/Q11_Wp.dfy  sha256 dbb1d19c2c30716d01f702f2d8f5a989282a9290b27943df05584ee909595244 — the wp file's half of the code review
Solutions/verus/q/q11_practice_ib/src/lib.rs  sha256 11f7df6aeee101a1c5a73ead9433236839871971354ea860c770a1b3b492281d — the crate root's half of the code review
Solutions/verus/q/q11_practice_ib/src/perm.rs  sha256 9d8eee3c0735a8f70ee795db99bcdccfbfee5d1f6f012d5df9ee3cb4c9544e97 — the permissions module's half of the code review

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. A verified probe confirms a claim (verdict kind 1). An error verdict alone refutes nothing: a wrong formula is exhibited by an executable check at a concrete start value.

- **Probe A** (B1 (a), splice template: is the formula the weakest precondition?). In `instructor/scratch/probe.dfy`, the problem's program and postcondition, with the answer's final formula over `x` pasted as `Pre`'s body:

  ```dafny
  module ProbeA {
    // y := x + 3; if y > 10 then y := y - 10
    function Prog(x: int): int
    {
      var y := x + 3;
      if y > 10 then y - 10 else y
    }

    ghost predicate Post(y: int) { y < 5 }

    ghost predicate Pre(x: int) { true }   // <- the answer's final formula, over x

    lemma Exact(x: int)
      ensures Pre(x) <==> Post(Prog(x))
    {
    }
  }
  ```

  Run `scripts/vcheck --module Q11 instructor/scratch/probe.dfy`. Verified: the formula is the weakest precondition (equivalent to it over the integers). A failure says only that some `x` separates the two sides: Probe A″ exhibits it. As shipped (`true`), the template fails at `Exact`'s postcondition; a correct formula spliced in verified on the pins (Dafny 4.11.0, 23 verified).
- **Probe A′** (B1 (a), one step of the trace). For a step the answer writes as "formula F becomes formula G by rule R", paste F and G as two predicates over `x` and `y` and state the step as a lemma: `lemma Step(x: int, y: int) ensures G(x, y) <==> <R applied to F>` with an empty body, in the same module as Probe A. Verified: the step is right. A failure is a gap until Probe A″ shows the two sides differ at a concrete value.
- **Probe A″** (B1 (b), (c), or any claimed value). A test runs the program on one start value:

  ```dafny
  module ProbeRun {
    @Test
    method AtValue()
    {
      var x := 0;                  // <- the start value
      var y := x + 3;
      if y > 10 { y := y - 10; }
      expect y < 5, "Q fails";     // <- or expect !(y < 5) for a claimed failure
    }
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. `FAILED` with the message: the claim about that value is false, a confirmed flaw. `PASSED`: the claim holds there. As shipped (`x := 0`, `expect y < 5`) it prints `1 passed, 0 failed`.
- **Probe C** (B2, the card pin). `sed -n '917,940p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B2 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step or an over-wide frame). Copy the declaration under review, with its file's `module` line and imports (for a crate file, its `use` lines), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`; delete the one line in question, or narrow the one `modifies` clause in question; run `scripts/vcheck --module Q11 instructor/scratch/probe.<ext>`. Verified: the line was dead, or the frame was wider than needed. Not verified: it is needed.

## B1 — A weakest precondition, step by step (hand-calculation; dimension: recomputation)

### recomputation
- **RC.a** — the trace runs backwards from Q, one statement per step, and each step names its rule (assignment, sequence, conditional). A missing rule name with a correct formula is a gap (3). A score ≤2 exhibits a step whose formula is not its rule applied to the previous formula: Probe A′ on that step fails, and Probe A″ shows the differing value.
- **RC.b** — the conditional step keeps a constraint for each way the condition can go (two implications, or an equivalent case split), including the branch in which nothing happens. A score ≤2 exhibits a start value that satisfies the answer's formula and ends outside Q, by Probe A″.
- **RC.c** — every simplification is an equivalence over the integers. A score ≤2 names the step and an integer at which its two sides differ (Probe A″ or Probe A′ shows it).
- **RC.d** — the final formula mentions only `x`, and Probe A verifies with it spliced in. If Probe A verifies, (a) is correct: do not invent a flaw, whatever the formula's shape.
- **RC.e** — (b)'s two runs agree with Probe A″ at the values the answer chose, and one satisfies the answer's formula and one does not. A score ≤2 pastes the Probe A″ run that contradicts a claimed final value or verdict.
- **RC.f** — (c) agrees with the answer's own (a). A score ≤2 exhibits, by Probe A″, a value that contradicts the stated set (a value in the set whose run fails Q, or one outside it whose run meets Q).

## B2 — Paper card 02.12 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B2 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 917–940). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cost, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a count given to the wrong row of the results table (produced against verified harnesses, manual against automatic, contracts against harnesses), or a tool given to the wrong checking method, contradicts the table or sentence it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q11`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q11` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q11_PracticeIB/std` (both Dafny files) and `scripts/vcheck --gate verus/q/q11_practice_ib` (the crate root and `src/perm.rs` together) each exit 0 and print only the summary line.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q11_PracticeIB/std` and `scripts/vaudit verus/q/q11_practice_ib` report no finding.
- **A4 — statements unchanged.** `scripts/specfreeze --check Q11` reports no finding. It accepts bodies for `AddCanon`, `Pre1` and `Pre2` (the open bodies of `expected/Q11.freeze`), and nothing else; `Q11_VcAnswer` keeps its empty import list.
- **A5 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q11 --report --strict` exits 0: both predictions filled, recorded and enabled; every shipped commented check uncommented (`SetCheck`, `CopyCheck`, `AddCanonCheck`, `acc_check`, `value_two_check`, `max_into_check`); the `formula:` form lines of H7d and H8d met; and, after the exit's scored run, the exit files repaired.
- **A6 — what is not reviewed.** The `CALIBRATION` block is your prose, read by no tool. No brittleness gate applies at this bar.

## Code-review focus — band: "design-lite"

At this bar, the conventions of the earlier bars bind (the proof reads, it has the shape its statement suggests, library and layer facts are called by name), plus the design calls a filled hole still makes: the case split matches the definition it unfolds, a loop's invariant and frame are stated where they are used, and no detour goes around the given representation.
- **C1 — frames no wider than the method needs (H1d, H2d).** Each loop that writes the heap states what it may modify, and no method writes outside `Repr`; a frame Probe D shows narrower-and-verifying is a reading note, never below 3. If the checks with a second, disjoint vector pass (A5), the frame keeps the other vector out: do not invent a flaw.
- **C2 — ghost fields assigned where the object changes (H1d, H2d).** Every write of `a` or `n` is matched by the update of `Contents` that `Valid()` needs, at the same place in the code; a ghost update far from its write, cited at `file:line`, is a reading note.
- **C3 — the refusal changes nothing (H3v, H4v).** On every path that returns `Err`, no field of `*self` is written before the return. The `ensures` already checks the values; this line reads the code for writes that are undone later, a finding only when cited at `file:line`.
- **C4 — the VC predicates are formulas (H7d, H8d).** `Pre1` and `Pre2` are arithmetic over `x` and `y` (the blocks' `form: formula:Pre1` and `formula:Pre2` lines, which A5 checks: no `var` binding, `match` or call). If A5 passes, read the formula for the hand computation it records; a formula in another but equivalent arithmetic form is correct: do not invent a flaw.
- **C5 — the soundness case unfolds, it does not detour (H9d).** The proof splits on the condition and uses the hypothesis for the branch; a helper lemma that restates `Wp`'s or `Exec`'s definition is a finding at this bar (Probe D on the helper's call shows it dead or needed).
- **C6 — permissions passed, never forged (H10v).** Each cell operation receives the permission parameter the signature gives, and nothing is `assume`d about a permission (A3 is the anchor). A read through `pd` borrowed shared for the read is the expected shape; do not invent a flaw in the order of the read and the write if A2 is green.
- **C7 — no dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.
