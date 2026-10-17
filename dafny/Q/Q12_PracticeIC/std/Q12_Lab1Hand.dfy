/*!
# Q12 — Lab 1: the hand part, Dafny (Exercises)

Imports: the given BigNat spine, layers L1-L4 (`QG_L1_BigNat` …
`QG_L4_BigNat`), nothing else. The layers are frozen and complete; read
them, never edit them. This module's import list is part of what it states:
keep it as shipped. This module keeps nonlinear arithmetic on, and the unit
proves lemmas by induction only where you write the induction (its options
turn automatic lemma induction off).

The hand part of Lab 1 (QPLAN §22.5): the four items below and their Verus
partners in verus/q/q12_practice_ic/src/lab1_hand.rs, done closed book (keep
the chapter, the other exercise files, search tools and /tutor closed; the
given spine may be open), 12 minutes each, BEFORE any Lab 1 run. Some of
them are also tasks the agents get in the lab's local stratum, so your own
hit rate can stand beside each arm's on the same tasks. Time each item from
its first edit; when its 12 minutes are up, write its row in the HAND
block at the end of this file (verified within the time, yes or no, and the
minutes it took), then finish it untimed. The lab's acceptance needs at
least 3 of the 4 within time in each language.

Done = `scripts/vcheck --gate dafny/Q/Q12_PracticeIC/std` prints only the
summary line and exits 0 and `scripts/vaudit dafny/Q/Q12_PracticeIC/std`
reports no finding (the unit's gate covers this file and
Q12_PracticeIC.dfy together).

This file ships with exactly 4 holes: H4, H5, H6 and H7, each counted by
`scripts/vcheck`. Item kinds and the slot protocol are in
dafny/Q/Q12_PracticeIC/std/Q12_PracticeIC.dfy's header.
*/
module Q12_Lab1Hand {
  // specfreeze: frozen-imports
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q12.H4d S12
  // uses: lemma-recursion
  // pair: Q12.H4v
  /** **H4.** The value is monotone in each limb: a limb sequence that is
      limb by limb at most another of the same length has at most its
      value. */
  lemma ToNatMono(a: seq<nat>, b: seq<nat>)
    requires |a| == |b| && forall i | 0 <= i < |a| :: a[i] <= b[i]
    ensures ToNat(a) <= ToNat(b)
    decreases |a|

  // item: Q12.H5d S12
  // uses: lemma-recursion
  /** **H5.** Multiplying by the limb 0 (layer L4's `MulLimb`) keeps the
      length and gives a zero in every limb. */
  lemma MulLimbZeroLimbs(s: seq<nat>)
    ensures |MulLimb(s, 0)| == |s| && forall i | 0 <= i < |s| :: MulLimb(s, 0)[i] == 0
    decreases |s|

  // item: Q12.H6d S12
  // uses: lemma-recursion
  /** **H6.** `Cmp` (layer L3) reads a missing limb as 0: a sequence compares
      equal to itself with one zero limb appended at the most significant
      end. No precondition. */
  lemma CmpTrailingZero(a: seq<nat>)
    ensures Cmp(a, a + [0]) == 0
    decreases |a|

  // item: Q12.H7d S12
  // uses: lemma-recursion
  /** **H7.** Normalizing never lengthens a sequence. */
  lemma NormalizeShorter(s: seq<nat>)
    ensures |Normalize(s)| <= |s|
    decreases |s|
}

/*
HAND (learner-owned; the lab report reads it, no script does). One row per
item, written when its 12 minutes are up: verified within the time (yes or
no) and the minutes it took.
  H4d ToNatMono:
  H5d MulLimbZeroLimbs:
  H6d CmpTrailingZero:
  H7d NormalizeShorter:
  H4v lemma_seq_to_nat_mono:
  H5v is_zero:
  H6v eq_big:
  H7v size_bound:
*/
