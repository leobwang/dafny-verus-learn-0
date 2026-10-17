# Q14 rubric — Practice II-B

> **Consumers:** `/grade-paper Q14` (B1, B2) and `/review-code Q14` (Gate, Code-review focus). Q14 has no agentic file, so there is no audit debrief. Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q14 --check` has recorded the Q14 prediction.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q14_solutions.tex  sha256 426ada17b61284d971f984dce8ec6060058688ba7a7bd73f1b090c0e45ec37ee — the written track's reference (B1, B2)
paper/Q14_problems.tex  sha256 45408929b0873dea7e470a58f9827054e92dcc2f3fcaafcfb2447bd46b233b28 — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q14_PracticeIIB/std/Q14_PracticeIIB.dfy  sha256 796c1b5f596022d02610d7280150f2ec03b657cfc4234aa9d773d0fc951a5284 — the main Dafny half of the code review
Solutions/dafny/Q/Q14_PracticeIIB/std/Q14_Loop.dfy  sha256 47f79bffc99f36cc622bcc27857956c655c1407a200ae94c742150cc88b193c8 — the loop file's half of the code review
Solutions/verus/q/q14_practice_iib/src/lib.rs  sha256 5dc888ee5a617f2b19eec5c6a186358497b35b445b53e55c2395b315c7a53b33 — the crate root's half of the code review
Solutions/verus/q/q14_practice_iib/src/perm.rs  sha256 6ae5220d876cb104a47b7cbeb1130355145fd336d426bfdecb6ed8f4f326446a — the permissions module's half of the code review

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. A verified probe confirms a claim (verdict kind 1). An error verdict alone refutes nothing: a condition a candidate breaks is exhibited by an executable check at a concrete witness.

- **Probe A** (B1 (a), splice template: do conditions (i) and (ii) hold for a candidate?). In `instructor/scratch/probe.dfy`, the problem's trait contract, with one candidate's precondition pasted as `PI`'s body and its postcondition as `QI`'s:

  ```dafny
  module ProbeA {
    // the trait's contract
    predicate PT(x: int) { 0 <= x <= 10 }
    predicate QT(x: int, y: int) { y > x }

    predicate PI(x: int) { true }           // <- the candidate's requires, over x
    predicate QI(x: int, y: int) { true }   // <- the candidate's ensures, over x and y

    // (i): every argument the trait admits, the candidate admits
    lemma PreOk(x: int)
      ensures PT(x) ==> PI(x)
    {
    }

    // (ii): under the trait's requires, every result the candidate allows, the trait allows
    lemma PostOk(x: int, y: int)
      ensures PT(x) && QI(x, y) ==> QT(x, y)
    {
    }
  }
  ```

  Run `scripts/vcheck --module Q14 instructor/scratch/probe.dfy`. An error on neither lemma: both conditions hold. An error on `PreOk` or `PostOk` says only that some witness breaks that condition: Probe A′ exhibits it. As shipped (`true`, `true`), `PreOk` verifies and `PostOk` fails:

  ```
  vcheck: instructor/scratch/probe.dfy [dafny, learner loop]: failed — 23 verified, 0 holes, 1 error
  instructor/scratch/probe.dfy:18:3: error: a postcondition could not be proved on this return path
  instructor/scratch/probe.dfy:17:37: related: this is the postcondition that could not be proved
  instructor/scratch/probe.dfy:4:36: related: this proposition could not be proved
  ```
- **Probe A′** (B1 (b), a claimed witness). A test evaluates the contracts at one witness:

  ```dafny
  module ProbeA2 {
    predicate PT(x: int) { 0 <= x <= 10 }
    predicate QT(x: int, y: int) { y > x }

    predicate PI(x: int) { true }           // <- the candidate's requires, over x
    predicate QI(x: int, y: int) { true }   // <- the candidate's ensures, over x and y

    @Test
    method AtWitness()
    {
      var x, y := 3, 3;                     // <- the claimed witness (for (i), y is unused)
      expect PT(x) && QI(x, y) && !QT(x, y), "the pair does not break (ii)";
      // for (i): expect PT(x) && !PI(x), "the value does not break (i)";
    }
  }
  ```

  Save it as `instructor/scratch/probe.test.dfy` and run `scripts/vcheck --test instructor/scratch/probe.test.dfy`. `PASSED`: the witness shows what the answer claims. `FAILED` with the message: it does not, a confirmed flaw. For a witness to (i), replace the `expect` line by the commented one. As shipped (`true`, `true`, the pair `(3, 3)`) it prints:

  ```
  vcheck: instructor/scratch/probe.test.dfy [dafny, test]: verified — 1 passed, 0 failed
  PASSED ProbeA2.AtWitness
  ```
- **Probe C** (B2, the card pin). `sed -n '2588,2631p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B2 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review, with its file's `module` line and imports (for a crate file, its `use` lines) and any helper or given definition it calls, into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`; delete the one line in question; run `scripts/vcheck --module Q14 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.
- **Probe F** (Gate A6, stability). `scripts/vcheck --brittleness --solvers dafny/Q/Q14_PracticeIIB/std` and `scripts/vcheck --brittleness verus/q/q14_practice_iib`: the summary line ends with `stable`. A `differs` line names each symbol whose verdict varies.

