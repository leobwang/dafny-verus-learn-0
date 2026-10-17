/*!
# Q09 — exit, Dafny half (Reference Solution)

Hole-free reference for `dafny/Q/Q09_InternalsIII/exit/Q09_Exit.dfy`
(author-only; never learner-visible). Same module, imports, given
declarations, item markers, `need:` and `form:` lines and order as the exit
file; both exit holes are filled. The file is silent: `scripts/vcheck --ref`
on it prints only the summary line. No declaration carries a resource
attribute.
*/
module Q09_Exit {
  import opened QG_L1_BigNat
  import Mul = Std.Arithmetic.Mul

  // Given (not an item): the sum of the limbs of a sequence, and how it adds
  // up over a concatenation, for X2.
  function LimbSum(s: seq<nat>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else s[0] + LimbSum(s[1..])
  }

  lemma LimbSumAppend(s: seq<nat>, t: seq<nat>)
    ensures LimbSum(s + t) == LimbSum(s) + LimbSum(t)
    decreases |s|
  {
    if |s| == 0 {
      assert s + t == t;
    } else {
      assert (s + t)[1..] == s[1..] + t;
      LimbSumAppend(s[1..], t);
    }
  }

  // item: Q09.X1d S11
  // uses: proof-split
  // need: lemma ProductPlusCarry(x: nat, y: nat, z: nat, n: nat)
  // need: requires x < Pow(n) && y < Pow(n) && z < Pow(n)
  // need: ensures x * y + z < Pow(n) * Pow(n)
  // pair: Q09.X1v
  // form: stable
  /** **X1.** A product plus a carry stays below the square. Reference:
      the product is at most `(p - 1) * (p - 1)` (`LemmaMulUpperBound`),
      which is `(p - 1) * p - (p - 1)` (`LemmaMulIsDistributiveSub`), and
      `(p - 1) * p < p * p` (`LemmaMulStrictInequality`); the carry fills
      at most the `p - 1` left over. Stable under both bundled solvers and
      seeds 1-3; the empty body and the one assertion
      `x * y <= (p - 1) * (p - 1)` are out of resource in all six rows. */
  lemma ProductPlusCarry(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y + z < Pow(n) * Pow(n)
  {
    var p := Pow(n);
    Mul.LemmaMulUpperBound(x, p - 1, y, p - 1);
    Mul.LemmaMulIsDistributiveSub(p - 1, p, 1);
    Mul.LemmaMulStrictInequality(p - 1, p, p);
  }

  // item: Q09.X2d S11
  // uses: trigger-rewrite
  // need: lemma SumFour(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
  // need: ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
  // need: LimbSum(s + t) == LimbSum(s) + LimbSum(t)
  // need: LimbSumAppend(s, t);
  // pair: Q09.X2v
  // form: trigger, stable
  // cfree: { LimbSumAppend(a + b + c, d); LimbSumAppend(a + b, c); LimbSumAppend(a, b); }
  /** **X2.** The limb sum of four concatenated parts. Reference: the
      quoted fact with its trigger moved to the composite term
      `LimbSum(s + t)`. The quoted multi-trigger fires on every pair of
      limb-sum terms, and each instance makes a new one, so the instances
      explode over the two variables; on `LimbSum(s + t)` the fact fires only
      at the three concatenations the goal holds. Stable under both bundled
      solvers and seeds 1-3. The `cfree:` line above (three direct calls,
      no quantifier) verifies too: the `need:` lines and the `trigger` form
      stop it. */
  lemma SumFour(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
    ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
  {
    assert forall s: seq<nat>, t: seq<nat> {:trigger LimbSum(s + t)} ::
      LimbSum(s + t) == LimbSum(s) + LimbSum(t)
    by {
      forall s: seq<nat>, t: seq<nat> ensures LimbSum(s + t) == LimbSum(s) + LimbSum(t) {
        LimbSumAppend(s, t);
      }
    }
  }
}

/*
EXPLAIN-BACK (learner-owned; advisory: no script reads this block and no
gate depends on it). After `scripts/firsttry.sh Q09 --exit` has scored the
exit, choose one exit item that passed, in either language, and write at
most 120 words: what the verifier needed for it, and why each step of your
proof is there. The detailed-tier viva opens on this block and asks you to
defend it against a probe run through `scripts/vcheck`.
  item:
  what the verifier needed, and why each step is there:
*/
