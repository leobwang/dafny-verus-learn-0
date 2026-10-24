// Topic (e) Q33 dev pair pv-v105-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_055b.rs` at bbe93f7 (MIT; HumanEval/55), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `fib`'s `requires` and `ensures` from its prose (the PROMPT comment below), with any
// definition they need, and one call whose `requires` hold in `fib_witness`. You may add proof
// annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/55
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

// O(n) non-recursive solution using same spec as 55a
#[verifier::memoize]
pub open spec fn spec_fib(n: nat) -> nat
    decreases n,
{
    if (n == 0) {
        0
    } else if (n == 1) {
        1
    } else {
        spec_fib((n - 1) as nat) + spec_fib((n - 2) as nat)
    }
}

fn fib(n: u32) -> (ret: Option<u32>)
{
    if n == 0 {
        return Some(0);
    }
    if n == 1 {
        return Some(1);
    }
    if n > 47 {
        return None;
    }
    let mut a: u32 = 0;
    let mut b: u32 = 1;
    let mut i: u32 = 2;

    for i in 1..n
    {
        let sum = a + b;
        a = b;
        b = sum;
    }
    Some(b)
}

/// A non-vacuity witness for `fib`: one call whose `requires` hold.
fn fib_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def fib(n: int):
    """Return n-th Fibonacci number.
    >>> fib(10)
    55
    >>> fib(1)
    1
    >>> fib(8)
    21
    """

*/

/*
### ENTRY POINT
fib
*/

/*
### CANONICAL SOLUTION
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fib(n - 1) + fib(n - 2)

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert candidate(10) == 55
    assert candidate(1) == 1
    assert candidate(8) == 21
    assert candidate(11) == 89
    assert candidate(12) == 144


*/
