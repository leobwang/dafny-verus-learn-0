# Q04 rubric — Proof craft, loops and libraries

> **Consumers:** `/grade-paper Q04` and `/grade-paper Q04 --post` (B1–B3), `/review-code Q04` (Gate, Code-review focus), and you, after `/contract Q04` (the audit debrief). Every line is a predicate about your artifacts, never an answer; where something sharper is needed, it is a verifier anchor: a command whose output settles the question.
> **Advisory:** a verifier check outranks any line here, and you may dispute a finding at the level of its labelled line. No line counts holes with grep, reads a verdict from an exit code alone, or treats "could not be proved" as a failing instance.
> **Predictions first:** like the bank, this file records verified tool behaviour. Open it only after `scripts/firsttry.sh Q04 --check` has recorded every Q04 prediction and T1's first try (the test-out is closed book).

Solution pins (scripts/ci.sh compares on every change; stale pins fail):
paper/solutions/Q04_solutions.tex  sha256 76cc26d8af39a5014801df0fa44ffb04c4e0e8ba0127b0bcc31cf4a33278989a — the written track's reference (B1–B3)
paper/Q04_problems.tex  sha256 3cf23d61d757754fc3679ba6456590f9f7dd8258fb3c014d5f9b6ba6638ee4ad — the problems these lines grade
Solutions/dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy  sha256 99762ec38eb6be36db3ba4a064b80cd88cab82f7544797a52bc08f92f922f789 — the formal reference B1 (a) precedes (H4d), and the library half of the Dafny code review
Solutions/verus/q/q04_proof_craft/src/library.rs  sha256 9318dc20cdee8b260f424390e2d4e5c210708ea1887abf036e1eec4161ea9223 — the formal reference B1 (b) precedes (H4v), and the library half of the Verus code review
Solutions/dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy  sha256 56146cb36f3f2b91929eedccf825bdadfae97b15342531e0d62e4de3f897070f — the core half of the Dafny code review
Solutions/verus/q/q04_proof_craft/src/lib.rs  sha256 1d0e316e850d25c489f4e191c3bdf5bf207278c64c708aceb3ea53edb8c8ab40 — the crate-root half of the Verus code review
Solutions/dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy  sha256 6a9729b1e9e90d58489d66c10643a3abdf5b9dcc5aa66ee6b69b7673921ab944 — the reference delivery behind the audit debrief (Dafny)
Solutions/verus/q/q04_proof_craft/src/agent.rs  sha256 57c6427ea578726c1319b9352106b115fafafd0f682f18d061d71aa0e9fd4cf0 — the reference delivery behind the audit debrief (Verus)

## Verifier anchors

Every probe goes in `instructor/scratch/` and runs through `scripts/vcheck` (or `scripts/vaudit` where named), one solver job at a time; the output is pasted verbatim. The program text below is the problems file's or the given layers'; the lines marked `<-` are where your own statements go. A verified probe confirms a step (verdict kind 1). An error verdict alone refutes nothing: a flaw is exhibited by an executable check (a `@Test` method with `expect`, run with `scripts/vcheck --test`), by a verified refutation, or, for a claim about what an instrument reports, by that instrument's pasted output.

