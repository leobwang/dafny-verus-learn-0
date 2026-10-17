//! Test fixture (tests/wrappers): a delivery of lab/task.rs that proves the
//! lemma by hand and adds no verifier attribute (the lab gate passes it, its
//! assumption audit included).
use vstd::prelude::*;

verus! {

pub open spec fn count(n: nat) -> nat
    decreases n,
{
    if n == 0 { 0 } else { count((n - 1) as nat) + 1 }
}

pub proof fn count_is_n(n: nat)
    ensures
        count(n) == n,
    decreases n,
{
    if n > 0 {
        count_is_n((n - 1) as nat);
    }
}

} // verus!
