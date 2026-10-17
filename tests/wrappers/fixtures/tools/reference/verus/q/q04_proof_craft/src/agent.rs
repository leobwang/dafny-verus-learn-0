//! Q04 agent file — synthetic tools fixture (Reference Solution): the twin of
//! verus/q/q04_proof_craft/src/agent.rs. Not course content.
use vstd::prelude::*;

verus! {

// reference-only: an invented delivery, so the twin's reference gate counts a task
pub proof fn agent_delivery()
    ensures
        1int + 1 == 2,
{
}

} // verus!
