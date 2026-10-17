/* CONTRACT
goal: implement and prove every statement of the STATEMENTS section of this file, changing no statement
allowed-files:
  - dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy`; never stack unverified edits
  - `scripts/vcheck --gate dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `scripts/specfreeze --against research/q08_statements.dfy dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` reports no change: no statement changed
  - `scripts/vaudit dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` reports no finding
  - `git diff` against the committed statements changes only the bodies of the STATEMENTS methods and the HELPERS section
  - every WITNESSES check is unchanged and verifies
  - new helper functions and lemmas go only under HELPERS
*/
/*!
# Q08 Flagship — spec-to-proof (Reference Solution)

Hole-free reference for `dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy`
(author-only): the proof that the contract is satisfiable as stated. The three
sections are empty, as shipped; the closing reference section, inside the
module, holds a reference set of statements (each method's header is what a
learner commits in STATEMENTS, as a method with no body), witnesses for them,
and the reference delivery: the methods' bodies and the helpers a contractor
puts under HELPERS. Silent under `scripts/vcheck --ref`; `scripts/vaudit --ref`
reports no finding.
*/
module {:disableNonlinearArithmetic} Q08_AgentFlagship {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import Power = Std.Arithmetic.Power

  // item: Q08.A1d S6

  // ### STATEMENTS (learner-owned: your statements, each a method with no
  //    body). Two operations on valid limb sequences (`seq<nat>`, least
  //    significant limb first):
  //    - the shift left by `k` limbs;
  //    - the split at `k` limbs into the low part and the part above it.

  // ### WITNESSES (learner-owned: your checks that the statements can be met
  //    and say something).

  // ### HELPERS (the contractor's: helper functions and lemmas, if any).

  // ===========================================================================
  // — clearly marked: everything below answers the agentic file —
  // ===========================================================================
  // A reference set of statements: `ShiftLimbs` (the value times `Pow(k)`,
  // still valid) and `SplitLimbs` (both parts valid, the value recombined, and
  // the low part below `Pow(k)`), each a method with one `ensures` clause.
  // Committed as research/q08_statements.dfy with no bodies, they leave the
  // file green with 2 holes (`bodyless-method`), the witnesses verifying
  // against them; the delivery below (bodies plus HELPERS) passes every
  // acceptance line: `vcheck --gate` with 0 holes, `specfreeze --against` the
  // statements with no finding, `vaudit` with no finding, the witnesses
  // unchanged (Solutions/plans/Q08-code-notes.md).
  //
  // Statement pitfalls the learner's audit and the rubric look for:
  //   - a quotient form, `ToNat(hi) == ToNat(a) / Pow(k)`: not well formed
  //     without a fact that `Pow(k)` is not 0 ("possible division by zero");
  //     the multiplicative form avoids it;
  //   - two `ensures` clauses on one method with no body: two holes, and the
  //     lint's multi-ensures rule, until the body arrives;
  //   - a function with no body in place of the method: its delivered body
  //     is a changed statement under `specfreeze --against`;
  //   - `Valid` forgotten in an `ensures` (the result is then any sequence
  //     with the right value, limbs of any size);
  //   - the empty input forgotten in the witnesses.
  // Soft spots a contract run shows: a contractor adds a `requires` to a
  // helper that a statement cannot discharge, then weakens the statement to
  // match (the freeze check catches it); proves the split through
  // `Normalize`; adds `{:fuel}` attributes (the `git diff` shows them) or a
  // resource attribute (`vaudit` reports it); turns a method into a function
  // to reuse it in a specification (a freeze change).

  method ShiftLimbs(a: seq<nat>, k: nat) returns (r: seq<nat>)
    requires Valid(a)
    ensures Valid(r) && ToNat(r) == ToNat(a) * Pow(k)
  {
    r := Zeros(k) + a;
    ZerosFacts(k);
    ToNatAppendL(Zeros(k), a);
    LemmaMulIsCommutative(ToNat(a), Pow(k));
    assert Valid(Zeros(k) + a);
  }

  method SplitLimbs(a: seq<nat>, k: nat) returns (lo: seq<nat>, hi: seq<nat>)
    requires Valid(a)
    ensures Valid(lo) && Valid(hi) && ToNat(a) == ToNat(lo) + Pow(k) * ToNat(hi) && ToNat(lo) < Pow(k)
  {
    if k <= |a| {
      lo := a[..k];
      hi := a[k..];
      assert a == lo + hi;
      ToNatAppendL(lo, hi);
      ToNatBound(lo);
    } else {
      lo := a;
      hi := [];
      ToNatBound(a);
      PowIsStdPow(|a|);
      PowIsStdPow(k);
      Power.LemmaPowStrictlyIncreases(BASE, |a|, k);
      LemmaMulBasics(Pow(k));
    }
  }

  // The reference witnesses.
  method Witnesses()
  {
    var r := ShiftLimbs([5, 1], 2);
    assert ToNat(r) == ToNat([5, 1]) * Pow(2);
    var lo, hi := SplitLimbs([7, 8, 9], 1);
    assert ToNat(lo) < Pow(1);
    var lo2, hi2 := SplitLimbs([7], 3);
    assert ToNat([7]) == ToNat(lo2) + Pow(3) * ToNat(hi2);
    var z := ShiftLimbs([], 4);
    assert ToNat(z) == 0;
  }

  // The reference HELPERS.

  function Zeros(k: nat): seq<nat>
    decreases k
  {
    if k == 0 then [] else [0] + Zeros(k - 1)
  }

  lemma {:induction false} ToNatAppendL(a: seq<nat>, b: seq<nat>)
    ensures ToNat(a + b) == ToNat(a) + Pow(|a|) * ToNat(b)
    decreases |a|
  {
    if |a| == 0 {
      assert a + b == b;
      LemmaMulBasics(ToNat(b));
    } else {
      assert (a + b)[1..] == a[1..] + b;
      ToNatAppendL(a[1..], b);
      LemmaMulIsAssociative(BASE, Pow(|a| - 1), ToNat(b));
      LemmaMulIsDistributive(BASE, ToNat(a[1..]), Pow(|a| - 1) * ToNat(b));
    }
  }

  lemma {:induction false} ZerosFacts(k: nat)
    ensures |Zeros(k)| == k && Valid(Zeros(k)) && ToNat(Zeros(k)) == 0
    decreases k
  {
    if k > 0 {
      ZerosFacts(k - 1);
      ToNatCons(0, Zeros(k - 1));
      ValidCons(0, Zeros(k - 1));
    }
  }
}

// AUDIT (learner-owned; after the contract run)
//   the statement that cost the contractor most, and why:
//   each helper's statement (does it assume what it should prove?):
