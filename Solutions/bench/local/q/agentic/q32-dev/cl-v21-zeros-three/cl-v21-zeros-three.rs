// Topic (e) course-local task cl-v21-zeros-three (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `lemma_null_count_three`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

/// How many elements are zero.
pub open spec fn null_count(s: Seq<int>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        (if s[0] == 0 { 1nat } else { 0nat }) + null_count(s.subrange(1, s.len() as int))
    }
}

/// Given: the zeros of a concatenation (proved).
pub proof fn lemma_null_count_append(a: Seq<int>, b: Seq<int>)
    ensures
        null_count(a + b) == null_count(a) + null_count(b),
    decreases a.len(),
{
    if a.len() == 0 {
        assert(a + b =~= b);
    } else {
        assert((a + b).subrange(1, (a + b).len() as int) =~= a.subrange(1, a.len() as int) + b);
        lemma_null_count_append(a.subrange(1, a.len() as int), b);
    }
}

/// The zeros of three pieces.
pub proof fn lemma_null_count_three(a: Seq<int>, b: Seq<int>, c: Seq<int>)
    ensures
        null_count(a + b + c) == null_count(a) + null_count(b) + null_count(c),
{
    lemma_null_count_append(a + b, c);
    lemma_null_count_append(a, b);
}

} // verus!
