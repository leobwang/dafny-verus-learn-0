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
# Q02 Implementer — implementer vs checks (`/contract Q02`)

What this file ships: three definitions over limb sequences, each stated by a prose
contract (its doc comment) and a partial formal one (its single `ensures`), each with a
hole for its body, and a live suite of six checks, two per definition. It is RED by
design: the three bodyless functions are 3 tool-counted holes, and each of the six checks
fails over them, one error per check (6 errors). Check command:

    scripts/vcheck dafny/Q/Q02_FirstSyntaxI/agent/Q02_AgentImplement.dfy

The file is outside every build: no unit includes it.

Learner follow-up (after the contractor delivers; THIS is the exercise):
1. Before the run: read the three contracts and run the command above; read every message.
2. In a FRESH session, run /contract Q02 on this file.
3. Tally the transcript: only the fast channel per edit? exactly one full gate, last?
   touched a statement or a check? reached for an escape hatch? Fill the LATENCY LOG below
   from the transcript's timings.
4. Check the artifact yourself: the gate output, `git diff` scope, `scripts/vaudit`.
5. Write ADVERSARIAL CHECKS (the block at the end of the module): inputs the shipped suite
   never tried, judged against the prose contracts. The doc contracts say more than the
   `ensures` lines and the checks do.
*/
module Q02_AgentImplement {
  import opened QG_L1_BigNat

  // item: Q02.A1d S3

  // ### The definitions. Their domain is every `seq<nat>`: a limb may be any natural
  //    number here, `BASE` or more included.

  /** The number of zero limbs of `s`: how many positions `i` have `s[i] == 0`. */
  function CountZeroLimbs(s: seq<nat>): nat
    ensures CountZeroLimbs(s) <= |s|

  /** The index of the most significant non-zero limb of `s`: the largest `i` with
      `s[i] != 0`, or `-1` when there is none (`s` empty, or every limb zero). */
  function TopIndex(s: seq<nat>): int
    ensures -1 <= TopIndex(s) < |s|

  /** The sum of the limbs of `s`, `s[0] + s[1] + … + s[|s| - 1]` as natural numbers (not
      the value `ToNat(s)`); 0 for the empty sequence. */
  function SumLimbs(s: seq<nat>): nat
    ensures |s| == 0 ==> SumLimbs(s) == 0

  // ### The shipped checks (do not edit)

  lemma CheckCountZeroLimbs1() { assert CountZeroLimbs([0, 5, 0]) == 2; }
  lemma CheckCountZeroLimbs2() { assert CountZeroLimbs([7]) == 0; }
  lemma CheckTopIndex1() { assert TopIndex([1, 0]) == 0; }
  lemma CheckTopIndex2() { assert TopIndex([0, 7]) == 1; }
  lemma CheckSumLimbs1() { assert SumLimbs([2, 3]) == 5; }
  lemma CheckSumLimbs2() { assert SumLimbs([4]) == 4; }

  // ### ADVERSARIAL CHECKS (learner-owned; after the contract run). Write each as a lemma
  //    like the shipped ones, below this line.
}

// LATENCY LOG (learner-owned; from the contract transcript)
//   fast-channel runs: count, typical wall time:
//   the one full gate run: wall time:
//   what the fast channel did not tell the contractor:
