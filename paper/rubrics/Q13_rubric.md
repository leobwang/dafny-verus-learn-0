# Q13 rubric — Practice II-A

> **Consumers:** `/grade-paper Q13` (B1, B2) and `/review-code Q13` (Gate, Code-review focus). Q13 has no agentic file, so there is no audit debrief. Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q13 --check` has recorded the Q13 prediction.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q13_solutions.tex  sha256 825fd2a148338f8f5249d2fb8f4c983e74e26df72ac6ed65ae7edb8cd17f3846 — the written track's reference (B1, B2)
paper/Q13_problems.tex  sha256 6b4d37ffff19e2d70442d63da5505814d38de3669ea78bdcf039998c17c3ca8e — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy  sha256 9c2d77675266dd3334c523ac46e8027b099aaf68a58f0e0b2f9389f621822eff — the Dafny half of the code review
Solutions/verus/q/q13_practice_iia/src/lib.rs  sha256 aea20956f01b968a5ac3218846ece94bc5c0a8c3370c3683ba927387450ae0c7 — the Verus half of the code review

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. A verified probe confirms a claim (verdict kind 1). An error verdict alone refutes nothing: a property a candidate lacks is exhibited by an executable check at a concrete pair.

- **Probe A** (B1 (a), splice template: is the candidate sound, is it complete?). In `instructor/scratch/probe.dfy`, the problem's reference postcondition, with one candidate pasted as `Cand`'s body:

  ```dafny
  module ProbeA {
    // Ramp's reference postcondition
    predicate Q(x: int, y: int) { y == (if x < 0 then 0 else x) }

    predicate Cand(x: int, y: int) { true }   // <- the candidate, over x and y

    // sound: every output the candidate allows is the reference's
    lemma Sound(x: int, y: int)
      ensures Cand(x, y) ==> Q(x, y)
    {
    }

    // complete: every reference output meets the candidate
    lemma Complete(x: int, y: int)
      ensures Q(x, y) ==> Cand(x, y)
    {
    }
  }
  ```

  Run `scripts/vcheck --module Q13 instructor/scratch/probe.dfy`. An error on neither lemma: the candidate is sound and complete. An error on `Sound` or `Complete` says only that some pair separates the two sides: Probe A′ exhibits it. As shipped (`true`), `Complete` verifies and `Sound` fails.
- **Probe A′** (B1 (b), a claimed pair). A test evaluates the candidate and the reference at one pair:

  ```dafny
  module ProbeA2 {
    predicate Q(x: int, y: int) { y == (if x < 0 then 0 else x) }

    predicate Cand(x: int, y: int) { true }   // <- the candidate, over x and y

    @Test
    method AtPair()
    {
      var x, y := 0, 1;                        // <- the claimed pair
      expect Cand(x, y) && !Q(x, y), "the pair does not show unsoundness";
      // for incompleteness: expect Q(x, y) && !Cand(x, y), "...";
    }
  }
  ```

  Save it as `instructor/scratch/probe.test.dfy` and run `scripts/vcheck --test instructor/scratch/probe.test.dfy`. `PASSED`: the pair shows what the answer claims. `FAILED` with the message: it does not, a confirmed flaw. As shipped (`true`, the pair `(0, 1)`) it prints `1 passed, 0 failed`.
- **Probe C** (B2, the card pin). `sed -n '2005,2031p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B2 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review, with its file's `module` line and imports (for a crate file, its `use` lines) and any helper it calls, into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`; delete the one line in question; run `scripts/vcheck --module Q13 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.
- **Probe E** (Code-review focus C5, the prose statement's two instruments). The block of `lemma_lt_at_any` in your crate: the use-site check `prose_use_site` uncommented and the witness `prose_witness` written are what A2 and A5 check. To read a statement against the prose, copy your statement (its signature, `requires` and `ensures`, with an empty body and `#[verifier::external_body]` above it) and the given client into `instructor/scratch/probe.rs`, add a client of your own that calls it on two sequences the prose covers, and run `scripts/vcheck --module Q13 instructor/scratch/probe.rs`. A call whose `requires` fails on a case the prose covers exhibits a statement narrower than the prose; an `ensures` the prose does not say is read, not probed (the hidden equivalence check is the learner's own run, A7).
- **Probe F** (Gate A6, stability). `scripts/vcheck --brittleness dafny/Q/Q13_PracticeIIA/std` and `scripts/vcheck --brittleness verus/q/q13_practice_iia`: the summary line ends with `stable`. A `differs` line names each symbol whose verdict varies.

