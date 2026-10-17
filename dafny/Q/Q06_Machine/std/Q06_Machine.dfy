/*!
# Q06 — The machine and the verifier loop (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`), L2
(`QG_L2_BigNat`) and L3 (`QG_L3_BigNat`), and two modules of Dafny's standard
library, `Std.Arithmetic.Power` (as `Power`) and `Std.Arithmetic.Mul` (as
`Mul`); nothing else: no earlier exercise file. The layers are frozen and
complete; read them, never edit them.

How to work this file:
1. Predictions first: fill every slot of the prediction block below (the
   verdict answers go in slots/Q06.slots), of specimens/Q06/P*.specimen and
   of the Python file's prediction block (harness/q/fvh_q/q06_stats.py), then
   record the first tries with `scripts/firsttry.sh Q06 --check`, before you
   run anything they are about.
2. Test-out next, closed book: T1 (below the prediction block) before any
   reading, without its hints. `scripts/firsttry.sh Q06 --check` records its
   first try, and refuses to while any prediction of the module is
   unrecorded: record the predictions first. If both files' T1 pass on that
   first try, you may skip the chapter section on triggers.
3. Replace each hole, then uncomment the checks beneath it (H4's property
   suite included).
4. Done = `scripts/vcheck --gate dafny/Q/Q06_Machine/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q06_Machine/std` reports
   no finding, `scripts/vcheck --test dafny/Q/Q06_Machine/std` passes every
   test, AND `scripts/firsttry.sh Q06 --report --strict` exits 0. H3 counts
   only with no resource attribute anywhere in this file.
5. Stuck for 20 minutes? /tutor Q06.

This file ships with exactly 5 holes: T1 (test-out) and H1–H4, each counted by
`scripts/vcheck`. Q06 as a whole ships 13 holes (5 here, 5 in the Verus file
verus/q/q06_machine/src/lib.rs, 3 in the Python file
harness/q/fvh_q/q06_stats.py), of which 2 are test-out items (T1 in each
verifier file); 9 predictions (7 verdicts and the 2 obligation specimens
P3 and P4); and 4 exit items (the exit files ship 2 + 2 holes).
Commit every prediction BEFORE you run anything it is about, open later files,
or read CI, the registry or the plan: their checks and headers give some
predictions away.

Item kinds: P prediction (a slot) · T test-out (closed book, after the
predictions) · W worked example (given, finished) · C card (WRITE: a success
here and a failure demo in specimens/Q06/; divergence, in the final section)
· H one-hole item · X exit item (the exit files) · A agent run (the agent
file). Slots: a verdict switch `// SLOT: CHECK <item>` here takes its answer
in slots/Q06.slots (`P1dv = ???` → `P1dv = "<answer>"`); an obligation slot
is the `// SLOT: FAILS ???` line of its specimen. Fill a slot, record the
first try, and only then enable it: `// SLOT: CHECK P1dv` becomes
`// CHECK P1dv`, and `// SLOT: FAILS …` becomes `// FAILS …`.

Exit (closed book): dafny/Q/Q06_Machine/exit/Q06_Exit.dfy and
verus/q/q06_machine/src/exit.rs, scored once by
`scripts/firsttry.sh Q06 --exit` (threshold 3 of 4, with at least 1 of the 2
in each language).

The tier viva (/viva Q06) examines Q04, Q05 and Q06. Before it, fill the
AUDIT ROWS block at the end of this file.

The agentic exercise (audited prover,
dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy) is at the bottom.
*/
module Q06_Machine {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power
  import Mul = Std.Arithmetic.Mul

  // ===========================================================================
  // The prediction block. Commit every prediction of this module before you
  // read past this block (the test-out T1 included), and record the first
  // tries:
  //     scripts/firsttry.sh Q06 --check
  // Verdict answers go in slots/Q06.slots. The obligation predictions are
  // the specimens specimens/Q06/P3d.dfy.specimen and P4v.rs.specimen; the
  // Python file harness/q/fvh_q/q06_stats.py holds P7 and P9.
  // ===========================================================================

