// Topic (e) Q33 dev pair pv-v102-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_073.rs` at bbe93f7 (MIT; HumanEval/73), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `smallest_change`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need, and one call whose `requires` hold in
// `smallest_change_witness`. You may add proof annotations; never change its executable code,
// and keep every other line.
/*
### ID
HumanEval/73
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

fn smallest_change(v: Vec<i32>) -> (change: usize)
{
    let mut ans: usize = 0;
    for i in 0..v.len() / 2
    {
        if v[i] != v[v.len() - i - 1] {
            ans += 1;
        }
    }
    ans
}

/// A non-vacuity witness for `smallest_change`: one call whose `requires` hold.
fn smallest_change_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT

def smallest_change(arr):
    """
    Given an array arr of integers, find the minimum number of elements that
    need to be changed to make the array palindromic. A palindromic array is an array that
    is read the same backwards and forwards. In one change, you can change one element to any other element.

    For example:
    smallest_change([1,2,3,5,4,7,9,6]) == 4
    smallest_change([1, 2, 3, 4, 3, 2, 2]) == 1
    smallest_change([1, 2, 3, 2, 1]) == 0
    """

*/

/*
### ENTRY POINT
smallest_change
*/

/*
### CANONICAL SOLUTION
    ans = 0
    for i in range(len(arr) // 2):
        if arr[i] != arr[len(arr) - i - 1]:
            ans += 1
    return ans

*/

/*
### TEST
def check(candidate):

    # Check some simple cases
    assert candidate([1,2,3,5,4,7,9,6]) == 4
    assert candidate([1, 2, 3, 4, 3, 2, 2]) == 1
    assert candidate([1, 4, 2]) == 1
    assert candidate([1, 4, 4, 2]) == 1

    # Check some edge cases that are easy to work out by hand.
    assert candidate([1, 2, 3, 2, 1]) == 0
    assert candidate([3, 1, 1, 3]) == 0
    assert candidate([1]) == 0
    assert candidate([0, 1]) == 1


*/
