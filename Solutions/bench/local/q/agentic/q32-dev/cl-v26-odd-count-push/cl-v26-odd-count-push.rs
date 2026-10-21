// Topic (e) course-local task cl-v26-odd-count-push (Q32 dev stratum, course-authored 2026-10-21; QPLAN §34.4).
// Make `scripts/vcheck --gate` verify this file by adding proof to `lemma_odd_tally_push`: loop invariants,
// assertions, lemma calls, lemmas of your own. Keep every line that is there: the definitions,
// its statement, its code and its attributes.
use vstd::prelude::*;

verus! {

/// How many elements are odd.
pub open spec fn odd_tally(s: Seq<int>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        (if s[0] % 2 != 0 { 1nat } else { 0nat }) + odd_tally(s.subrange(1, s.len() as int))
    }
}

/// Given: the odd elements of a concatenation (proved).
pub proof fn lemma_odd_tally_append(a: Seq<int>, b: Seq<int>)
    ensures
        odd_tally(a + b) == odd_tally(a) + odd_tally(b),
    decreases a.len(),
{
    if a.len() == 0 {
        assert(a + b =~= b);
    } else {
        assert((a + b).subrange(1, (a + b).len() as int) =~= a.subrange(1, a.len() as int) + b);
        lemma_odd_tally_append(a.subrange(1, a.len() as int), b);
    }
}

/// Pushing x adds one exactly when x is odd.
pub proof fn lemma_odd_tally_push(s: Seq<int>, x: int)
    ensures
        odd_tally(s.push(x)) == odd_tally(s) + (if x % 2 != 0 { 1nat } else { 0nat }),
{
    assert(s.push(x) =~= s + seq![x]);
    lemma_odd_tally_append(s, seq![x]);
    assert(seq![x].subrange(1, 1) =~= Seq::<int>::empty());
    assert(odd_tally(Seq::<int>::empty()) == 0);
    assert(odd_tally(seq![x]) == (if x % 2 != 0 { 1nat } else { 0nat }) + odd_tally(seq![x].subrange(1, 1)));
}

} // verus!
