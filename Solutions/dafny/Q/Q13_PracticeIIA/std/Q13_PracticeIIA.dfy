/*!
# Q13 — Practice II-A (Reference Solution)

Hole-free reference for `dafny/Q/Q13_PracticeIIA/std/Q13_PracticeIIA.dfy`
(author-only; never learner-visible). Same modules, imports, names,
statements, item markers and order as the exercise file. Every hole is
filled, every check is live, and the verdict switch is enabled; the verdict
answer is in `Solutions/slots/Q13.slots`, its hash in `expected/Q13.pins`.
Each item uses at most the one lemma of its own the tier allows, in its
`HELPERS` area.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. `Q13_Library` turns nonlinear arithmetic off and comes last in
the file, as in the exercise file.
*/
module Q13_PracticeIIA {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat

  // ===========================================================================
  // The prediction block. Commit the prediction of this module before you
  // read past this block, and record the first try:
  //     scripts/firsttry.sh Q13 --check
  // The verdict answer goes in slots/Q13.slots. The Verus crate has no
  // prediction block of its own.
  // ===========================================================================

  // item: Q13.P1dv S2 verdict
  /** **P1.** Warm-up: two specifications of one method, and a client of each.
      Dafny, in a module of this unit's options, with layers L1 and L2 opened:

          method TopA(s: seq<nat>) returns (t: nat)
            requires Canonical(s) && |s| > 0
            ensures t < BASE
          { t := s[|s| - 1]; }

          method TopB(s: seq<nat>) returns (t: nat)
            requires Canonical(s) && |s| > 0
            ensures t != 0 ==> t == s[|s| - 1]
          { t := s[|s| - 1]; }

          method ClientA(s: seq<nat>) requires Canonical(s) && |s| > 0
          { var t := TopA(s); assert t == s[|s| - 1]; }

          method ClientB(s: seq<nat>) requires Canonical(s) && |s| > 0
          { var t := TopB(s); assert t == s[|s| - 1]; }

      Verus, in a crate of its own over layer L1's `BigNat`: `top_a` and
      `top_b` return `a.limbs[a.limbs.len() - 1]` under `requires a.wf(),
      a@.len() > 0`, with `ensures t < BASE` and `ensures t != 0 ==> t ==
      a@[a@.len() - 1]`; `client_a` and `client_b` call them and
      `assert(t == a@[a@.len() - 1])`.

      Which clients verify? Answer form: `D:<labels> V:<labels>`, the labels
      `a` and `b` of the clients that verify, in label order (`D:a b`), or
      `none`. */
  // CHECK P1dv

  // ===========================================================================
  // Holes
  // ===========================================================================

  // HELPERS (Q13.H2d): at most one lemma of your own, here.
  // reference-only: the learner's own helper (the tier allows one)
  lemma NormalizeIdem(s: seq<nat>)
    ensures Normalize(Normalize(s)) == Normalize(s)
    decreases |s|
  {
    if |s| > 0 && s[|s| - 1] == 0 {
      NormalizeIdem(s[..|s| - 1]);
    }
  }

  // item: Q13.H2d S4
  // uses: lemma-recursion
  /** **H2.** Normalizing twice changes nothing, and normalizing a
      concatenation keeps the low part whole unless the high part normalizes
      away. No skeleton: the induction is yours. Which of the two
      postconditions does the other one need, and on which argument does the
      recursion shrink? */
  lemma NormalizeConcat(a: seq<nat>, b: seq<nat>)
    ensures Normalize(Normalize(a + b)) == Normalize(a + b) &&
            Normalize(a + b) == (if Normalize(b) == [] then Normalize(a) else a + Normalize(b))
    decreases |b|
  {
    NormalizeIdem(a + b);
    if |b| > 0 {
      if b[|b| - 1] == 0 {
        assert (a + b)[..|a + b| - 1] == a + b[..|b| - 1];
        NormalizeConcat(a, b[..|b| - 1]);
      }
    } else {
      assert a + b == a;
    }
  }

  method NormalizeConcatCheck()
  {
    NormalizeConcat([3], [0, 0]);
    assert Normalize([3] + [0, 0]) == Normalize([3]);
  }
}

