/*!
# Q11 — Practice I-B (Reference Solution)

Hole-free reference for `dafny/Q/Q11_PracticeIB/std/Q11_PracticeIB.dfy`
(author-only; never learner-visible). Same modules, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live, every verdict switch is enabled, and the two
predicates of `Q11_VcAnswer` hold their answers; the verdict answers are in
`Solutions/slots/Q11.slots`, their hashes in `expected/Q11.pins`.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Each `// cfree:` line is a construct-free answer that must
fail in place of the body it follows (H5d's inside its block, which
`firsttry --empty-body` runs; Pre1's and Pre2's in Q11_VcAnswer, outside
any item block, probed by hand); the results are in
`Solutions/plans/Q11-code-notes.md`.
*/
module Q11_PracticeIB {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat

  // ===========================================================================
  // The prediction block (the warm-ups). Commit both predictions before you
  // read past this block, and record the first tries:
  //     scripts/firsttry.sh Q11 --check
  // Verdict answers go in slots/Q11.slots.
  // Verdict vocabulary for `D:<v> V:<v>` answers: `ok` (verifies), `fail` (a
  // verification error), `timeout` (out of resource or time), `err:<stage>`
  // (refused before verification; <stage> as scripts/vcheck prints it:
  // `parse` or `resolve`).
  // ===========================================================================

  // item: Q11.P1dv S6 verdict
  /** **P1.** A method that writes a field of a second object of its own
      type.

        Dafny:
          class Cell {
            var n: nat

            method CopyTo(other: Cell)
              modifies this
            {
              other.n := n;
            }
          }

        Verus:
          pub struct Cell {
              pub n: u64,
          }

          impl Cell {
              pub fn copy_to(&mut self, other: &mut Self) {
                  other.n = self.n;
              }
          }

      Each is a file of its own. What does `scripts/vcheck` say about each?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // CHECK P1dv

  // item: Q11.P2dv S7 verdict
  /** **P2.** A ghost variable assigned from a compiled one, then used to
      compute a compiled variable.

        Dafny:
          method Bump(x: nat) {
            ghost var g := x;
            var y := g + 1;
          }

        Verus (inside `verus! { }`, with `use vstd::prelude::*;`):
          fn bump(x: u64) {
              let ghost g = x;
              let y = g + 1;
          }

      Each is a file of its own. What does `scripts/vcheck` say about each?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // CHECK P2dv

  // ===========================================================================
  // A class with dynamic frames
  // ===========================================================================

  // item: Q11.W1d S6
  /** **W1.** A vector of limbs with dynamic frames. `Repr` is the set of heap
      objects the vector is made of (itself and its array); `Valid()` reads
      exactly `this` and `Repr`; the constructor promises `fresh(Repr)`, so a
      new vector shares no object with anything that existed before.
      `Contents` is the ghost view: the first `n` slots of `a`. H1d and H2d
      are this class's methods. */
  class LimbVec {
    var a: array<nat>
    var n: nat
    ghost var Contents: seq<nat>
    ghost var Repr: set<object>

    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && a in Repr && n <= a.Length && Contents == a[..n]
    }

    constructor (cap: nat)
      ensures Valid() && fresh(Repr) && Contents == [] && a.Length == cap
    {
      a := new nat[cap];
      n := 0;
      Contents := [];
      Repr := {this, a};
    }

    // item: Q11.H1d S6
    // uses: dynamic-frames, old
    /** **H1d.** Overwrite the limb at position `i`.

        Reference: one array write, then the ghost view re-read from the
        array. The frame conjunct holds because `Repr` is not changed. */
    method Set(i: nat, x: nat)
      requires Valid() && i < |Contents|
      modifies Repr
      ensures Valid() && Contents == old(Contents)[i := x] && fresh(Repr - old(Repr))
    {
      a[i] := x;
      Contents := a[..n];
    }

