/*!
# Q10 — Practice I-A (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) to L5
(`QG_L5_BigNat`), and Dafny's standard library: `Std.Wrappers` (for
`Option`) in the module `Q10_PracticeIA`, and `Std.Arithmetic.DivMod` in the
module `Q10_Search`, all opened; nothing else: no earlier exercise file. The
layers are frozen and complete; read them, never edit them. Nonlinear
arithmetic is off in `Q10_Search` (the attribute on its `module` line),
which comes last in this file; it is on in `Q10_PracticeIA`.

How to work this file:
1. Predictions first: fill both slots of the prediction block below (the
   verdict answers go in slots/Q10.slots), then record the first tries with
   `scripts/firsttry.sh Q10 --check`, before you run anything they are
   about.
2. Replace each hole, then uncomment the checks beneath it. Every statement
   is given; each item has one hole.
3. Done = `scripts/vcheck --gate dafny/Q/Q10_PracticeIA/std` prints only the
   summary line and exits 0, `scripts/vaudit dafny/Q/Q10_PracticeIA/std`
   reports no finding, AND `scripts/firsttry.sh Q10 --report --strict` exits
   0.
4. Stuck for 20 minutes? /tutor Q10.

This file ships with exactly 5 holes (H1 to H5), each counted by
`scripts/vcheck`. Q10 as a whole ships 12 holes (5 here and 7 in the Verus
crate verus/q/q10_practice_ia/src/lib.rs); 2 predictions (both verdicts, in
the block below); and 2 exit items (the exit files ship 1 + 1 holes).
Commit every prediction BEFORE you run anything it is about, open later
files, or read CI, the registry or the plan: their checks and headers give
some predictions away.

Item kinds: P prediction (a slot) · H one-hole item · X exit item (the exit
files). Slots: a verdict switch `// SLOT: CHECK <item>` here takes its
answer in slots/Q10.slots (`P1dv = ???` → `P1dv = "<answer>"`). Fill a slot,
record the first try, and only then enable it: `// SLOT: CHECK P1dv`
becomes `// CHECK P1dv`.

Exit (closed book, timed): dafny/Q/Q10_PracticeIA/exit/Q10_Exit.dfy and
verus/q/q10_practice_ia/src/exit.rs, scored once by
`scripts/firsttry.sh Q10 --exit` (threshold 1 of the 2 items).
*/
module Q10_PracticeIA {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened Std.Wrappers

  // ===========================================================================
  // The prediction block. Commit both predictions of this module before you
  // read past this block, and record the first tries:
  //     scripts/firsttry.sh Q10 --check
  // Verdict answers go in slots/Q10.slots. The Verus crate has no prediction
  // block of its own: both predictions are here.
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
  // SLOT: CHECK P1dv

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
  // SLOT: CHECK P2dv

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q10.H1d S1
  // uses: exec-check, lemma-call
  // pair: Q10.H1v
  // form: no-call:ToNat
  /** **H1.** A canonical number as one word: `Some` of its value when the
      value fits in one limb, `None` when it does not. This is the Dafny
      mirror of the Verus crate's `to_u64`. Method clause: decide from the
      number of limbs and from the limbs themselves; `ToNat` is the
      specification, so the method's code does not call it. Why does no
      canonical number of two or more limbs fit, and what must the verifier
      be told in each case? */
  method ToU64(s: seq<nat>) returns (r: Option<nat>)
    requires Canonical(s)
    ensures r.Some? <==> ToNat(s) < BASE
    ensures r.Some? ==> r.value == ToNat(s)
  {
    assume false;  // HOLE: replace this line with the method's code and its proof
  }
  // Hint(1): split on the number of limbs. For one limb, the verifier must
  //    see that `s` is the one-element sequence of its first limb, and what
  //    that sequence is worth (layer L2).
  // Hint(2): for two or more limbs, layer L5 bounds a canonical number from
  //    below by a power of `BASE`, and says that every power is positive.

  method ToU64Check()
  {
    // Uncomment as you go:
    // var r := ToU64([5]);
    // assert r == Some(5);
  }

  // item: Q10.H2d S2
  // uses: quantified-ensures
  /** **H2.** Specify a shift. `Shift` puts a zero limb below `s`, which
      multiplies its value by `BASE`, and keeps the empty number empty. Its
      body is given and it ships with no `ensures`. Write its `ensures` so
      that the body verifies against it and the given client `ShiftTwice`
      verifies once its labelled assume (the hole) is deleted. Besides the
      value, what does a caller of `Shift` need to know about the result? */
  method Shift(s: seq<nat>) returns (r: seq<nat>)
    requires Valid(s)
  {
    if |s| == 0 {
      r := [];
    } else {
      r := [0] + s;
    }
  }
  // Hint(1): read what `ShiftTwice` promises, and what its second call of
  //    `Shift` needs from its first.
  // Hint(2): a specification can be too strong as well as too weak: check
  //    each branch of the body against yours.

