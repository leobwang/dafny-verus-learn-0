/*!
# Q15 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q15_PracticeIIC/exit/Q15_Exit.dfy`
(author-only; never learner-visible). Same module, imports, statement and
item marker. The `cfree:` lines are the construct-free answers the author
measured: each verifies and fails the block's form.
*/
module Q15_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q15.X1d S11
  // need: lemma NoCarryValid(a: seq<nat>, b: seq<nat>)
  // need: ensures Valid(a) && Valid(b)
  // form: trigger
  // cfree: { assert forall i | 0 <= i < |a| :: a[i] + b[i] < BASE; }
  // cfree: { forall i | 0 <= i < |a| ensures a[i] < BASE && b[i] < BASE { assert a[i] + b[i] < BASE; } }
  /** **X1.** No carry, so both are digits. The hypothesis is a quantified
      fact whose trigger, as given, never fires on the terms the conclusion
      holds. Prove the lemma with a quantified step of your own that carries
      an explicit trigger. */
  lemma NoCarryValid(a: seq<nat>, b: seq<nat>)
    requires |a| == |b|
    requires forall i {:trigger a[i], b[i]} | 0 <= i < |a| :: a[i] + b[i] < BASE
    ensures Valid(a) && Valid(b)
  {
    forall i {:trigger a[i]} {:trigger b[i]} | 0 <= i < |a|
      ensures a[i] < BASE && b[i] < BASE
    {
      assert a[i] + b[i] < BASE;
    }
  }
}
