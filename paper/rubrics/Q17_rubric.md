# Q17 rubric — Practice III-B

> **Consumers:** `/grade-paper Q17` (B1, B2; then `--post` on B1), `/review-code Q17` (Gate, Code-review focus) and you, after `/contract Q17` (the audit debrief). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **No prediction:** Q17 has no prediction item, so this file may be read at any time; it names no invariant, lemma or statement of the module's problems.

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q17_solutions.tex  sha256 19f64bd932a2ee7f94712d6aadacde63632caa654f95cdc56cb4723d473f8dbd — the written track's reference (B1, B2)
paper/Q17_problems.tex  sha256 fb770a9c6d491113331fb9f0461e2941a74eed95e92dfe9d2aeef1fdbbb21bf7 — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q17_PracticeIIIB/std/Q17_PracticeIIIB.dfy  sha256 c9c1c0d48d8700b348aacde2821134472b380756ced872872e64a92f9b4e4d7a — H1's half of the code review
Solutions/dafny/Q/Q17_PracticeIIIB/std/Q17_Vcgen.dfy  sha256 0254ac116d02ce242f0df6e8a8b21f2d50f3b44b6e414103d32105c0dc45a751 — H3's half of the code review
Solutions/verus/q/q17_practice_iiib/src/perm.rs  sha256 b51cbb4143d2c23ce5269bf7de4123673bd3bad5bb4d1f23b500cd297e5c412b — H2's half of the code review
Solutions/dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy  sha256 02579980b6c04bbfb2432c89ba9b8976b3f17afe275555ff6f59b8f6ff868df3 — the delivery the audit debrief compares with

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck`, one solver job at a time; the output is pasted verbatim. A verified probe or a passing executed check confirms a claim (verdict kind 1). An error verdict alone refutes nothing: a blueprint's formula is shown false only by a verified refutation at a concrete instance (Probe A), an executed check at a concrete run (Probe B), or the learner's own verified proof contradicting it (`--post`).

- **Probe A** (B1 (a)–(c), a claimed fact about sequences or multisets, Dafny). Instantiate the claim at one concrete instance, negate it, and ask the verifier to prove the negation:

  ```dafny
  module ProbeA {
    // A claimed fact about sequences, negated, at one concrete instance.
    lemma AtInstance()
      ensures !(multiset([5, 3, 1]) == multiset([1, 3]))   // <- the claim at the instance
    {
    }
  }
  ```

  Save it as `instructor/scratch/probe.dfy` and run `scripts/vcheck --module Q17 instructor/scratch/probe.dfy`. **Verified**: the claim is false at that instance, a verified refutation. **An error**: the instance does not refute it; that is not a confirmation either. As shipped (the placeholder claim) it verifies; with a true claim in its place it fails at the postcondition. Choose the instance the claim is about (a sequence, an index, an element), never one of the module's items.
- **Probe B** (B1 (d)–(e), a claimed run of the W2 language: a counterexample to a statement, or a witness's run). Copy `dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy`, as shipped, to `instructor/scratch/probe.dfy`, and append inside its module, before the module's closing brace, a test method that executes the run:

  ```dafny
    method {:test} ProbeB()
    {
      var c := Assign(1, Plus(Var(0), Const(5)));   // <- the claimed command
      var q := Lt(Var(1), Const(9));                // <- the claimed postcondition
      var s: State := (y: nat) => 0;                // <- the claimed start state
      var r := Exec(c, s, 1);                       // <- the claimed fuel
      expect r.Done?;
      expect Holds(q, r.s);                         // <- each fact the claim needs, one per expect
    }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. **`1 passed`**: every `expect` held on that run. **`FAILED`**: the first false `expect` is named; that fact does not hold there. `Exec`, `Holds`, `Pre`, `Vcs` and `Update` are compiled, so a run, a precondition and each side condition can be evaluated in one state; validity in every state cannot, and stays the verifier's (or the argument's). As shipped the placeholder run passes.
