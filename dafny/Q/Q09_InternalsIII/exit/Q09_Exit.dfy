/*!
# Q09 — exit, Dafny half (closed book)

Closed book: keep the chapter, the exercise files, later modules' files,
search tools and /tutor closed. At most the given spine (dafny/given/Q/) and
the standard library's `Std.Arithmetic.Mul` may be open.

This file ships with exactly 2 holes (X1, X2); the Verus half
(verus/q/q09_internals_iii/src/exit.rs) ships with 2 holes. Score both halves
in one sitting with

    scripts/firsttry.sh Q09 --exit

Threshold: 3 of the 4 exit items, with at least 1 of the 2 in each language.
The first full run (every block attempted) is the score; repair every block
afterwards, after which the strict gate covers this file too. Both items
count only if they verify under both Z3 binaries bundled with Dafny and
seeds 1-3 (`scripts/vcheck --brittleness --solvers` on this file) with no
resource attribute; X2 counts only with an explicit trigger. This module
keeps nonlinear arithmetic on. This file is in no build: work it with
`scripts/vcheck dafny/Q/Q09_InternalsIII/exit/Q09_Exit.dfy`.

Then fill the EXPLAIN-BACK block at the end of this file.
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
  /** **X1.** A product plus a carry stays below the square. Prove it,
      splitting the nonlinear reasoning into named library facts
      (`Std.Arithmetic.Mul`, imported as `Mul`), so that it verifies under
      both bundled solvers and seeds 1-3 with no resource attribute. */
  lemma ProductPlusCarry(x: nat, y: nat, z: nat, n: nat)
    requires x < Pow(n) && y < Pow(n) && z < Pow(n)
    ensures x * y + z < Pow(n) * Pow(n)

  // item: Q09.X2d S11
  // uses: trigger-rewrite
  // need: lemma SumFour(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
  // need: ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
  // need: LimbSum(s + t) == LimbSum(s) + LimbSum(t)
  // need: LimbSumAppend(s, t);
  // pair: Q09.X2v
  // form: trigger, stable
  /** **X2.** The limb sum of four concatenated parts. This attempt states
      the append fact once, for every pair of sequences, and proves it:

          assert forall s: seq<nat>, t: seq<nat> {:trigger LimbSum(s), LimbSum(t)} ::
            LimbSum(s + t) == LimbSum(s) + LimbSum(t)
          by {
            forall s: seq<nat>, t: seq<nat> ensures LimbSum(s + t) == LimbSum(s) + LimbSum(t) {
              LimbSumAppend(s, t);
            }
          }

      Rewrite the trigger of the quoted fact (keep the fact and its proof)
      so that the lemma verifies under both bundled solvers and seeds 1-3. */
  lemma SumFour(a: seq<nat>, b: seq<nat>, c: seq<nat>, d: seq<nat>)
    ensures LimbSum(a + b + c + d) == LimbSum(a) + LimbSum(b) + LimbSum(c) + LimbSum(d)
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