  // item: Q06.P1dv S9 verdict
  /** **P1.** Skipping verification. Each file below is run directly (not
      through the course wrappers), on its own, in a scratch directory.

        Dafny, file p1.dfy, run as `dafny test --no-verify --target py p1.dfy`:
          module P1 {
            lemma Wrong(x: nat)
              ensures x + 1 == x
            {
            }

            @Test
            method Passes() {
              expect 1 + 1 == 2;
            }
          }

        Verus, file p1.rs, run as
        `verus p1.rs --crate-type=lib --no-verify --output-json`:
          use vstd::prelude::*;

          verus! {

          proof fn wrong(x: nat)
              ensures
                  x + 1 == x,
          {
          }

          } // verus!

      What is the exit code of each command, and what is the value of the
      `success` field in the JSON document that Verus prints?
      Answer form: `D:<exit> V:<exit> <true|false>`, each <exit> a numeral. */
  // SLOT: CHECK P1dv

  // item: Q06.P2dv S9 verdict
  /** **P2.** Out of budget. A lemma whose proof runs out of the pinned
      resource limit (the limit the course wrappers pass to each verifier) is
      checked with `scripts/vcheck --json`, once in each language. What is
      the exit code of `scripts/vcheck` itself, and the value of the
      `verdict` field of the JSON document it prints?
      Answer form: `D:<exit> <verdict> V:<exit> <verdict>`, each <exit> a
      numeral and each <verdict> one of the words that field takes:
      `verified`, `failed`, `inconclusive`, `refused`, `killed(memory)`,
      `error`. */
  // SLOT: CHECK P2dv

  // item: Q06.P5dv S11 verdict
  /** **P5.** A reveal in a narrow scope. What does `scripts/vcheck` say about
      each of these, verified on its own?

        Dafny:
          opaque function F(x: nat): nat
          {
            x + 1
          }

          lemma FAbove(x: nat)
            ensures F(x) > x
          {
            assert true by { reveal F(); }
          }

        Verus:
          #[verifier::opaque]
          pub open spec fn f(x: nat) -> nat {
              x + 1
          }

          pub proof fn lemma_f_above(x: nat)
              ensures
                  f(x) > x,
          {
              assert(true) by { reveal(f); }
          }

      Answer form: `D:<v> V:<v>`, each v one of `ok` (verifies), `fail` (a
      verification error), `timeout` (out of resource or time),
      `err:<stage>` (refused before verification; the stage as
      `scripts/vcheck` prints it: `parse` or `resolve`). */
  // SLOT: CHECK P5dv

  // item: Q06.P6dv S12 verdict
  /** **P6.** Resource attributes. Three files, each holding one small lemma
      that verifies:

        [a] Dafny:
          lemma {:rlimit 1000} Small(x: nat)
            ensures x + 0 == x
          {
          }

        [b] Verus:
          #[verifier::rlimit(1)]
          pub proof fn lemma_small(x: nat)
              ensures
                  x + 0 == x,
          {
          }

        [c] Verus: the same as [b], with `#[verifier::rlimit(4)]`.

      For which of the three files does `scripts/vaudit` report a finding?
      Answer form: the labels in label order, separated by single spaces, or
      `none`. */
  // SLOT: CHECK P6dv

  // item: Q06.P8dv S10 verdict
  /** **P8.** The libraries' own trusted parts. Dafny's bundled standard
      library and Verus's `vstd` each hold declarations that are trusted
      rather than proved.
      Dafny: when `scripts/vaudit` audits a unit that uses the standard
      library (this file's unit does), does its report list any finding
      located inside the standard library?
      Verus: when `scripts/vcheck` verifies a crate that uses `vstd` (every
      run carries `--no-cheating`), does it report the trusted sites inside
      `vstd`?
      Answer form: `D:<yes|no> V:<yes|no>`. */
  // SLOT: CHECK P8dv

  // ===========================================================================
  // Test-out (closed book: after every prediction of this module is recorded,
  // before any reading; `scripts/firsttry.sh Q06 --check` refuses T1's first
  // try until then)
  // ===========================================================================

  // item: Q06.T1d S11
  // uses: trigger
  // pair: Q06.T1v
  /** **T1.** (test-out) A fact about every limb, used for limb 1. The
      quantified hypothesis carries an explicit trigger. Which term must the
      proof mention before the solver uses the hypothesis for limb 1? */
  lemma SecondLimb(s: seq<nat>)
    requires |s| > 1
    requires forall k {:trigger Head(Drop(s, k))} | 0 <= k < |s| :: Head(Drop(s, k)) < 100
    ensures s[1] < 100
  // Hint(1): the trigger is the shape of term that switches the hypothesis on.
  // Hint(2): one `assert` about limb 1, written in the trigger's own terms.

  // ===========================================================================
  // Worked example
  // ===========================================================================