- **Probe C** (B2, the card pin). `sed -n '5507,5533p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B2 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review, with its file's `module` line and every declaration it calls (for the crate, its `use` lines), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, renaming the module (Dafny) so it does not clash with the exercise's; delete the one line in question; run `scripts/vcheck --module Q17 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.
- **Probe E** (Gate A6, stability). `scripts/vcheck --brittleness dafny/Q/Q17_PracticeIIIB/std` and `scripts/vcheck --brittleness verus/q/q17_practice_iiib`: the summary line ends with `stable`. A `differs` line names each symbol whose verdict varies.
- **Probe F** (Audit debrief D2, the statement freeze of the run). `scripts/specfreeze --against research/q17_statements.dfy dafny/Q/Q17_PracticeIIIB/agent/Q17_AgentMetatheory.dfy` reports no change; `git log --format=%H -1 -- research/q17_statements.dfy` names a commit older than the run's first edit.

## B1 — The blueprint of H1 and H3 (informal proof first; dimensions: statement-fidelity, induction-soundness, case-exhaustiveness, blueprint-quality, gap-accounting)

The grade is the minimum over the five dimensions; at least 3 on every one unlocks formal work. A blueprint that differs from any other correct one is correct: grade its own invariant, lemmas and statements.

### statement-fidelity
- **SF.a** — H1's invariant, with the class's methods, gives every postcondition the trait states: each `Model` equation, the minimum of `ExtractMin`, `Valid()` again, and the frame (`fresh(Repr - old(Repr))`), and the constructor can establish it from nothing. A conjunct no method needs is a reading note; a postcondition no conjunct supports scores ≤2, quoting the postcondition beside the invariant.
- **SF.b** — H3's statement in words matches the item's prose: what it assumes of the side conditions, of the start state and of the run, and what it concludes, for every command, postcondition, state and fuel. A statement that is stronger than the prose (claims more than partial correctness) or weaker (a condition the prose does not give, a conclusion it does not draw) scores ≤2, quoting the clause beside the prose's words.
- **SF.c** — every invented lemma's statement, and every H3 statement, is true. A false one scores ≤2 only with Probe A's verified refutation or Probe B's executed run pasted; one that cannot be refuted at small instances stands.

### induction-soundness
- **IS.a** — every loop invariant is stated as a formula (each conjunct, bounds included), and (c) shows its three duties: true on entry, kept by one iteration (with the step's effect on the array named), and with the negated guard giving what the method needs after the loop. An invariant in words only scores ≤2 on this dimension, quoting the words.
- **IS.b** — every recursive lemma names its measure, and each recursive use is at a strictly smaller instance. H3's statements are proved by the metatheory run, not by you: B1 is not graded on their proofs, only on whether (d) says what each statement claims.
- **IS.c** — a fact is used only where it holds: an invariant at a state the loop never reaches, a side condition in a state the statement does not assume it in, or a lemma whose `requires` the step has not established, scores ≤2 with the step quoted.

### case-exhaustiveness
- **CE.a** — H1's frames name every method and both of `Insert`'s paths (with and without growth), and every object each writes; a missing path is a gap (3) when declared, ≤2 when the blueprint claims completeness without it, with the path named.
- **CE.b** — H3's (d) covers the run that ends and the run that does not, and (e) gives a concrete command, postcondition, state and fuel for each claim of failure (Probe B can execute it). A claimed failure with no instance scores ≤2 on this dimension.

### blueprint-quality
- **BQ.a** — the operational test: someone could formalize H1 without inventing a statement. Each invented lemma has a name and an exact `requires`/`ensures`; each step names the lemma or fact it uses. A step that says "by the invariant" with no conjunct named scores ≤2, quoting it.
- **BQ.b** — two to four invented lemmas for H1, or one invariant carrying the problem, each used in (c). A lemma no step uses is a reading note; a lemma that restates a method's own postcondition is a finding at 2, quoted beside the shipped clause.
- **BQ.c** — H3's statements are written so that the contractor needs no further statement from you to start (each a formula over the W2 language's own names, with one `ensures` per lemma); a statement given only in words in (d) scores ≤2 on this dimension.