  /** The given client: with `Shift` specified, it verifies with no assume. */
  method ShiftTwice(s: seq<nat>) returns (r: seq<nat>)
    requires Canonical(s)
    ensures Canonical(r) && ToNat(r) == BASE * (BASE * ToNat(s))
  {
    assume false;  // HOLE: delete this line once `Shift` is specified
    var r1 := Shift(s);
    r := Shift(r1);
  }

  // item: Q10.H3d S3
  // uses: assert, lemma-recursion
  // pair: Q10.H3v
  /** **H3.** The top limb's place value: an assertion repair. `ToNat` peels
      the lowest limb; this lemma peels the highest. This attempt does not
      verify (run it to see where it fails):

          {
            if |s| > 1 {
              ToNatTopLimb(s[1..]);
              assert Pow(|s| - 1) * s[|s| - 1] == BASE * (Pow(|s| - 2) * s[|s| - 1]);
            } else {
              assert s[..0] == [];
            }
          }

      Repair it: copy it in as the body, add what the verifier is missing,
      and change no line of the attempt. The recursive call speaks about one
      slice of `s` and the unfolding of `ToNat` about another: which two? */
  lemma ToNatTopLimb(s: seq<nat>)
    requires |s| > 0
    ensures ToNat(s) == ToNat(s[..|s| - 1]) + Pow(|s| - 1) * s[|s| - 1]
    decreases |s|
  // HOLE: this lemma has no body; write `{ … }` below the decreases line.
  // Hint(1): in the recursive case, take the tail of `s`, then drop its top
  //    limb; then drop the top limb of `s`, then take the tail. Are the two
  //    slices the same sequence?
  // Hint(2): the verifier reasons about slices of slices only when an
  //    assertion names them.

  // item: Q10.H4d S4
  // uses: invariant
  // pair: Q10.H4v
  /** **H4.** The forward-scan normalize. `NormLen` scans the limbs once,
      from the lowest up, and remembers in `n` one past the last non-zero
      limb it has seen; after the loop, L5's `NormalizeTrim` turns that into
      the postcondition. The code, the loop's `decreases` and the final call
      are given: write the loop invariants. What has the scan established
      about the limbs below `i`, and what does `NormalizeTrim` need at the
      exit? */
  method NormLen(s: seq<nat>) returns (n: nat)
    ensures n <= |s| && s[..n] == Normalize(s)
  {
    assume false;  // HOLE: delete this line, then write the loop invariants
    n := 0;
    var i := 0;
    while i < |s|
      decreases |s| - i
    {
      if s[i] != 0 {
        n := i + 1;
      }
      i := i + 1;
    }
    NormalizeTrim(s, n);
  }
  // Hint(1): read `NormalizeTrim`'s three preconditions with `i == |s|` in
  //    mind: each becomes one invariant about `n` and `i`.
  // Hint(2): bounds on `n` and `i` come first; then the limb just below `n`;
  //    then the limbs from `n` up to `i`.

  method NormLenCheck()
  {
    // Uncomment as you go:
    // var n := NormLen([3, 0]);
    // assert n == 1;
  }
}

// =============================================================================
// The search item. Nonlinear arithmetic is off in this module (the attribute
// on its `module` line), which comes last in the file: a fact about a
// product or a remainder by a product comes from a named library lemma.
// =============================================================================
module {:disableNonlinearArithmetic} Q10_Search {
  import opened QG_L1_BigNat
  import opened QG_L5_BigNat
  import opened Std.Arithmetic.DivMod

  // item: Q10.H5d S5
  // uses: library-call
  // pair: Q10.H5v
  /** **H5.** Search, then name: a remainder of a remainder. Taking `x`
      modulo `Pow(n + 1)` and then modulo `Pow(n)` is the same as taking it
      modulo `Pow(n)`. Find the lemma of `Std.Arithmetic.DivMod` (opened)
      that does the work, and call it with arguments that meet its
      `requires`. Why is `0 < Pow(n)` part of the statement? */
  lemma ModPowSucc(x: nat, n: nat)
    ensures 0 < Pow(n) && x % Pow(n + 1) % Pow(n) == x % Pow(n)
  // HOLE: this lemma has no body; write `{ … }` below the ensures line.
  // Hint(1): by its definition, `Pow(n + 1)` is `BASE` times `Pow(n)`: look
  //    for a lemma about a remainder by a product.
  // Hint(2): its `requires` asks for positive factors; layer L5 gives one of
  //    them.
}

/*
CALIBRATION (learner-owned; no script reads it). Planned minutes, design §7.5;
write your actual minutes beside each line.
  brief 15 · warm-up 8 · u64 round-trip pair 24 · spec items 15 ·
  assertion repairs 16 · normalize invariant pair 24 · search-then-name 20 ·
  ring buffer (V) 20 · exit 20 · paper 15 · ledger 5 · total 182
*/