- **Probe A** (B1 (a), splice template: does the blueprint close as written?). In `instructor/scratch/probe.dfy`, filled from your blueprint alone:

  ```dafny
  module ProbeA {
    import opened QG_L1_BigNat
    import opened QG_L2_BigNat
    import opened QG_L3_BigNat

    // One bodyless lemma per helper your blueprint names that is not a lemma of L1-L3:
    // its statement only, exactly as you wrote it.
    lemma Helper1(a: seq<nat>, b: seq<nat>)
      requires true          // <- your helper's hypotheses
      ensures true           // <- your helper's conclusion

    // The target under a probe name. Its body is your blueprint, transcribed: one branch
    // per case you list, your induction hypothesis as a call of CmpAgrees itself at the
    // instance you name, and only the calls and asserts you name, in your order.
    lemma CmpAgrees(a: seq<nat>, b: seq<nat>)
      requires Valid(a) && Valid(b)
      ensures -1 <= Cmp(a, b) <= 1
              && (Cmp(a, b) < 0 <==> ToNat(a) < ToNat(b))
              && (Cmp(a, b) == 0 <==> ToNat(a) == ToNat(b))
      decreases |a| + |b|
    {
                             // <- your cases, calls and asserts
    }
  }
  ```

  Run `scripts/vcheck --module Q04 instructor/scratch/probe.dfy` (the module's given layers and the library file's unit options, so no induction happens for you; the count includes the layers' own tasks). Verified, with one hole per pasted helper and no other: the decomposition closes, given those helpers. A resolve error on a helper exactly as written: that statement is not formalizable as written (paste the error). A verification error: a gap until Probe A″ exhibits a false step or an uncovered instance. A reference blueprint spliced into this template verified on the pins (Dafny 4.11.0).
- **Probe A′** (B1 (b), splice template: is the clause enough, and do the named facts settle the length cases?). In `instructor/scratch/probe.rs`, the problems file's code under a probe name, with your clause spliced into the invariant and your facts for the two length cases written as calls of L3's lemmas by name:

  ```rust
  use vstd::prelude::*;
  use qg_bignat_l3::*;
  use core::cmp::Ordering;

  verus! {

  pub fn blueprint_cmp(a: &BigNat, b: &BigNat) -> (r: Ordering)
      requires
          a.wf(),
          b.wf(),
      ensures
          (r == Ordering::Less) == (a.to_nat() < b.to_nat()),
          (r == Ordering::Equal) == (a.to_nat() == b.to_nat()),
          (r == Ordering::Greater) == (a.to_nat() > b.to_nat()),
  {
      let n = a.limbs.len();
      let m = b.limbs.len();
      if n < m {
          proof {
              // <- your facts for a shorter a: L3's lemmas, called by name
          }
          return Ordering::Less;
      }
      if n > m {
          proof {
              // <- your facts for a longer a
          }
          return Ordering::Greater;
      }
      let mut i = n;
      while i > 0 && a.limbs[i - 1] == b.limbs[i - 1]
          invariant
              i <= n,
              n == a@.len(),
              n == b@.len(),
              true,  // <- your missing clause, over i, n, a@ and b@
          decreases i,
      {
          i = i - 1;
      }
      if i == 0 {
          proof {
              assert(a@ =~= b@);
          }
          Ordering::Equal
      } else if a.limbs[i - 1] < b.limbs[i - 1] {
          proof {
              lemma_lt_at(a@, b@, (i - 1) as int);
          }
          Ordering::Less
      } else {
          proof {
              lemma_lt_at(b@, a@, (i - 1) as int);
          }
          Ordering::Greater
      }
  }

  } // verus!
  ```

  Run `scripts/vcheck --module Q04 instructor/scratch/probe.rs`. Verified: the clause is enough and the named facts settle the length cases. An error at the end of the loop body or at a `lemma_lt_at` call: the clause as written does not carry what the call needs (a gap until a reachable state that breaks the clause is exhibited). An error at a length case's `return`: the named facts do not chain as written. With the problems file's code as above and a reference clause and reference facts spliced in, the template verified on the pins (Verus 0.2026.09.27.3cf1832); as shipped (every `<-` line empty or `true`) it fails.
- **Probe A″** (B1, a step claimed false, or an induction-hypothesis instance claimed uncovered). A test file stands alone, so it carries copies of the problems file's definitions:

  ```dafny
  module ProbeStep {
    const BASE: nat := 18446744073709551616

    function ToNat(s: seq<nat>): nat
      decreases |s|
    {
      if |s| == 0 then 0 else s[0] + BASE * ToNat(s[1..])
    }

    function Head(s: seq<nat>): nat
    {
      if |s| == 0 then 0 else s[0]
    }

    function Tail(s: seq<nat>): seq<nat>
    {
      if |s| == 0 then [] else s[1..]
    }

    function Cmp(a: seq<nat>, b: seq<nat>): int
      decreases |a| + |b|
    {
      if |a| == 0 && |b| == 0 then 0
      else
        var c := Cmp(Tail(a), Tail(b));
        if c != 0 then c
        else if Head(a) < Head(b) then -1
        else if Head(a) > Head(b) then 1
        else 0
    }

    @Test
    method StepOnExample()
    {
      var a: seq<nat>, b: seq<nat> := [], [];   // <- the concrete sequences
      expect true, "the step fails";            // <- the step's claim, at a and b
    }
  }
  ```

  Run `scripts/vcheck --test instructor/scratch/probe.dfy`. `FAILED` with the message: the claim is false at those sequences, a confirmed flaw. For an induction-hypothesis instance, the claim is the stated order's comparison between the instance needed and the current one (for an induction on a length, that length of the instance is smaller): `FAILED` shows the stated hypothesis does not cover it. `PASSED`: the claim holds there, and nothing is refuted. As shipped (`expect true`) it prints `1 passed, 0 failed`.
- **Probe B** (B2, what each instrument reports). One body per run. Dafny, in `instructor/scratch/probe.dfy`:

  ```dafny
  module {:disableNonlinearArithmetic} ProbeB2 {
    import Mul = Std.Arithmetic.Mul

    // <- a declaration of your own, if the body under test uses one

    lemma ScaleLe(a: nat, b: nat, w: nat)
      requires a <= b
      ensures a * w <= b * w
    {
                             // <- the body under test
    }
  }
  ```

  Verus, in `instructor/scratch/probe.rs`:

  ```rust
  use vstd::prelude::*;
  use vstd::arithmetic::mul::*;
  use vstd::calc;        // needed only if the body under test uses calc!

  verus! {

  // <- a declaration of your own, if the body under test uses one

  pub proof fn lemma_scale_le(a: nat, b: nat, w: nat)
      requires
          a <= b,
      ensures
          a * w <= b * w,
  {
                             // <- the body under test
  }

  } // verus!
  ```

  Run `scripts/vcheck --module Q04 --gate instructor/scratch/probe.<ext>`, then `scripts/vaudit instructor/scratch/probe.<ext>`. The two outputs are the answer key to "does the gate pass?" and "does the audit report a finding?" for that body; whether a body keeps the contract's "only standard-library lemma calls" line is settled by reading it against the agent file's CONTRACT block.
- **Probe C** (B3, the card pin). `sed -n '614,638p' ~/code/research/agentic-formal-veri/cheatsheets.md | sha256sum` must print the hash that problem B3 prints. Run it before grading any field.
- **Probe D** (Code-review focus, a dead step). Copy the declaration under review, with its file's imports (and, for a crate file, `use qg_bignat_l3::*;` and the `vstd` imports it has), into `instructor/scratch/probe.dfy` or `instructor/scratch/probe.rs`, delete the one line in question, and run `scripts/vcheck --module Q04 instructor/scratch/probe.<ext>`. Verified without the line: the line is dead. Not verified: it is needed.

## B1 — A blueprint for H4d and H4v (informal-proof-first)

### statement-fidelity
- **SF.a** — (a) proves the lemma as stated: both validity hypotheses, all three claims (the range, the order, the equality), the same directions. A dropped hypothesis or claim scores ≤2 only with sequences on which the restated claim and the lemma differ, shown by Probe A″ (for example a claim stated without validity, refuted at invalid limbs).
- **SF.b** — (b) argues about the code as given: its loop, its three outcomes after the loop and its two early returns. A rewritten function is a gap (3) unless the rewrite changes what the clause must say, shown by Probe A′ verifying on one and not the other.

### induction-soundness
- **IS.a** — the induction is named (on what, with which order), and the induction hypothesis is a formula with its quantifiers explicit, over valid sequences. An IH in words only is a gap (3).
- **IS.b** — every use of the IH is at an instance the stated IH provides, in every case where the step uses it. A score ≤2 names the use, the instance it needs and the instances the stated IH covers, and exhibits concrete `a` and `b` at which the needed instance is not covered, by Probe A″ (`FAILED` on the stated order's comparison).
- **IS.c** — every equation or inequality a step uses holds, and the IH's `requires` are established where it is used. A score ≤2 exhibits sequences at which the step's claim is false, by Probe A″. A requirement that holds but is not argued is a gap (3).
- **IS.d** — (b)'s clause holds on entry and is kept by one pass, and with the other invariant clauses and the negated guard supplies what each outcome after the loop needs; Probe A′ verifies with it spliced in. When Probe A′ does not verify, the clause scores ≤2 only with an exhibited state where it holds, the guard holds, and after one pass it fails, or a reachable state where the loop ends and the outcome's claim is false.

### case-exhaustiveness
- **CE.a** — (a)'s cases cover every pair of sequences (the branches of `Cmp` as defined, or a split shown equivalent to them), each case states its condition, and each case's argument applies to every pair in it. A score ≤2 exhibits `a` and `b` that fall in no case, or in a case whose argument fails on them (Probe A″).
- **CE.b** — (b) covers the two length cases and the three outcomes after the loop. A missing one is a gap (3) unless the answer claims an outcome that Probe A′'s code cannot reach or misreads one that it can, shown by the probe.

### blueprint-quality
- **BQ.a** — every helper fact is named by its statement (an equation or bound between named values, with its hypotheses) and attributed: a lemma of L1–L3 by its name, a new lemma with its full `requires` and `ensures`, or a declared gap. The operational test is Probe A filled from the blueprint alone, with nothing invented: if it verifies with one hole per pasted helper, do not invent a flaw. A Probe A that does not verify is a gap (3) unless Probe A″ exhibits a false step.
- **BQ.b** — the step where the tails decide says why a difference between the tails' values outweighs any difference between the heads, naming the fact about the heads it rests on. An argument that asserts it without a reason is a gap (3), recorded for the `--post` diff.
- **BQ.c** — (b) names each fact of the length cases by its statement and the lemma of L3 that states it, and says which `requires` of `lemma_lt_at` the clause supplies. The operational test is Probe A′ with those facts as named calls: if it verifies, do not invent a flaw. A clause that is true in every reachable state but leaves Probe A′ unverified (an equivalent formula the verifier cannot use as written) is a gap (3), never a flaw.

### gap-accounting
- **GA.a** — declared gaps score 3. An undeclared step that is false at an exhibited input is a flaw (≤2). An undeclared step that is true but unjustified is recorded as a gap (3), never as a flaw.

## The --post pass

Runs once `scripts/vcheck --gate dafny/Q/Q04_ProofCraft/std` and `scripts/vcheck --gate verus/q/q04_proof_craft` both exit 0 (H4d and H4v are in them). Re-score `blueprint-quality` of B1 only, with your verified `CmpCorrect` and `cmp` as the oracle:
- **BQ.d** — diff the blueprint against the proofs: the helpers it named against the calls and asserts `CmpCorrect` makes; the IH instance against the recursive call's arguments; the cases against the branches; (b)'s clause against the clause you wrote, and (b)'s named facts against how your `cmp` gets them. Record each fact the proof needed that the blueprint did not name, and each named helper the proof never used.
- **BQ.e** — record whether formalizing forced a change the paper missed (an extra fact, a different instance, a reworded clause, the way the length facts entered the function). A blueprint whose decomposition survived formalization scores 4; each missed fact is a finding at 3, never lower unless the blueprint's step was false at an exhibited input.

The gradebook gets a `paper-post` row with the new `blueprint-quality` score.

## B2 — Green, clean, and out of contract (concept; dimension: correctness)

### correctness
- **CO.a** — each claim of (a) about the gate and the audit, per body and per language, agrees with Probe B's output for that body. A claim scores ≤2 only with Probe B's pasted output that contradicts it. A claim the answer hedges ("probably") is graded as the claim it makes.
- **CO.b** — each claim of (a) about the contract line agrees with the agent file's CONTRACT block, read against the body. A score ≤2 quotes the acceptance line the claim contradicts, beside the body.
- **CO.c** — (b)'s body passes both instruments (Probe B, both outputs pasted) and breaks the contract line in a way other than an `assert`. A body that the gate or the audit rejects, or that keeps the line (only library calls), scores ≤2 with the pasted output or the quoted body. A body the answer did not run but that passes Probe B is correct: do not invent a flaw.
- **CO.d** — (b) names an artifact that shows the breach. Naming an instrument that does not report it scores ≤2 only with that instrument's pasted output on (b)'s own body (Probe B).

## B3 — Paper card 02.2 (paper-card; dimension: card-fidelity)

### card-fidelity
- **CF.a** — Probe C prints the hash B3 prints. Otherwise the card is not graded ("card pin stale: the author must re-pin it").
- **CF.b** — all eight fields are filled (task shape, oracle, what is trusted, cheat surface, metric, budget, variance, artifact), each answering its own question. An empty field, or one that answers another field's question, scores 1 for that field.
- **CF.c** — each field agrees with the pinned range (`cheatsheets.md` lines 614–638). A field scores ≤2 only by quoting the pinned line it contradicts, with its line number, beside the field's own sentence.
- **CF.d** — a field for which the range is silent is correct when it says so, and better when it says what would be needed; silence in the range is never a contradiction. A field that asserts a figure the range does not contain (a run count, an interval, a cost, a release) scores ≤2 only by naming the field and the quoted absence: the range lines that state the setup or the results without it.
- **CF.e** — figures stay attached to what the range attaches them to: a count, a time or a call budget given to the wrong system (the method or the baseline), run (best of several or a single one), task set or model contradicts the table or sentence it comes from, and CF.c applies.
- **CF.f** — wording is free: a field in your own words that agrees with the range scores 4, however short; a field need not cover every fact the range offers. The card's grade is the minimum over its fields; do not invent a flaw in a field that agrees.

## Gate

The mechanical preconditions of `/review-code Q04`; each anchor's output is pasted into the review.
- **A1 — units green.** `scripts/vcheck Q04` reports the three units verified.
- **A2 — zero holes, tool-counted.** `scripts/vcheck --gate dafny/Q/Q04_ProofCraft/core`, `scripts/vcheck --gate dafny/Q/Q04_ProofCraft/std`, `scripts/vcheck --gate verus/q/q04_proof_craft` and `scripts/vcheck --gate dafny/checks/Q04_checks.dfy` each exit 0 and print only the summary line. After both contract runs, `scripts/vcheck --gate dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy` and `scripts/vcheck --gate verus/q/q04_proof_craft/src/agent.rs` do too.
- **A3 — audit, pinned.** `scripts/vaudit dafny/Q/Q04_ProofCraft/core`, `scripts/vaudit dafny/Q/Q04_ProofCraft/std`, `scripts/vaudit verus/q/q04_proof_craft` and `scripts/vaudit dafny/checks/Q04_checks.dfy` report no finding; `scripts/vaudit --compare expected/Q04_AgentRetriever.audit dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy` and `scripts/vaudit --compare expected/q04_proof_craft_agent.audit verus/q/q04_proof_craft/src/agent.rs` report no difference.
- **A4 — slots, first tries and shipped lines.** `scripts/firsttry.sh Q04 --report --strict` exits 0 (every slot filled and recorded, the test-out blocks written and their checks uncommented, and, after the exit's scored run, the exit files repaired).
- **A5 — statements unchanged.** `scripts/specfreeze --check Q04` reports no finding.
- **A6 — what is not reviewed.** The card demos under `specimens/Q04/card-*` are red by design (their failures are pinned) and are never finished or reviewed; the obligation specimens `specimens/Q04/P4d.dfy.specimen`, `P5d.dfy.specimen` and `P9v.rs.specimen` are predictions, covered by A4 alone. The `TOOLCHAIN LAB`, `SEARCH LOG`, `COMPARISON` and `CALIBRATION` blocks are your prose, read by no tool and not code-reviewed. A2 and A3 skip the specimens. No brittleness gate applies at this bar.

## Code-review focus — band: "proof-shape"

- **C1 — the method clauses no instrument sees.** Each hole's docstring states how it is to be proved (a recursive call and a `calc` chain; one `forall` statement; one `assert forall … by`; library lemmas and L3's bridge only, with no lemma of your own; L3's lemmas called by name with no `broadcast use`; one clause and one group line; a nonlinear assertion), and each exit block states its own once the exit is repaired. Read each proof against its docstring and cite `file:line` for a clause that is not met. If every clause is met, do not invent a flaw.
- **C2 — chains read as chains.** In each `calc` or `calc!` you wrote, every step is one move a reader can name (an unfolding, a call, a regrouping), and each hint serves the step it is attached to: Probe D on a hint shows it needed. A hint Probe D shows dead is a finding at this bar; without that evidence, do not invent a flaw.
- **C3 — local facts stay local.** A fact that one step or one instance needs reads best where that step is: its hint, the `forall` statement's body, an `assert … by` block. A call made before a chain for one step, or an `assert` whose fact reaches later lines that do not need it, is a readability note at most, never a grade below 3; a call Probe D shows needed by several steps belongs where it is. Do not invent a flaw.
- **C4 — the induction follows the recursion.** Each recursive call is at the argument the definition recurses on (the verifier checks the shipped `decreases`), and the case split matches the definition's branches. A split that is correct but follows no definition is a readability note, never a grade below 3.
- **C5 — invariants say what the loop has established.** The clause you wrote in H4v says what the scanned part has in common, in terms of the loop's variables; any further clause you added is needed (Probe D). A clause Probe D shows dead is a finding.
- **C6 — automation scoped and minimal.** A lemma group is brought into the one function that needs it, never broadcast for the whole module; a nonlinear assertion's `requires` lists only the facts its product needs (Probe D on each clause); a library call is the one the step needs. If Probe D shows every call and clause needed, do not invent a flaw.
- **C7 — names say what things are.** Any name you introduced (a `let` for a power or an index, a helper in an exit block where the block allows one) says what it holds. If you introduced none, there is nothing to review here: do not invent a flaw.
- **C8 — no dead scaffolding.** No commented-out experiments and no unused helpers in your own lines. Prediction slots and their answers stay as the strict report wants them: a *wrong* prediction left visible is a feature, never a finding.

## Audit debrief — after /contract Q04

Questions for you, after each contract run (Dafny, then Verus). Each is settled by the transcript, the artifact or a command, and none has a secret answer.
- **D1 — did the diff stay in the three bodies?** `git diff -U0 -- dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy` (Verus: `verus/q/q04_proof_craft/src/agent.rs`). Every hunk is inside a goal's body; no signature, `requires`, `ensures`, attribute, doc comment or import line changed, and no declaration was added or removed.
- **D2 — is every body only library calls, each with its receipt?** Read each body in the diff: one library lemma call per line, each followed by `// found-by: <rung>` with a rung from the contract's list. An `assert`, a `calc` (Verus: `calc!`, `broadcast use`) or a call of anything the contractor declared is a breach the gate and the audit cannot see (your B2); name the line.
- **D3 — are the gate and the audit clean?** Run `scripts/vcheck --gate <file>` yourself: exit 0, only the summary line. Run `scripts/vaudit --compare expected/Q04_AgentRetriever.audit dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy` (Verus: `--compare expected/q04_proof_craft_agent.audit verus/q/q04_proof_craft/src/agent.rs`): no difference.
- **D4 — does each receipt match the transcript?** For each `// found-by:` line, find the moment in the transcript where that lemma's name first appears, and the action that produced it (a hover, a search of the library source, a documentation page, a model's suggestion, nothing visible). A receipt whose rung the transcript does not show is a false receipt; quote the moment.
- **D5 — did the contractor try a name that does not exist?** Count the runs in the transcript that failed before verification on a lemma name (a resolution-stage failure), and the names involved. None of them is in the final file; that is why the transcript is the only record.
- **D6 — did it re-verify after every edit?** Count the edits and the verifier runs between them: the contract's acceptance asks for one run after each edit. Stacked edits are a breach; name the first.
- **D7 — how did the race go?** Put your `SEARCH LOG` beside the receipts: for each goal, your rung and minutes against the contractor's rung and the transcript's elapsed time. Where did the same lemma take you a different rung, and why?
- **D8 — which rule of your contract v0 fired?** In Q03 you wrote down the rule you expected to fire first (contract v0 review, D7). Check the transcripts: which rules did these runs test, which rule fired first, and which rule did nothing test? Write one transcript moment that earns a rule for your v1 notes, in the rule format `CLAUDE.md`'s contract slot shows.
