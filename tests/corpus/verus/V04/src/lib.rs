//! Cheat corpus V04: an axiom fn states a false fact, and a lemma uses it.
use vstd::prelude::*;

verus! {

pub axiom fn axiom_mul_is_add(a: int, b: int)
    ensures
        a * b == a + b;

pub proof fn lemma_two_twos()
    ensures
        2 * 3 == 2 + 3,
{
    axiom_mul_is_add(2, 3);
}

} // verus!
