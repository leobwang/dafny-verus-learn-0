/*!
# Q02 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q02_FirstSyntaxI/exit/Q02_Exit.dfy` (author-only): every
block written out, every check uncommented, every `need:` line met. Silent under
`scripts/vcheck --ref`. The scored answers' evidence is in Solutions/plans/Q02-author-notes.md.
*/
module Q02_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q02.X1d S4
  // uses: decreases
  // need: function Upto(i: nat, n: nat): seq<nat>
  // need: lemma UptoCheck() ensures Upto(2, 5) == [2, 3, 4]
  // ### X1d · S4 — Write `function Upto(i: nat, n: nat): seq<nat>`, which returns
  //    `[i, i + 1, …, n - 1]` (empty when `i >= n`), by recursion that counts `i` up. Then
  //    uncomment the check.
  // (Reference) `i` grows, so Dafny's default measure (the parameters in order) fails:
  // the measure is the distance `n - i`, which the guard keeps positive at each call.
  // reference-only: the learner writes this function (a prompt-as-heading block)
  function Upto(i: nat, n: nat): seq<nat>
    decreases n - i
  { if i >= n then [] else [i] + Upto(i + 1, n) }
  // reference-only: the learner uncomments this check
  lemma UptoCheck() ensures Upto(2, 5) == [2, 3, 4] {}

  // item: Q02.X2d S6
  // uses: frame, quantified-ensures
  // need: method ZeroAt(a: array<nat>, i: nat)
  // need: ZeroAt(a, 1); assert a[0] == 7 && a[1] == 0 && a[2] == 7;
  // ### X2d · S6 — Write `method ZeroAt(a: array<nat>, i: nat)`, which sets `a[i]` to 0 when
  //    `i < a.Length`, with what Dafny needs to accept the write and a postcondition that
  //    lets the check verify. Then uncomment the check.
  // (Reference) `modifies a` permits the write; the postcondition must describe EVERY
  // element, because a caller knows about `a` after the call only what it says: the check
  // asserts the untouched elements too.
  // reference-only: the learner writes this method (a prompt-as-heading block)
  method ZeroAt(a: array<nat>, i: nat) modifies a
    ensures forall j | 0 <= j < a.Length :: a[j] == (if j == i then 0 else old(a[j]))
  { if i < a.Length { a[i] := 0; } }
  // reference-only: the learner uncomments this check
  method ZeroAtCheck() {
    var a := new nat[3](_ => 7);
    ZeroAt(a, 1);
    assert a[0] == 7 && a[1] == 0 && a[2] == 7;
  }

  // item: Q02.X3d S3
  // uses: assert-by
  // need: lemma ToNatDropTwoZeros(s: seq<nat>)
  // need: ensures ToNat(s[..|s| - 2]) == ToNat(s)
  /** **X3d.** Dropping the two most significant limbs, both zero, keeps the value.
      (Reference) With `p := s[..|s| - 2]`, `s` is `p + [0] + [0]`: L1's worked lemma, once
      on `p` and once on `p + [0]`, each inside its own `assert … by`, and the sequence
      equality closes the chain. */
  lemma ToNatDropTwoZeros(s: seq<nat>)
    requires |s| >= 2 && s[|s| - 1] == 0 && s[|s| - 2] == 0
    ensures ToNat(s[..|s| - 2]) == ToNat(s)
  {
    var p := s[..|s| - 2];
    assert ToNat(p + [0]) == ToNat(p) by {
      ToNatAppendZero(p);
    }
    assert ToNat(p + [0] + [0]) == ToNat(p + [0]) by {
      ToNatAppendZero(p + [0]);
    }
    assert s == p + [0] + [0];
  }
}