## B1 — Which contracts may stand in for the trait's (concept; dimension: correctness)

### correctness
- **CO.a** — each of (a)'s ten claims (does (i) hold? does (ii) hold? for five candidates) agrees with Probe A on that candidate. A claim that a condition holds is confirmed by its lemma verifying; a claim that it fails is confirmed only by (b)'s witness, through Probe A′. A score ≤2 pastes the Probe A run that contradicts a "fails" (the lemma verifies), or the Probe A′ run (`FAILED`) on the witness given for a "fails", or names a "fails" with no witness.
- **CO.b** — every witness in (b) breaks the condition it is given for: for (i), the trait's precondition holds and the candidate's does not; for (ii), the trait's precondition and the candidate's postcondition hold and the trait's postcondition does not. Any witness that shows it is correct, whatever its numbers: do not invent a flaw in a witness Probe A′ passes.
- **CO.c** — (b) gives a witness for every condition (a) says fails, and none for a condition (a) says holds. A missing witness is a gap (3).
- **CO.d** — condition (ii) is the problem's: it holds the trait's precondition fixed. A witness to (ii) whose `x` the trait's precondition does not admit shows nothing, and Probe A′ prints `FAILED` on it; the finding pastes that run once and does not count the same misreading again under CO.a.
- **CO.e** — (c) names one condition for the client's call and the other for what it concludes, and its reason says what the client establishes before the call and what it may assume after it. A reason that contradicts the answer's own (a) scores ≤2, quoting both; wording is free.

