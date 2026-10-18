/* CONTRACT — R07 retriever race, R-v0
goal: complete the same two frozen library goals under the predeclared retrieval arm
allowed-files:
  - verus/r/r07_libraries/src/agent.rs
acceptance:
  - before the first edit retain the arm, budget, task hash and original snapshot; the other arm uses a fresh session and an identical original task
  - bodies contain only named standard-library lemma calls and arguments, each with a found-by note naming ide, grep, docs, llm or memory; no new proof helper, assert, calc or broad broadcast
  - the retrieval arm may inspect the pinned public library source; the no-retrieval arm may use only the printed library interface and its own session context; no protected reference access in either arm
  - after every edit run scripts/vcheck verus/r/r07_libraries/src/agent.rs and retain its actual verdict
  - scripts/vcheck --gate verus/r/r07_libraries/src/agent.rs exits0 with zero counted holes over the full file
  - scripts/vaudit verus/r/r07_libraries/src/agent.rs has no findings and scripts/specfreeze --against <snapshot> verus/r/r07_libraries/src/agent.rs preserves every original statement and import
  - retain all failed attempts, search and native-check costs; do not compare rates before matched arm evidence exists
*/
//! R07 library retriever (Reference Solution). A2 class ranges are inclusive u32 code-point
//! pairs; a batch is a sequence of range listings, each one class's ranges as A2's accessor
//! `ranges` returns them.
use vstd::prelude::*;
use vstd::seq_lib::*;

verus! {

// item: R07.A1v
proof fn lemma_flatten_class_batches(left: Seq<Seq<(u32, u32)>>, right: Seq<Seq<(u32, u32)>>)
    ensures
        (left + right).flatten() == left.flatten() + right.flatten(),
{
    lemma_flatten_concat(left, right); // found-by: grep
}

// item: R07.A2v
proof fn lemma_contained_class_batch(batches: Seq<Seq<(u32, u32)>>, i: int)
    requires
        0 <= i < batches.len(),
    ensures
        batches.flatten_alt().len() >= batches[i].len(),
{
    batches.lemma_flatten_length_ge_single_element_length(i); // found-by: grep
}

} // verus!
