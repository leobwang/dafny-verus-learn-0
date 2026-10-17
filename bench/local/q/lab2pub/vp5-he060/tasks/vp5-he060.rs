// Lab 2 public task vp5-he060 (Q15; QPLAN §25.6): HumanEval-Verus `human_eval_060.rs` at
// bbe93f7 (MIT; bench/local/q/lab2pub/NOTICE), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py
// (verus-lab2-form).
// Write `sum_to_n`'s `requires` and `ensures` from its prose (the PROMPT comment below), with
// any definition they need (a spec fn they name must be `pub open`), and one call whose
// `requires` hold in `sum_to_n_witness`. You may add proof annotations (loop invariants,
// assertions, proof blocks, lemmas); never change its executable code, and keep every other
// line of the file.
/*
### ID
HumanEval/60
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

pub open spec fn spec_sum_to_n(n: nat) -> nat
    decreases n,
{
    if (n == 0) {
        0
    } else {
        n + spec_sum_to_n((n - 1) as nat)
    }
}

fn sum_to_n(n: u32) -> (sum: Option<u32>)
{
    if n >= 92682 {
        return None;
    }
    let mut res: u32 = 0;
    let mut sum: u32 = 0;
    let mut i: u32 = 0;
    while i < n
        decreases n - i,
    {
        i += 1;
        res = i + res;
    }
    Some(res)
}

/// A non-vacuity witness for `sum_to_n`: one call whose `requires` hold.
fn sum_to_n_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def sum_to_n(n: int):
    """sum_to_n is a function that sums numbers from 1 to n.
    >>> sum_to_n(30)
    465
    >>> sum_to_n(100)
    5050
    >>> sum_to_n(5)
    15
    >>> sum_to_n(10)
    55
    >>> sum_to_n(1)
    1
    """

*/

/*
### ENTRY POINT
sum_to_n
*/

/*
### CANONICAL SOLUTION
    return sum(range(n + 1))

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert candidate(1) == 1
    assert candidate(6) == 21
    assert candidate(11) == 66
    assert candidate(30) == 465
    assert candidate(100) == 5050


*/
