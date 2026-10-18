// Reference Solution.
//! # R13 — Pipelines and trust (Reference Solution)
//!
//! Imports: the given regex spine `rg_re_a1`, `rg_re_a1b`, `rg_re_a2`; nothing else: no
//! earlier exercise file.
//!
//! Each item below comes with a fake delivery, shown and run in the chapter (§8): a
//! version of the same task that some instrument reports as fine while it is not. Run
//! its instruments and attribute it in `research/r13_forensics.md` first, then replace
//! the hole with the honest proof; the statement stays as shipped.
//!
//! Done = `scripts/vcheck --gate verus/r/r13_pipelines` prints only the summary line and
//! exits 0, `scripts/vaudit verus/r/r13_pipelines` reports no finding,
//! `scripts/specfreeze --check R13` reports none, AND
//! `scripts/firsttry.sh R13 --report --strict` exits 0.
//!
//! This file ships with exactly 4 holes: T1 (closed-book test-out) and H1–H3.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a2::char_class::CharClass;

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

// item: R13.T1v
// pair: R13.T1d
// triv: { false }
/// **T1.** (closed book) An executable matcher with the regex semantics as its contract.
///
/// Reference: an exec fn cannot call the spec `matches`; A2's `deriv_match` is the
/// executable matcher with exactly this postcondition.
pub fn accepts_r13(r: &Re, s: &Vec<char>) -> (b: bool)
    ensures
        b == matches(*r, s@),
{
    deriv_match(r, s)
}

// item: R13.H1v
// pair: R13.H1d
/// **H1.** Taking derivatives by `u + v` is taking them by `u`, then by `v`.
///
/// Reference: induction on `u.len()`. For the empty `u`, `u + v =~= v`. Otherwise the
/// first character of `u + v` is `u[0]` and the rest is `u.drop_first() + v`; with those
/// two facts stated, `derivs` unfolds once on each side and the recursive call closes it.
pub proof fn lemma_derivs_cat_r13(r: Re, u: Seq<char>, v: Seq<char>)
    ensures
        derivs(r, u + v) == derivs(derivs(r, u), v),
    decreases u.len(),
{
    if u.len() == 0 {
        assert(u + v =~= v);
    } else {
        assert((u + v)[0] == u[0]);
        assert((u + v).drop_first() =~= u.drop_first() + v);
        lemma_derivs_cat_r13(deriv(r, u[0]), u.drop_first(), v);
    }
}

// item: R13.H2v
// pair: R13.H2d
// triv: { false }
/// **H2.** Every character of `s` lies in the class `cc`: a verified loop over A2's class
/// API.
///
/// Reference: the invariant is the `forall` over the prefix read so far; a character
/// outside the class ends the loop with `false`, and its index is the witness that the
/// postcondition's `forall` fails.
pub fn class_covers_r13(cc: &CharClass, s: &Vec<char>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < s@.len() ==> cc@.contains(#[trigger] s@[i])),
{
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
}

// item: R13.H3v
// pair: R13.H3d
/// **H3.** A word matches exactly when its derivatives end in a nullable regex.
///
/// Reference: induction on `u.len()`. For the empty `u` it is `lemma_nullable_correct`.
/// Otherwise the recursive call on `(deriv(r, u[0]), u.drop_first())` and
/// `lemma_deriv_correct(r, u[0], u.drop_first())` chain, once
/// `seq![u[0]] + u.drop_first() =~= u` is stated.
pub proof fn lemma_nullable_derivs_r13(r: Re, u: Seq<char>)
    ensures
        nullable(derivs(r, u)) == matches(r, u),
    decreases u.len(),
{
    if u.len() == 0 {
        lemma_nullable_correct(r);
        assert(u =~= Seq::<char>::empty());
    } else {
        lemma_nullable_derivs_r13(deriv(r, u[0]), u.drop_first());
        lemma_deriv_correct(r, u[0], u.drop_first());
        assert(seq![u[0]] + u.drop_first() =~= u);
    }
}

} // verus!
