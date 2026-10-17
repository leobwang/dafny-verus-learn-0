/*!
# Q06 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q06_Machine/exit/Q06_Exit.dfy` (author-only;
never learner-visible). Same module, imports, names, statements, item markers
and order as the exit file; both blocks are filled and silent under
`scripts/vcheck --ref`. No declaration carries a resource attribute (X2 is a
budget item).
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
  /** **X1.** A differential check of two candidates.

      Reference: one pass over the samples that returns the index of the
      first disagreement. The invariant (every sample before `k` agrees)
      gives the `-1` exit its `forall`; the early return carries its
      witness. The suite (live here) passes: `HalfA` agrees with `Half` on
      every sample, and `HalfB` first disagrees at index 2 (the sample 3). */
  method FirstDisagreement(f: nat -> int, g: nat -> int, samples: seq<nat>) returns (r: int)
    ensures -1 <= r < |samples|
    ensures r == -1 <==> forall k | 0 <= k < |samples| :: f(samples[k]) == g(samples[k])
    ensures r >= 0 ==> f(samples[r]) != g(samples[r])
  {
    var k := 0;
    while k < |samples|
      invariant 0 <= k <= |samples|
      invariant forall j | 0 <= j < k :: f(samples[j]) == g(samples[j])
      decreases |samples| - k
    {
      if f(samples[k]) != g(samples[k]) {
        return k;
      }
      k := k + 1;
    }
    return -1;
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

  @Test
  method AgreeingCandidate() {
    var r := FirstDisagreement(HalfA, Half, [0, 2, 3, 10]);
    expect r == -1;
  }

  @Test
  method PlantedCandidate() {
    var r := FirstDisagreement(HalfB, Half, [0, 2, 3, 10]);
    expect r == 2;
  }

  // item: Q06.X2d S11
  // uses: opaque-reveal, rlimit
  // need: lemma LowOfShift(x: nat, y: nat, m: nat)
  // need: ensures Low(x + m * y, m) == Low(x, m)
  // pair: Q06.X2v
  /** **X2.** Adding a multiple of `m` does not change the low part.
      This attempt, over a transparent copy of `Low`, does not verify at the
      pinned resource limit:

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

      Reference: reveal `Low`, then `DivMod.LemmaModMultiplesVanish(y, x, m)`
      states `(m * y + x) % m == x % m`. No resource attribute. */
  lemma LowOfShift(x: nat, y: nat, m: nat)
    requires m > 0
    ensures Low(x + m * y, m) == Low(x, m)
  {
    reveal Low();  // did: unfolds Low's body for this proof
    DivMod.LemmaModMultiplesVanish(y, x, m);
  }
}
