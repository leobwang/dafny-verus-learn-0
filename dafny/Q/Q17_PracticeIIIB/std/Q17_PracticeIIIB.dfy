/*!
# Q17 — Practice III-B (Exercises)

Imports: none. H1 is about a priority queue of naturals and needs neither
the BigNat spine nor the standard library; the unit includes the spine
(layers L1-L7) as every unit of the tier does, and this file uses none of
it. The unit's second file, std/Q17_Vcgen.dfy, holds the module `Q17_Vcgen`
(H3).

How to work this module (the hard practice tier), in this order:
1. The blueprint first: problem B1 of paper/Q17_problems.tex (H1's
   invariant and lemmas; H3's statements in words), graded by
   `/grade-paper Q17` (3 or more on every dimension) BEFORE any formal
   work. This module has no prediction block.
2. H1 here; then H2 in the Verus crate (verus/q/q17_practice_iiib, its file
   src/perm.rs); then H3 in std/Q17_Vcgen.dfy, which ends with the commit
   of your statements to research/q17_statements.dfy; then the metatheory
   run, `/contract Q17` on dafny/Q/Q17_PracticeIIIB/agent/
   Q17_AgentMetatheory.dfy, and its audit.
3. Each problem ships its statement (H3: its prose) and nothing else: no
   skeleton, no hint about the decomposition. Your own predicates and
   lemmas go in the item's `HELPERS` area, above the item; a helper method
   of the class goes inside the class.
4. Done = `scripts/vcheck --gate dafny/Q/Q17_PracticeIIIB/std` prints only
   the summary line and exits 0, `scripts/vaudit dafny/Q/Q17_PracticeIIIB/std`
   reports no finding, AND `scripts/firsttry.sh Q17 --report --strict`
   exits 0; then `/review-code Q17` (bar `library-pr`) and `/grade-paper
   Q17` after the formal work. The unit's gate covers this file and
   std/Q17_Vcgen.dfy together.
5. Stuck for 20 minutes? /tutor Q17.

This file ships with exactly 3 holes, all of them H1's (the constructor,
`Insert` and `ExtractMin`), each counted by `scripts/vcheck`;
std/Q17_Vcgen.dfy ships 1 (H3). Q17 as a whole ships 6 holes (4 in this
unit and 2 in the Verus crate, H2's two operations), no prediction and no
exit file: the module's exit is the verifier part above plus the two
reviews.

Item kinds: W worked example · H one problem (one or more holes) · A an
agentic run (the agent file).
*/
module Q17_PracticeIIIB {

  // ===========================================================================
  // The priority queue (H1)
  // ===========================================================================

  // Given (not an item): a priority queue of naturals, specified on its ghost
  // model `Model` and its ghost frame `Repr`.
  trait PQueue {
    ghost var Model: multiset<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr

    method Insert(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Model == old(Model) + multiset{x} && fresh(Repr - old(Repr))

    method ExtractMin() returns (m: nat)
      requires Valid() && |Model| > 0
      modifies Repr
      ensures Valid() && m in old(Model) && (forall y | y in old(Model) :: m <= y)
      ensures Model == old(Model) - multiset{m} && fresh(Repr - old(Repr))
  }

  // HELPERS (Q17.H1d): your predicates and lemmas, here.

  // item: Q17.H1d S6
  // uses: dynamic-frames, invariant
  /** **H1.** Implement the trait by `ArrayPQ`: the queue's elements are the
      prefix `a[..n]` of the array `a`, kept in descending order, so the
      minimum is the prefix's last element. Write the representation
      invariant `Valid()` (it replaces the placeholder `true`), the
      constructor, `Insert` and `ExtractMin`, meeting the trait's model and
      frame specifications, which the class restates. When the array is
      full, `Insert` moves the elements to a new, larger array. The plain
      implementation, with an invariant that says only what the prefix
      holds, does not verify. Then uncomment `Peek` and the check below the
      class. Which objects does each method write, and which of them are
      new? What must `Valid()` say for `ExtractMin`'s answer to be the
      minimum? */
  class ArrayPQ extends PQueue {
    var a: array<nat>
    var n: nat

    ghost predicate Valid()
      reads this, Repr
    {
      true
    }

    constructor ()
      ensures Valid() && fresh(Repr) && Model == multiset{}
    {
      assume false;  // HOLE: delete this line and implement
    }

    method Insert(x: nat)
      requires Valid()
      modifies Repr
      ensures Valid() && Model == old(Model) + multiset{x} && fresh(Repr - old(Repr))
    {
      assume false;  // HOLE: delete this line and implement
    }

    method ExtractMin() returns (m: nat)
      requires Valid() && |Model| > 0
      modifies Repr
      ensures Valid() && m in old(Model) && (forall y | y in old(Model) :: m <= y)
      ensures Model == old(Model) - multiset{m} && fresh(Repr - old(Repr))
    {
      assume false;  // HOLE: delete this line and implement
    }

    // `Peek` reads the queue through your representation.
    // Uncomment as you go:
    // method Peek() returns (m: nat)
    //   requires Valid() && |Model| > 0
    //   ensures m in Model && forall y | y in Model :: m <= y
    // {
    //   m := a[n - 1];
    // }
  }

  method ArrayPQCheck()
  {
    // Uncomment as you go:
    // var q := new ArrayPQ();
    // q.Insert(5);
    // q.Insert(3);
    // q.Insert(8);
    // var m := q.ExtractMin();
    // assert m == 3 && q.Model == multiset{5, 8};
  }
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 10 · blueprint 30 · priority-queue refinement with frames (D) 50 ·
  permission ring buffer (V, gated) 50 · VC-generator soundness statements
  (D) 35 · metatheory run 15 · /review-code 15 · paper 15 · ledger 5 ·
  total 225
Then run `scripts/firsttry.sh Q17 --record`.
*/
