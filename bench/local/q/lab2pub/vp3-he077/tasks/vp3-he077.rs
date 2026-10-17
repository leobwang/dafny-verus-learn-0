// Lab 2 public task vp3-he077 (Q15; QPLAN §25.6): HumanEval-Verus `human_eval_077.rs` at
// bbe93f7 (MIT; bench/local/q/lab2pub/NOTICE), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py
// (verus-lab2-form).
// Write `iscube`'s `requires` and `ensures` from its prose (the PROMPT comment below), with any
// definition they need (a spec fn they name must be `pub open`), and one call whose `requires`
// hold in `iscube_witness`. You may add proof annotations (loop invariants, assertions, proof
// blocks, lemmas); never change its executable code, and keep every other line of the file.
// lab2-quantified-definition: cube
/*
### ID
HumanEval/77
*/
/*
### VERUS BEGIN
*/
use vstd::{invariant, prelude::*};

verus! {

pub open spec fn cube(x: nat) -> nat {
    x * x * x
}

fn iscube(n: u64) -> (out: bool)
{
    let mut left = 0;
    let mut right = 2642245;

    while (left <= right)
        decreases right - left,
    {
        let i = (right + left) / 2;
        let v: u64 = i * i * i;
        if (v == n) {
            return true;
        } else if (left == right) {
            return false;
        } else if (v > n) {
            right = i;
        } else if (v < n) {
            left = i + 1;
        }
    }

    return false;
}

/// A non-vacuity witness for `iscube`: one call whose `requires` hold.
fn iscube_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT

def iscube(a):
    '''
    Write a function that takes an integer a and returns True
    if this ingeger is a cube of some integer number.
    Note: you may assume the input is always valid.
    Examples:
    iscube(1) ==> True
    iscube(2) ==> False
    iscube(-1) ==> True
    iscube(64) ==> True
    iscube(0) ==> True
    iscube(180) ==> False
    '''

*/

/*
### ENTRY POINT
iscube
*/

/*
### CANONICAL SOLUTION
    a = abs(a)
    return int(round(a ** (1. / 3))) ** 3 == a

*/

/*
### TEST
def check(candidate):

    # Check some simple cases
    assert candidate(1) == True, "First test error: " + str(candidate(1))
    assert candidate(2) == False, "Second test error: " + str(candidate(2))
    assert candidate(-1) == True, "Third test error: " + str(candidate(-1))
    assert candidate(64) == True, "Fourth test error: " + str(candidate(64))
    assert candidate(180) == False, "Fifth test error: " + str(candidate(180))
    assert candidate(1000) == True, "Sixth test error: " + str(candidate(1000))


    # Check some edge cases that are easy to work out by hand.
    assert candidate(0) == True, "1st edge test error: " + str(candidate(0))
    assert candidate(1729) == False, "2nd edge test error: " + str(candidate(1728))


*/
