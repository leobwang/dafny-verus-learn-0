// Topic (e) Q33 dev pair pv-v104-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_122.rs` at bbe93f7 (MIT; HumanEval/122), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `add_elements`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need, and one call whose `requires` hold in `add_elements_witness`.
// You may add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/122
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

/// Implementation of add_elements
fn add_elements(arr: Vec<i32>, k: u32) -> (result: i64)
{
    let mut res: i64 = 0;
    for i in 0..k
    {
        if -99 <= arr[i as usize] && arr[i as usize] <= 99 {
            res += arr[i as usize] as i64;
        }
    }
    res
}

/// A non-vacuity witness for `add_elements`: one call whose `requires` hold.
fn add_elements_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT

def add_elements(arr, k):
    """
    Given a non-empty array of integers arr and an integer k, return
    the sum of the elements with at most two digits from the first k elements of arr.

    Example:

        Input: arr = [111,21,3,4000,5,6,7,8,9], k = 4
        Output: 24 # sum of 21 + 3

    Constraints:
        1. 1 <= len(arr) <= 100
        2. 1 <= k <= len(arr)
    """

*/

/*
### ENTRY POINT
add_elements
*/

/*
### CANONICAL SOLUTION
    return sum(elem for elem in arr[:k] if len(str(elem)) <= 2)

*/

/*
### TEST
def check(candidate):

    # Check some simple cases
    assert candidate([1,-2,-3,41,57,76,87,88,99], 3) == -4
    assert candidate([111,121,3,4000,5,6], 2) == 0
    assert candidate([11,21,3,90,5,6,7,8,9], 4) == 125
    assert candidate([111,21,3,4000,5,6,7,8,9], 4) == 24, "This prints if this assert fails 1 (good for debugging!)"

    # Check some edge cases that are easy to work out by hand.
    assert candidate([1], 1) == 1, "This prints if this assert fails 2 (also good for debugging!)"


*/
