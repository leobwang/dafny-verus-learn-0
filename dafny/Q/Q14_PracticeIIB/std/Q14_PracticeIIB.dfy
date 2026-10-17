/*!
# Q14 — Practice II-B (Exercises)

Imports: none in the module `Q14_Term`; the given BigNat spine, layers L1
(`QG_L1_BigNat`) to L6 (`QG_L6_BigNat`), each by name (`L1` … `L6`), and
Dafny's `Std.Arithmetic.Power` (as `Power`) in the module `Q14_Cached`;
nothing else: no earlier exercise file. The layers are frozen and complete;
read them, never edit them. Nonlinear arithmetic is off in `Q14_Cached`
(the attribute on its `module` line), which comes last in this file; it is on
in `Q14_Term`. The unit's second file, std/Q14_Loop.dfy, holds the module
`Q14_Loop`.

How to work this file (the intermediate practice tier), in this order: the
prediction P1; then H1 (the refinement, in `Q14_Cached` below); then the
Verus crate verus/q/q14_practice_iib (H2, then H3's Verus half); then H3 here
(in `Q14_Term`); then std/Q14_Loop.dfy (H4); then the crate's src/perm.rs
(H5).
1. Predictions first: fill the slot of the prediction block below (its answer
   goes in slots/Q14.slots), then record the first try with
   `scripts/firsttry.sh Q14 --check`, before you run anything it is about.
2. Each item ships its statement and nothing else: no skeleton. You choose
   the induction and the shape of the proof. Each item allows at most one
   lemma of your own: write it in the item's `HELPERS` area, above the item,
   with a statement of your own and its proof.
3. Done = `scripts/vcheck --gate dafny/Q/Q14_PracticeIIB/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q14_PracticeIIB/std`
   reports no finding, AND `scripts/firsttry.sh Q14 --report --strict` exits
   0. The unit's gate covers this file and std/Q14_Loop.dfy together.
4. Stuck for 20 minutes? /tutor Q14.

This file ships with exactly 2 holes (H1 and H3), each counted by
`scripts/vcheck`; std/Q14_Loop.dfy ships 1 (H4). Q14 as a whole ships 9
holes (3 in this unit and 6 in the Verus crate: H2's three methods, H3 and
H5's two operations); 1 prediction (a verdict, in the block below); and 1
exit item (the Dafny exit file ships 1 hole; the Verus exit file ships
none). Commit the prediction BEFORE you run anything it is about, open later
files, or read CI, the registry or the plan: their checks and headers give
some predictions away.

Item kinds: P prediction (a slot) · W worked example · H one-hole item · X
exit item (the exit files). Slots: a verdict switch `// SLOT: CHECK <item>`
here takes its answer in slots/Q14.slots (`P1dv = ???` → `P1dv =
"<answer>"`). Fill the slot, record the first try, and only then enable it:
`// SLOT: CHECK P1dv` becomes `// CHECK P1dv`.

Exit (closed book, timed): dafny/Q/Q14_PracticeIIB/exit/Q14_Exit.dfy, scored
once by `scripts/firsttry.sh Q14 --exit` (threshold: the 1 item must pass).
*/
module Q14_Term {

  // ===========================================================================
  // The prediction block. Commit the prediction of this module before you
  // read past this block, and record the first try:
  //     scripts/firsttry.sh Q14 --check
  // The verdict answer goes in slots/Q14.slots. The Verus crate has no
  // prediction block of its own.
  // Verdict vocabulary for `D:<v> V:<v>` answers: `ok` (verifies), `fail` (a
  // verification error), `timeout` (out of resource or time), `err:<stage>`
  // (refused before verification; <stage> as scripts/vcheck prints it:
  // `parse` or `resolve`).
  // ===========================================================================

  // item: Q14.P1dv S7 verdict
  /** **P1.** Warm-up: a recursion that swaps its two arguments and shortens
      one of them.

        Dafny, with no `decreases` clause:
          function Swap2(a: seq<nat>, b: seq<nat>): nat
          {
            if |a| == 0 then |b| else Swap2(b, a[1..])
          }

        Verus (inside `verus! { }`, with `use vstd::prelude::*;`), with the
        measure written as the two lengths in parameter order:
          pub open spec fn swap2(a: Seq<nat>, b: Seq<nat>) -> nat
              decreases a.len(), b.len(),
          {
              if a.len() == 0 { b.len() } else { swap2(b, a.drop_first()) }
          }

      Each is a file of its own. What does `scripts/vcheck` say about each?
      Answer form: `D:<v> V:<v>` with the verdict vocabulary above. */
  // SLOT: CHECK P1dv

  // ===========================================================================
  // Termination (H3's Dafny half; work it after the Verus crate's H3)
  // ===========================================================================

