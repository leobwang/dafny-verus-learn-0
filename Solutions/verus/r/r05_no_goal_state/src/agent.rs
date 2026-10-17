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
//! R05 obligation prover (Reference Solution); save snapshot first.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
verus! {
pub proof fn lemma_chunk_in_star(a: Re,u: Seq<char>)
    requires matches(a,u),
    ensures matches(Re::Star(Box::new(a)),u),
{
    if u.len() > 0 {
        assert(u.subrange(0, u.len() as int) =~= u);
        assert(u.subrange(u.len() as int, u.len() as int) =~= Seq::<char>::empty());
        assert(matches(Re::Star(Box::new(a)), Seq::<char>::empty()));
    }
}
pub proof fn lemma_join_star_words(a: Re,u: Seq<char>,v: Seq<char>)
    requires matches(Re::Star(Box::new(a)),u),matches(Re::Star(Box::new(a)),v),
    ensures matches(Re::Star(Box::new(a)),u+v),
    decreases u.len(),
{
    let st = Re::Star(Box::new(a));
    let t = u + v;
    if u.len() == 0 {
        assert(t =~= v);
    } else {
        let i = choose|i: int|
            1 <= i <= u.len() && matches(a, #[trigger] u.subrange(0, i)) && matches(
                st,
                u.subrange(i, u.len() as int),
            );
        lemma_join_star_words(a, u.subrange(i, u.len() as int), v);
        assert(t.subrange(0, i) =~= u.subrange(0, i));
        assert(t.subrange(i, t.len() as int) =~= u.subrange(i, u.len() as int) + v);
    }
}
// item: R05.A1v
pub proof fn lemma_append_chunk(a: Re,u: Seq<char>,v: Seq<char>)
    requires matches(Re::Star(Box::new(a)),u), matches(a,v),
    ensures matches(Re::Star(Box::new(a)),u+v),
{ lemma_chunk_in_star(a,v); lemma_join_star_words(a,u,v); }

pub proof fn lemma_collapse_star_cat(a: Re,s: Seq<char>)
    requires matches(Re::Cat(Box::new(Re::Star(Box::new(a))),Box::new(Re::Star(Box::new(a)))),s),
    ensures matches(Re::Star(Box::new(a)),s),
{
    let st=Re::Star(Box::new(a));
    let i=choose|i:int| 0 <= i <= s.len() && matches(st,#[trigger] s.subrange(0,i)) && matches(st,s.subrange(i,s.len() as int));
    lemma_join_star_words(a,s.subrange(0,i),s.subrange(i,s.len() as int));
    assert(s.subrange(0,i)+s.subrange(i,s.len() as int) =~= s);
}

/* OBLIGATION LOG — learner-owned after the contract run.
   Fast-channel calls and failed obligations per lemma: ...
   Added facts/helpers, and deletion probes in a scratch copy: ...
   One final full gate: command / exit / zero-hole count / timestamp: ...
   Audit and snapshot comparison: ...
   Latency/call cost, remaining uncertainty and correction: ...
*/
}
