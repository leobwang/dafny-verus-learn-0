// R12_HINT_SITES: [{"name":"i1"},{"name":"i2"},{"name":"a3"}]
// R12_SOURCE_SPANS: [{"symbol":"prime_length","start":29,"end":47}]
// R12 public task: humaneval-verus human_eval_082.rs (MIT (set and HumanEval prompts)); proof annotations moved into hint sites.
/*
### ID
HumanEval/82
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

pub open spec fn is_divisible(n: int, divisor: int) -> bool {
    (n % divisor) == 0
}

pub open spec fn is_prime(n: int) -> bool {
    if n < 2 {
        false
    } else {
        (forall|k: int| 2 <= k < n ==> !is_divisible(n as int, k))
    }
}

// Implementation following the ground-truth
// This function checks whether a given string length is prime
fn prime_length(str: &[char]) -> (result: bool)
    ensures
        result == is_prime(str.len() as int),
{
    if str.len() < 2 {
        return false;
    }
    for index in 2..str.len()
        invariant
            /*R12_HINT:i1*/ true,
            /*R12_HINT:i2*/ true,
    {
        if ((str.len() % index) == 0) {
            assert(/*R12_HINT:a3*/ true);
            return false;
        }
    }
    true
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT

def prime_length(string):
    """Write a function that takes a string and returns True if the string
    length is a prime number or False otherwise
    Examples
    prime_length('Hello') == True
    prime_length('abcdcba') == True
    prime_length('kittens') == True
    prime_length('orange') == False
    """

*/

/*
### ENTRY POINT
prime_length
*/

/*
### CANONICAL SOLUTION
    l = len(string)
    if l == 0 or l == 1:
        return False
    for i in range(2, l):
        if l % i == 0:
            return False
    return True

*/

/*
### TEST
def check(candidate):

    # Check some simple cases
    assert candidate('Hello') == True
    assert candidate('abcdcba') == True
    assert candidate('kittens') == True
    assert candidate('orange') == False
    assert candidate('wow') == True
    assert candidate('world') == True
    assert candidate('MadaM') == True
    assert candidate('Wow') == True
    assert candidate('') == False
    assert candidate('HI') == True
    assert candidate('go') == True
    assert candidate('gogo') == False
    assert candidate('aaaaaaaaaaaaaaa') == False

    # Check some edge cases that are easy to work out by hand.
    assert candidate('Madam') == True
    assert candidate('M') == False
    assert candidate('0') == False


*/