## B2 — Paper card 06.9 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B2 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 2588–2631). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a token count, a cost, an interval, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a count given to the wrong workflow (C0–C4), a false-success count read as a valid count, a share of accepted candidates read as a share of all runs, or a check put in the wrong part of the acceptance condition contradicts the line it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q14`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q14` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q14_PracticeIIB/std` and `scripts/vcheck --gate verus/q/q14_practice_iib` each exit 0 and print only the summary line. Each gate covers both files of its unit.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q14_PracticeIIB/std` and `scripts/vaudit verus/q/q14_practice_iib` report no finding.
- **A4 — statements unchanged.** `scripts/specfreeze --check Q14` reports no finding: every shipped signature, `requires`, `ensures` and `decreases`, the trait's contracts and the inherited statements included, is as shipped. A measure you add where none shipped is allowed.
- **A5 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q14 --report --strict` exits 0: the prediction filled, recorded and enabled; every shipped commented check uncommented (`CmpCorrectCheck`, `pair_acc_check`, `sum_limbs_check`, `InterleaveSpecCheck`, `list_check`); H3v's `form: loop-dir:i:down` line met (the loop on `i` only steps `i` down, reads `v` at indices that add `i` and computes the sum); and, after the exit's scored run, the exit file repaired.
- **A6 — stable under seeds.** Probe F: both sweeps end `stable` (gate 6 of `/review-code`, from this bar up). The spread of resource counts is reported, not graded: this rubric pins no threshold.
- **A7 — what is not reviewed by a tool.** The `CALIBRATION` block is your prose, read by no tool. A5's form checks that H3v's loop steps `i` down and reads `v` at indices that add `i`, but it cannot follow an index through a helper or another sequence (C5 reads that), and no tool counts the helpers you wrote (C1 reads them): record both as read, never as passed by a tool.

## Code-review focus — band: "design-judgment"

At this bar, the conventions of the earlier bars bind (the proof reads, the induction follows the recursion it unfolds, library and layer facts are called by name, an invariant or measure is named where it is used), plus design judgment: where each fact lives (a `requires`, an invariant, a ghost or tracked value, a helper's statement) is a choice the code defends, and the proof is stable under seeds (A6).
- **C1 — the one helper earns its place (H1d, H3d, H3v).** Each item's `HELPERS` area holds at most one lemma or proof fn of your own (a spec fn that only names a sub-term is a definition, not a lemma), with a statement of its own that the main proof calls. A helper that restates the item's goal, or one Probe D shows dead, is a finding; two helpers for one item is a finding at this bar (the tier allows one), cited at `file:line`. H2v, H4d and H5v ship no `HELPERS` area: their reasoning lives in their bodies, and a separate helper written for one of them is a reading note, cited at `file:line`.
- **C2 — the measure is a choice the code defends (H3d; X1d once the exit is scored).** The lemma's `decreases` names a quantity that every recursive call of the proof shrinks, and it is written where the default (the parameters in order) would not do (P1dv). If A2 is green, the measure is sound: a finding here is about reading, cited at `file:line`, never about correctness.
- **C3 — the refinement proves what the shortcut assumes (H1d).** The proof's cases are `Cmp`'s own (each branch of the given `Cmp` is handled, or the proof says why one argument covers several); a fact the proof needs about canonical limb sequences is stated once and named where it is used; every step about powers is a named lemma call (nonlinear arithmetic is off in `Q14_Cached`). If A2 and A6 hold, the case split is right: do not invent a flaw in its order.
- **C4 — the implementation answers to the trait (H2v).** Each method establishes the trait's `ensures` as stated through `total` and uses only what the trait's `requires` give it (the verifier refuses a `requires` on an implementation, so A1 anchors that part). `from_big`'s two directions are both proved by its body: the uncommented check exercises one input only, so the reader checks that the refusal branch names the layer fact it rests on. An `ensures` the implementation adds beyond the trait's is allowed and is a reading note only if no caller uses it.
- **C5 — erased, and in the stated direction (H3v).** No exec line reads the ghost bound (the verifier refuses one: A1 is the anchor); the bound appears only in the specification, the invariants and proof code. The loop runs from the top limb down: its index starts at the vector's length and goes down to 0, as the docstring requires. A loop in the other direction fails A5's `form: loop-dir:i:down` line (the anchor: its `form loop-dir:i:down not met` line), a finding at grade ≤2 whatever the verifier says. The form reads how `i` steps and each index of `v` the body reads (a `v[v.len() - i]` fails it); a loop that steps `i` down but adds the limbs from the low end by a route the form cannot follow (a helper, another sequence) is the same finding, quoted at `file:line` (A7). The helper, if any, relates the two ends of `limb_sum` as the hint says (C1).
- **C6 — the loop rule's case reads as the rule (H4d).** The recursive call is on less fuel (the shipped `decreases`), each side condition is used in the state where it holds, and the step that makes a side condition usable (its membership in `Vcs`, as the hint says) sits next to its use. If A2 and A6 hold, the case analysis is right: do not invent a flaw in its order.
- **C7 — every permission has one owner, readable from the code (H5v).** At each step of `push_front` and of `sum`'s loop, each tracked permission is held by the list, by a node or by a named local, and the code shows where it moves; the loop's invariant answers the docstring's question (what the loop holds of the node it is at, and what it hands to the next step). A tracked or ghost update that no invariant or call uses is dead (Probe D on it). No permission comes from an `assume` or an `external_body` (A3).
- **C8 — automation used on purpose.** A `broadcast use`, a `reveal`, a `by (nonlinear_arith)` step or a library call is scoped to the body that needs it and carries a short reason; one that Probe D shows unneeded is a reading note. The `{:disableNonlinearArithmetic}` attributes of `Q14_Cached` and `Q14_Loop` ship on their `module` lines: removing one is a finding at grade 1, whatever the verifier says.
- **C9 — no dead code.** No commented-out experiments and no unused helpers in your own lines. The prediction slot and its answer stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.