  // Given (not an item): the two sequences' elements in turn, from `a`; once
  // one runs out, the rest of the other.
  function Interleave(a: seq<nat>, b: seq<nat>): seq<nat>
    decreases |a| + |b|
  {
    if |a| == 0 then b else [a[0]] + Interleave(b, a[1..])
  }

  // HELPERS (Q14.H3d): at most one lemma of your own, here.

  // item: Q14.H3d S7
  // uses: decreases, lemma-recursion
  // pair: Q14.H3v
  /** **H3.** Interleaving keeps the length and the elements, and appending
      one element to each side appends both at the end: when the lengths are
      equal, `a`'s new element comes first; when `a` is one longer, `b`'s
      comes first. No skeleton, and no measure: the lemma's measure is yours.
      Which call of the lemma does the swapped recursion of `Interleave`
      need, and which of the two cases does each case call? */
  lemma InterleaveSpec(a: seq<nat>, b: seq<nat>, x: nat, y: nat)
    ensures |Interleave(a, b)| == |a| + |b| &&
            multiset(Interleave(a, b)) == multiset(a) + multiset(b) &&
            (|a| == |b| ==> Interleave(a + [x], b + [y]) == Interleave(a, b) + [x, y]) &&
            (|a| == |b| + 1 ==> Interleave(a + [y], b + [x]) == Interleave(a, b) + [x, y])
  // HOLE: this lemma has no body; write its measure and `{ … }` below the
  //    ensures line.
  // Hint: a sequence with one element appended is not a sequence the
  //    verifier takes apart by itself: which slices of `a + [x]` must it see?

  method InterleaveSpecCheck(a: seq<nat>, b: seq<nat>)
    requires |a| == |b|
  {
    // Uncomment as you go:
    // InterleaveSpec(a, b, 3, 4);
    // assert |Interleave(a, b)| == 2 * |a|;
    // assert Interleave(a + [3], b + [4])[2 * |a| + 1] == 4;
  }
}

// =============================================================================
// The refinement (H1; work it first). Nonlinear arithmetic is off in this
// module (the attribute on its `module` line), which comes last in the file.
// =============================================================================
module {:disableNonlinearArithmetic} Q14_Cached refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat
  import L5 = QG_L5_BigNat
  import L6 = QG_L6_BigNat
  import Power = Std.Arithmetic.Power

  // Given (not items): a number that caches its length. `Wf` asks for
  // canonical limbs and a correct cache; `Add` normalizes L4's sum; `Cmp`
  // decides by the cached lengths first and calls L3's `Cmp` only when they
  // are equal.
  datatype Num = Num(limbs: seq<nat>, len: nat)
  type BigNat = Num

  ghost function Val(x: BigNat): nat { L1.ToNat(x.limbs) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x.limbs) && x.len == |x.limbs| }

  function Zero(): BigNat { Num([], 0) }
  function FromNat(n: nat): BigNat { var s := L2.FromNat(n); Num(s, |s|) }
  function Add(a: BigNat, b: BigNat): BigNat { var s := L2.Normalize(L4.Add(a.limbs, b.limbs)); Num(s, |s|) }
  function Cmp(a: BigNat, b: BigNat): int
  {
    if a.len < b.len then -1 else if a.len > b.len then 1 else L3.Cmp(a.limbs, b.limbs)
  }

  // Given (not items): three of QG_L4_Spec's four lemmas, proved.
  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    L6.FromNatCanonical(n);
  }

  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    L6.NormalizeAddCorrect(a.limbs, b.limbs);
  }

  // HELPERS (Q14.H1d): at most one lemma of your own, here.

  // item: Q14.H1d S6
  // uses: refines
  /** **H1.** Prove the statement `CmpCorrect` inherits from QG_L4_Spec, for
      this refinement:
          requires Wf(a) && Wf(b)
          ensures (Cmp(a, b) < 0 <==> Val(a) < Val(b)) && (Cmp(a, b) == 0 <==> Val(a) == Val(b))
      No skeleton. When the cached lengths differ, `Cmp` answers without
      looking at a limb: what must be true of the values for that answer to
      be right, and which layer lemmas bound a canonical number from above
      and from below? */
  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    assume false;  // HOLE: delete this line and write the proof
  }
  // Hint: the layers state their bounds with L1's `Pow`, and `Power`'s
  //    lemmas speak of the standard library's power: which layer lemma
  //    bridges the two?

  method CmpCorrectCheck(x: BigNat, y: BigNat)
    requires Wf(x) && Wf(y) && x.len < y.len
  {
    // Uncomment as you go:
    // CmpCorrect(x, y);
    // assert Val(x) < Val(y);
  }
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 15 · warm-up 5 · abstract-BigNat refinement (D) 35 · trait with ghost
  view (V) 30 · termination + erasure (pair) 25 · loop-rule soundness (D) 30 ·
  permission node list (V) 30 · exit 20 · paper 15 · ledger 5 · total 210
Then run `scripts/firsttry.sh Q14 --record`.
*/
