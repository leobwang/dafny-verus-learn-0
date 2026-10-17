/*!
# Q08 — Internals II: refinement, permissions, verified wp (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`), L2
(`QG_L2_BigNat`), L3 (`QG_L3_BigNat`) and L4 (`QG_L4_BigNat`, and its limb
implementation `QG_L4_Limbs`, imported as `Limbs`); nothing else: no earlier
exercise file. This unit's dfyconfig.toml includes the layers and turns the
standard library on. The layers are frozen and complete; read them, never
edit them.

Q08's Dafny exercises are three files of this unit: this one (the prediction
block, the test-out T1, the worked example W1 and the cards C1 and C4),
std/Q08_Canon.dfy (two refinements of L4's QG_L4_Spec: H1d, H2d, H7d) and
std/Q08_Wp.dfy (a verified weakest precondition: W2, H8d–H10d). The Verus
half is the crate verus/q/q08_internals_ii (src/lib.rs and src/perm.rs).

How to work this file (the order is the module's, for every file):
1. Predictions first: fill every slot of the prediction block below and of
   the Verus crate's prediction block (verus/q/q08_internals_ii/src/lib.rs);
   the verdict answers go in slots/Q08.slots. Then record the first tries
   with `scripts/firsttry.sh Q08 --check`, before you run anything they are
   about.
2. Test-out next, closed book: T1d (below the prediction block) and T1v (in
   src/lib.rs) before any reading, without their hints.
   `scripts/firsttry.sh Q08 --check` records each first try (it runs the
   block's commented check in a scratch copy), and refuses to while any
   prediction of the module is unrecorded: record the predictions first. Only
   then uncomment the check. If a T1 passes on that first try, you may skip
   the chapter section it tests (the chapter names it).
3. Then read the chapter (docs/Q08_InternalsII.md), the cards and the worked
   examples. A card's failure demo is a specimen: open it only after step 1.
4. Replace each hole (std/Q08_Canon.dfy, then std/Q08_Wp.dfy), then
   uncomment the checks beneath it. Read Hint(1) only when stuck, Hint(2)
   only when still stuck.
5. Done = `scripts/vcheck --gate dafny/Q/Q08_InternalsII/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q08_InternalsII/std`
   reports no finding, AND `scripts/firsttry.sh Q08 --report --strict` exits
   0.
6. Stuck for 20 minutes? /tutor Q08.

This file ships with exactly 1 hole: T1 (test-out), counted by
`scripts/vcheck`; std/Q08_Canon.dfy ships 3 and std/Q08_Wp.dfy 3. Q08 as a
whole ships 12 holes (7 in this unit; 5 in the Verus crate, 3 in src/lib.rs
and 2 in src/perm.rs), of which 2 are test-out items (T1 in each verifier);
6 predictions (all verdicts); and 4 exit items (the exit files ship 2 + 2
holes). Commit every prediction BEFORE you run anything it is about, open
later files, or read CI, the registry or the plan: their checks and headers
give some predictions away.

Item kinds: P prediction (a slot) · T test-out (closed book, after the
predictions) · W worked example (given, finished) · C card (WRITE: a success
here and a failure demo in specimens/Q08/; divergence, in the final section)
· H one-hole item · X exit item (the exit files) · A agent run (the agent
files). Slots: a verdict switch `// SLOT: CHECK <item>` here takes its answer
in slots/Q08.slots (`P1dv = ???` → `P1dv = "<answer>"`). Fill a slot, record
the first try, and only then enable it: `// SLOT: CHECK P1dv` becomes
`// CHECK P1dv`.

Exit (closed book): dafny/Q/Q08_InternalsII/exit/Q08_Exit.dfy and
verus/q/q08_internals_ii/src/exit.rs, scored once by
`scripts/firsttry.sh Q08 --exit` (threshold 3 of 4, with at least 1 of the 2
in each language). After the score, fill the EXPLAIN-BACK block at the end
of the Dafny exit file.

The agentic exercise (the spec-to-proof flagship,
agent/Q08_AgentFlagship.dfy and verus/q/q08_internals_ii/src/agent.rs) and
the CALIBRATION block are at the bottom.
*/
module {:disableNonlinearArithmetic} Q08_InternalsII {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import Limbs = QG_L4_Limbs

  // ===========================================================================
  // The prediction block. Commit every prediction of this module before you
  // read past this block (the test-out T1 included), and record the first
  // tries:
  //     scripts/firsttry.sh Q08 --check
  // Verdict answers go in slots/Q08.slots. The Verus crate's prediction block
  // (verus/q/q08_internals_ii/src/lib.rs) holds P2 and P6.
  // Verdict vocabulary for `D:<v> V:<v>` answers: `ok` (verifies), `fail` (a
  // verification error), `timeout` (out of resource or time), `err:<stage>`
  // (refused before verification; <stage> as scripts/vcheck prints it:
  // `parse` or `resolve`).
  // ===========================================================================

  // item: Q08.P1dv S6 verdict
  /** **P1.** Strengthening and weakening across a frozen statement.

        Dafny: an abstract module, and a module that refines it with [a] or
        with [b].
          abstract module Spec {
            lemma Bound(x: nat)
              requires x < 10
              ensures x < 20
          }

          [a] module RefA refines Spec {
                lemma Bound(x: nat)
                  ensures x < 15
                {
                }
              }

          [b] module RefB refines Spec {
                lemma Bound(x: nat)
                  requires x < 5
                {
                }
              }

        Verus: a trait, and its implementation on a struct with [a] or with
        [b] as its `bump`.
          pub trait Counter: Sized {
              spec fn count(&self) -> nat;

              fn bump(&mut self)
                  requires
                      old(self).count() < 100,
                  ensures
                      final(self).count() == old(self).count() + 1,
              ;
          }

          pub struct Small {
              pub n: u64,
          }

          impl Counter for Small {
              open spec fn count(&self) -> nat {
                  self.n as nat
              }

              [a] fn bump(&mut self)
                      ensures
                          final(self).n == old(self).n + 1,
                  {
                      self.n = self.n + 1;
                  }

              [b] fn bump(&mut self)
                      requires
                          old(self).n < 50,
                  {
                      self.n = self.n + 1;
                  }
          }

      Each case is a file of its own (four files). What does `scripts/vcheck`
      say about each?
      Answer form: `D:<v> <v> V:<v> <v>` ([a] first, then [b], in each
      language), with the verdict vocabulary above. */
  // SLOT: CHECK P1dv

  // item: Q08.P3d S6 verdict
  /** **P3.** A refined lemma with a measure of its own. A module refines L4's
      QG_L4_Spec as L4's own QG_L4_Limbs does (`BigNat = seq<nat>`, `Val` is
      L1's `ToNat`, `Wf` is L1's `Valid`, `FromNat` is L2's), with every
      other member defined and proved, and proves the inherited
      `FromNatCorrect` like this, recursing on itself under a `decreases`
      clause of its own:

          lemma FromNatCorrect(n: nat)
            decreases n
          {
            if n > 0 {
              FromNatCorrect(n - 1);
            }
            L3.FromNatCorrect(n);
          }

      What does `scripts/vcheck` say about the file?
      Answer form: `D:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P3d

  // item: Q08.P4dv S7 verdict
  /** **P4.** A recursive definition with no measure written. A binary tree
      and its size, recursive on both children, with no `decreases` clause:

        Dafny:
          datatype Tree = Leaf | Node(l: Tree, r: Tree)

          function Size(t: Tree): nat
          {
            match t
            case Leaf => 1
            case Node(l, r) => Size(l) + Size(r) + 1
          }

        Verus:
          pub enum Tree {
              Leaf,
              Node(Box<Tree>, Box<Tree>),
          }

          pub open spec fn size(t: Tree) -> nat {
              match t {
                  Tree::Leaf => 1,
                  Tree::Node(l, r) => size(*l) + size(*r) + 1,
              }
          }

      What does `scripts/vcheck` say about each file?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P4dv

  // item: Q08.P5dv S8 verdict
  /** **P5.** A weakest precondition, by hand. Over the integers, the program

          x := x + 1;
          if x > 0 then y := x else y := 0

      and the postcondition `y > 0`. Which formula over the initial value of
      `x` is the program's weakest precondition for that postcondition (up to
      logical equivalence)?

          a) x > 0
          b) x >= 0
          c) true
          d) x > -2

      Answer form: one letter, `a`, `b`, `c` or `d`. */
  // SLOT: CHECK P5dv

  // ===========================================================================
  // Test-out (closed book: after every prediction of this module is recorded,
  // before any reading; `scripts/firsttry.sh Q08 --check` refuses T1's first
  // try until then)
  // ===========================================================================

  // Given (not an item): a machine word, as a newtype whose values are the
  // integers in its range.
  newtype u64 = x: int | 0 <= x < 0x1_0000_0000_0000_0000

  // item: Q08.T1d S7
  /** **T1.** (test-out) Add two machine words and a carry: return the low
      word of the sum and the carry out. Every value of type `u64` is a
      machine word, so the body may give `lo` and `hi` only values that are
      provably in range. Which values can the full sum take, and when does it
      fit in one word? */
  method AddWithCarry(x: u64, y: u64, c: u64) returns (lo: u64, hi: u64)
    requires c <= 1
    ensures lo as int + hi as int * BASE == x as int + y as int + c as int
    ensures hi <= 1
  {
    assume false;  // HOLE: delete this line and implement
  }
  // Hint(1): compute the full sum as an `int` first.
  // Hint(2): two cases, by comparing the sum with `BASE`; in each, convert
  //    back to `u64` with `as`, which the verifier checks.

  method AddWithCarryCheck() {
    // Uncomment as you go:
    // var lo, hi := AddWithCarry(3, 4, 1);
    // assert hi == 0 && lo == 8;
  }

  // ===========================================================================
  // Worked example
  // ===========================================================================

  // item: Q08.W1d S6
  /** **W1.** A client of the frozen statements. `Limbs` is L4's limb
      implementation of QG_L4_Spec (QG_L4_Limbs). This client calls only the
      lemmas whose statements QG_L4_Spec fixes, `FromNatCorrect`, `AddCorrect`
      and `CmpCorrect`, and never looks inside the definitions: what it
      concludes holds for any module that refines QG_L4_Spec, whatever its
      representation. Here: adding a positive number gives a well-formed
      result that compares above the first argument. */
  lemma SumAbove(m: nat, n: nat)
    requires n > 0
    ensures Limbs.Wf(Limbs.Add(Limbs.FromNat(m), Limbs.FromNat(n)))
    ensures Limbs.Cmp(Limbs.FromNat(m), Limbs.Add(Limbs.FromNat(m), Limbs.FromNat(n))) < 0
  {
    Limbs.FromNatCorrect(m);
    Limbs.FromNatCorrect(n);
    // Both arguments are well-formed with values m and n, so the statement of
    // AddCorrect applies: the sum is well-formed with value m + n.
    Limbs.AddCorrect(Limbs.FromNat(m), Limbs.FromNat(n));
    // Both arguments of Cmp are well-formed; CmpCorrect turns the order of
    // the values (m < m + n) into the sign of Cmp.
    Limbs.CmpCorrect(Limbs.FromNat(m), Limbs.Add(Limbs.FromNat(m), Limbs.FromNat(n)));
  }

  // ===========================================================================
  // WRITE card (a success here, a pinned failure demo in specimens/Q08/)
  // ===========================================================================

  // item: Q08.C1d S6 write:refines
  /** ### C1 — card: `module M refines QG_L4_Spec`.
      Jurisdiction: an implementation held to frozen statements. L4's abstract
      module QG_L4_Spec declares a type, four functions and four lemmas, with
      the lemmas' statements and no bodies. A module that refines it defines
      the type and every function, and proves each lemma: the refining lemma
      repeats only the lemma's name and parameters, and its statement is the
      one it inherits. It may add declarations of its own, such as a helper
      lemma. Success: `CardNat`, a model in which a big number is a `nat`.
      Failure: specimens/Q08/card-c1d.dfy.specimen (a definition that breaks an
      inherited statement). */
  module CardNat refines QG_L4_Spec {
    type BigNat = nat

    ghost function Val(x: BigNat): nat { x }
    ghost predicate Wf(x: BigNat) { true }

    function Zero(): BigNat { 0 }
    function FromNat(n: nat): BigNat { n }
    function Add(a: BigNat, b: BigNat): BigNat { a + b }
    function Cmp(a: BigNat, b: BigNat): int { if a < b then -1 else if a == b then 0 else 1 }

    lemma ZeroCorrect()
    {
    }

    lemma FromNatCorrect(n: nat)
    {
    }

    lemma AddCorrect(a: BigNat, b: BigNat)
    {
    }

    lemma CmpCorrect(a: BigNat, b: BigNat)
    {
    }

    // A helper lemma of the refining module's own: not in QG_L4_Spec.
    lemma AddCommutes(a: BigNat, b: BigNat)
      ensures Add(a, b) == Add(b, a)
    {
    }
  }

  // ===========================================================================
  // Final section: divergence card. Record every prediction of this module
  // (scripts/firsttry.sh Q08 --check) before you read on or open its demos.
  // ===========================================================================

  // item: Q08.C4dv S6 diverge:q08-c4
  /** ### C4 — divergence card. Demos: specimens/Q08/card-c4dv-d.dfy.specimen
      and specimens/Q08/card-c4dv-v.rs.specimen. */
}

