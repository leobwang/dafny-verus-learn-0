# Q07 rubric — Internals I: proof engineering, translation

> **Consumers:** `/grade-paper Q07` and `/grade-paper Q07 --post` (B1–B3), `/review-code Q07` (Gate, Code-review focus), and you, after `/contract Q07` and the local replay (the audit debrief) and after you fill the port's `FIDELITY` block (its self-review). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q07 --check` has recorded every Q07 prediction and T1's first try (the test-out is closed book).

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q07_solutions.tex  sha256 dc773b9e09660308e64394444c932a8b3159f631f603e2649d5ec65c3f7cac69 — the written track's reference (B1–B3)
paper/Q07_problems.tex  sha256 65510730ac925364a9af7b2994bbda5faf81ab11b6bd7da52bf6bd69155135c2 — the problems these lines grade, with the card's pinned range
Solutions/dafny/Q/Q07_InternalsI/std/Q07_InternalsI.dfy  sha256 b6c79eed1c53091e63b6c65913ce98a11fb8e9762995bb282984700a0a7db3b0 — the formal reference B1 (a) precedes (H3d), and the Dafny half of the code review
Solutions/verus/q/q07_internals_i/src/lib.rs  sha256 03bc9ba14eff1e6aec285c82b25ee9be857198ceac6c0c42a6fda1c9dd3faffb — the formal reference B1 (b) precedes (H5v), and the crate-root half of the Verus code review
Solutions/verus/q/q07_internals_i/src/port.rs  sha256 15aca44522426f9ee180588ae28c4f7b1b3f439dbe61b76a860c83aa457c538c — the port half of the Verus code review
Solutions/dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy  sha256 65d48e4ca684375550e335090e51cce85bfc23ed0cd54235e3b7c419029161af — the reference delivery behind the audit debrief (Dafny)
Solutions/verus/q/q07_internals_i/src/agent.rs  sha256 e01f8ae3588e0412e3b15853671f536e441c6e4d2cf2d0de44a2b143b5477563 — the reference delivery behind the audit debrief (Verus)

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck` (or `scripts/vaudit` and `scripts/specfreeze` where named), one solver job at a time; the output is pasted verbatim. The program text below is the problems file's or the given layers'; the lines marked `<-` are where your own statements go. A verified probe confirms a step (verdict kind 1). An error verdict alone refutes nothing: a flaw is exhibited by an executable check (a `@Test` method with `expect`, run with `scripts/vcheck --test`), by a verified refutation, or, for a claim about what an instrument reports, by that instrument's pasted output.

- **Probe A** (B1 (a), splice template: does the chain close as written?). In `instructor/scratch/probe.dfy`, filled from your blueprint alone:

  ```dafny
  module {:disableNonlinearArithmetic} ProbeA {
    import opened QG_L1_BigNat

    // One bodyless lemma per fact your blueprint names, with the parameters its
    // statement needs: its statement only, exactly as you wrote it.
    lemma Fact1(a: int, b: int, c: int)
      requires true          // <- the fact's hypotheses
      ensures true           // <- the fact's conclusion

    // The target under a probe name. Its body is your blueprint, transcribed: each
    // fact as a call at the arguments you name, in your order, and only the asserts
    // you name.
    lemma DigitStaysLimb(r: nat, x: nat, d: nat)
      requires 0 < d < BASE && r < d && x < BASE
      ensures (r * BASE + x) / d < BASE
    {
                             // <- your calls and asserts
    }
  }
  ```

  Run `scripts/vcheck --module Q07 instructor/scratch/probe.dfy` (the module's given layers; the probe's own `module` line keeps nonlinear arithmetic off, as in the exercise file; the count includes the layers' own tasks). Verified, with one hole per pasted fact and no other: the chain closes, given those facts. That says nothing about whether each fact is true: Probes A″ and A‴ judge that. A resolve error on a fact exactly as written: that statement is not formalizable as written (paste the error). A verification error: a gap until Probe A″ exhibits a false step. A reference chain spliced into this template verified on the pins (Dafny 4.11.0); as shipped (`requires true`, an empty body) the template fails at the target's postcondition.
- **Probe A′** (B1 (b), splice template). In `instructor/scratch/probe.rs`, your chain with L3's lemmas and `vstd::arithmetic`'s called by name and every other fact pasted as a helper:

  ```rust
  use vstd::prelude::*;
  use vstd::arithmetic::mul::*;
  use vstd::arithmetic::div_mod::*;
  use qg_bignat_l4::*;

  verus! {

  // One helper per fact your blueprint names that is not a lemma of L1-L4 or of
  // vstd::arithmetic, with the parameters its statement needs: its statement only.
  proof fn fact1(a: int, b: int, c: int)
      requires
          true,  // <- the fact's hypotheses
      ensures
          true,  // <- the fact's conclusion
  {
      #[verifier::proof_note("ProbeA2")] assume(false);
  }

  // The target under a probe name. Its body is your blueprint, transcribed: each fact
  // as a call at the arguments you name (L3's and vstd's lemmas by name, your own as
  // fact1, ...), in your order, and only the asserts you name. No nonlinear_arith.
  proof fn drop_one_more(v: nat, n: nat)
      ensures
          v / weight(n + 1) == (v / weight(n)) / BASE,
  {
      // <- your calls and asserts
  }

  } // verus!
  ```

  Run `scripts/vcheck --module Q07 instructor/scratch/probe.rs`. Verified, with one hole per pasted helper: the chain closes, given those helpers. A `precondition not satisfied` at a call: a hypothesis of that fact is not established where the chain uses it (a gap until Probe A″ shows the hypothesis false there). A reference chain spliced in verified on the pins (Verus 0.2026.09.27.3cf1832); as shipped the template fails at the target's postcondition.
- **Probe A″** (B1, a step or a fact claimed false). A test file stands alone, so it carries copies of the definitions it needs:

  ```dafny
  module ProbeStep {
    const BASE: nat := 18446744073709551616

    // BASE to the power n (L3's weight; L1's Pow).
    function Weight(n: nat): nat
    {
      if n == 0 then 1 else BASE * Weight(n - 1)
    }

    @Test
    method StepOnExample()
    {
      var a: int, b: int, c: int := 0, 0, 1;   // <- the concrete values
      expect true, "the step fails";           // <- the step's claim, at those values
    }
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. For a fact, the claim is "its hypotheses imply its conclusion" at the values. `FAILED` with the message: the claim is false there, a confirmed flaw. `PASSED`: the claim holds there, and nothing is refuted. As shipped (`expect true`) it prints `1 passed, 0 failed`. Dafny's `/` and `%` agree with Verus's specification division on the naturals these problems use, so a Verus step is checked here too.
- **Probe A‴** (B1, is a named arithmetic fact true?). In `instructor/scratch/probe.dfy`, one fact per run, in a module with Dafny's default arithmetic (nonlinear arithmetic on), the parameters renamed as the fact needs:

  ```dafny
  module ProbeFact {
    // One fact per run: its statement exactly as your blueprint gives it, with an
    // empty body, in a module with Dafny's default arithmetic (nonlinear on).
    lemma Fact(a: int, b: int, c: int)
      requires true          // <- the fact's hypotheses
      ensures true           // <- the fact's conclusion
    {
    }
  }
  ```

  Run `scripts/vcheck instructor/scratch/probe.dfy`. Verified: the fact is true. A failure or an out-of-resource verdict refutes nothing (the nonlinear solver is incomplete, and a quotient defeats it often): only Probe A″ exhibits a false fact.
- **Probe B** (B2, what each instrument reports). One edit per run, each language in a file of its own. The snapshot, as committed before any edit, in `instructor/scratch/frozen.dfy`:

  ```dafny
  module {:disableNonlinearArithmetic} Shelf {
    function Doubled(c: nat): nat { c + c }

    // ### FROZEN
    lemma PairBelow(a: nat, b: nat, c: nat)
      requires a < c && b < c
      ensures a + b < Doubled(c)
    {
      assert a + b < c + c;
    }
  }
  ```

  and in `instructor/scratch/frozen.rs`:

  ```rust
  use vstd::prelude::*;

  verus! {

  pub open spec fn doubled(c: nat) -> nat {
      c + c
  }

  // ### FROZEN
  pub proof fn pair_below(a: nat, b: nat, c: nat)
      requires
          a < c,
          b < c,
      ensures
          a + b < doubled(c),
  {
      assert(a + b < c + c);
  }

  } // verus!
  ```

  The file under test, `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, is the problems file's code in that language with the one edit applied. Run `scripts/vcheck --module Q07 --gate instructor/scratch/probe.<ext>`, then `scripts/specfreeze --against instructor/scratch/frozen.<ext> instructor/scratch/probe.<ext>`, then `scripts/vaudit instructor/scratch/probe.<ext>`. The three outputs are the answer key to "does the gate pass?", "does the freeze report a change?" and "does the audit report a finding?" for that edit; whether an edit keeps "change no statement", and which contract line an edit breaks, are settled by reading it against the file and against the agent file's CONTRACT block. The shipped code with no edit passes all three on the pins, in each language.
- **Probe C** (B3, the card pin). `sed -n '795,825p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B3 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step or a fuel count). Copy the declaration under review, with its file's `module` line and imports (for a crate file, its `use` lines, `use qg_bignat_l4::*;` among them), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`; delete the one line in question, or lower the one fuel count by one; run `scripts/vcheck --module Q07 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Verified with the lower count: the count was more than the proof needs. Not verified: it is needed.
- **Probe E** (Code-review focus, a library fact you re-proved). A scoped search of the pinned library source for the shape of your helper's conclusion, pasted with its hits: Dafny, `unzip -p .toolchain/dafny-4.11.0/dafny/DafnyStandardLibraries.doo program | grep -n -A4 '<pattern>'`; Verus, `grep -rn -A6 '<pattern>' ~/.cargo/registry/src/*/vstd-0.0.0-2026-09-20-0158/arithmetic/` (the `vstd` that `VERSIONS.md` pins). A hit whose `ensures` gives your helper's conclusion under hypotheses your call site meets is the evidence for C1; the finding quotes the search, never the lemma's name alone.

## B1 — Two quotients, every step named (informal-proof-first)

### statement-fidelity
- **SF.a** — (a) proves the lemma as stated: all three hypotheses available, the strict `<` of the postcondition, `/` the integer quotient. (b) proves the stated equation for every `v` and `n`, with no hypothesis added (such as a positive `v`). A dropped or added hypothesis scores ≤2 only with values at which the restated claim and the lemma differ, shown by Probe A″.

### induction-soundness
- **IS.a** — B1 has no induction and no loop; this dimension grades the chain instead. Each step is an instance of a fact the answer names, used at arguments the answer gives, and every hypothesis of the fact is shown to hold there. A hypothesis that holds but is not argued is a gap (3).
- **IS.b** — every fact the chain names is true as stated, and every step's claim holds at its arguments. A score ≤2 exhibits values at which a named fact's hypotheses hold and its conclusion fails, or at which a step's claim is false (Probe A″, `FAILED`). Probe A‴ verifying confirms a fact; its failing refutes nothing.
- **IS.c** — a fact's hypotheses are met as the fact states them: a non-strict bound does not meet a strict hypothesis, and a divisor's positivity is a hypothesis like any other. A use whose hypothesis is true but not derived in the chain is a gap (3); a fact restated with a weaker hypothesis that makes it false scores ≤2 with Probe A″.

### case-exhaustiveness
- **CE.a** — the chain covers every input the `requires` allow (in (a) every `r`, `x`, `d`, `d = 1` and `r = 0` included; in (b) every `v` and `n`, `n = 0` and `v = 0` included), with no case split needed. If the answer splits into cases, each case states its condition and its argument holds on every input in it. A score ≤2 exhibits an input that no case covers, or on which a case's argument fails (Probe A″).

### blueprint-quality
- **BQ.a** — every fact is named by its statement (an equation or inequality between named quantities, with its hypotheses) and attributed: a library fact by what it states (its name optional), a lemma of L3 by its name, a new lemma with its full `requires` and `ensures`, or a declared gap. The operational test is Probe A (Probe A′ for (b)) filled from the blueprint alone, with nothing invented: if it verifies with one hole per pasted fact, do not invent a flaw. A Probe A that does not verify is a gap (3) unless Probe A″ exhibits a false step.
- **BQ.b** — (a) says which steps the solver takes without a named fact, with nonlinear arithmetic off, and why. A step claimed free that needs a named fact (Probe A without the fact fails, with it verifies) is a gap (3), recorded for the `--post` diff. A step claimed to need a named fact that the solver takes unaided is a reading note, never below 3: calling a true fact is harmless.
- **BQ.c** — (b) names every hypothesis of each fact and how it is met, from what the opaque `weight` lets the solver see. A missing fact that Probe A′ shows needed (a `precondition not satisfied` at a call, gone once the fact is added) is a gap (3), never a flaw.

### gap-accounting
- **GA.a** — declared gaps score 3. An undeclared step that is false at an exhibited input is a flaw (≤2). An undeclared step that is true but unjustified is recorded as a gap (3), never as a flaw.

## The --post pass

Runs once `scripts/vcheck --gate dafny/Q/Q07_InternalsI/std` exits 0 (H3d is in that unit), and again for (b) once `scripts/vcheck --gate verus/q/q07_internals_i` exits 0 (H5v). Re-score `blueprint-quality` of B1 only, with your verified `DivLimbStep` and `lemma_div_weight_succ` as the oracle:
- **BQ.d** — diff the blueprint against the proofs: the facts it named against the calls and assertions each proof makes, the arguments of each use against the call's, and the steps it called free against what the proof left to the solver. Record each fact a proof needed that the blueprint did not name, and each named fact no proof used.
- **BQ.e** — record whether formalizing forced a change the paper missed (an extra fact, a different argument, a hypothesis the chain had not derived, an order of factors). A blueprint whose chain survived formalization scores 4; each missed fact is a finding at 3, never lower unless the blueprint's step was false at an exhibited input.

The gradebook gets a `paper-post` row with the new `blueprint-quality` score.

## B2 — What a refactor's dashboard sees (concept; dimension: correctness)

### correctness
- **CO.a** — each claim of (a) about the gate, the freeze and the audit, per edit and per language, agrees with Probe B's output for that edit. A claim scores ≤2 only with Probe B's pasted output that contradicts it. A claim the answer hedges ("probably") is graded as the claim it makes.
- **CO.b** — each claim of (a) about "change no statement" agrees with the edit, read against the shipped file: a statement is a declaration's signature with its `requires` and `ensures`, in any section. A score ≤2 quotes the statement the claim misreads, before and after the edit.
- **CO.c** — (b)'s edit changes no statement, passes all three instruments (Probe B, all three outputs pasted) and breaks a line of the Dafny CONTRACT that the chapter quotes. An edit that an instrument flags, that changes a statement, or that breaks no contract line scores ≤2 with the pasted output or the quoted line beside the edit. An edit the answer did not run but that passes Probe B is correct: do not invent a flaw.
- **CO.d** — (b) names the contract line by its words and an artifact that shows the breach. Naming an instrument as that artifact scores ≤2 only with that instrument's pasted output on (b)'s own edit (Probe B).

## B3 — Paper card 02.8 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B3 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 795–825). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cost, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a figure given to the wrong system (the method, a few-shot baseline, another prover), the wrong benchmark, the wrong metric (which pass@K) or the wrong comparison contradicts the table or sentence it comes from, and CF.c applies. So does a step of the method given to the wrong component (the verifier, the search, the critique).
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q07`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q07` reports both units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q07_InternalsI/std`, `scripts/vcheck --gate verus/q/q07_internals_i` (the crate root and `src/port.rs` together) and `scripts/vcheck --gate dafny/checks/Q07_checks.dfy` each exit 0 and print only the summary line. After both contract runs, `scripts/vcheck --gate dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` and `scripts/vcheck --gate verus/q/q07_internals_i/src/agent.rs` do too.
- **A3 — audit.** `scripts/vaudit dafny/Q/Q07_InternalsI/std`, `scripts/vaudit verus/q/q07_internals_i` and `scripts/vaudit dafny/checks/Q07_checks.dfy` report no finding; after both contract runs, `scripts/vaudit dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` and `scripts/vaudit verus/q/q07_internals_i/src/agent.rs` report no finding (Q07 pins no `.audit` file: a delivered agent file has no attribute and no assumption, so an empty report is the check).
- **A4 — the suites run.** `scripts/vcheck --test dafny/checks/Q07_checks.dfy` and `scripts/vcheck --test verus/q/q07_internals_i` pass every test, H7's uncommented differential suite included (as shipped the crate has no live test, and an empty test set never passes).
- **A5 — statements unchanged.** `scripts/specfreeze --check Q07` reports no finding. It accepts added `requires` and `ensures` clauses on `from_u128` in `verus/q/q07_internals_i/src/port.rs` (an open statement: `expected/Q07.freeze` lists it under `open_specs`) and a body for `from_nat_mirror` in the same file (an open body), and nothing else.
- **A6 — slots, first tries, shipped lines and forms.** `scripts/firsttry.sh Q07 --report --strict` exits 0: every prediction filled, recorded and enabled; the test-out blocks written; every shipped commented check uncommented (H7's use-site check and suite); every `form:` line met (H5 without `nonlinear_arith`, H6 and H7 without `*`, `/` or `%` in code; X1v and X2v likewise once the exit is repaired); and, after the exit's scored run, the exit files repaired.
- **A7 — what is not reviewed.** The card demos under `specimens/Q07/card-*` are red by design (their failures are pinned) and are never finished or reviewed. The check unit's mutant evaluation prints and expects nothing; its lines are the `FIDELITY` block's evidence, not code under review. The `FIDELITY`, `REVIEW`, `COMPARISON`, `CALIBRATION` and `EXPLAIN-BACK` blocks are your prose, read by no tool and not code-reviewed (`FIDELITY` has its own review below). The agent files are the contractor's work and the debrief's. A2 and A3 skip the specimens. No brittleness gate applies at this bar.

## Code-review focus — band: "library-conventions"

At this bar, the conventions of Dafny's standard library and of `vstd`, read from their sources, bind your own lines; findings about a missed library fact are delivered as search queries (Probe E), never as lemma names.
- **C1 — library facts called, never re-proved (H2d, H3d, H5v; X1d and X2v once repaired).** Each arithmetic step that a lemma of `Std.Arithmetic` or `vstd::arithmetic` states is a call of that lemma, or of a lemma of the given layers. A helper of your own whose conclusion such a lemma gives, under hypotheses your call site meets, is a finding at this bar, evidenced by Probe E's pasted search. If Probe E finds no such lemma, the helper stands: do not invent a flaw.
- **C2 — names in the library's grammar.** Any name you introduced follows the convention of its file, which follows its library: a Verus proof fn `lemma_<what it states>` in snake case, as in `vstd`; a Dafny lemma in UpperCamelCase naming what it states (the standard library prefixes `Lemma`; the course's files do not, and either reads). A name that says how or when instead of what (`Helper1`, `Step2`, `Fix`) is a finding. If you introduced none, there is nothing to review here: do not invent a flaw.
- **C3 — fuel and reveals scoped to the proof that needs them (T1d, T1v, H1d, H4v, H9v).** A fuel attribute sits on the one lemma that needs it, a `reveal` or `reveal_with_fuel` inside the one proof that needs it, never on a function, a module or a lemma that does not. A count that Probe D shows larger than needed is a reading note, never below 3; a scope wider than one proof is a finding only when Probe D verifies the narrower one.
- **C4 — bit-vector facts on words, inside proofs (H6v, H7v; X1v once repaired).** Each `by (bit_vector)` assertion mentions only fixed-width terms and sits in a `proof { }` block, and the code carries no `*`, `/` or `%` (A6's form lines). An assertion Probe D shows dead is a finding at this bar; without that evidence, do not invent a flaw.
- **C5 — the port reads like its source (H7v, H8v).** The mirror follows `FromNat`'s definition case by case, under the measure it shipped with; the port's `ensures` names the layer's own spec fns rather than restating their definitions; the body's split is a shift and casts, as H6 taught. If the use-site check and the suite pass (A4, A6), the contract is strong enough for them; a finding here is about reading the port against its source, cited at `file:line`.
- **C6 — intent stays in the shipped contracts.** Q07's statements ship frozen; A5 is the anchor. A changed `requires`, `ensures`, measure or check line is a finding at grade 1, whatever the verifier says; the clauses added to `from_u128` and the body of `from_nat_mirror` are the holes themselves, not a change.
- **C7 — no dead code.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.

## Audit debrief — after /contract Q07

Questions for you, after each contract run (Dafny, then Verus) and after the local replay. Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — did the FROZEN statements stay?** `scripts/specfreeze --against research/q07_frozen.dfy dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` (Verus: `--against research/q07_frozen.rs verus/q/q07_internals_i/src/agent.rs`) reports no change.
- **D2 — did any API statement change?** `git diff <the snapshot's commit> -- dafny/Q/Q07_InternalsI/agent/Q07_AgentRefactor.dfy` (Verus: `verus/q/q07_internals_i/src/agent.rs`). Read every line of each `API` statement before and after: a conjunct dropped, a relation relaxed, a `requires` added or an attribute added is a breach that no machine line sees (your B2); name the line. If every `API` statement's lines are unchanged in the diff, none changed.
- **D3 — where do the new lemmas sit, and does each serve its callers?** Every added lemma (Verus: proof fn) is under `HELPERS`. For each helper, list its callers; each call verifies (the gate), and its `requires` asks only for what the callers' own hypotheses give. A helper stated for exactly today's callers is a note; a `requires` that an `API` statement's hypotheses cannot give is a finding.
- **D4 — is every body within the bound?** Count the code lines of each proof body (blank lines and comments excluded) against the `REFACTOR` comment of the file: 3 in the Dafny file, 4 in the Verus file.
- **D5 — are the gate and the audit clean?** Run the contract's gate, zero-holes and audit lines yourself (A2's and A3's agent forms) and compare them with the contractor's last report of them.
- **D6 — was fuel added?** In the diff's added lines: no `{:fuel` attribute (Verus: no `reveal_with_fuel` call). An added one is a breach that the gate, the freeze and the audit all pass (your B2).
- **D7 — did it re-verify after every edit?** Count the edits and the verifier runs between them in the transcript; name the first stacked edit.
- **D8 — the replay (A2d).** Read `research/runs/Q07/<run>/patch.diff` and its run record (`run.json`, `verify.json`) as data, never applying the patch to your tree: which acceptance lines the record re-checked and with what result, and D1–D6 asked of the patch. An empty patch is a result: record it as one. If `scripts/contract_local.sh Q07 --available` exits 3 on your machine, record its reason as this item's answer.
- **D9 — COMPARISON.** For each run: the acceptance lines it met, the statements it changed, and what only a reader could catch. For the replay, its `verify.json` and your own check of the lines it lists for your audit.
- **D10 — which moment earns a rule?** Name one transcript moment (a statement it weakened, a helper's `requires`, an attribute, a stacked edit) that deserves a rule in your next contract version, and write it in the rule format of `CLAUDE.md`'s contract slot.

## The port's FIDELITY block — your own review

After H9 verifies and the block is filled. Advisory: no script reads the block, and the tier viva may open on it.
- **D11 — is every mutant row a run?** For each of M1–M3, the Verus column cites the `scripts/vcheck` summary line of a scratch copy of the crate with that one change to your `from_u128`, and the Dafny column cites the printed `Valid` and `ToNat` lines of the check unit's mutant evaluation that decide it (they are in the file `stdout.txt` of the `raw_dir` that `scripts/vcheck --test --json dafny/checks/Q07_checks.dfy` reports). A `failed` Verus verdict counts as the contract's rejection only with a sample row whose mutant output breaks the contract, as the `MUTANTS` block asks (otherwise only your proof broke). A row filled without its run is a finding against your own block.
- **D12 — does each verdict follow from its contract?** For each row, name the clause of each contract that accepts or rejects the mutant's output, read from the definitions (layer L1's `Valid` and `ToNat`; the spec fns your `ensures` names, in layer L1's crate). A verdict you cannot trace to a clause is open.
- **D13 — do the suite's rows still match the sample's?** The differential suite below `port.rs`'s `verus!` block ships the check unit's six sample rows, row for row. Once uncommented, it keeps all six as shipped: compare each row with the check unit's `expect` for the same input. A row dropped or changed weakens the differential claim.
- **D14 — is the last line evidenced?** The mirror line says what H9 proved and what it rests on, relative to the mirror; the last line answers its question with a direction (the port promises more, the source promises more, or the same) and cites its evidence (a mutant row, a definition's clause). A line without evidence is a finding against your block; this rubric does not supply the answer.
