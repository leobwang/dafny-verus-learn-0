// Lab 2 public task vp2-he033 (Q15; QPLAN §25.6): HumanEval-Verus `human_eval_033.rs` at
// bbe93f7 (MIT; bench/local/q/lab2pub/NOTICE), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py
// (verus-lab2-form).
// Write `sort_third`'s `requires` and `ensures` from its prose (the PROMPT comment below), with
// any definition they need (a spec fn they name must be `pub open`), and one call whose
// `requires` hold in `sort_third_witness`. You may add proof annotations (loop invariants,
// assertions, proof blocks, lemmas); never change its executable code, and keep every other
// line of the file.
/*
### ID
HumanEval/33
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

// This function counts the number of elements of `s` that are equal to `x`.
pub open spec fn count<T>(s: Seq<T>, x: T) -> int
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        count(s[1..], x) + if s[0] == x {
            1int
        } else {
            0int
        }
    }
}

// This is the function we were asked to write.
fn sort_third(l: Vec<i32>) -> (l_prime: Vec<i32>)
{
    let l_len = l.len();
    let mut pos_being_set_to_smallest: usize = 0;
    let mut l_prime: Vec<i32> = l;
    // Iterate `pos_being_set_to_smallest` by 3 from 0 to `l_len`. Each time,
    // look for the smallest element at a position divisible by three in the
    // part of the vector at or past `pos_being_set_to_smallest`. Swap that
    // element with the one at `pos_being_set_to_smallest`.
    while pos_being_set_to_smallest < l_len
        decreases l_len + 3 - pos_being_set_to_smallest,
    {
        // Iterate `pos_during_scan_for_smallest` by 3 from `pos_being_set_to_smallest`
        // to `l_len`. Keep track of the position of the smallest element found so far
        // in `pos_of_smallest_found_so_far`.
        let mut pos_of_smallest_found_so_far: usize = pos_being_set_to_smallest;
        let mut pos_during_scan_for_smallest: usize = pos_being_set_to_smallest;
        while pos_during_scan_for_smallest < l_len
            decreases l_len + 3 - pos_during_scan_for_smallest,
        {
            if l_prime[pos_during_scan_for_smallest] < l_prime[pos_of_smallest_found_so_far] {
                pos_of_smallest_found_so_far = pos_during_scan_for_smallest;
            }
            pos_during_scan_for_smallest = pos_during_scan_for_smallest + 3;
        }
        // Swap the elements at positions `pos_being_set_to_smallest`
        // and `pos_of_smallest_found_so_far`.
        let v1 = l_prime[pos_being_set_to_smallest];
        let v2 = l_prime[pos_of_smallest_found_so_far];
        l_prime.set(pos_being_set_to_smallest, v2);
        l_prime.set(pos_of_smallest_found_so_far, v1);
        pos_being_set_to_smallest = pos_being_set_to_smallest + 3;
    }
    l_prime
}

/// A non-vacuity witness for `sort_third`: one call whose `requires` hold.
fn sort_third_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def sort_third(l: list):
    """This function takes a list l and returns a list l' such that
    l' is identical to l in the indicies that are not divisible by three, while its values at the indicies that are divisible by three are equal
    to the values of the corresponding indicies of l, but sorted.
    >>> sort_third([1, 2, 3])
    [1, 2, 3]
    >>> sort_third([5, 6, 3, 4, 8, 9, 2])
    [2, 6, 3, 4, 8, 9, 5]
    """

*/

/*
### ENTRY POINT
sort_third
*/

/*
### CANONICAL SOLUTION
    l = list(l)
    l[::3] = sorted(l[::3])
    return l

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert tuple(candidate([1, 2, 3])) == tuple(sort_third([1, 2, 3]))
    assert tuple(candidate([5, 3, -5, 2, -3, 3, 9, 0, 123, 1, -10])) == tuple(sort_third([5, 3, -5, 2, -3, 3, 9, 0, 123, 1, -10]))
    assert tuple(candidate([5, 8, -12, 4, 23, 2, 3, 11, 12, -10])) == tuple(sort_third([5, 8, -12, 4, 23, 2, 3, 11, 12, -10]))
    assert tuple(candidate([5, 6, 3, 4, 8, 9, 2])) == tuple([2, 6, 3, 4, 8, 9, 5])
    assert tuple(candidate([5, 8, 3, 4, 6, 9, 2])) == tuple([2, 8, 3, 4, 6, 9, 5])
    assert tuple(candidate([5, 6, 9, 4, 8, 3, 2])) == tuple([2, 6, 9, 4, 8, 3, 5])
    assert tuple(candidate([5, 6, 3, 4, 8, 9, 2, 1])) == tuple([2, 6, 3, 4, 8, 9, 5, 1])


*/
