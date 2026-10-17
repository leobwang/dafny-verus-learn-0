/* CONTRACT
goal: give CountZeroLimbs, TopIndex and SumLimbs bodies that meet their doc contracts, so that every shipped check in this file verifies
allowed-files:
  - dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy
acceptance:
  - per edit, feedback only from the fast channel `scripts/vcheck --symbol Q02_AgentImplement.<Name> dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy`, run on the definition just edited and on the checks that use it; never stack unverified edits
  - exactly one full `scripts/vcheck --gate dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy` run, as the last verifier command: exit 0, only the summary line printed
  - zero tool-counted holes in the allowed file
  - `git diff` shows only the bodies of CountZeroLimbs, TopIndex and SumLimbs: no signature, `ensures`, doc comment or check line changed, no declaration added or removed
  - `scripts/vaudit --compare expected/Q02_AgentImplement.audit dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy` reports no difference (an empty report: no finding)
*/
/*!
# Q02 Implementer — implementer vs checks (Reference Solution)

Hole-free reference for `dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy`
(author-only): the proof that the contract is satisfiable as stated. The three
definitions meet their prose contracts, the six shipped checks (verbatim) verify, and the
closing reference section holds the adversarial checks and the author's note on the
planted soft spots. Silent under `scripts/vcheck --ref`; `scripts/vaudit --ref` reports
no finding, which expected/Q02_AgentImplement.audit pins (an empty report).
*/
module Q02_AgentImplement {
  import opened QG_L1_BigNat

  // item: Q02.A1d S3

  // ### The definitions. Their domain is every `seq<nat>`: a limb may be any natural
  //    number here, `BASE` or more included.

  /** The number of zero limbs of `s`: how many positions `i` have `s[i] == 0`. */
  function CountZeroLimbs(s: seq<nat>): nat
    ensures CountZeroLimbs(s) <= |s|
  {
    if |s| == 0 then 0 else (if s[0] == 0 then 1 else 0) + CountZeroLimbs(s[1..])
  }

  /** The index of the most significant non-zero limb of `s`: the largest `i` with
      `s[i] != 0`, or `-1` when there is none (`s` empty, or every limb zero). */
  function TopIndex(s: seq<nat>): int
    ensures -1 <= TopIndex(s) < |s|
  {
    if |s| == 0 then -1 else if s[|s| - 1] != 0 then |s| - 1 else TopIndex(s[..|s| - 1])
  }

  /** The sum of the limbs of `s`, `s[0] + s[1] + … + s[|s| - 1]` as natural numbers (not
      the value `ToNat(s)`); 0 for the empty sequence. */
  function SumLimbs(s: seq<nat>): nat
    ensures |s| == 0 ==> SumLimbs(s) == 0
  {
    if |s| == 0 then 0 else s[0] + SumLimbs(s[1..])
  }

  // ### The shipped checks (do not edit)

  lemma CheckCountZeroLimbs1() { assert CountZeroLimbs([0, 5, 0]) == 2; }
  lemma CheckCountZeroLimbs2() { assert CountZeroLimbs([7]) == 0; }
  lemma CheckTopIndex1() { assert TopIndex([1, 0]) == 0; }
  lemma CheckTopIndex2() { assert TopIndex([0, 7]) == 1; }
  lemma CheckSumLimbs1() { assert SumLimbs([2, 3]) == 5; }
  lemma CheckSumLimbs2() { assert SumLimbs([4]) == 4; }

  // ### ADVERSARIAL CHECKS (learner-owned; after the contract run). Write each as a lemma
  //    like the shipped ones, below this line.

  // ===========================================================================
  // — clearly marked: everything below answers the agentic file —
  // ===========================================================================
  // The reference delivery is the three bodies above (recursion on the length; each
  // `ensures` follows from the recursive call's). The adversarial checks below hold for
  // it; each one fails a planted soft spot, a wrong body that passes all six shipped
  // checks and its partial `ensures`:
  //
  //   CountZeroLimbs  soft spot: count the limbs with `s[i] % BASE == 0`, so a limb equal
  //                   to BASE counts as zero (the domain is every seq<nat>).
  //                   Caught by AdvCountZeroLimbsBase.
  //   TopIndex        soft spot: scan down from the top and stop at index 0, returning 0
  //                   for an all-zero sequence (0 satisfies `-1 <= r < |s|` when s is not
  //                   empty). Caught by AdvTopIndexAllZero; AdvTopIndexEmpty pins the
  //                   empty case the contract names.
  //   SumLimbs        soft spot: sum `s[i] % BASE`, which agrees with the true sum on every
  //                   shipped check (all limbs below BASE). Caught by AdvSumLimbsBase.
  //
  // The chapter (DV2b) shows one gamed implementation passing the shipped suite and failing
  // these.
  lemma AdvCountZeroLimbsBase() { assert CountZeroLimbs([BASE]) == 0; }
  lemma AdvTopIndexAllZero() { assert TopIndex([0, 0]) == -1; }
  lemma AdvTopIndexEmpty() { assert TopIndex([]) == -1; }
  lemma AdvSumLimbsBase() { assert SumLimbs([BASE, 1]) == BASE + 1; }
}

// LATENCY LOG (learner-owned; from the contract transcript)
//   fast-channel runs: count, typical wall time:
//   the one full gate run: wall time:
//   what the fast channel did not tell the contractor:
