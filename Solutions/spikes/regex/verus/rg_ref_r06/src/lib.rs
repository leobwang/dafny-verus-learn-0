//! R06 decomposer reference (R06.A1v; author notes §7.4): the top statement
//! `lemma_backwards_correct` and the reference decomposition, over layers A1 and A1b
//! (`lemma_star_one`, `lemma_star_concat`).
//!
//! Reference material (DVR0, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;

verus! {

pub proof fn lemma_backwards_str_length(s: Seq<char>)
    ensures
        backwards_str(s).len() == s.len(),
    decreases s.len(),
{
    if s.len() > 0 {
        lemma_backwards_str_length(s.subrange(1, s.len() as int));
    }
}

pub proof fn lemma_backwards_str_append(u: Seq<char>, v: Seq<char>)
    ensures
        backwards_str(u + v) == backwards_str(v) + backwards_str(u),
    decreases u.len(),
{
    let w = u + v;
    if u.len() == 0 {
        assert(w =~= v);
        assert(backwards_str(v) + backwards_str(u) =~= backwards_str(v));
    } else {
        let u1 = u.subrange(1, u.len() as int);
        assert(w.subrange(1, w.len() as int) =~= u1 + v);
        assert(w[0] == u[0]);
        lemma_backwards_str_append(u1, v);
        assert(backwards_str(w) =~= backwards_str(v) + backwards_str(u));
    }
}

pub proof fn lemma_backwards_str_involution(s: Seq<char>)
    ensures
        backwards_str(backwards_str(s)) == s,
    decreases s.len(),
{
    if s.len() > 0 {
        let t = s.subrange(1, s.len() as int);
        let h = seq![s[0]];
        lemma_backwards_str_append(backwards_str(t), h);
        assert(h.subrange(1, 1) =~= Seq::<char>::empty());
        assert(backwards_str(Seq::<char>::empty()) =~= Seq::<char>::empty());
        assert(backwards_str(h) =~= h);
        lemma_backwards_str_involution(t);
        assert(s =~= h + t);
    }
}

pub proof fn lemma_backwards_involution(r: Re)
    ensures
        backwards(backwards(r)) == r,
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            lemma_backwards_involution(*a);
            lemma_backwards_involution(*b);
        },
        Re::Cat(a, b) => {
            lemma_backwards_involution(*a);
            lemma_backwards_involution(*b);
        },
        Re::Star(a) => {
            lemma_backwards_involution(*a);
        },
        _ => {},
    }
}

pub proof fn lemma_backwards_sound(r: Re, s: Seq<char>)
    requires
        matches(r, s),
    ensures
        matches(backwards(r), backwards_str(s)),
    decreases r, s.len(),
{
    let n = s.len() as int;
    match r {
        Re::Eps => {
            assert(backwards_str(s) =~= Seq::<char>::empty());
        },
        Re::Chr(c) => {
            assert(s.subrange(1, 1) =~= Seq::<char>::empty());
            assert(backwards_str(Seq::<char>::empty()) =~= Seq::<char>::empty());
            assert(backwards_str(s) =~= seq![c]);
        },
        Re::Alt(a, b) => {
            if matches(*a, s) {
                lemma_backwards_sound(*a, s);
            } else {
                lemma_backwards_sound(*b, s);
            }
        },
        Re::Cat(a, b) => {
            let i = choose|i: int|
                0 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                    *b,
                    s.subrange(i, s.len() as int),
                );
            let p = s.subrange(0, i);
            let q = s.subrange(i, n);
            lemma_backwards_sound(*a, p);
            lemma_backwards_sound(*b, q);
            assert(s =~= p + q);
            lemma_backwards_str_append(p, q);
            let w = backwards_str(s);
            let j = backwards_str(q).len() as int;
            assert(w.subrange(0, j) =~= backwards_str(q));
            assert(w.subrange(j, w.len() as int) =~= backwards_str(p));
        },
        Re::Star(a) => {
            if s.len() == 0 {
                assert(backwards_str(s) =~= Seq::<char>::empty());
            } else {
                let i = choose|i: int|
                    1 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                        r,
                        s.subrange(i, s.len() as int),
                    );
                let p = s.subrange(0, i);
                let q = s.subrange(i, n);
                lemma_backwards_sound(*a, p);
                lemma_star_one(backwards(*a), backwards_str(p));
                lemma_backwards_sound(r, q);
                lemma_star_concat(backwards(*a), backwards_str(q), backwards_str(p));
                assert(s =~= p + q);
                lemma_backwards_str_append(p, q);
            }
        },
        Re::Empty => {},
    }
}

pub proof fn lemma_backwards_correct(r: Re, s: Seq<char>)
    ensures
        matches(backwards(r), backwards_str(s)) <==> matches(r, s),
{
    if matches(r, s) {
        lemma_backwards_sound(r, s);
    }
    if matches(backwards(r), backwards_str(s)) {
        lemma_backwards_sound(backwards(r), backwards_str(s));
        lemma_backwards_involution(r);
        lemma_backwards_str_involution(s);
    }
}

} // verus!
