// Topic (e) Q33 dev pair pv-v108-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_008.rs` at bbe93f7 (MIT; HumanEval/8), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `sum_product`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need, and one call whose `requires` hold in `sum_product_witness`.
// You may add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/8
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

/// Specification for taking the product of a sequence of numbers
pub open spec fn product(numbers: Seq<u32>) -> int {
    numbers.fold_left(1, |acc: int, x| acc * x)
}

/// Implementation.  We leave the consequences of an intermediate
/// overflow during the product calculation underspecified.
#[verifier::spinoff_prover]
fn sum_product(numbers: Vec<u32>) -> (result: (u64, Option<u32>))
{
    let mut sum_value: u64 = 0;
    let mut prod_value: Option<u32> = Some(1);
    for index in 0..numbers.len()
    {
        sum_value += numbers[index] as u64;
        prod_value =
        match prod_value {
            Some(v) => v.checked_mul(numbers[index]),
            None => None,
        };
    }
    (sum_value, prod_value)
}

/// A non-vacuity witness for `sum_product`: one call whose `requires` hold.
fn sum_product_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List, Tuple


def sum_product(numbers: List[int]) -> Tuple[int, int]:
    """ For a given list of integers, return a tuple consisting of a sum and a product of all the integers in a list.
    Empty sum should be equal to 0 and empty product should be equal to 1.
    >>> sum_product([])
    (0, 1)
    >>> sum_product([1, 2, 3, 4])
    (10, 24)
    """

*/

/*
### ENTRY POINT
sum_product
*/

/*
### CANONICAL SOLUTION
    sum_value = 0
    prod_value = 1

    for n in numbers:
        sum_value += n
        prod_value *= n
    return sum_value, prod_value

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([]) == (0, 1)
    assert candidate([1, 1, 1]) == (3, 1)
    assert candidate([100, 0]) == (100, 0)
    assert candidate([3, 5, 7]) == (3 + 5 + 7, 3 * 5 * 7)
    assert candidate([10]) == (10, 10)

*/
