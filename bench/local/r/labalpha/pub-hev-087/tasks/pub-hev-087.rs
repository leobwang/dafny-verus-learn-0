// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"d1","kind":"decreases"},{"name":"a3"}]
// R12_SOURCE_SPANS: [{"symbol":"concatenate_impl","start":43,"end":63}]
// R12 public task: humaneval-verus human_eval_028.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/28
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

pub closed spec fn concat_helper(strings: Seq<Seq<char>>, i: nat) -> Seq<char>
    recommends
        i <= strings.len(),
    decreases strings.len() - i,
{
    if (i >= strings.len()) {
        seq![]
    } else {
        strings[i as int] + concat_helper(strings, i + 1)
    }
}

pub open spec fn concatenate(strings: Seq<Seq<char>>) -> Seq<char> {
    concat_helper(strings, 0)
}

proof fn sanity_check() {
    assert(concatenate(seq![seq!['a'], seq!['b'], seq!['c']]) == seq!['a', 'b', 'c']) by (compute);
    assert(concatenate(Seq::empty()) == Seq::<char>::empty());
    assert(concatenate(seq![seq!['a', 'z'], seq!['b'], seq!['c', 'y']]) == seq![
        'a',
        'z',
        'b',
        'c',
        'y',
    ]) by (compute);
}

fn concatenate_impl(strings: Vec<Vec<char>>) -> (joined: Vec<char>)
    ensures
        joined@ == concatenate(strings.deep_view()),
{
    let mut i = 0;
    let mut joined = vec![];

    while (i < strings.len())
        invariant
            /*R12_HINT:i1*/ true,
            /*R12_HINT:i2*/ true,
        decreases /*R12_DECREASES:d1*/ (0 as int),
    {
        assert(/*R12_HINT:a3*/ true);

        let mut copy_str = strings[i].clone();
        joined.append(&mut copy_str);
        i = i + 1;
    }
    return joined;
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List


def concatenate(strings: List[str]) -> str:
    """ Concatenate list of strings into a single string
    >>> concatenate([])
    ''
    >>> concatenate(['a', 'b', 'c'])
    'abc'
    """

*/

/*
### ENTRY POINT
concatenate
*/

/*
### CANONICAL SOLUTION
    return ''.join(strings)

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([]) == ''
    assert candidate(['x', 'y', 'z']) == 'xyz'
    assert candidate(['x', 'y', 'z', 'w', 'k']) == 'xyzwk'

*/
