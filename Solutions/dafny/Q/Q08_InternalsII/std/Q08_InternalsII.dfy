/*!
# Q08 — Internals II: refinement, permissions, verified wp (Reference Solution)

Hole-free reference for `dafny/Q/Q08_InternalsII/std/Q08_InternalsII.dfy`
(author-only; never learner-visible). Same module, imports, names, statements,
item markers and order as the exercise file. The test-out hole is filled, its
check is live, and every verdict switch is enabled; the verdict answers are in
`Solutions/slots/Q08.slots`, their hashes in `expected/Q08.pins`.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned: the count pins in
`expected/Q08.counts`, the statement freeze in `expected/Q08.freeze`, the
WRITE-card failure demo by its in-file `// EXPECT` line, and the divergence
demos by their sidecars under `expected/specimens/Q08/`.
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
  // CHECK P1dv

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
  // CHECK P3d

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
  // CHECK P4dv

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
  // CHECK P5dv

  // ===========================================================================
  // Test-out (closed book: after every prediction of this module is recorded,
  // before any reading; `scripts/firsttry.sh Q08 --check` refuses T1's first
  // try until then)
  // ===========================================================================

  // Given (not an item): a machine word, as a newtype whose values are the
  // integers in its range.
  newtype u64 = x: int | 0 <= x < 0x1_0000_0000_0000_0000

  // item: Q08.T1d S7
  /** **T1.** (test-out) Add two machine words and a carry.

      Reference: the full sum `s` lies in `[0, 2 * BASE - 1]`, so it is either
      a word itself (carry out 0) or a word plus `BASE` (carry out 1). Each
      `as u64` is a checked conversion: the verifier proves that the value is
      in the newtype's range, which the case split makes evident. The carry
      out is a literal in each branch, so the postcondition's product is a
      product by 0 or by 1. */
  method AddWithCarry(x: u64, y: u64, c: u64) returns (lo: u64, hi: u64)
    requires c <= 1
    ensures lo as int + hi as int * BASE == x as int + y as int + c as int
    ensures hi <= 1
  {
    var s: int := x as int + y as int + c as int;
    if s < BASE {
      lo, hi := s as u64, 0;
    } else {
      lo, hi := (s - BASE) as u64, 1;
    }
  }

  method AddWithCarryCheck() {
    // reference-only: live in the twin, commented in the learner file
    var lo, hi := AddWithCarry(3, 4, 1);
    assert hi == 0 && lo == 8;
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
// — clearly marked: everything below answers the agentic file —
// =============================================================================
// The reference statements and delivery of
// dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy (and of its Verus twin)
// are that file's own twin, Solutions/dafny/Q/Q08_InternalsII/agent/
// Q08_AgentFlagship.dfy (Solutions/verus/q/q08_internals_ii/src/agent.rs): a
// reference set of statements and witnesses, the reference delivery with its
// helpers, and the author's note on the statement pitfalls and the soft spots,
// in a closing section under this same heading. They live there, beside the
// file they answer, so one copy is verified and kept.

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line (the test-out first tries are
recorded by `scripts/firsttry.sh Q08 --check`, not here).
  setup 5 · test-out 10 · read 45 · worked 30 · cards 6 · predicts 20 ·
  holes 56 · verified wp 30 · agent 20 · paper 15 ·
  exit + explain-back 28 · calib 5 · total 270
Then run `scripts/firsttry.sh Q08 --record`.
*/