### gap-accounting
- **GA.a** — declared gaps are honest and specific (score-3 territory, never lower for being declared). An undeclared gap confirmed by Probe A or B, or by the plan's own contradiction quoted, scores ≤2.
- **GA.b** — `--post` re-scores blueprint-quality only, against the learner's verified files and the delivered proofs: where a proof needed a lemma, a stronger invariant or a statement the blueprint lacks, record it in the diff table; it lowers the post score only where the blueprint claimed completeness at that step.

## B2 — Paper card 12.12 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B2 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question, and the closing line names one trusted part of this module. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 5507–5533). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, a time, a cost) scores ≤2 only by naming the field and the quoted absence.
- **CF.e** — figures stay attached to what the range attaches them to: a defect count given to the wrong layer of the table contradicts the table, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short. The closing line is graded for an argument, not for a particular answer. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q17`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q17` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q17_PracticeIIIB/std` and `scripts/vcheck --gate verus/q/q17_practice_iiib` each exit 0 and print only the summary line. The Dafny unit reaches it only after the metatheory run's proofs are copied back into `Q17_Vcgen.dfy` (its header's step 3): until then each of your statements is a counted hole, as it should be.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q17_PracticeIIIB/std` and `scripts/vaudit verus/q/q17_practice_iiib` report no finding.
- **A4 — statements unchanged.** `scripts/specfreeze --check Q17` reports no finding: every shipped signature, `requires`, `ensures`, frame and `decreases`, the given trait's and the W2 language's definitions included, is as shipped. What you added (helpers, your statements) is new, so the freeze does not see it (C2 and C6 read it).
- **A5 — every shipped check uncommented, as shipped.** `scripts/firsttry.sh Q17 --report --strict` exits 0: `Peek` and `ArrayPQCheck` (H1), `ring_check` (H2) and `CountCorrect`'s three lines (H3) uncommented, no hole left, no `lever:` line. The report counts commented lines, not their text: `git diff` of each check against the shipped file shows only removed comment markers, and a check edited as it was uncommented (a weaker `ensures` on `Peek`, a dropped `assert`) is a finding at grade 1, whatever the gate says.
- **A6 — stable under seeds.** Probe E: both sweeps end `stable` (gate 6 of `/review-code`). The spread of resource counts is reported, not graded: this rubric pins no threshold.
- **A7 — what is not reviewed.** The agent file is reviewed in the audit debrief, not here. B1's grade is `/grade-paper`'s, not this review's. The hidden check of `VcSound` (H3d) runs only in the grader container, which the learner starts from their own terminal after the metatheory run and their AUDIT (the chapter's §4 gives the line; the guard refuses it in this session, so never run or name it here). The chapter's rule is one run, after the statement is final, and the first run is the one reported (as with a first try). Record the verdict word the learner reports from that first run (`faithful`, `strong`, `weak`, `vacuous`, `undecided`, `mismatch` or `context`) as reported, with the outcome words they paste, or `not run` without one; a later run, if the learner reports one, is recorded beside it as later and anchors nothing. Never record the check as passed or failed yourself; C6 says what a reported word anchors.

## Code-review focus — band: "library-pr"

