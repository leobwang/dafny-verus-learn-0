// Topic (e) Q33 dev pair pv-v109-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_020.rs` at bbe93f7 (MIT; HumanEval/20), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `closest_pair`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need, and one call whose `requires` hold in `closest_pair_witness`.
// You may add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/20
*/
/*
### VERUS BEGIN
*/
use vstd::math::abs;
use vstd::prelude::*;

verus! {

// TODO: Put your solution (the specification, implementation, and proof) to the task here
// Implementation
fn closest_pair(numbers: Vec<i32>) -> (res: (i32, i32))
{
    let mut closest_pair_high = numbers[0];
    let mut closest_pair_low = numbers[1];
    if closest_pair_high < closest_pair_low {
        let temp = closest_pair_high;
        closest_pair_high = closest_pair_low;
        closest_pair_low = temp;
    }
    let mut min_diff = closest_pair_high as i64 - closest_pair_low as i64;

    let mut i = 1;
    while i < numbers.len()
        decreases numbers.len() - i,
    {
        let mut j = 0;
        while j < i
            decreases i - j,
        {
            let diff = if numbers[i] < numbers[j] {
                numbers[j] as i64 - numbers[i] as i64
            } else {
                numbers[i] as i64 - numbers[j] as i64
            };
            if diff < min_diff {
                closest_pair_low =
                if numbers[i] < numbers[j] {
                    numbers[i]
                } else {
                    numbers[j]
                };
                closest_pair_high =
                if numbers[i] > numbers[j] {
                    numbers[i]
                } else {
                    numbers[j]
                };
                min_diff = closest_pair_high as i64 - closest_pair_low as i64;
            }
            j += 1;
        }
        i += 1;
    }

    return (closest_pair_low, closest_pair_high);
}

/// A non-vacuity witness for `closest_pair`: one call whose `requires` hold.
fn closest_pair_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List, Tuple


def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    """ From a supplied list of numbers (of length at least two) select and return two that are the closest to each
    other and return them in order (smaller number, larger number).
    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])
    (2.0, 2.2)
    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0])
    (2.0, 2.0)
    """

*/

/*
### ENTRY POINT
find_closest_elements
*/

/*
### CANONICAL SOLUTION
    closest_pair = None
    distance = None

    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                if distance is None:
                    distance = abs(elem - elem2)
                    closest_pair = tuple(sorted([elem, elem2]))
                else:
                    new_distance = abs(elem - elem2)
                    if new_distance < distance:
                        distance = new_distance
                        closest_pair = tuple(sorted([elem, elem2]))

    return closest_pair

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([1.0, 2.0, 3.9, 4.0, 5.0, 2.2]) == (3.9, 4.0)
    assert candidate([1.0, 2.0, 5.9, 4.0, 5.0]) == (5.0, 5.9)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.2]) == (2.0, 2.2)
    assert candidate([1.0, 2.0, 3.0, 4.0, 5.0, 2.0]) == (2.0, 2.0)
    assert candidate([1.1, 2.2, 3.1, 4.1, 5.1]) == (2.2, 3.1)


*/
