/*! # Q04 agent file — synthetic tools fixture (Reference Solution): the twin of
    dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy. Not course content. */
module Q04_AgentRetriever {
  // item: Q04.A1d S5
  const Agent := 1

  // reference-only: an invented delivery, so the twin's reference gate counts a task
  lemma AgentIsOne()
    ensures Agent == 1
  {
  }
}
