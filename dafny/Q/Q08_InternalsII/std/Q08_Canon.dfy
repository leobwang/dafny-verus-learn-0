/*!
# Q08 — Internals II: two refinements of QG_L4_Spec (Exercises)

Imports: each module below refines L4's abstract module QG_L4_Spec and
imports the given layers L1–L4 by name (`L1` … `L4`), never opened, so that
their names cannot clash with the members it defines. Nothing else: no
earlier exercise file. The layers are frozen and complete; read them, never
edit them.

How to work this file: after the predictions, the test-out and the worked
example W1 and card C1 of std/Q08_InternalsII.dfy (that file's header gives
the module's order and its done gate, which covers this file: the unit is
dafny/Q/Q08_InternalsII/std).
1. Each hole is a refined lemma whose body is `{ assume false; }`: its
   statement is the one QG_L4_Spec gives it, quoted in its block. Replace the
   body with a proof and leave the lemma's header as it ships (the statement
   freeze, `scripts/specfreeze --check Q08`, compares it). You may add lemmas
   of your own to the refining module.
2. Read Hint(1) only when stuck, Hint(2) only when still stuck.
3. Stuck for 20 minutes? /tutor Q08.

This file ships with exactly 3 holes: H1d, H2d and H7d, each counted by
`scripts/vcheck` at its own line. Every other refined lemma of the two
modules ships proved.
*/

// A refinement whose well-formedness is canonical form, and whose addition
// normalizes L4's sum.
module {:disableNonlinearArithmetic} Q08_Canon refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.FromNat(n) }
  function Add(a: BigNat, b: BigNat): BigNat { L2.Normalize(L4.Add(a, b)) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }

  // item: Q08.H1d S6
  // uses: refines
  /** **H1d.** Prove the inherited statement of `AddCorrect`, for this
      refinement:
          requires Wf(a) && Wf(b)
          ensures Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)
      What does L4 already say about `L4.Add`, and what is left once the sum
      is normalized? */
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    assume false;  // HOLE: delete this line and write the proof
  }
  // Hint(1): L4's AddCorrect is a statement about `L4.Add` on valid
  //    arguments; is a canonical numeral valid?
  // Hint(2): L3 has two lemmas about `L2.Normalize`: one for the value, one
  //    for the form.

  // item: Q08.H2d S6
  // uses: refines
  /** **H2d.** Prove the inherited statement of `FromNatCorrect`, for this
      refinement:
          ensures Wf(FromNat(n)) && Val(FromNat(n)) == n
      L3 gives the value and validity of `L2.FromNat(n)`. Why is its top limb
      never 0? */
  lemma FromNatCorrect(n: nat)
  {
    assume false;  // HOLE: delete this line and write the proof
  }
  // Hint(1): the part L3 does not give needs an induction on `n / BASE`.
  // Hint(2): write that induction as a lemma of your own in this module,
  //    with its own statement, and call it here.
}

// A second refinement: the same well-formedness, and L4's addition itself,
// with no normalization.
module {:disableNonlinearArithmetic} Q08_CanonRaw refines QG_L4_Spec {
  import L1 = QG_L1_BigNat
  import L2 = QG_L2_BigNat
  import L3 = QG_L3_BigNat
  import L4 = QG_L4_BigNat

  type BigNat = seq<nat>

  ghost function Val(x: BigNat): nat { L1.ToNat(x) }
  ghost predicate Wf(x: BigNat) { L2.Canonical(x) }

  function Zero(): BigNat { [] }
  function FromNat(n: nat): BigNat { L2.Normalize(L2.FromNat(n)) }
  function Add(a: BigNat, b: BigNat): BigNat { L4.Add(a, b) }
  function Cmp(a: BigNat, b: BigNat): int { L3.Cmp(a, b) }

  lemma ZeroCorrect()
  {
  }

  lemma FromNatCorrect(n: nat)
  {
    L3.FromNatCorrect(n);
    L3.NormalizeToNat(L2.FromNat(n));
    L3.NormalizeCanonical(L2.FromNat(n));
  }

  lemma CmpCorrect(a: BigNat, b: BigNat)
  {
    L4.CmpCorrect(a, b);
  }

  // item: Q08.H7d S6
  // uses: refines
  /** **H7d.** Prove the inherited statement of `AddCorrect`, for this
      refinement, whose `Add` does not normalize:
          requires Wf(a) && Wf(b)
          ensures Wf(Add(a, b)) && Val(Add(a, b)) == Val(a) + Val(b)
      Why is the schoolbook sum of two canonical numerals canonical, with no
      normalization? */
  lemma AddCorrect(a: BigNat, b: BigNat)
  {
    assume false;  // HOLE: delete this line and write the proof
  }
  // Hint(1): `L4.Add` is `L4.AddC` at carry 0; prove what you need about
  //    `L4.AddC` at every carry `c <= 1`, in a lemma of your own.
  // Hint(2): `L4.AddC` is opaque; L4's `AddCCorrect` gives the value of a
  //    sum, and the value of a canonical numeral with limbs is positive.
}
