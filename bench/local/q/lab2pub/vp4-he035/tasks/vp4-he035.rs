// Lab 2 public task vp4-he035 (Q15; QPLAN §25.6): HumanEval-Verus `human_eval_035.rs` at
// bbe93f7 (MIT; bench/local/q/lab2pub/NOTICE), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py
// (verus-lab2-form).
// Write `max_element`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need (a spec fn they name must be `pub open`), and one call whose
// `requires` hold in `max_element_witness`. You may add proof annotations (loop invariants,
// assertions, proof blocks, lemmas); never change its executable code, and keep every other
// line of the file.
/*
### ID
HumanEval/35
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

fn max_element(a: &Vec<i32>) -> (max: i32)
{
    let mut max = a[0];
    for i in 1..a.len()
    {
        if a[i] > max {
            max = a[i];
        }
    }
    max
}

/// A non-vacuity witness for `max_element`: one call whose `requires` hold.
fn max_element_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def max_element(l: list):
    """Return maximum element in the list.
    >>> max_element([1, 2, 3])
    3
    >>> max_element([5, 3, -5, 2, -3, 3, 9, 0, 123, 1, -10])
    123
    """

*/

/*
### ENTRY POINT
max_element
*/

/*
### CANONICAL SOLUTION
    m = l[0]
    for e in l:
        if e > m:
            m = e
    return m

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert candidate([1, 2, 3]) == 3
    assert candidate([5, 3, -5, 2, -3, 3, 9, 0, 124, 1, -10]) == 124

*/
