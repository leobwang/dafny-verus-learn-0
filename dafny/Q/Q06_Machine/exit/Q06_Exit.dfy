/*!
# Q06 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) may
be open.

This file ships with exactly 2 holes (X1, X2); the Verus half
(verus/q/q06_machine/src/exit.rs) ships with 2 holes. Score both halves in one
sitting with

    scripts/firsttry.sh Q06 --exit

Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language.
The first full run (every block attempted) is the score; repair every block
afterwards, after which the strict gate covers this file too (and runs X1's
suite: `scripts/vcheck --test dafny/Q/Q06_Machine/exit/Q06_Exit.dfy`). X1
counts only with its suite uncommented and verifying; X2 counts only with no
resource attribute in this file. This file is in no build: work it
with `scripts/vcheck dafny/Q/Q06_Machine/exit/Q06_Exit.dfy`.
*/
module Q06_Exit {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import DivMod = Std.Arithmetic.DivMod

  // Given (not an item): the low part of `x` modulo `m`, for X2. Opaque: its
  // body is hidden from every proof that does not reveal it.
  opaque function Low(x: nat, m: nat): nat
    requires m > 0
  {
    x % m
  }

  // item: Q06.X1d S12
  // uses: property-test
  // need: method FirstDisagreement(f: nat -> int, g: nat -> int, samples: seq<nat>) returns (r: int)
  // need: ensures -1 <= r < |samples|
  // need: ensures r == -1 <==> forall k | 0 <= k < |samples| :: f(samples[k]) == g(samples[k])
  // need: ensures r >= 0 ==> f(samples[r]) != g(samples[r])
  // pair: Q06.X1v
  /** **X1.** A differential check of two candidates: compare `f` and `g` on
      the samples and return the index of the first sample on which they
      disagree, or `-1` when they agree on every sample. Then uncomment the
      suite below it: the agreeing candidate must give `-1`, the planted one
      the index of its first disagreement. */
  method FirstDisagreement(f: nat -> int, g: nat -> int, samples: seq<nat>) returns (r: int)
    ensures -1 <= r < |samples|
    ensures r == -1 <==> forall k | 0 <= k < |samples| :: f(samples[k]) == g(samples[k])
    ensures r >= 0 ==> f(samples[r]) != g(samples[r])
  {
    assume false;
  }

  // The reference and the two candidates the suite compares (given): a
  // correct candidate and a planted one that rounds up.
  function Half(x: nat): int
  {
    x / 2
  }

  function HalfA(x: nat): int
  {
    (x - x % 2) / 2
  }

  function HalfB(x: nat): int
  {
    (x + 1) / 2
  }

  // Uncomment as you go:
  // @Test
  // method AgreeingCandidate() {
  //   var r := FirstDisagreement(HalfA, Half, [0, 2, 3, 10]);
  //   expect r == -1;
  // }
  //
  // @Test
  // method PlantedCandidate() {
  //   var r := FirstDisagreement(HalfB, Half, [0, 2, 3, 10]);
  //   expect r == 2;
  // }

  // item: Q06.X2d S11
  // uses: opaque-reveal, rlimit
  // need: lemma LowOfShift(x: nat, y: nat, m: nat)
  // need: ensures Low(x + m * y, m) == Low(x, m)
  // pair: Q06.X2v
  /** **X2.** Adding a multiple of `m` does not change the low part. Prove it
      at the pinned resource limit, with no resource attribute. This attempt,
      over a transparent copy of `Low`, does not verify at that limit:

          function LowT(x: nat, m: nat): nat
            requires m > 0
          {
            x % m
          }

          lemma LowOfShiftT(x: nat, y: nat, m: nat)
            requires m > 0
            ensures LowT(x + m * y, m) == LowT(x, m)
          {
          }
  */
  lemma LowOfShift(x: nat, y: nat, m: nat)
    requires m > 0
    ensures Low(x + m * y, m) == Low(x, m)
}
