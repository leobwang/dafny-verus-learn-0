/*!
# Q10 — Practice I-A (Reference Solution)

Hole-free reference for `dafny/Q/Q10_PracticeIA/std/Q10_PracticeIA.dfy`
(author-only; never learner-visible). Same modules, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live, and every verdict switch is enabled; the
verdict answers are in `Solutions/slots/Q10.slots`, their hashes in
`expected/Q10.pins`. The annotation hole H4d marks the learner's lines with
`@hole-begin` / `@hole-end` for the empty-body gate's region mode, and the
`// cfree:` lines are the construct-free answers the author measured
(Solutions/plans/Q10-code-notes.md).

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. Every output the module quotes is pinned (`expected/Q10.counts`,
`expected/Q10.freeze`). `Q10_Search` turns nonlinear arithmetic off and comes
last in the file, as in the exercise file.
*/
module Q10_PracticeIA {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened Std.Wrappers

  // ===========================================================================
  // The prediction block.
  // ===========================================================================

  // item: Q10.P1dv S1 verdict
  /** **P1.** Warm-up: a cast to one word. Dafny, in a module of this unit's
      options (the `std` unit), with layer L1 opened:

          method Low(x: nat) returns (b: bv64)
            requires x < BASE
            ensures b as nat == x
          {
            b := x as bv64;
          }

      Verus, in a crate of its own:

          fn low(x: u128) -> (r: u64)
              requires
                  x < 0x1_0000_0000_0000_0000u128,
              ensures
                  r == x,
          {
              x as u64
          }

      What does `scripts/vcheck` say about each?
      Answer form: `D:<v> V:<v>`, each v one of `ok` (verifies), `fail` (a
      verification error), `timeout` (out of resource or time), `err:<stage>`
      (refused before verification; the stage as `scripts/vcheck` prints it:
      `parse` or `resolve`). */
  // CHECK P1dv

  // item: Q10.P2dv S4 verdict
  /** **P2.** Warm-up: a loop that stops on `!=`. Dafny, in a module of this
      unit's options, with no `decreases` clause on the loop:

          method Count(s: seq<nat>) returns (i: nat)
            ensures i == |s|
          {
            i := 0;
            while i != |s|
              invariant i <= |s|
            {
              i := i + 1;
            }
          }

      Verus, in a crate of its own:

          fn count(v: &Vec<u64>) -> (i: usize)
              ensures
                  i == v.len(),
          {
              let mut i: usize = 0;
              while i != v.len()
                  invariant
                      i <= v.len(),
                  decreases v.len() - i,
              {
                  i = i + 1;
              }
              i
          }

      What does `scripts/vcheck` say about each?
      Answer form: `D:<v> V:<v>`, each v as in P1. */
  // CHECK P2dv

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q10.H1d S1
  // uses: exec-check, lemma-call
  // pair: Q10.H1v
  // form: no-call:ToNat
  // cfree: { var v := ToNat(s); if v < BASE { r := Some(v); } else { r := None; } }
  /** **H1.** A canonical number as one word.

      Reference: the empty number is 0, and a single limb is its own value
      (the sequence identity `s == [s[0]]`, then L2's `ToNatSingleton`); a
      canonical number of two or more limbs is at least `Pow(|s| - 1)` (L5's
      `CanonicalLower`), and `Pow(|s| - 1) == BASE * Pow(|s| - 2)` with
      `Pow(|s| - 2) > 0` (L5's `PowPositive`) puts it at or above `BASE`. The
      `cfree:` line computes `ToNat` in compiled code: it verifies (the layer
      function is compiled), which the prompt's method clause excludes in
      words only (Solutions/plans/Q10-code-notes.md). */
  method ToU64(s: seq<nat>) returns (r: Option<nat>)
    requires Canonical(s)
    ensures r.Some? <==> ToNat(s) < BASE
    ensures r.Some? ==> r.value == ToNat(s)
  {
    if |s| == 0 {
      return Some(0);
    } else if |s| == 1 {
      assert s == [s[0]];
      ToNatSingleton(s[0]);
      return Some(s[0]);
    } else {
      CanonicalLower(s);
      PowPositive(|s| - 2);
      assert BASE <= Pow(|s| - 1);
      return None;
    }
  }

  method ToU64Check()
  {
    var r := ToU64([5]);
    assert r == Some(5);
  }

