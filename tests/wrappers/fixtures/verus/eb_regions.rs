//! Test fixture (tests/wrappers): the region mode RGN of the empty-body gate
//! (QPLAN §6 Q18). Each item's learner lines sit between `@hole-begin` and
//! `@hole-end` markers, as in a reference twin. Invented functions; none is a
//! course item.
use vstd::prelude::*;

verus! {

// item: Q09.H4v S3
pub fn count_to(n: u64) -> (r: u64)
    ensures
        r == n,
{
    let mut i: u64 = 0;
    let mut r: u64 = 0;
    while i < n
        invariant
            r == i,
            // @hole-begin Q09.H4v
            i <= n,
            // @hole-end Q09.H4v
        decreases n - i,
    {
        i = i + 1;
        r = r + 1;
    }
    r
}

// item: Q09.H6v S3
pub fn walk_to(m: u64) -> (r: u64)
    ensures
        r == m,
{
    let mut k: u64 = 0;
    while k < m
        invariant
            // @hole-begin Q09.H6v
            k <= m,
            // @hole-end Q09.H6v
        decreases m - k,
    {
        k = k + 1;
    }
    k
}

// item: Q09.H5v S3
pub proof fn lemma_double(n: nat)
    ensures
        n + n == 2 * n,
{
    // @hole-begin Q09.H5v
    assert(n + n == 2 * n);
    // @hole-end Q09.H5v
}

} // verus!