  // item: Q06.W1d S11
  /** **W1.** An opaque function and a scoped `reveal`. Outside a `reveal`,
      the verifier knows `Twice` by its signature only. `reveal Twice();`
      inside an `assert … by { … }` unfolds it for that assertion alone: the
      asserted fact is what the rest of the proof can see, never the
      definition. */
  opaque function Twice(x: nat): nat
  {
    2 * x
  }

  lemma TwiceEven(x: nat)
    ensures Twice(x) % 2 == 0
  {
    assert Twice(x) == 2 * x by { reveal Twice(); }
    // Here the equation is known and the body of Twice is not: the
    // postcondition follows from the equation.
  }

  // ===========================================================================
  // WRITE cards (each: a success here, a pinned failure demo in specimens/Q06/)
  // ===========================================================================

  // item: Q06.C1d S11 write:trigger
  /** ### C1 — card: triggers (`{:trigger …}`).
      Jurisdiction: a quantified fact is used only for the terms that match
      its trigger, so a proof switches it on by mentioning such a term.
      Success: `OddBound` asserts a fact about `Odd(3)`, which fires the
      hypothesis at `i = 3`. Failure: specimens/Q06/card-c1d.dfy.specimen
      (the same lemma; no term of the trigger's shape appears). */
  function Odd(i: nat): nat
  {
    2 * i + 1
  }

  lemma OddBound(s: seq<nat>)
    requires |s| > 3
    requires forall i {:trigger Odd(i)} | 0 <= i < |s| :: s[i] < Odd(i)
    ensures s[3] < 7
  {
    assert s[3] < Odd(3);
  }

  // item: Q06.C2d S11 write:opaque-reveal
  /** ### C2 — card: `opaque` and a scoped `reveal`.
      Jurisdiction: an opaque definition stays folded until a `reveal`
      unfolds it, inside that reveal's scope only, so the solver sees the
      body exactly where a proof asks for it. Success: `MidBetween` reveals
      `Mid` for its whole body. Failure: specimens/Q06/card-c2d.dfy.specimen
      (the reveal is confined to an `assert … by` and the body is needed
      after it). */
  opaque function Mid(a: nat, b: nat): nat
  {
    (a + b) / 2
  }

  lemma MidBetween(a: nat, b: nat)
    requires a <= b
    ensures a <= Mid(a, b) <= b
  {
    reveal Mid();
  }

  // item: Q06.C3d S11 write:rlimit
  /** ### C3 — card: proofs that fit the resource limit.
      Jurisdiction: every unit verifies under one pinned resource limit; a
      proof that exhausts it gets an out-of-resource verdict, which says
      nothing about whether the goal is true or nearly proved. Make the
      proof fit by giving the solver the steps it does not find, never by
      raising the limit. Success: `FourthPowerMono` with four library facts
      about products. Failure: specimens/Q06/card-c3d.dfy.specimen (the same
      lemma with an empty body). */
  lemma FourthPowerMono(x: nat, y: nat)
    requires x <= y
    ensures x * x * x * x <= y * y * y * y
  {
    Mul.LemmaMulInequality(x, y, x);      // x * x <= y * x
    Mul.LemmaMulInequality(x, y, y);      // x * y <= y * y
    var a, b := x * x, y * y;
    Mul.LemmaMulInequality(a, b, a);      // a * a <= b * a
    Mul.LemmaMulInequality(a, b, b);      // a * b <= b * b
  }

  // item: Q06.C4d S12 write:property-test
  /** ### C4 — card: bounded property tests.
      Jurisdiction: before a proof, check a property of a candidate's outputs
      on chosen samples. The checker is a verified method whose postcondition
      is two-sided (`ok` exactly when every sample has the property), so no
      constant answer verifies; `@Test` methods run it with `expect` on a
      correct candidate (it must pass) and on a planted one (it must be
      rejected): `scripts/vcheck --test` on the unit. The verifier checks the
      checker; the test run checks the candidates. Success: `AllBelow` and
      the two tests below it. Failure: specimens/Q06/card-c4d.dfy.specimen (a
      one-sided checker, which a constant answer satisfies). */
  method AllBelow(f: nat -> nat, samples: seq<nat>, bound: nat) returns (ok: bool)
    ensures ok <==> forall k | 0 <= k < |samples| :: f(samples[k]) < bound
  {
    ok := true;
    var k := 0;
    while k < |samples|
      invariant 0 <= k <= |samples|
      invariant ok <==> forall j | 0 <= j < k :: f(samples[j]) < bound
      decreases |samples| - k
    {
      ok := ok && f(samples[k]) < bound;
      k := k + 1;
    }
  }

