/*!
# Q15 — Lab 2's prose specifications, Dafny half (Exercises)

Imports: the given BigNat spine, layers L1 (`QG_L1_BigNat`) to L6
(`QG_L6_BigNat`), all opened; nothing else. The layers are frozen and
complete; read them, never edit them.

Three prose tasks (Lab 2, design §11.2: specification quality). Each ships a
method's signature and its implementation, and no specification: you write
its `requires` and `ensures` from the prose. Its code is given; you may add
proof lines to its body (assertions, lemma calls), never change its code.
Then uncomment the use-site check in its client, write a non-vacuity witness
(one call whose `requires` hold) in its witness method, and delete the
client's assume.

What grades a specification: the use-site check (an adequate one verifies
it), your witness, /review-code, and, in the grader container, a hidden
two-way check against the author's specification and the kill of mutants of
the given code (QPLAN §25.5, §25.6). You start the hidden check from your
own terminal, never from a Claude session: the chapter's §5 gives the line,
and it prints one verdict word per specification, with the outcome words of
the checks behind it (which side and direction differ; Q13's §2).

Done = `scripts/vcheck --gate dafny/Q/Q15_PracticeIIC/std` prints only the
summary line and exits 0, `scripts/vaudit dafny/Q/Q15_PracticeIIC/std`
reports no finding, AND `scripts/firsttry.sh Q15 --report --strict` exits 0.

This file ships with exactly 3 holes (H3, H4 and H5), each counted by
`scripts/vcheck`: one labelled assume per client. The prediction block and
the slot protocol are in Q15_PracticeIIC.dfy's header.
*/
module Q15_Lab2Specs {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened QG_L5_BigNat
  import opened QG_L6_BigNat

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q15.H3d S13
  // uses: ensures, witness
  // prose: EvenLimbs
  /** **H3.** Prose task. *Every other limb of a limb sequence, starting from
      the lowest: the limbs at positions 0, 2, 4, … of `s`, in that order, and
      no other limb.* Write `EvenLimbs`'s specification. */
  method EvenLimbs(s: seq<nat>) returns (r: seq<nat>)
  {
    if |s| <= 1 {
      r := s;
    } else {
      var t := EvenLimbs(s[2..]);
      r := [s[0]] + t;
    }
  }

  method EvenLimbsUse(s: seq<nat>)
    requires |s| == 5
  {
    assume false;  // HOLE: delete once EvenLimbs is specified
    // Uncomment as you go:
    // var r := EvenLimbs(s);
    // assert r == [s[0], s[2], s[4]];
  }

  /** Your non-vacuity witness for `EvenLimbs`: one call whose `requires` hold. */
  method EvenLimbsWitness()
  {
  }

  // item: Q15.H4d S13
  // uses: ensures, witness
  // prose: TopDiff
  /** **H4.** Prose task. *The index of the highest limb at which two limb
      sequences of one length differ, or -1 when they are equal: above that
      index they agree at every position.* Write `TopDiff`'s specification. */
  method TopDiff(a: seq<nat>, b: seq<nat>) returns (i: int)
  {
    if |a| == 0 || |b| == 0 {
      i := -1;
    } else if a[|a| - 1] != b[|b| - 1] {
      i := |a| - 1;
    } else {
      i := TopDiff(a[..|a| - 1], b[..|b| - 1]);
    }
  }

  method TopDiffUse(a: seq<nat>, b: seq<nat>)
    requires |a| == 3 && |b| == 3 && a[0] != b[0] && a[1..] == b[1..]
  {
    assume false;  // HOLE: delete once TopDiff is specified
    // Uncomment as you go:
    // var i := TopDiff(a, b);
    // assert i == 0;
  }

  /** Your non-vacuity witness for `TopDiff`: one call whose `requires` hold. */
  method TopDiffWitness()
  {
  }

  // item: Q15.H5d S13
  // uses: ensures, witness
  // prose: SatSub
  /** **H5.** Prose task. *Saturating subtraction of two valid numbers: the
      difference as layer L6's `Sub` gives it when the first is at least the
      second, and the empty sequence (zero) otherwise.* Write `SatSub`'s
      specification. */
  method SatSub(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
  {
    if ToNat(a) < ToNat(b) {
      r := [];
    } else {
      r := FromNat(ToNat(a) - ToNat(b));
    }
  }

  method SatSubUse(a: seq<nat>, b: seq<nat>)
    requires Valid(a) && Valid(b) && ToNat(a) < ToNat(b)
  {
    assume false;  // HOLE: delete once SatSub is specified
    // Uncomment as you go:
    // var r := SatSub(a, b);
    // assert r == [];
    // var d := SatSub(b, a);
    // assert d == Sub(b, a);
  }

  /** Your non-vacuity witness for `SatSub`: one call whose `requires` hold. */
  method SatSubWitness()
  {
  }
}
