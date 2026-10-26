// Reference Solution.
//! # R13 — Pipelines and trust (Exercises)
//!
//! Standalone R track. Import only the frozen layers A1 to A4; no earlier learner file is
//! needed. The paired exercise is dafny/R/R13_Pipelines/std/R13_Pipelines.dfy.
//!
//! Record the six predictions first (scripts/firsttry.sh R13 --check), then attempt T1
//! closed book. Four typed holes ship in this crate.
//!
//! Each item comes with a fake delivery, shown and run in the chapter (§8): a version of
//! the same task that some instrument reports as fine while it is not. Run its
//! instruments and attribute it in research/r13_forensics.md first, then replace the hole
//! with the honest proof; the statement stays as shipped.
//!
//! File order: the test-out (T1), then H1 (derivatives of a concatenation), H2 (a class
//! loop) and H3 (nullable derivatives), and a given compiled use-site test of T1 and H2.
//!
//! Done: scripts/vcheck --gate verus/r/r13_pipelines exits 0 with zero holes,
//! scripts/vaudit verus/r/r13_pipelines reports no finding, scripts/specfreeze --check R13
//! reports none, and scripts/firsttry.sh R13 --report --strict exits 0.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a2::char_class::CharClass;

// =============================================================================
// Test-out (closed book)
// =============================================================================

verus! {

// item: R13.T1v
// pair: R13.T1d
// triv: { false }
/// **T1.** Closed book: an executable matcher with the regex semantics as its contract.
/// `matches` is a spec fn: what may an exec fn call instead, and which layer supplies an
/// executable matcher with this postcondition?
pub fn accepts_r13(r: &Re, s: &Vec<char>) -> (b: bool)
    ensures
        b == matches(*r, s@),
{
    // ref-begin R13.T1v
    deriv_match(r, s)
    // ref-end R13.T1v
}
// Hint(1): the chapter's fake delivery for T1 (§8) shows the call that is refused, and the stage that refuses it.
// Hint(2): A2 re-supplies the derivative matcher.
// Reference checks (enabled):
// reference-only: enabled shipped check
fn accepts_check_r13() {
    let mut s: Vec<char> = Vec::new();
    s.push('a');
    let b = accepts_r13(&Re::Chr('a'), &s);
    assert(s@ =~= seq!['a']);
    assert(b);
}
// end reference checks

} // verus!

// =============================================================================
// The repairs
// =============================================================================

verus! {

/// Given: the derivative by every character of `u`, in order.
pub open spec fn derivs(r: Re, u: Seq<char>) -> Re
    decreases u.len(),
{
    if u.len() == 0 {
        r
    } else {
        derivs(deriv(r, u[0]), u.drop_first())
    }
}

// item: R13.H1v
// pair: R13.H1d
/// **H1.** Taking derivatives by `u + v` is taking them by `u`, then by `v`. The fake
/// delivery trusts an `external_body` proof fn. What are the first character and the
/// rest of `u + v` when `u` is not empty, and which call is the induction hypothesis?
pub proof fn lemma_derivs_cat_r13(r: Re, u: Seq<char>, v: Seq<char>)
    ensures
        derivs(r, u + v) == derivs(derivs(r, u), v),
    decreases u.len(),
{
    // @hole-begin R13.H1v
    if u.len() == 0 {
        assert(u + v =~= v);
    } else {
        assert((u + v)[0] == u[0]);
        assert((u + v).drop_first() =~= u.drop_first() + v);
        lemma_derivs_cat_r13(deriv(r, u[0]), u.drop_first(), v);
    }
    // @hole-end R13.H1v
}
// Hint(1): induction on u.len() with a recursive call; the base case needs `u + v =~= v`.
// Hint(2): state what `(u + v)[0]` and `(u + v).drop_first()` are, then recurse on the derivative by u[0].

// item: R13.H2v
// pair: R13.H2d
// triv: { false }
/// **H2.** Every character of `s` lies in the class `cc`: a verified loop over A2's class
/// API, where the fake delivery trusts an `external_body` helper. What does the loop know
/// about the prefix it has read, and what ends it early?
pub fn class_covers_r13(cc: &CharClass, s: &Vec<char>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < s@.len() ==> cc@.contains(#[trigger] s@[i])),
{
    // ref-begin R13.H2v
    let mut k: usize = 0;
    while k < s.len()
        invariant
            k <= s.len(),
            forall|i: int| 0 <= i < k ==> cc@.contains(#[trigger] s@[i]),
        decreases s.len() - k,
    {
        if !cc.class_member(s[k]) {
            return false;
        }
        k = k + 1;
    }
    true
    // ref-end R13.H2v
}
// Hint(1): a `while` loop over k with an invariant about the indices below k.
// Hint(2): `cc.class_member(c)` is executable and promises `cc@.contains(c)`.

// item: R13.H3v
// pair: R13.H3d
/// **H3.** A word matches exactly when its derivatives end in a nullable regex. The fake
/// delivery proves it only for the empty word. Which A1b fact is the base case, and which
/// A2 fact moves one character from the word into the regex?
pub proof fn lemma_nullable_derivs_r13(r: Re, u: Seq<char>)
    ensures
        nullable(derivs(r, u)) == matches(r, u),
    decreases u.len(),
{
    // @hole-begin R13.H3v
    if u.len() == 0 {
        lemma_nullable_correct(r);
        assert(u =~= Seq::<char>::empty());
    } else {
        lemma_nullable_derivs_r13(deriv(r, u[0]), u.drop_first());
        lemma_deriv_correct(r, u[0], u.drop_first());
        assert(seq![u[0]] + u.drop_first() =~= u);
    }
    // @hole-end R13.H3v
}
// Hint(1): induction on u.len(); the base case is A1b's `lemma_nullable_correct`.
// Hint(2): A2's `lemma_deriv_correct` on (r, u[0], u.drop_first()), and the word rebuilt from its first character and the rest.

} // verus!

// Given (not an item): the compiled use-site check of T1 and H2. It runs your bodies;
// `scripts/vcheck --test` executes it once they are done.
#[test]
fn repair_sample_test() {
    let ab = Re::Cat(Box::new(Re::Chr('a')), Box::new(Re::Star(Box::new(Re::Chr('b')))));
    assert!(accepts_r13(&ab, &vec!['a', 'b', 'b']));
    assert!(!accepts_r13(&ab, &vec!['b']));
    let af = CharClass::class_range('a', 'f');
    assert!(class_covers_r13(&af, &vec!['c', 'a', 'f']));
    assert!(!class_covers_r13(&af, &vec!['c', 'z']));
}
