// R12_HINT_SITES: [{"name":"a1"},{"name":"i2"},{"name":"i3"},{"name":"i4"}]
// R12_SOURCE_SPANS: [{"symbol":"vowels_count","start":24,"end":64}]
// R12 public task: humaneval-verus human_eval_064.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/64
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

spec fn is_vowel(c: char) -> bool {
    c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'A' || c == 'E' || c == 'I'
        || c == 'O' || c == 'U'
}

spec fn vowels(s: Seq<char>) -> Seq<char> {
    s.filter(|c| is_vowel(c))
}

fn vowels_count(s: &str) -> (ret: u32)
    requires
        s@.len() <= u32::MAX,
    ensures
        ret == vowels(s@).len() + if (s@.len() > 0 && (s@.last() == 'y' || s@.last() == 'Y')) {
            1int  // add 1 if the last letter is 'y'

        } else {
            0int
        },
{
    let mut ctr = 0;
    let len = s.unicode_len();
    if len == 0 {
        return ctr;
    }
    assert(/*R12_HINT:a1*/ true);
    let mut i = 0;
    for i in 0..len
        invariant
            /*R12_HINT:i2*/ true,
            /*R12_HINT:i3*/ true,
            /*R12_HINT:i4*/ true,
    {
        let c = s.get_char(i);
        reveal_with_fuel(Seq::filter, 2);
        assert(s@[..i + 1].drop_last() =~= s@[..i]);
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u' || c == 'A' || c == 'E' || c
            == 'I' || c == 'O' || c == 'U') {
            ctr += 1;
        }
    }
    assert(ctr == vowels(s@).len()) by {
        assert(s@[..len] =~= s@);
    }
    let c = s.get_char(len - 1);
    if (c == 'y' || c == 'Y') {
        ctr += 1
    }
    ctr
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT

FIX = """
Add more test cases.
"""

def vowels_count(s):
    """Write a function vowels_count which takes a string representing
    a word as input and returns the number of vowels in the string.
    Vowels in this case are 'a', 'e', 'i', 'o', 'u'. Here, 'y' is also a
    vowel, but only when it is at the end of the given word.

    Example:
    >>> vowels_count("abcde")
    2
    >>> vowels_count("ACEDY")
    3
    """

*/

/*
### ENTRY POINT
vowels_count
*/

/*
### CANONICAL SOLUTION
    vowels = "aeiouAEIOU"
    n_vowels = sum(c in vowels for c in s)
    if s[-1] == 'y' or s[-1] == 'Y':
        n_vowels += 1
    return n_vowels

*/

/*
### TEST
def check(candidate):

    # Check some simple cases
    assert candidate("abcde") == 2, "Test 1"
    assert candidate("Alone") == 3, "Test 2"
    assert candidate("key") == 2, "Test 3"
    assert candidate("bye") == 1, "Test 4"
    assert candidate("keY") == 2, "Test 5"
    assert candidate("bYe") == 1, "Test 6"
    assert candidate("ACEDY") == 3, "Test 7"

    # Check some edge cases that are easy to work out by hand.
    assert True, "This prints if this assert fails 2 (also good for debugging!)"


*/