At this bar, the conventions of the earlier bars bind (the proof reads, the induction follows the recursion it unfolds, an invariant is named where it is used, where each fact lives is defended, the proof is stable under seeds), plus the library pull request's: documentation on every declaration you wrote, helper factoring, trigger hygiene, no needless automation, golf only where it clarifies.
- **C1 — documented.** Every lemma, predicate, helper method and proof fn you added carries a comment above it (`///` in Verus; `//` or `/** */` in Dafny) that says what it states or does, in one or two lines. A missing or wrong comment (one that says something the declaration does not) is a finding, cited at `file:line`, the comment quoted beside the statement.
- **C2 — factored.** Each invented lemma or helper is used, states a fact or does a step its caller cannot get in one line, and does not restate a method's own contract; none is dead (Probe D on its call). Two to four lemmas for H1 is the tier's range: more is a reading note, not a finding, when each earns its place.
- **C3 — the invariant (H1d).** `Valid()` holds each fact once, each conjunct is used by some method (Probe D on the conjunct), and the class's methods restate the trait's contracts exactly as shipped (A4). If A2 is green the implementation is sound: a finding here is about reading, cited at `file:line`.
- **C4 — frames (H1d).** Each method's loop says what it writes, and each new object enters `Repr` where it is created. A loop with no frame of its own that verifies anyway is a reading note; a `Repr` that grows by an object no method wrote is a finding, cited at `file:line`.
- **C5 — permissions (H2v).** Each operation borrows the one permission it changes, mutably and in place, and moves no permission out of `perms` and back; the assertion that carries `wf` across the write names the slots it is about. Read `push_back`'s growth: every element moves exactly once, in order. If A2 and A6 hold, do not invent a flaw in the order of the moves.
- **C6 — the statements (H3d).** Each statement you wrote is the prose's: general over commands, postconditions, states and fuels (a statement specialized to `Count`, or to a class of commands the prose does not name, is a finding at grade 1, quoted beside the prose), one `ensures` per lemma, and its witness is a call whose `requires` hold at a run that ends (Probe B can execute the run). A statement the contractor proved in one or two lines is read against the prose with special care. A reported verdict on `VcSound` (A7, the first run) anchors this line: `strong`, `weak`, `vacuous` or `mismatch` is a finding at grade 2 (a specialized statement stays at grade 1), stated with the verdict word and the outcome words as reported, and the statement is then read for where it differs, quoted beside the prose; never guess or state the author's statement. `undecided` anchors nothing: the reader decides it by the prose and Probe B. `faithful`, `context` and `not run` leave the line to the reading above, and the other statements are read as above.
- **C7 — automation used on purpose.** A `reveal`, a `broadcast use` or a scoped `nonlinear_arith` step is scoped to the body that needs it and carries a short reason; one that Probe D shows unneeded is a reading note. Triggers you write are on terms the proof instantiates.
- **C8 — no dead code.** No commented-out experiments and no unused helpers in your own lines; the shipped checks stay uncommented.

## Audit debrief — after /contract Q17

Questions for you, after the metatheory run. Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — committed first.** Probe F's second command names the commit of `research/q17_statements.dfy`, and it precedes the run. A freeze reference written after the run is no reference.
- **D2 — statements unchanged.** Probe F's first command reports no change; paste it. Any change is a broken contract, whatever else the run did.
- **D3 — the allowlist held.** `git diff --stat` after the run lists only the agent file (and `.claude/state/contract-allowlist`).
- **D4 — as strong as the prose.** For each statement, compare it with the item's prose and with B1 (d): a statement the contractor proved too easily (a short proof, a proof that never uses a hypothesis you thought essential) is a finding; say which hypothesis was unused (Probe D on a copy) or which conclusion was weaker than meant.
- **D5 — stop and report.** If a statement was false or unprovable, did the contractor stop and say so, and leave the statement as written? A delivery that "proved" it by any other route breaks A3's audit or D2's freeze: name which.
- **D6 — the helpers.** List each lemma the run added under HELPERS; for each, is it a fact you would have stated (B1 (d)'s optional statements), and does `scripts/vaudit` report none of them? A helper with a trust escape is a finding whatever the gate says.
- **D7 — re-verify after every edit?** Count the edits and the verifier runs between them in the transcript; name the first stacked edit.
- **D8 — which moment earns a rule?** Name one transcript moment that deserves a rule in your contract's v2 (Q18), in the rule format of `CLAUDE.md`'s contract slot.
