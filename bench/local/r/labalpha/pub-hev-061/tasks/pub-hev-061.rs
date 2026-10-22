// R12_HINT_SITES: [{"name":"i1"},{"name":"a2"},{"name":"a3"},{"name":"i4"},{"name":"i5"},{"name":"i6"},{"name":"i7"},{"name":"i8"},{"name":"a9"},{"name":"a10"},{"name":"a11"},{"name":"a12"},{"name":"a13"},{"name":"a14"}]
// R12_SOURCE_SPANS: [{"symbol":"filter_by_prefix","start":19,"end":66}]
// R12 public task: humaneval-verus human_eval_029.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/29
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

spec fn to_seq(s: Vec<Vec<char>>) -> Seq<Seq<char>> {
    s@.map_values(|v: Vec<char>| v@)
}

fn filter_by_prefix(strings: Vec<Vec<char>>, prefix: Vec<char>) -> (res: Vec<Vec<char>>)
    ensures
        to_seq(res) == to_seq(strings).filter(|s: Seq<char>| prefix@.is_prefix_of(s)),
{
    let mut result = Vec::new();
    for i in 0..strings.len()
        invariant
            /*R12_HINT:i1*/ true,
    {
        assert(/*R12_HINT:a2*/ true);
        proof {
            to_seq(strings)[..i].lemma_filter_push(
                strings[i as int]@,
                |s: Seq<char>| prefix@.is_prefix_of(s),
            );
        }
        if strings[i].len() >= prefix.len() {
            let mut flag = true;
            assert(/*R12_HINT:a3*/ true);
            for j in 0..prefix.len()
                invariant
                    /*R12_HINT:i4*/ true,
                    /*R12_HINT:i5*/ true,
                    /*R12_HINT:i6*/ true,
                    /*R12_HINT:i7*/ true,
                    /*R12_HINT:i8*/ true,
            {
                if strings[i][j] != prefix[j] {
                    flag = false;
                    assert(/*R12_HINT:a9*/ true);
                } else {
                    if (flag) {
                        assert(/*R12_HINT:a10*/ true);
                    } else {
                        assert(/*R12_HINT:a11*/ true);
                        assert(/*R12_HINT:a12*/ true);
                    }
                }
            }
            assert(/*R12_HINT:a13*/ true);
            if flag {
                result.push(strings[i].clone());
            }
        }
    }
    assert(/*R12_HINT:a14*/ true);
    result
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT
from typing import List


def filter_by_prefix(strings: List[str], prefix: str) -> List[str]:
    """ Filter an input list of strings only for ones that start with a given prefix.
    >>> filter_by_prefix([], 'a')
    []
    >>> filter_by_prefix(['abc', 'bcd', 'cde', 'array'], 'a')
    ['abc', 'array']
    """

*/

/*
### ENTRY POINT
filter_by_prefix
*/

/*
### CANONICAL SOLUTION
    return [x for x in strings if x.startswith(prefix)]

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate([], 'john') == []
    assert candidate(['xxx', 'asd', 'xxy', 'john doe', 'xxxAAA', 'xxx'], 'xxx') == ['xxx', 'xxxAAA', 'xxx']

*/
