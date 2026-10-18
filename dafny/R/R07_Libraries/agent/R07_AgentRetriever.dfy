/* CONTRACT — R07 retriever race, R-v0
goal: complete the same two frozen library goals under the predeclared retrieval arm
allowed-files:
  - dafny/R/R07_Libraries/agent/R07_AgentRetriever.dfy
acceptance:
  - before the first edit retain the arm, budget, task hash and original snapshot; the other arm uses a fresh session and an identical original task
  - bodies contain only named standard-library lemma calls and arguments, each with a found-by note naming ide, grep, docs, llm or memory; no new proof helper, assert, calc or broad broadcast
  - the retrieval arm may inspect the pinned public library source; the no-retrieval arm may use only the printed library interface and its own session context; no protected reference access in either arm
  - after every edit run scripts/vcheck dafny/R/R07_Libraries/agent/R07_AgentRetriever.dfy and retain its actual verdict
  - scripts/vcheck --gate dafny/R/R07_Libraries/agent/R07_AgentRetriever.dfy exits0 with zero counted holes over the full file
  - scripts/vaudit dafny/R/R07_Libraries/agent/R07_AgentRetriever.dfy has no findings and scripts/specfreeze --against <snapshot> dafny/R/R07_Libraries/agent/R07_AgentRetriever.dfy preserves every original statement and import
  - retain all failed attempts, search and native-check costs; do not compare rates before matched arm evidence exists
*/
/*! R07 library retriever (Exercises). A2 re-supplies the class API; no earlier learner file.
A batch is a sequence of range listings: each listing is one class's ranges as A2's
accessor ClassRanges returns them (inclusive code-point pairs). */
module R07_AgentRetriever {
  import opened RG_A2_Deriv
  import S = Std.Collections.Seq

  // item: R07.A1d
  lemma FlattenClassBatches(left: seq<seq<CRange>>, right: seq<seq<CRange>>)
    ensures S.Flatten(left + right) == S.Flatten(left) + S.Flatten(right)

  // item: R07.A2d
  lemma ContainedClassBatch(batches: seq<seq<CRange>>, i: int)
    requires 0 <= i < |batches|
    ensures |S.FlattenReverse(batches)| >= |batches[i]|
}