  // item: Q10.H2d S2
  // uses: quantified-ensures
  /** **H2.** Specify a shift.

      Reference `ensures`: `Valid(r) && ToNat(r) == BASE * ToNat(s) &&
      (Canonical(s) ==> Canonical(r))`. Too weak (the canonicity conjunct
      left out): `ShiftTwice` fails its `Canonical(r)`; too strong (`r == [0]
      + s`): the body fails on the empty input. */
  method Shift(s: seq<nat>) returns (r: seq<nat>)
    requires Valid(s)
    ensures Valid(r) && ToNat(r) == BASE * ToNat(s) && (Canonical(s) ==> Canonical(r))
  {
    if |s| == 0 {
      r := [];
    } else {
      r := [0] + s;
    }
  }

  /** The given client: with `Shift` specified, it verifies with no assume. */
  method ShiftTwice(s: seq<nat>) returns (r: seq<nat>)
    requires Canonical(s)
    ensures Canonical(r) && ToNat(r) == BASE * (BASE * ToNat(s))
  {
    var r1 := Shift(s);
    r := Shift(r1);
  }

  // item: Q10.H3d S3
  // uses: assert, lemma-recursion
  // pair: Q10.H3v
  /** **H3.** The top limb's place value: an assertion repair.

      Reference: the quoted attempt plus one sequence identity, which lets
      the recursive call's statement (about `s[1..][..|s| - 2]`) meet the
      unfolding of `ToNat(s[..|s| - 1])` (about `s[..|s| - 1][1..]`). */
  lemma ToNatTopLimb(s: seq<nat>)
    requires |s| > 0
    ensures ToNat(s) == ToNat(s[..|s| - 1]) + Pow(|s| - 1) * s[|s| - 1]
    decreases |s|
  {
    if |s| > 1 {
      ToNatTopLimb(s[1..]);
      assert s[1..][..|s| - 2] == s[..|s| - 1][1..];
      assert Pow(|s| - 1) * s[|s| - 1] == BASE * (Pow(|s| - 2) * s[|s| - 1]);
    } else {
      assert s[..0] == [];
    }
  }

  // item: Q10.H4d S4
  // uses: invariant
  // pair: Q10.H4v
  // cfree: { n := |Normalize(s)|; }
  /** **H4.** The forward-scan normalize: the loop invariants.

      Reference: three invariants: the bounds `0 <= n <= i <= |s|`; the limb
      just below `n`, when there is one, is not zero; and every limb from `n`
      up to `i` is zero. At the exit `i == |s|`, which is exactly L5's
      `NormalizeTrim` precondition. */
  method NormLen(s: seq<nat>) returns (n: nat)
    ensures n <= |s| && s[..n] == Normalize(s)
  {
    n := 0;
    var i := 0;
    while i < |s|
      // @hole-begin Q10.H4d
      invariant 0 <= n <= i <= |s|
      invariant n == 0 || s[n - 1] != 0
      invariant forall j | n <= j < i :: s[j] == 0
      // @hole-end Q10.H4d
      decreases |s| - i
    {
      if s[i] != 0 {
        n := i + 1;
      }
      i := i + 1;
    }
    NormalizeTrim(s, n);
  }

  method NormLenCheck()
  {
    var n := NormLen([3, 0]);
    assert n == 1;
  }
}

// =============================================================================
// The search item: nonlinear arithmetic is off in this module, which comes
// last in the file.
// =============================================================================
module {:disableNonlinearArithmetic} Q10_Search {
  import opened QG_L1_BigNat
  import opened QG_L5_BigNat
  import opened Std.Arithmetic.DivMod

  // item: Q10.H5d S5
  // uses: library-call
  // pair: Q10.H5v
  /** **H5.** Search, then name: a remainder of a remainder.

      Reference: `LemmaModMod(x, Pow(n), BASE)` (`Std.Arithmetic.DivMod`:
      `x % (a * b) % a == x % a` for positive `a`, `b`), after L5's
      `PowPositive(n)`; `Pow(n + 1)` unfolds to `BASE * Pow(n)`, and Dafny's
      encoding lets the call's `Pow(n) * BASE` meet it. */
  lemma ModPowSucc(x: nat, n: nat)
    ensures 0 < Pow(n) && x % Pow(n + 1) % Pow(n) == x % Pow(n)
  {
    PowPositive(n);
    LemmaModMod(x, Pow(n), BASE);
  }
}