  // A candidate that clips to the limit 1000, and a planted one that lets
  // 1000 itself through.
  function Clip(x: nat): nat
  {
    if x < 1000 then x else 999
  }

  function ClipPlanted(x: nat): nat
  {
    if x <= 1000 then x else 999
  }

  @Test
  method ClipPasses() {
    var ok := AllBelow(Clip, [0, 999, 1000, 1001, BASE], 1000);
    expect ok;
  }

  @Test
  method ClipPlantedRejected() {
    var ok := AllBelow(ClipPlanted, [0, 999, 1000, 1001, BASE], 1000);
    expect !ok;
  }

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q06.H1d S11
  // uses: trigger
  // pair: Q06.H1v
  /** **H1.** The first prefix is below one limb's weight. The hypothesis
      bounds every prefix by a power of BASE, and its trigger is `Pow(k)`.
      Which term must appear before the solver uses it for the prefix of
      length 1, and what does that term equal? */
  lemma FirstPrefix(s: seq<nat>)
    requires |s| >= 1
    requires forall k {:trigger Pow(k)} | 0 <= k <= |s| :: ToNat(s[..k]) < Pow(k)
    ensures ToNat(s[..1]) < BASE
  // Hint(1): name the instance you need in a term the trigger matches.
  // Hint(2): one `assert` that relates that term to BASE.

  // Given (not an item): two limbs packed into one number. Opaque: its body
  // is hidden from every proof that does not reveal it.
  opaque function Pack(lo: nat, hi: nat): nat
  {
    lo + BASE * hi
  }

  // item: Q06.H2d S11
  // uses: opaque-reveal
  // pair: Q06.H2v
  /** **H2.** Packing two limbs gives the value of the two-limb sequence.
      `Pack` is opaque. Where must its body be visible, and which layer facts
      give the value of `[lo, hi]` one limb at a time? */
  lemma PackToNat(lo: nat, hi: nat)
    ensures Pack(lo, hi) == ToNat([lo, hi])
  // Hint(1): reveal `Pack` in the scope that needs its body.
  // Hint(2): L2's `ToNatCons` and `ToNatSingleton` each give one step; the
  //    solver must also see `[lo] + [hi]` as the sequence `[lo, hi]`.

  // item: Q06.H3d S11
  // uses: rlimit
  /** **H3.** Two numbers below `Pow(n)` multiply to less than `Pow(2 * n)`.
      This attempt does not verify at the pinned resource limit:

          lemma TwoShifts(x: nat, y: nat, n: nat)
            requires x < Pow(n) && y < Pow(n)
            ensures x * y < Pow(2 * n)
          {
            PowIsStdPow(n);
            PowIsStdPow(2 * n);
            Power.LemmaPowAdds(BASE, n, n);
            Power.LemmaPowPositive(BASE, n);
          }

      Write a proof that verifies at the pinned limit, with no resource
      attribute. Which fact does the solver fail to find on its own? */
  lemma TwoShifts(x: nat, y: nat, n: nat)
    requires x < Pow(n) && y < Pow(n)
    ensures x * y < Pow(2 * n)
  // Hint(1): the attempt gets the powers right; what it lacks is a bound on a
  //    product of two bounded numbers.
  // Hint(2): `Std.Arithmetic.Mul` (imported as `Mul`) states such bounds;
  //    name `Pow(n)` in a local variable first.

  // Given (not an item): the reference split of a two-limb sum into its low
  // limb and its carry.
  function RefSplit(a: nat, b: nat): (nat, nat)
  {
    ((a + b) % BASE, (a + b) / BASE)
  }

  // item: Q06.H4d S12
  // uses: property-test
  // pair: Q06.H4v
  /** **H4.** A bounded property check of a limb adder: `CheckSplit(f,
      samples)` is true exactly when `f` agrees with `RefSplit` on every
      sample. Its postcondition is two-sided, so no constant answer verifies.
      Then uncomment the suite below: the correct candidate `AddCarryA` must
      pass and the planted `AddCarryB` must be rejected under
      `scripts/vcheck --test dafny/Q/Q06_Machine/std`. Which invariant
      carries "every sample so far agrees" to the end of the loop? */
  method CheckSplit(f: (nat, nat) -> (nat, nat), samples: seq<(nat, nat)>) returns (ok: bool)
    ensures ok <==> forall k | 0 <= k < |samples| :: f(samples[k].0, samples[k].1) == RefSplit(samples[k].0, samples[k].1)
  {
    assume false;
  }
  // Hint(1): one loop over the samples that stops at the first disagreement.
  // Hint(2): the invariant says that every sample before `k` agrees.

