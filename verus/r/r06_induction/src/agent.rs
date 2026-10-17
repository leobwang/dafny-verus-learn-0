/* CONTRACT — R06 decomposer, R-v0
goal: prove the one top statement by decomposition, preserving its contract
allowed-files:
  - verus/r/r06_induction/src/agent.rs
acceptance:
  - first add each new helper as a typed hole; rerun green with only leaf holes before proving a helper
  - after every edit scripts/vcheck verus/r/r06_induction/src/agent.rs shows no error; holes are allowed only until the final delivery
  - scripts/vcheck --gate verus/r/r06_induction/src/agent.rs exits 0 with zero counted holes on the whole file
  - scripts/specfreeze --against <snapshot> verus/r/r06_induction/src/agent.rs keeps the original top statement unchanged
  - scripts/vaudit verus/r/r06_induction/src/agent.rs reports no finding; no new assumptions or weakened claims
  - retain the transcript, each green leaf stage and the delivered dependency tree
*/
/* R06 decomposer (Exercises). Save the original snapshot before /contract R06.
A1/A1b only; no earlier learner file is imported. */
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
verus! {
// item: R06.A1v
pub proof fn lemma_backwards_correct(r: Re,s: Seq<char>)
    ensures matches(backwards(r),backwards_str(s)) <==> matches(r,s),
{ #[verifier::proof_note("R06.A1v")] assume(false); }
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
