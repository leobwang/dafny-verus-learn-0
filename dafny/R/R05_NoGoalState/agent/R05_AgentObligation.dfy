/* CONTRACT — R05 obligation prover, R-v0
goal: prove both supplied lemmas, preserving every statement
allowed-files:
  - dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy
acceptance:
  - per edit use only scripts/vcheck --symbol <qualified-name> dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy; record each command, verdict and elapsed time
  - exactly one full scripts/vcheck --gate dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy run, last; exit0 with zero counted holes is required for delivery
  - scripts/vaudit dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy reports no finding
  - scripts/specfreeze --against <snapshot> dafny/R/R05_NoGoalState/agent/R05_AgentObligation.dfy reports no statement change
  - no assumptions, weakened guarantees, strengthened inputs or filtered final verification
  - stop and report if the final gate fails; do not spend a second final gate or call an incomplete delivery done
*/
/*! R05 obligation prover (Exercises). Save the snapshot before /contract R05.
The two holes import only given A1. Find needed helper facts in this file;
no call into a learner exercise. The fast channel diagnoses a named symbol;
only the one final whole-file gate decides the delivery. See CONTRACT.
*/
module R05_AgentObligation {
  import opened RG_A1_Re
  // item: R05.A1d
  lemma AppendChunk(a: Re, u: seq<char>, v: seq<char>)
    requires Matches(Star(a), u) && Matches(a, v)
    ensures Matches(Star(a), u + v)

  lemma CollapseStarCat(a: Re, s: seq<char>)
    requires Matches(Cat(Star(a), Star(a)), s)
    ensures Matches(Star(a), s)

/* OBLIGATION LOG — learner-owned after the contract run.
   Fast-channel calls and failed obligations per lemma: ...
   Added facts/helpers, and deletion probes in a scratch copy: ...
   One final full gate: command / exit / zero-hole count / timestamp: ...
   Audit and snapshot comparison: ...
   Latency/call cost, remaining uncertainty and correction: ...
*/
}
