// Topic (e) Q33 dev pair pv-v103-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_030.rs` at bbe93f7 (MIT; HumanEval/30), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `get_positive`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need, and one call whose `requires` hold in `get_positive_witness`.
// You may add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/30
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

fn get_positive(input: Vec<i32>) -> (positive_list: Vec<i32>)
{
    let mut positive_list = Vec::<i32>::new();
    let input_len = input.len();
    for pos in 0..input_len
    {
        let n = input[pos];
        if n > 0 {
            positive_list.push(n);
        }
    }
    positive_list
}

/// A non-vacuity witness for `get_positive`: one call whose `requires` hold.
fn get_positive_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def get_positive(l: list):
    """Return only positive numbers in the list.
    >>> get_positive([-1, 2, -4, 5, 6])
    [2, 5, 6]
    >>> get_positive([5, 3, -5, 2, -3, 3, 9, 0, 123, 1, -10])
    [5, 3, 2, 3, 9, 123, 1]
    """

*/

/*
### ENTRY POINT
get_positive
*/

/*
### CANONICAL SOLUTION
    return [e for e in l if e > 0]

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert candidate([-1, -2, 4, 5, 6]) == [4, 5, 6]
    assert candidate([5, 3, -5, 2, 3, 3, 9, 0, 123, 1, -10]) == [5, 3, 2, 3, 3, 9, 123, 1]
    assert candidate([-1, -2]) == []
    assert candidate([]) == []


*/
