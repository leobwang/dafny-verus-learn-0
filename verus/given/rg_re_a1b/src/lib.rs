//! rg_re_a1b — regex spine, layer A1b (PROVIDED, complete; frozen).
//! Do not open this crate before R02 and R05 are done: it re-supplies, complete and proved,
//! the answers to R02's holes (`lemma_nullable_correct`, `lemma_cat_eps_left`) and R05's
//! band-1 facts (`lemma_cat_assoc`, `lemma_star_one`, `lemma_star_concat`). Finish their
//! holes and record their first tries (`scripts/firsttry.sh R02 --check`,
//! `scripts/firsttry.sh R05 --check`) first.
//! Imported by R06–R16: band-1 facts re-supplied after their original exercises.
//! Use only the layer chain declared by your module; PLAN.md §2.2 and §2.4.
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;

verus! {

/// `nullable` is the empty-string case of `matches`.
pub proof fn lemma_nullable_correct(r: Re)
    ensures
        nullable(r) <==> matches(r, Seq::<char>::empty()),
    decreases r,
{
    let e = Seq::<char>::empty();
    assert(e.subrange(0, 0) =~= e);
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_correct(*a);
            lemma_nullable_correct(*b);
        },
        _ => {},
    }
}

/// `Eps` is a left unit of `Cat`.
pub proof fn lemma_cat_eps_left(r: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Eps), Box::new(r)), s) <==> matches(r, s),
{
    let e = Re::Cat(Box::new(Re::Eps), Box::new(r));
    assert(s.subrange(0, s.len() as int) =~= s);
    if matches(r, s) {
        assert(s.subrange(0, 0) =~= Seq::<char>::empty());
        assert(matches(Re::Eps, s.subrange(0, 0)));
    }
    if matches(e, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(Re::Eps, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            );
        assert(s.subrange(0, i).len() == 0);
    }
}

/// `Eps` is a right unit of `Cat`.
pub proof fn lemma_cat_eps_right(r: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(r), Box::new(Re::Eps)), s) <==> matches(r, s),
{
    let e = Re::Cat(Box::new(r), Box::new(Re::Eps));
    assert(s.subrange(0, s.len() as int) =~= s);
    if matches(r, s) {
        assert(s.subrange(s.len() as int, s.len() as int) =~= Seq::<char>::empty());
        assert(matches(r, s.subrange(0, s.len() as int)));
    }
    if matches(e, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(r, #[trigger] s.subrange(0, i)) && matches(
                Re::Eps,
                s.subrange(i, s.len() as int),
            );
        assert(s.subrange(i, s.len() as int).len() == 0);
        assert(i == s.len());
    }
}

/// Concatenation is associative on languages.
pub proof fn lemma_cat_assoc(a: Re, b: Re, c: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(Re::Cat(Box::new(a), Box::new(b))), Box::new(c)), s)
            <==> matches(Re::Cat(Box::new(a), Box::new(Re::Cat(Box::new(b), Box::new(c)))), s),
{
    let ab = Re::Cat(Box::new(a), Box::new(b));
    let bc = Re::Cat(Box::new(b), Box::new(c));
    if matches(Re::Cat(Box::new(ab), Box::new(c)), s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(ab, #[trigger] s.subrange(0, i)) && matches(
                c,
                s.subrange(i, s.len() as int),
            );
        let u = s.subrange(0, i);
        let k = choose|k: int|
            0 <= k <= u.len() && matches(a, #[trigger] u.subrange(0, k)) && matches(
                b,
                u.subrange(k, u.len() as int),
            );
        let v = s.subrange(k, s.len() as int);
        assert(u.subrange(0, k) =~= s.subrange(0, k));
        assert(u.subrange(k, u.len() as int) =~= v.subrange(0, i - k));
        assert(v.subrange(i - k, v.len() as int) =~= s.subrange(i, s.len() as int));
        assert(matches(bc, v));
    }
    if matches(Re::Cat(Box::new(a), Box::new(bc)), s) {
        let k = choose|k: int|
            0 <= k <= s.len() && matches(a, #[trigger] s.subrange(0, k)) && matches(
                bc,
                s.subrange(k, s.len() as int),
            );
        let v = s.subrange(k, s.len() as int);
        let j = choose|j: int|
            0 <= j <= v.len() && matches(b, #[trigger] v.subrange(0, j)) && matches(
                c,
                v.subrange(j, v.len() as int),
            );
        let u = s.subrange(0, k + j);
        assert(u.subrange(0, k) =~= s.subrange(0, k));
        assert(u.subrange(k, u.len() as int) =~= v.subrange(0, j));
        assert(v.subrange(j, v.len() as int) =~= s.subrange(k + j, s.len() as int));
        assert(matches(ab, u));
    }
}

/// One word of `a` is a word of `a*`.
pub proof fn lemma_star_one(a: Re, u: Seq<char>)
    requires
        matches(a, u),
    ensures
        matches(Re::Star(Box::new(a)), u),
{
    if u.len() > 0 {
        assert(u.subrange(0, u.len() as int) =~= u);
        assert(u.subrange(u.len() as int, u.len() as int) =~= Seq::<char>::empty());
        assert(matches(Re::Star(Box::new(a)), Seq::<char>::empty()));
    }
}

/// `Star` absorbs the concatenation of two of its words.
pub proof fn lemma_star_concat(a: Re, u: Seq<char>, v: Seq<char>)
    requires
        matches(Re::Star(Box::new(a)), u),
        matches(Re::Star(Box::new(a)), v),
    ensures
        matches(Re::Star(Box::new(a)), u + v),
    decreases u.len(),
{
    let st = Re::Star(Box::new(a));
    let t = u + v;
    if u.len() == 0 {
        assert(t =~= v);
    } else {
        let i = choose|i: int|
            1 <= i <= u.len() && matches(a, #[trigger] u.subrange(0, i)) && matches(
                st,
                u.subrange(i, u.len() as int),
            );
        lemma_star_concat(a, u.subrange(i, u.len() as int), v);
        assert(t.subrange(0, i) =~= u.subrange(0, i));
        assert(t.subrange(i, t.len() as int) =~= u.subrange(i, u.len() as int) + v);
    }
}

} // verus!
