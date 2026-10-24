// Topic (e) Q33 dev pair pv-v101-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_003b.rs` at bbe93f7 (MIT; HumanEval/3), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `below_zero`'s `requires` and `ensures` from its prose (the PROMPT comment below), with
// any definition they need, and one call whose `requires` hold in `below_zero_witness`. You may
// add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/3
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

pub open spec fn sum(s: Seq<i64>) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s.last() + sum(s.drop_last())
    }
}

fn below_zero(operation: &[i64]) -> (r: bool)
{
    // We use i128 since it allows us to have sufficiently large numbers without overflowing.
    let mut s = 0i128;
    for i in 0usize..operation.len()
    {
        s = s + operation[i] as i128;
        if s < 0 {
            return true;
        }
    }
    false
}

/// A non-vacuity witness for `below_zero`: one call whose `requires` hold.
fn below_zero_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List


def below_zero(operations: List[int]) -> bool:
    """ You're given a list of deposit and withdrawal operations on a bank account that starts with
    zero balance. Your task is to detect if at any point the balance of account fallls below zero, and
    at that point function should return True. Otherwise it should return False.
    >>> below_zero([1, 2, 3])
    False
    >>> below_zero([1, 2, -4, 5])
    True
    """

*/

/*
### ENTRY POINT
below_zero
*/

/*
### CANONICAL SOLUTION
    balance = 0

    for op in operations:
        balance += op
        if balance < 0:
            return True

    return False

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([]) == False
    assert candidate([1, 2, -3, 1, 2, -3]) == False
    assert candidate([1, 2, -4, 5, 6]) == True
    assert candidate([1, -1, 2, -2, 5, -5, 4, -4]) == False
    assert candidate([1, -1, 2, -2, 5, -5, 4, -5]) == True
    assert candidate([1, -2, 2, -2, 5, -5, 4, -4]) == True

*/