  // The samples and the two candidates the suite runs (given): limb pairs at
  // the carry boundary, a correct adder and a planted one.
  function Boundary(): seq<(nat, nat)>
  {
    [(0, 0), (1, BASE - 1), (BASE - 1, 1), (BASE - 1, BASE - 1), (BASE / 2, BASE / 2)]
  }

  function AddCarryA(a: nat, b: nat): (nat, nat)
  {
    if a + b < BASE then (a + b, 0) else (a + b - BASE, 1)
  }

  function AddCarryB(a: nat, b: nat): (nat, nat)
  {
    if a + b <= BASE then (a + b, 0) else (a + b - BASE, 1)
  }

  // Uncomment as you go:
  // @Test
  // method GoodPasses() {
  //   var ok := CheckSplit(AddCarryA, Boundary());
  //   expect ok;
  // }
  //
  // @Test
  // method PlantedRejected() {
  //   var ok := CheckSplit(AddCarryB, Boundary());
  //   expect !ok;
  // }

  // ===========================================================================
  // Final section: divergence card. Record every prediction of this module
  // (scripts/firsttry.sh Q06 --check) before you read on or open its demos.
  // ===========================================================================

  // item: Q06.C5dv S9 diverge:q06-c5
  /** ### C5 — divergence card. Demos: specimens/Q06/card-c5dv-d.dfy.specimen
      and specimens/Q06/card-c5dv-v.rs.specimen. */
}

// =============================================================================
// ## Exercise (AGENTIC) — audited prover (`/contract Q06`)
// =============================================================================
// File: dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy. Shipped state: green,
// with exactly 1 tool-counted hole (the frozen top lemma `CanonicalUnique`)
// and an empty SKELETON section. Check command (the file's own header gives
// the steps in full):
//
//     scripts/vcheck dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy
//
// Steps (after this file is done):
// 1. Before the run: write your skeleton (at most 5 leaf lemmas as holes, and
//    the top lemma's proof from them), copy the file to
//    research/q06_skeleton.dfy, and commit both.
// 2. In a FRESH session, run /contract Q06.
// 3. Audit the statements (`scripts/specfreeze --against`), the assumptions
//    (`scripts/vaudit`) and each leaf's usefulness.
// 4. Write in the agent file's AUDIT block which leaf took the contractor
//    longest, and why.
// The lesson: a green, audit-clean delivery proves the statements you wrote;
// whether they were the right statements is your audit, not the gate's.

/*
AUDIT ROWS (learner-owned; advisory: no script reads this block and no gate
depends on it). Before the moderate-tier viva (/viva Q06), once
`scripts/firsttry.sh <ID> --report --strict` passes for Q04, Q05 and Q06,
write on each line below the number of findings you expect `scripts/vaudit`
to report for that target and their kinds; then run `scripts/vaudit` on each
target and write whether the line held. The viva opens on any line that did
not hold.
  dafny/Q/Q04_ProofCraft/core/Q04_ProofCraft.dfy   expected:        held:
  dafny/Q/Q04_ProofCraft/std/Q04_Library.dfy       expected:        held:
  verus/q/q04_proof_craft                          expected:        held:
  dafny/Q/Q04_ProofCraft/exit/Q04_Exit.dfy         expected:        held:
  verus/q/q04_proof_craft/src/exit.rs              expected:        held:
  dafny/Q/Q05_Frames/std/Q05_Frames.dfy            expected:        held:
  verus/q/q05_frames                               expected:        held:
  dafny/Q/Q05_Frames/exit/Q05_Exit.dfy             expected:        held:
  verus/q/q05_frames/src/exit.rs                   expected:        held:
  dafny/Q/Q06_Machine/std/Q06_Machine.dfy          expected:        held:
  verus/q/q06_machine                              expected:        held:
  dafny/Q/Q06_Machine/exit/Q06_Exit.dfy            expected:        held:
  verus/q/q06_machine/src/exit.rs                  expected:        held:
*/

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  setup 5 · test-out 10 · read 48 · worked 25 · cards 8 · predicts 22 ·
  holes 36 · property tests 15 · statistics by hand 30 · EVAL.md v0 15 ·
  TRUST.md v0 10 · agent 15 · paper 15 · exit 22 · calib 5 · total 281
  (+ tier viva 30)
*/
