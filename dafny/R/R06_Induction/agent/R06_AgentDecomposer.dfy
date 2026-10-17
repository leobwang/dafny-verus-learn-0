/* CONTRACT — R06 decomposer, R-v0
goal: prove the one top statement by decomposition, preserving its contract
allowed-files:
  - dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy
acceptance:
  - first add each new helper as a typed hole; rerun green with only leaf holes before proving a helper
  - after every edit scripts/vcheck dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy shows no error; holes are allowed only until the final delivery
  - scripts/vcheck --gate dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy exits 0 with zero counted holes on the whole file
  - scripts/specfreeze --against <snapshot> dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy keeps the original top statement unchanged
  - scripts/vaudit dafny/R/R06_Induction/agent/R06_AgentDecomposer.dfy reports no finding; no new assumptions or weakened claims
  - retain the transcript, each green leaf stage and the delivered dependency tree
*/
/* R06 decomposer (Exercises). Save the original snapshot before /contract R06.
A1/A1b only; no earlier learner file is imported. */
module R06_AgentDecomposer {
  import opened RG_A1_Re
  import opened RG_A1b_Facts
  // item: R06.A1d
  lemma BackwardsCorrect(r: Re, s: seq<char>)
    ensures Matches(Backwards(r), BackwardsStr(s)) <==> Matches(r, s)
}

/* DECOMPOSITION — learner-owned,22 min after the run.
   Draw helper nodes and caller edges. For every helper state its job and the
   transcript step when it first appeared as a hole. Mark any edit after which
   verification was not green, and the final full gate's count and scope.
   Delete one helper/step in an independent scratch copy to test necessity;
   record the actual observation without claiming unique minimality.
   AGENT DASHBOARD — goal / leaf stages / final gate / audit / freeze /
   transcript / correction: ...
*/