    // item: Q11.H2d S6
    // uses: dynamic-frames, old, invariant
    /** **H2d.** Make this vector's contents a copy of `other`'s.

        Reference: a copy loop whose invariant is the copied prefix and whose
        loop frame is `a` alone; the disjointness of the two `Repr`s frames
        `other` (its `Valid()` and its contents) with no further invariant. */
    method CopyFrom(other: LimbVec)
      requires Valid() && other.Valid() && Repr !! other.Repr
      requires |other.Contents| <= a.Length
      modifies Repr
      ensures Valid() && Contents == other.Contents && fresh(Repr - old(Repr))
      ensures other.Contents == old(other.Contents)
    {
      var i := 0;
      while i < other.n
        invariant i <= other.n && a[..i] == other.a[..i]
        modifies a
      {
        a[i] := other.a[i];
        i := i + 1;
      }
      n := other.n;
      Contents := a[..n];
    }
  }

  method SetCheck(v: LimbVec, w: LimbVec)
    requires v.Valid() && w.Valid() && v.Repr !! w.Repr && |v.Contents| == 3
    modifies v.Repr
  {
    // reference-only: live in the twin, commented in the learner file
    v.Set(1, 7);
    assert v.Valid() && v.Contents[1] == 7 && |v.Contents| == 3;
    assert w.Valid() && w.Contents == old(w.Contents);
  }

  method CopyCheck(v: LimbVec, w: LimbVec)
    requires v.Valid() && w.Valid() && v.Repr !! w.Repr && |w.Contents| <= v.a.Length
    modifies v.Repr
  {
    // reference-only: live in the twin, commented in the learner file
    v.CopyFrom(w);
    assert v.Valid() && v.Contents == w.Contents;
    assert w.Valid() && w.Contents == old(w.Contents);
  }

  // ===========================================================================
  // A subset type
  // ===========================================================================

  // Given (not an item): canonical limb sequences as a type of their own.
  type CanonSeq = s: seq<nat> | Canonical(s) witness []

  // item: Q11.H5d S7
  // uses: subset-type, lemma-call
  /** **H5d.** The sum of two canonical numbers, as a canonical number.

      Reference: the normalized sum, with the three layer lemmas called as
      statements in the body: `AddCorrect` (the sum is valid, with the sum of
      the values), `NormalizeCanonical` (the subset constraint) and
      `NormalizeToNat` (the value is kept). */
  function AddCanon(a: CanonSeq, b: CanonSeq): (r: CanonSeq)
    ensures ToNat(r) == ToNat(a) + ToNat(b)
  {
    AddCorrect(a, b);
    NormalizeCanonical(Add(a, b));
    NormalizeToNat(Add(a, b));
    Normalize(Add(a, b))
  }
  // cfree: { Normalize(Add(a, b)) }

  method AddCanonCheck(a: CanonSeq, b: CanonSeq, c: CanonSeq) {
    // reference-only: live in the twin, commented in the learner file
    var r := AddCanon(AddCanon(a, b), c);
    assert Canonical(r) && ToNat(r) == ToNat(a) + ToNat(b) + ToNat(c);
  }
}

// =============================================================================
// VCs by hand (H7d, H8d): three modules. Q11_VcProg holds the given programs
// and postconditions; Q11_VcAnswer holds the two predicates and imports
// nothing; Q11_VcCheck imports both and holds the two `Exact` lemmas.
// =============================================================================

module Q11_VcProg {
  // Given (not an item): two straight-line programs over two integers, each
  // returning the final values of its variables, and their postconditions.

  // x := x + 2 * y; y := x - y
  function Prog1(x: int, y: int): (int, int)
  {
    var x1 := x + 2 * y;
    var y1 := x1 - y;
    (x1, y1)
  }

  ghost predicate Post1(r: (int, int)) { r.0 > 0 && r.1 < 10 }

  // y := if x > y then x - y else y - x; x := x + y
  function Prog2(x: int, y: int): (int, int)
  {
    var y1 := if x > y then x - y else y - x;
    var x1 := x + y1;
    (x1, y1)
  }

  ghost predicate Post2(r: (int, int)) { r.0 >= 5 && r.1 <= 3 }
}

module Q11_VcAnswer {
  // specfreeze: frozen-imports

  // The answer of Q11.H7d: the weakest precondition of Prog1 for Post1.
  ghost predicate Pre1(x: int, y: int) { x + 2 * y > 0 && x + y < 10 }
  // cfree[Pre1]: { Post1(Prog1(x, y)) }
  // cfree[Pre1]: { var x1 := x + 2 * y; var y1 := x1 - y; x1 > 0 && y1 < 10 }

  // The answer of Q11.H8d: the weakest precondition of Prog2 for Post2.
  ghost predicate Pre2(x: int, y: int) {
    (x > y ==> 2 * x - y >= 5 && x - y <= 3) && (x <= y ==> y >= 5 && y - x <= 3)
  }
  // cfree[Pre2]: { Post2(Prog2(x, y)) }
  // cfree[Pre2]: { var y1 := if x > y then x - y else y - x; var x1 := x + y1; x1 >= 5 && y1 <= 3 }
}

module Q11_VcCheck {
  import opened Q11_VcProg
  import opened Q11_VcAnswer

  // item: Q11.H7d S8
  // uses: requires, function
  // form: formula:Pre1
  /** **H7d.** The weakest precondition of `Prog1` for `Post1`, by hand.

      Reference: substitute backwards. `y1 < 10` with `y1 := x1 - y` is
      `x1 - y < 10`; with `x1 := x + 2 * y`, `x1 > 0 && x1 - y < 10` is
      `x + 2 * y > 0 && x + y < 10`. The lemma then verifies with an empty
      body: both sides unfold to the same arithmetic. */
  lemma Pre1Exact(x: int, y: int)
    ensures Pre1(x, y) <==> Post1(Prog1(x, y))
  {
  }

  // item: Q11.H8d S8
  // uses: requires, function
  // form: formula:Pre2
  /** **H8d.** The weakest precondition of `Prog2` for `Post2`, by hand.

      Reference: the conditional assignment splits the precondition in two
      implications, one per branch, each the backward substitution of that
      branch: for `x > y`, `y1 = x - y` and `x1 = 2 * x - y`; otherwise
      `y1 = y - x` and `x1 = y`. */
  lemma Pre2Exact(x: int, y: int)
    ensures Pre2(x, y) <==> Post2(Prog2(x, y))
  {
  }
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 15 · warm-up 8 · Repr/Valid class (D) 20 · &mut + Result API (V) 20 ·
  subset types (D) 12 · modes (V) 12 · VCs by hand 20 ·
  wp soundness for if (D) 15 · points-to primer (V) 15 · exit 20 ·
  paper 15 · ledger 5 · total 177
Then run `scripts/firsttry.sh Q11 --record`.
*/