// =============================================================================
// The library goals. Nonlinear arithmetic is off in this module (the
// attribute on its `module` line), which comes last in the file: a product
// step comes from a named lemma of `Std.Arithmetic.Mul` (opened).
// =============================================================================
module {:disableNonlinearArithmetic} Q13_Library {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened Std.Arithmetic.Mul

  // HELPERS (Q13.H4d): at most one lemma of your own, here.

  // item: Q13.H4d S5
  // uses: library-call, calc
  // pair: Q13.H4v
  /** **H4.** The value of `n` equal non-zero limbs. `seq(n, _ => d)` is the
      sequence of `n` copies of `d`. With nonlinear arithmetic off, every
      product step is a library lemma: which steps need one, and in which
      order do they turn `ToNat` of the sequence into the right-hand side? */
  lemma RepeatValue(d: nat, n: nat)
    requires 0 < d < BASE
    ensures ToNat(seq(n, _ => d)) * (BASE - 1) == d * (Pow(n) - 1)
    decreases n
  {
    var s := seq(n, _ => d);
    if n == 0 {
      LemmaMulBasics(d);
    } else {
      var t := seq(n - 1, _ => d);
      assert s[1..] == t;
      RepeatValue(d, n - 1);
      PowPositive(n - 1);
      var T := ToNat(t);
      var P := Pow(n - 1);
      assert ToNat(s) == d + BASE * T;
      LemmaMulIsDistributiveAddOtherWay(BASE - 1, d, BASE * T);
      LemmaMulIsAssociative(BASE, T, BASE - 1);
      assert (BASE * T) * (BASE - 1) == BASE * (d * (P - 1));
      LemmaMulIsDistributiveSub(d, P, 1);
      LemmaMulIsAssociative(BASE, d, P);
      LemmaMulIsCommutative(BASE, d);
      LemmaMulIsAssociative(d, BASE, P);
      LemmaMulIsDistributiveSub(BASE, d * P, d);
      LemmaMulIsDistributiveSub(d, BASE, 1);
      LemmaMulIsDistributiveSub(d, BASE * P, 1);
      assert Pow(n) == BASE * P;
    }
  }

  // HELPERS (Q13.H5d): at most one lemma of your own, here.

  // item: Q13.H5d S4
  // uses: invariant, decreases, library-call
  // form: loop-dir:up, no-call:ToNat
  /** **H5.** The value of a limb sequence, by a loop from the LOW limb: keep
      the place value of the next limb in a variable and add one product per
      step. The loop computes the value: `ToNat` may appear in your
      invariants, assertions and lemma calls, never in compiled code. No
      skeleton: the loop, its invariant and every product step are yours
      (nonlinear arithmetic is off). What does the loop know about the limbs
      it has not read yet? */
  // cfree: { v := 0; var i := |s|; while i > 0 invariant 0 <= i <= |s| && v == ToNat(s[i..]) { assert s[i - 1..][1..] == s[i..]; v := s[i - 1] + BASE * v; i := i - 1; } assert s[0..] == s; }
  // cfree: { v := 0; var j := 0; while j < |s| invariant 0 <= j <= |s| && v == ToNat(s[|s| - j..]) decreases |s| - j { assert s[|s| - j - 1..][1..] == s[|s| - j..]; v := s[|s| - j - 1] + BASE * v; j := j + 1; } assert s[0..] == s; }
  // cfree: { v := ToNat(s); }
  // cfree: { v := ToNat(s); var j := 0; while j < 1 { j := j + 1; } }
  method ValueLoop(s: seq<nat>) returns (v: nat)
    ensures v == ToNat(s)
  {
    v := 0;
    var w: nat := 1;
    var i := 0;
    assert s[0..] == s;
    LemmaMulBasics(ToNat(s));
    while i < |s|
      invariant 0 <= i <= |s| && w == Pow(i)
      invariant v + w * ToNat(s[i..]) == ToNat(s)
      decreases |s| - i
    {
      ghost var t := ToNat(s[i + 1..]);
      assert ToNat(s[i..]) == s[i] + BASE * t by {
        assert s[i..][1..] == s[i + 1..];
      }
      MulNonneg(w, s[i]);
      LemmaMulIsDistributiveAdd(w, s[i], BASE * t);
      LemmaMulIsAssociative(w, BASE, t);
      LemmaMulIsCommutative(w, BASE);
      v := v + w * s[i];
      w := w * BASE;
      i := i + 1;
    }
    LemmaMulBasics(w);
  }

  method ValueLoopCheck()
  {
    var v := ValueLoop([2, 1]);
    assert v == 2 + BASE;
  }
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 15 · warm-up 5 · sub with borrow (V) 35 · normalize idempotent (D) 30 ·
  prose statement (V) 25 · library goal (pair) 30 · accumulator (D) 20 ·
  exit 20 · paper 15 · ledger 5 · total 200
Then run `scripts/firsttry.sh Q13 --record`.
*/
