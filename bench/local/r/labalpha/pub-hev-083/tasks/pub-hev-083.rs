// R12_HINT_SITES: [{"name":"i1","identifiers":["Vec","i","i32","len","max_so_far","number","numbers","pos","result","rolling_max","seq_max"]},{"name":"i2","identifiers":["Vec","i","i32","len","max_so_far","number","numbers","pos","result","rolling_max","seq_max"]},{"name":"i3","identifiers":["Vec","i","i32","len","max_so_far","number","numbers","pos","result","rolling_max","seq_max"]}]
// R12_SOURCE_SPANS: [{"symbol":"rolling_max","start":27,"end":48}]
// R12 public task: humaneval-verus human_eval_009.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/9
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

spec fn seq_max(a: Seq<i32>) -> i32
    decreases a.len(),
{
    if a.len() == 0 {
        i32::MIN
    } else if a.last() > seq_max(a.drop_last()) {
        a.last()
    } else {
        seq_max(a.drop_last())
    }
}

fn rolling_max(numbers: Vec<i32>) -> (result: Vec<i32>)
    ensures
        result.len() == numbers.len(),  // result vector should have the same length as input
        forall|i: int| 0 <= i < numbers.len() ==> result[i] == seq_max(numbers@[..i + 1]),
{
    let mut max_so_far = i32::MIN;
    let mut result = Vec::with_capacity(numbers.len());
    for pos in 0..numbers.len()
        invariant
            /*R12_HINT:i1*/ true,
            /*R12_HINT:i2*/ true,
            /*R12_HINT:i3*/ true,
    {
        let number = numbers[pos];
        if number > max_so_far {
            max_so_far = number;
        }
        result.push(max_so_far);
        assert(numbers@[..pos + 1].drop_last() =~= numbers@[..pos]);
    }
    result
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List, Tuple


def rolling_max(numbers: List[int]) -> List[int]:
    """ From a given list of integers, generate a list of rolling maximum element found until given moment
    in the sequence.
    >>> rolling_max([1, 2, 3, 2, 3, 4, 2])
    [1, 2, 3, 3, 3, 4, 4]
    """

*/

/*
### ENTRY POINT
rolling_max
*/

/*
### CANONICAL SOLUTION
    running_max = None
    result = []

    for n in numbers:
        if running_max is None:
            running_max = n
        else:
            running_max = max(running_max, n)

        result.append(running_max)

    return result

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([]) == []
    assert candidate([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert candidate([4, 3, 2, 1]) == [4, 4, 4, 4]
    assert candidate([3, 2, 3, 100, 3]) == [3, 3, 3, 100, 100]

*/
