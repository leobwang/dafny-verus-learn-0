//! Q04 — synthetic tools fixture (Reference Solution): the twin of
//! verus/q/q04_proof_craft/src/lib.rs (tests/wrappers/fixtures/tools).
use vstd::prelude::*;

#[cfg(test)]
mod tests;

verus! {

// item: Q04.P2dv S2 verdict
// CHECK P2dv

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
    assert(double(3) == 6) by (compute_only);
}

// item: Q04.H1v S3
// uses: calc
// pair: Q04.H1d
pub proof fn h1(x: nat)
    ensures
        x + 0 == x,
{
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
    if n > 0 {
        let m = (n - 1) as nat;
        sum_formula(m);
        assert(sum(n) == n + sum(m));
        assert(2 * sum(m) == m * (m + 1));
        // did: the product step of the induction
        assert(n * (n + 1) == m * (m + 1) + 2 * n) by (nonlinear_arith)
            requires
                n == m + 1,
        ;
        assert(2 * sum(n) == 2 * n + 2 * sum(m));
        assert(2 * sum(n) == n * (n + 1));
    } else {
        assert(sum(n) == 0);
    }
}

} // verus!
