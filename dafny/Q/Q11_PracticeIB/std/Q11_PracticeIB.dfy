/*!
# Q11 — Practice I-B (Exercises)

Imports: the given BigNat spine, layers L1-L5 (`QG_L1_BigNat` …
`QG_L5_BigNat`), nothing else: no earlier exercise file. This unit's
dfyconfig.toml includes the layers and turns the standard library on. The
layers are frozen and complete; read them, never edit them.

Q11's Dafny exercises are two files of this unit: this one (the prediction
block, the class W1 with H1 and H2, H5, and the VC items H7 and H8 in the
three modules at the end) and std/Q11_Wp.dfy (a small language: W2, H9). The
Verus half is the crate verus/q/q11_practice_ib (src/lib.rs and
src/perm.rs).

How to work this file (the order is the module's, for every file):
1. Predictions first: fill both slots of the prediction block below (the
   answers go in slots/Q11.slots), and record the first tries with
   `scripts/firsttry.sh Q11 --check` before you run anything they are about.
2. Then the holes, in order: H1, H2 and H5 here, H3, H4 and H6 in
   verus/q/q11_practice_ib/src/lib.rs, H7 and H8 here, H9 in
   std/Q11_Wp.dfy, H10 in verus/q/q11_practice_ib/src/perm.rs. After each,
   uncomment the checks beneath it. Read the hint only when stuck.
3. Done = `scripts/vcheck --gate dafny/Q/Q11_PracticeIB/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q11_PracticeIB/std`
   reports no finding, AND `scripts/firsttry.sh Q11 --report --strict` exits
   0, and `scripts/specfreeze --check Q11` reports no change. The unit's
   gate covers this file and std/Q11_Wp.dfy together.
4. Stuck for 20 minutes? /tutor Q11.

This file ships with exactly 5 holes: H1, H2, H5, H7 and H8, each counted by
`scripts/vcheck`; std/Q11_Wp.dfy ships 1 (H9). Q11 as a whole ships 10 holes
(6 in this unit; 4 in the Verus crate, 3 in src/lib.rs and 1 in
src/perm.rs); 2 predictions (both verdicts); and 2 exit items (the exit
files ship 1 + 1 holes). Commit every prediction BEFORE you run anything it
is about, open later files, or read CI, the registry or the plan: their
checks and headers give some predictions away.

Item kinds: P prediction (a slot) · W worked example (given, finished) · H
one-hole item · X exit item (the exit files). Slots: a verdict switch
`// SLOT: CHECK <item>` here takes its answer in slots/Q11.slots
(`P1dv = ???` → `P1dv = "<answer>"`). Fill a slot, record the first try,
and only then enable it: `// SLOT: CHECK P1dv` becomes `// CHECK P1dv`.

Exit (closed book): dafny/Q/Q11_PracticeIB/exit/Q11_Exit.dfy and
verus/q/q11_practice_ib/src/exit.rs, scored once by
`scripts/firsttry.sh Q11 --exit` (threshold 1 of the 2).
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
  // SLOT: CHECK P1dv

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
  // SLOT: CHECK P2dv

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
    /** **H1d.** Overwrite the limb at position `i` with `x`. Which objects
        does the body write, and what must the ghost fields say afterwards
        for `Valid()` to hold again? */
    method Set(i: nat, x: nat)
      requires Valid() && i < |Contents|
      modifies Repr
      ensures Valid() && Contents == old(Contents)[i := x] && fresh(Repr - old(Repr))
    {
      assume false;  // HOLE: delete this line and implement
    }
    // Hint: `Contents` is ghost: the verifier knows only what you assign to it.

    // item: Q11.H2d S6
    // uses: dynamic-frames, old, invariant
    /** **H2d.** Make this vector's contents a copy of `other`'s, with a loop.
        The two vectors share no object (`Repr !! other.Repr`), and this
        vector's array is long enough. What does the loop write, and what
        must its invariant say about the part copied so far? */
    method CopyFrom(other: LimbVec)
      requires Valid() && other.Valid() && Repr !! other.Repr
      requires |other.Contents| <= a.Length
      modifies Repr
      ensures Valid() && Contents == other.Contents && fresh(Repr - old(Repr))
      ensures other.Contents == old(other.Contents)
    {
      assume false;  // HOLE: delete this line and implement
    }
    // Hint: which heap locations may the loop change, if it says nothing
    //    about its frame, and what does the verifier then forget?
  }

  method SetCheck(v: LimbVec, w: LimbVec)
    requires v.Valid() && w.Valid() && v.Repr !! w.Repr && |v.Contents| == 3
    modifies v.Repr
  {
    // Uncomment as you go:
    // v.Set(1, 7);
    // assert v.Valid() && v.Contents[1] == 7 && |v.Contents| == 3;
    // assert w.Valid() && w.Contents == old(w.Contents);
  }

  method CopyCheck(v: LimbVec, w: LimbVec)
    requires v.Valid() && w.Valid() && v.Repr !! w.Repr && |w.Contents| <= v.a.Length
    modifies v.Repr
  {
    // Uncomment as you go:
    // v.CopyFrom(w);
    // assert v.Valid() && v.Contents == w.Contents;
    // assert w.Valid() && w.Contents == old(w.Contents);
  }

  // ===========================================================================
  // A subset type
  // ===========================================================================

  // Given (not an item): canonical limb sequences as a type of their own.
  type CanonSeq = s: seq<nat> | Canonical(s) witness []

  // item: Q11.H5d S7
  // uses: subset-type, lemma-call
  /** **H5d.** The sum of two canonical numbers, as a canonical number: the
      normalized sum. Write the function's body. Its result must be a
      `CanonSeq` (the subset constraint) with the value of the `ensures`;
      a function body may call lemmas as statements before its expression.
      Which layer lemmas say each of the two facts? */
  function AddCanon(a: CanonSeq, b: CanonSeq): (r: CanonSeq)
    ensures ToNat(r) == ToNat(a) + ToNat(b)
  // HOLE: this function has no body; write `{ … }` below the ensures line.
  // Hint: the value of `Add` (layer L4) holds only for valid arguments; is
  //    a canonical sequence valid?

  method AddCanonCheck(a: CanonSeq, b: CanonSeq, c: CanonSeq) {
    // Uncomment as you go:
    // var r := AddCanon(AddCanon(a, b), c);
    // assert Canonical(r) && ToNat(r) == ToNat(a) + ToNat(b) + ToNat(c);
  }
}

