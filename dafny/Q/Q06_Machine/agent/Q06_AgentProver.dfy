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
# Q06 Prover — audited prover (`/contract Q06`)

What this file ships: one frozen top lemma, `CanonicalUnique` (a canonical
numeral is determined by its value), as a hole, and an empty SKELETON section
below it. It is green: `scripts/vcheck` reports it verified, with exactly 1
tool-counted hole (the top lemma) and no error. Check command:

    scripts/vcheck dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy

The file is outside every build: no unit includes it.

Before the run (your skeleton; this is the main work):
1. In SKELETON, write at most 5 leaf lemmas, each a statement with no body (a
   hole), and replace the top lemma's hole by a proof that calls them, until
   the file is green with only the leaves' holes. Never change the top
   lemma's statement.
2. Copy the file to research/q06_skeleton.dfy, the statement snapshot that the
   contract's freeze check compares against, and commit both (`git commit`),
   so that the contract's `git diff` compares the run with your skeleton.

Learner follow-up (after the contractor delivers; THIS is the exercise):
1. In a FRESH session, run /contract Q06 on this file.
2. Audit the statements: `scripts/specfreeze --against research/q06_skeleton.dfy
   dafny/Q/Q06_Machine/agent/Q06_AgentProver.dfy`.
3. Audit the assumptions: `scripts/vaudit` on this file, and the contract's
   `--compare` line.
4. Audit each leaf's usefulness: call it once on concrete arguments, or say
   why its `requires` can hold.
5. Write in AUDIT (the block at the end) which leaf took the contractor
   longest, and why.
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

  // ### SKELETON (learner-owned: your leaf lemmas, at most 5, each with no
  //    body). One decomposition that works: a lower bound on a canonical
  //    numeral's value, an order between the lengths of canonical numerals,
  //    and a monotonicity fact about `Pow`.
}

// AUDIT (learner-owned; after the contract run)
//   the leaf that took the contractor longest, and why:
//   each leaf's usefulness (a concrete call, or why its `requires` can hold):
