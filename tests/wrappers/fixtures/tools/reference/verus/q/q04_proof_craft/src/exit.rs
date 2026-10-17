//! Q04 exit — synthetic tools fixture (Reference Solution): the twin of
//! verus/q/q04_proof_craft/src/exit.rs.
use vstd::prelude::*;

verus! {

pub open spec fn double(n: nat) -> nat {
    n + n
}

// item: Q04.X1v S4
// uses: calc
// need: pub proof fn double_is_twice(n: nat)
pub proof fn double_is_twice(n: nat)
    ensures
        double(n) == 2 * n,
{
}

// item: Q04.X2v S5
// uses: lemma-call
pub proof fn double_mono(a: nat, b: nat)
    requires
        a <= b,
    ensures
        double(a) <= double(b),
{
    double_is_twice(a);
    double_is_twice(b);
}

} // verus!
