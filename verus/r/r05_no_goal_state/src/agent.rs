/* CONTRACT — R05 obligation prover, R-v0
goal: prove both supplied lemmas, preserving every statement
allowed-files:
  - verus/r/r05_no_goal_state/src/agent.rs
acceptance:
  - per edit use only scripts/vcheck --symbol <qualified-name> verus/r/r05_no_goal_state/src/agent.rs; record each command, verdict and elapsed time
  - exactly one full scripts/vcheck --gate verus/r/r05_no_goal_state/src/agent.rs run, last; exit0 with zero counted holes is required for delivery
  - scripts/vaudit verus/r/r05_no_goal_state/src/agent.rs reports no finding
  - scripts/specfreeze --against <snapshot> verus/r/r05_no_goal_state/src/agent.rs reports no statement change
  - no assumptions, weakened guarantees, strengthened inputs or filtered final verification
  - stop and report if the final gate fails; do not spend a second final gate or call an incomplete delivery done
*/
//! R05 obligation prover (Exercises); save snapshot first.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
verus! {
// item: R05.A1v
pub proof fn lemma_append_chunk(a: Re,u: Seq<char>,v: Seq<char>)
    requires matches(Re::Star(Box::new(a)),u), matches(a,v),
    ensures matches(Re::Star(Box::new(a)),u+v),
{ #[verifier::proof_note("R05.A1v")] assume(false); }

pub proof fn lemma_collapse_star_cat(a: Re,s: Seq<char>)
    requires matches(Re::Cat(Box::new(Re::Star(Box::new(a))),Box::new(Re::Star(Box::new(a)))),s),
    ensures matches(Re::Star(Box::new(a)),s),
{ #[verifier::proof_note("R05.A1v")] assume(false); }

/* OBLIGATION LOG — learner-owned after the contract run.
   Fast-channel calls and failed obligations per lemma: ...
   Added facts/helpers, and deletion probes in a scratch copy: ...
   One final full gate: command / exit / zero-hole count / timestamp: ...
   Audit and snapshot comparison: ...
   Latency/call cost, remaining uncertainty and correction: ...
*/
}
