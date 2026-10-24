// Topic (e) Q33 dev pair pv-v107-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_042.rs` at bbe93f7 (MIT; HumanEval/42), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `incr_list`'s `requires` and `ensures` from its prose (the PROMPT comment below), with
// any definition they need, and one call whose `requires` hold in `incr_list_witness`. You may
// add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/42
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

fn incr_list(l: Vec<i32>) -> (result: Vec<i32>)

{
    let mut result = Vec::with_capacity(l.len());
    for i in 0..l.len()
    {
        result.push(l[i] + 1);
    }
    result
}

/// A non-vacuity witness for `incr_list`: one call whose `requires` hold.
fn incr_list_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def incr_list(l: list):
    """Return list with elements incremented by 1.
    >>> incr_list([1, 2, 3])
    [2, 3, 4]
    >>> incr_list([5, 3, 5, 2, 3, 3, 9, 0, 123])
    [6, 4, 6, 3, 4, 4, 10, 1, 124]
    """

*/

/*
### ENTRY POINT
incr_list
*/

/*
### CANONICAL SOLUTION
    return [(e + 1) for e in l]

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert candidate([]) == []
    assert candidate([3, 2, 1]) == [4, 3, 2]
    assert candidate([5, 2, 5, 2, 3, 3, 9, 0, 123]) == [6, 3, 6, 3, 4, 4, 10, 1, 124]


*/
