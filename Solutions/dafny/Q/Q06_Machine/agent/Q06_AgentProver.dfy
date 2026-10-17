/* CONTRACT
goal: prove every leaf lemma of the skeleton in this file (the lemmas of its SKELETON section), so that the file verifies with zero holes
allowed-files:
  - dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy`; never stack unverified edits
  - `scripts/vcheck --gate dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `scripts/specfreeze --against research/q06_skeleton.dfy dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy` reports no change: no statement of the skeleton changed
  - `git diff` against the committed skeleton shows only the bodies of the leaf lemmas: no statement, attribute, doc comment or other line changed
  - no new lemma, function or method: the skeleton's leaves (at most 5) are the only lemmas you prove
  - `scripts/vaudit --compare expected/Q06_AgentProver.audit dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy` reports no difference (an empty report: no finding)
*/
/*!
# Q06 Prover — audited prover (Reference Solution)

Hole-free reference for `dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy`
(author-only): the proof that the contract is satisfiable as stated. The top
lemma's proof is in place; the SKELETON section is empty, as shipped, and the
closing reference section holds the reference skeleton (three leaves, each
proved) and the author's note on the soft spots a contract run shows. Silent under `scripts/vcheck --ref`; `scripts/vaudit
--ref` reports no finding, which expected/Q06_AgentProver.audit pins (an
empty report, the delivered state).
*/
module Q06_AgentProver {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Power = Std.Arithmetic.Power

  // item: Q06.A1d S12

  // ### The top lemma (frozen statement): a canonical numeral is determined
  //    by its value.
  lemma CanonicalUnique(a: seq<nat>, b: seq<nat>)
    requires Canonical(a) && Canonical(b) && ToNat(a) == ToNat(b)
    ensures a == b
    decreases |a|
  {
    if |a| < |b| {
      CanonicalLengthOrder(a, b);
    } else if |b| < |a| {
      CanonicalLengthOrder(b, a);
    } else if |a| > 0 {
      ValidTail(a);
      ValidTail(b);
      if |a| > 1 {
        assert a[1..][|a| - 2] == a[|a| - 1];
        assert b[1..][|b| - 2] == b[|b| - 1];
      }
      CanonicalUnique(a[1..], b[1..]);
      assert a == [a[0]] + a[1..];
      assert b == [b[0]] + b[1..];
    }
  }

  // ### SKELETON (learner-owned: your leaf lemmas, at most 5, each with no
  //    body). One decomposition that works: a lower bound on a canonical
  //    numeral's value, an order between the lengths of canonical numerals,
  //    and a monotonicity fact about `Pow`.

  // ===========================================================================
  // — clearly marked: everything below answers the agentic file —
  // ===========================================================================
  // The reference skeleton is the three leaves below: PowMono (two bridges and
  // Power.LemmaPowIncreases), ToNatLowerBound (recursion on s[1..]; the top
  // limb of a canonical numeral is not 0, so its tail is canonical too) and
  // CanonicalLengthOrder (L2's ToNatBound for the shorter numeral,
  // ToNatLowerBound for the longer, PowMono between them). The top lemma
  // splits on the lengths (CanonicalLengthOrder rules out unequal lengths),
  // then recurses on the tails: equal values give equal low limbs and equal
  // tail values. Each leaf's empty body is lever-needed under the file's
  // manual induction; none falls to automation as shipped.
  //
  // Soft spots a contract run shows (the learner's audit looks for them):
  //   - a leaf whose `requires` is strengthened until it is vacuous, so the
  //     leaf is proved and useless (the usefulness check: call each leaf once
  //     on concrete arguments, or say why its `requires` can hold);
  //   - a changed leaf statement (`scripts/specfreeze --against` reports it);
  //   - a sixth lemma, a helper the contract forbids (`git diff` shows it);
  //   - a leaf proved by an `{:induction}` attribute: allowed by the gate,
  //     visible in the diff, and a breach of "only the bodies".

  // The reference skeleton: three leaves, each proved.

  lemma PowMono(m: nat, n: nat)
    requires m <= n
    ensures Pow(m) <= Pow(n)
  {
    PowIsStdPow(m);
    PowIsStdPow(n);
    Power.LemmaPowIncreases(BASE, m, n);
  }

  lemma ToNatLowerBound(s: seq<nat>)
    requires Canonical(s) && |s| > 0
    ensures Pow(|s| - 1) <= ToNat(s)
    decreases |s|
  {
    if |s| > 1 {
      assert s[1..][|s[1..]| - 1] == s[|s| - 1];
      ValidTail(s);
      ToNatLowerBound(s[1..]);
    }
  }

  lemma CanonicalLengthOrder(a: seq<nat>, b: seq<nat>)
    requires Canonical(a) && Canonical(b) && |a| < |b|
    ensures ToNat(a) < ToNat(b)
  {
    ToNatBound(a);
    ToNatLowerBound(b);
    PowMono(|a|, |b| - 1);
  }
}

// AUDIT (learner-owned; after the contract run)
//   the leaf that took the contractor longest, and why:
//   each leaf's usefulness (a concrete call, or why its `requires` can hold):