// =============================================================================
// VCs by hand (H7, H8): three modules. Q11_VcProg holds the given programs
// and postconditions; Q11_VcAnswer holds the two predicates you complete and
// imports nothing (its import list is frozen: keep it as shipped);
// Q11_VcCheck imports both and holds the two `Exact` lemmas, H7 and H8.
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

  // Q11.H7d's answer: replace the placeholder body `true`.
  ghost predicate Pre1(x: int, y: int) { true }

  // Q11.H8d's answer: replace the placeholder body `true`.
  ghost predicate Pre2(x: int, y: int) { true }
}

module Q11_VcCheck {
  import opened Q11_VcProg
  import opened Q11_VcAnswer

  // item: Q11.H7d S8
  // uses: requires, function
  // form: formula:Pre1
  /** **H7d.** VCs by hand. Compute, by hand, the weakest precondition of
      `Prog1` (in Q11_VcProg: two assignments) for `Post1`, as arithmetic over
      `x` and `y`, and write it as the body of `Pre1` in Q11_VcAnswer in place
      of the placeholder `true`. Q11_VcAnswer imports nothing, and its import
      list is frozen: the answer is your own formula, not a call of the given
      program. When `Pre1` is right, `Pre1Exact` below verifies with an empty
      body: then delete its labelled `assume false;`. Which formula over the
      initial `x` and `y` does each assignment, read from the last one back,
      turn the postcondition into? */
  lemma Pre1Exact(x: int, y: int)
    ensures Pre1(x, y) <==> Post1(Prog1(x, y))
  {
    assume false;  // HOLE: Q11.H7d — write Pre1 in Q11_VcAnswer, then delete this line
  }

  // item: Q11.H8d S8
  // uses: requires, function
  // form: formula:Pre2
  /** **H8d.** As H7d, for `Prog2` (a conditional assignment, then an
      assignment), `Post2` and `Pre2`: when `Pre2` is right, `Pre2Exact`
      verifies with an empty body; then delete its labelled `assume false;`.
      What does the conditional assignment do to the precondition? */
  lemma Pre2Exact(x: int, y: int)
    ensures Pre2(x, y) <==> Post2(Prog2(x, y))
  {
    assume false;  // HOLE: Q11.H8d — write Pre2 in Q11_VcAnswer, then delete this line
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