## B1 — Sound, complete, both or neither (concept; dimension: correctness)

### correctness
- **CO.a** — each of (a)'s ten claims (sound? complete? for five candidates) agrees with Probe A on that candidate. A claim that a candidate is sound or complete is confirmed by its lemma verifying; a claim that it is not is confirmed only by (b)'s pair, through Probe A′. A score ≤2 pastes the Probe A run that contradicts a "yes", or the Probe A′ run (`FAILED`) on the pair given for a "no", or names a "no" with no pair.
- **CO.b** — every pair in (b) shows the property it is given for: for unsoundness, the candidate holds and the reference does not; for incompleteness, the reference holds and the candidate does not. Any pair that shows it is correct, whatever its numbers: do not invent a flaw in a pair Probe A′ passes.
- **CO.c** — (b) gives a pair for every property (a) says a candidate lacks, and none for a property (a) says it has. A missing pair is a gap (3).
- **CO.d** — (c) names a candidate for the client and one for the implementer, and its reason distinguishes what a caller may conclude from what the body must establish. A reason that contradicts the answer's own (a) scores ≤2, quoting both; wording is free.
- **CO.e** — the definitions are the problem's (soundness: the candidate implies the reference; completeness: the reference implies the candidate). An answer that swaps them throughout is graded by its own definitions only after the swap is named as one finding (2); do not count each swapped claim again.

