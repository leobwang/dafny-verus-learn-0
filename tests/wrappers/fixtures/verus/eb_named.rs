//! Test fixture (tests/wrappers): an invented proof fn with a named return (a
//! witness) for the empty-body gate's `{ arbitrary() }` body (QPLAN §30 Q65).
use vstd::prelude::*;

verus! {

pub open spec fn count3(n: nat) -> nat
    decreases n,
{
    if n == 0 { 0 } else { 1 + count3((n - 1) as nat) }
}

pub proof fn witness_three() -> (r: nat)
    ensures
        count3(r) == 3,
{
    reveal_with_fuel(count3, 4);
    3
}

} // verus!
