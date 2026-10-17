//! Q04 — synthetic tools fixture (tests/wrappers/fixtures/tools). Not course content.
use vstd::prelude::*;

#[cfg(test)]
mod tests;

verus! {

// item: Q04.P2dv S2 verdict
// SLOT: CHECK P2dv

pub fn twice(x: u32) -> (r: u32)
    requires
        x < 1000,
    ensures
        r == 2 * x,
{
    x + x
}

pub open spec fn double(n: nat) -> nat {
    n + n
}

// item: Q04.P11v S2 value
// **P11.** What is `double(3)`? Answer form: numeral
pub proof fn p11() {
    // SLOT: assert(double(3) == ???) by (compute_only);
}

// item: Q04.H1v S3
// uses: calc
// pair: Q04.H1d
pub proof fn h1(x: nat)
    ensures
        x + 0 == x,
{
    #[verifier::proof_note("Q04.H1v")] assume(false);
}

pub open spec fn sum(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        0
    } else {
        n + sum((n - 1) as nat)
    }
}

// item: Q04.H3v S3
// uses: lemma-call
pub proof fn sum_formula(n: nat)
    ensures
        2 * sum(n) == n * (n + 1),
    decreases n,
{
    #[verifier::proof_note("Q04.H3v")] assume(false);
}

} // verus!