## B2 — Paper card 05.5 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B2 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 2005–2031). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cost, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a score given to the wrong stage (code, specification, proof, end to end), the wrong system or the wrong part of the benchmark, or a check given to the wrong place in the order the range states, contradicts the table or sentence it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q13`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q13` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q13_PracticeIIA/std` and `scripts/vcheck --gate verus/q/q13_practice_iia` each exit 0 and print only the summary line.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q13_PracticeIIA/std` and `scripts/vaudit verus/q/q13_practice_iia` report no finding.
- **A4 — statements unchanged.** `scripts/specfreeze --check Q13` reports no finding: every shipped signature, `requires`, `ensures` and `decreases` is as shipped, and `Q13_Library`'s nonlinear attribute is still on its `module` line (a deleted one is `freeze-lever-removed`). The prose item's statement is new, so the freeze does not see it (C5 reads it).
- **A5 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q13 --report --strict` exits 0: the prediction filled, recorded and enabled; every shipped commented check uncommented (`sub_check`, `prose_use_site`, `NormalizeConcatCheck`, `ValueLoopCheck`); the `form: no-nl` lines of H4v and X1v met (no `nonlinear_arith` in those blocks); H5d's `form: loop-dir:up, no-call:ToNat` line met (its loop counts up, reads `s` from the low end at its counter and computes `v`; no compiled `ToNat`); no `lever:` line (the strict report's lever freeze: `Q13_Library`'s nonlinear attribute still there); and, after the exit's scored run, the exit file repaired.
- **A6 — stable under seeds.** Probe F: both sweeps end `stable` (gate 6 of `/review-code`, from this bar up). The spread of resource counts is reported, not graded: this rubric pins no threshold.
- **A7 — what is not reviewed.** The `CALIBRATION` block is your prose, read by no tool. The hidden equivalence check of the prose item runs only in the grader container (QPLAN §19.0), which the learner starts from their own terminal (the chapter's §2 gives the line; the guard refuses it in this session, so never run or name it here). The chapter's rule is one run per item, after the statement is final, and the first run is the one reported (as with a first try). Record the verdict word the learner reports from that first run (`faithful`, `strong`, `weak`, `vacuous`, `undecided`, `mismatch` or `context`) as reported, with the outcome words they paste, or `not run` without one; a later run, if the learner reports one, is recorded beside it as later and anchors nothing. Never record the check as passed or failed yourself; C5 says what a reported word anchors.

## Code-review focus — band: "design-judgment"

At this bar, the conventions of the earlier bars bind (the proof reads, the induction follows the recursion it unfolds, library and layer facts are called by name, an invariant or measure is named where it is used), plus design judgment: where each fact lives (a `requires`, an invariant, a ghost record, a helper's statement) is a choice the code defends, and the proof is stable under seeds (A6).
- **C1 — the one helper earns its place (H1v, H2d, H3v, H4d, H4v, H5d).** Each item's `HELPERS` area holds at most one lemma or proof fn of your own (a spec fn that only names a sub-term is a definition, not a lemma), with a statement of its own that the main proof calls. A helper that restates the item's goal, or one Probe D shows dead, is a finding. Two helpers for one item is a finding at this bar (the tier allows one), cited at `file:line`.
- **C2 — the induction is the definition's (H2d, H3v, H4d, H4v).** The recursive call shrinks the argument the unfolded definition shrinks, and the `decreases` (shipped or yours) names it. If A2 is green, the measure is sound: a finding here is about reading, cited at `file:line`, never about correctness.
- **C3 — the ghost record says what the code did (H1v).** The loop's ghost state names one value per step (the borrows, or an equivalent record), it is updated where the code updates its own state, and the invariant relates each written limb to it. A ghost value that no invariant or call uses is dead (Probe D on its update). Exec code reads no ghost value (the verifier refuses that, so A1 is the anchor).
- **C4 — the invariant is a generalization, stated once (H5d).** The loop's invariant is a statement about every step, from which the postcondition follows at the exit; each product step under nonlinear arithmetic off is a named library call or a layer lemma, never an `assume`. The loop runs from the low limb with the place value in a variable, as the prompt asks: A5's form line checks that the loop's counter only steps up, that every index of `s` the body reads adds the counter (a loop that counts up but reads `s` from the top fails it) and that the loop computes `v`, so the anchor of a wrong direction is A5's `form loop-dir:up not met` line, a finding at grade 1; a compiled `ToNat` call is A5's `form no-call:ToNat not met` line, the same grade. The form cannot follow an index through a helper or into another sequence: a loop that reads the limbs from the top that way is the same finding, cited at `file:line`. If A2, A5 and A6 hold and the limbs are read from the low end, the invariant is right: do not invent a flaw in its form.
- **C5 — the prose statement says what the prose says (H3v).** The statement has the name and parameters the block gives, its `requires` cover every case the prose covers (not only sequences of one length, not only canonical ones), its `ensures` is the prose's conclusion, and the witness's call meets every `requires`. A narrower `requires` is a finding only when Probe E exhibits the case; a stronger or different `ensures` is a finding when it says something the prose does not, quoted beside the prose. A reported verdict (A7, the first run) anchors this line: `strong`, `weak`, `vacuous` or `mismatch` is a finding at grade 2, whatever Probe E shows, stated with the verdict word and the outcome words as reported (they name the side and the direction of the difference), and the statement is then read for where it differs, quoted beside the prose; never guess or state the author's statement. `undecided` anchors nothing: the reader decides it, by the prose, Probe E and the reading above. `faithful`, `context` (the learner's own definitions did not verify there: the gate's anchors rule) and `not run` leave the line to the reading above. If the use site, the witness and the gate all pass, Probe E finds no case and no reported verdict anchors a finding, the statement stands: do not invent a flaw.
- **C6 — where the spec lives (H1v, H5d).** A fact a caller needs is in an `ensures`; a fact the body needs about its inputs is in a `requires` already shipped or in a layer's validity predicate; a fact only the proof needs is in an invariant or a helper. Repeating a layer's predicate inline instead of calling it (`wf`, `Valid`, `Canonical`) is a reading note, cited at `file:line`.
- **C7 — automation used on purpose.** A `broadcast use`, a `reveal` or a library call is scoped to the body that needs it and carries a short reason; a group or reveal that Probe D shows unneeded is a reading note. No `nonlinear_arith` in the Verus library item (H4v) and none in the exit: A5 checks both blocks' form lines. The `{:disableNonlinearArithmetic}` attribute on `Q13_Library`'s `module` line stays as shipped: the anchor is A4's `scripts/specfreeze --check Q13` with no `freeze-lever-removed` finding (A5's strict report prints the same as a `lever:` line); a removed attribute is a finding at grade 1, whatever the verifier says.
- **C8 — no dead code.** No commented-out experiments and no unused helpers in your own lines. The prediction slot and its answer stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.