// =============================================================================
// ## Exercise (AGENTIC) — the spec-to-proof flagship (`/contract Q08`)
// =============================================================================
// Files: dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy and
// verus/q/q08_internals_ii/src/agent.rs. Shipped state: green, with no hole,
// and three empty sections, STATEMENTS, WITNESSES and HELPERS. Check commands
// (each file's header gives the steps in full):
//
//     scripts/vcheck dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy
//     scripts/vcheck verus/q/q08_internals_ii/src/agent.rs
//
// Steps (after this unit and the Verus crate are done):
// 1. Before the run (this is your half): in STATEMENTS, state each operation
//    the section names, as a signature with its correctness statement and no
//    body; in WITNESSES, write checks that show every statement satisfiable
//    and meaningful. Copy each file to research/q08_statements.dfy (.rs) and
//    commit both.
// 2. In a FRESH session, run /contract Q08 (one file per run): the contractor
//    writes the bodies and proofs, and helpers only under HELPERS.
// 3. Audit the delivery: the freeze check against your committed statements,
//    the diff's scope, each helper's statement, your witnesses, and the
//    transcript. Write in the file's AUDIT block which statement cost the
//    contractor most, and why.
// The lesson: you own the statements and the contractor owns the proofs; a
// green delivery is only as good as what you stated.

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line (the test-out first tries are
recorded by `scripts/firsttry.sh Q08 --check`, not here).
  setup 5 · test-out 10 · read 45 · worked 30 · cards 6 · predicts 20 ·
  holes 56 · verified wp 30 · agent 20 · paper 15 ·
  exit + explain-back 28 · calib 5 · total 270
Then run `scripts/firsttry.sh Q08 --record`.
*/
