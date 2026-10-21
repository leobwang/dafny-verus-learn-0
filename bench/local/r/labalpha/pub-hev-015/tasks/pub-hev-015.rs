// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"a3"}]
// R12_SOURCE_SPANS: [{"symbol":"flip_case","start":43,"end":66}]
// R12 public task: humaneval-verus human_eval_027.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/27
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

pub open spec fn is_upper_case(c: char) -> bool {
    c >= 'A' && c <= 'Z'
}

pub open spec fn is_lower_case(c: char) -> bool {
    c >= 'a' && c <= 'z'
}

pub open spec fn shift_plus_32_spec(c: char) -> char {
    ((c as u8) + 32) as char
}

pub open spec fn shift_minus_32_spec(c: char) -> char {
    ((c as u8) - 32) as char
}

// This spec function tranforms a lowercase character to uppercase and vice-versa
pub open spec fn flip_case_spec(c: char) -> char {
    if is_lower_case(c) {
        shift_minus_32_spec(c)
    } else if is_upper_case(c) {
        shift_plus_32_spec(c)
    } else {
        c
    }
}

// Implementation following the ground-truth (i.e, swapcase())
fn flip_case(str: &[char]) -> (flipped_case: Vec<char>)
    ensures
        str@.len() == flipped_case@.len(),
        forall|i: int| 0 <= i < str.len() ==> flipped_case[i] == flip_case_spec(#[trigger] str[i]),
{
    let mut flipped_case = Vec::with_capacity(str.len());

    for index in 0..str.len()
        invariant
            /*R12_HINT:i1*/ true,
            /*R12_HINT:i2*/ true,
            forall|i: int| 0 <= i < index ==> flipped_case[i] == flip_case_spec(#[trigger] str[i]),
    {
        if (str[index] >= 'a' && str[index] <= 'z') {
            flipped_case.push(((str[index] as u8) - 32) as char);
        } else if (str[index] >= 'A' && str[index] <= 'Z') {
            flipped_case.push(((str[index] as u8) + 32) as char);
        } else {
            flipped_case.push(str[index]);
        }
        assert(/*R12_HINT:a3*/ true);
    }
    flipped_case
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def flip_case(string: str) -> str:
    """ For a given string, flip lowercase characters to uppercase and uppercase to lowercase.
    >>> flip_case('Hello')
    'hELLO'
    """

*/

/*
### ENTRY POINT
flip_case
*/

/*
### CANONICAL SOLUTION
    return string.swapcase()

*/

/*
### TEST


METADATA = {
    'author': 'jt',
    'dataset': 'test'
}


def check(candidate):
    assert candidate('') == ''
    assert candidate('Hello!') == 'hELLO!'
    assert candidate('These violent delights have violent ends') == 'tHESE VIOLENT DELIGHTS HAVE VIOLENT ENDS'

*/
