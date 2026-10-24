// Topic (e) Q33 dev pair pv-v110-q33d (public; QPLAN §35.4, Δ416): humaneval-verus
// `human_eval_031.rs` at bbe93f7 (MIT; HumanEval/31), its specification, its proofs and the
// definitions only its specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `is_prime_impl`'s `requires` and `ensures` from its prose (the PROMPT comment below),
// with any definition they need, and one call whose `requires` hold in `is_prime_impl_witness`.
// You may add proof annotations; never change its executable code, and keep every other line.
/*
### ID
HumanEval/31
*/
/*
### VERUS BEGIN
*/
use vstd::prelude::*;

verus! {

// Verus does not yet support quantifiers when using proof-by-compute
// proof fn sanity_check() {
//     assert(is_prime(6) == false) by (compute);
//     assert(is_prime(101) == true) by (compute);
//     assert(is_prime(11) == true) by (compute);
//     assert(is_prime(13441) == true) by (compute);
//     assert(is_prime(61) == true) by (compute);
//     assert(is_prime(4) == false) by (compute);
//     assert(is_prime(1) == false) by (compute);
// }
// implementation
fn is_prime_impl(n: u8) -> (res: bool)
{
    if n < 2 {
        return false;
    }
    let mut k = 2;
    let mut res = true;

    while (k < n)
        decreases n - k,
    {

        res = res && n % k != 0;
        k = k + 1;
    }
    return res;
}

/// A non-vacuity witness for `is_prime_impl`: one call whose `requires` hold.
fn is_prime_impl_witness() {
}

} // verus!

/*
### VERUS END
*/

/*
### PROMPT


def is_prime(n):
    """Return true if a given number is prime, and false otherwise.
    >>> is_prime(6)
    False
    >>> is_prime(101)
    True
    >>> is_prime(11)
    True
    >>> is_prime(13441)
    True
    >>> is_prime(61)
    True
    >>> is_prime(4)
    False
    >>> is_prime(1)
    False
    """

*/

/*
### ENTRY POINT
is_prime
*/

/*
### CANONICAL SOLUTION
    if n < 2:
        return False
    for k in range(2, n - 1):
        if n % k == 0:
            return False
    return True

*/

/*
### TEST


METADATA = {}


def check(candidate):
    assert candidate(6) == False
    assert candidate(101) == True
    assert candidate(11) == True
    assert candidate(13441) == True
    assert candidate(61) == True
    assert candidate(4) == False
    assert candidate(1) == False
    assert candidate(5) == True
    assert candidate(11) == True
    assert candidate(17) == True
    assert candidate(5 * 17) == False
    assert candidate(11 * 7) == False
    assert candidate(13441 * 19) == False


*/
