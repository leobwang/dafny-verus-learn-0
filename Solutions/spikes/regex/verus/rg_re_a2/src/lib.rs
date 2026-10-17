//! Regex layer A2 (declared by R07; PLAN §2.2, §2.5 step 4): re-supplies R03's character-class
//! API (`char_class`) and R06's derivative family: `deriv`, `lemma_deriv_correct` (R06.H1v),
//! `deriv_exec`, the matcher `deriv_match` (R06.H2v) over `Vec<char>` and `matches_str` over
//! `&str`, tied to the spec. `lemma_nullable_correct` comes from A1b.
//!
//! Reference material (DVR0, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;

pub mod char_class;

verus! {

/// The derivative of `r` by `c`.
pub open spec fn deriv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv(*a, c)), Box::new(deriv(*b, c))),
        Re::Cat(a, b) => if nullable(*a) {
            Re::Alt(Box::new(Re::Cat(Box::new(deriv(*a, c)), b)), Box::new(deriv(*b, c)))
        } else {
            Re::Cat(Box::new(deriv(*a, c)), b)
        },
        Re::Star(a) => Re::Cat(Box::new(deriv(*a, c)), Box::new(Re::Star(a))),
    }
}

/// Derivative correctness: `deriv(r, c)` matches `s` iff `r` matches `c` followed by `s`.
pub proof fn lemma_deriv_correct(r: Re, c: char, s: Seq<char>)
    ensures
        matches(deriv(r, c), s) <==> matches(r, seq![c] + s),
    decreases r,
{
    let w = seq![c] + s;
    assert(w.len() == s.len() + 1);
    match r {
        Re::Chr(d) => {
            assert(w[0] == c);
        },
        Re::Alt(a, b) => {
            lemma_deriv_correct(*a, c, s);
            lemma_deriv_correct(*b, c, s);
        },
        Re::Cat(a, b) => {
            let da = deriv(*a, c);
            let cat = Re::Cat(Box::new(da), b);
            lemma_nullable_correct(*a);
            assert(w.subrange(0, 0) =~= Seq::<char>::empty());
            assert(w.subrange(0, w.len() as int) =~= w);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    0 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        *b,
                        w.subrange(i, w.len() as int),
                    );
                if i == 0 {
                    lemma_deriv_correct(*b, c, s);
                } else {
                    lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                    assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                    assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                    assert(matches(da, s.subrange(0, i - 1)));
                    assert(matches(cat, s));
                }
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(cat, s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        *b,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
            if nullable(*a) && matches(deriv(*b, c), s) {
                lemma_deriv_correct(*b, c, s);
                assert(matches(*a, w.subrange(0, 0)));
            }
        },
        Re::Star(a) => {
            let da = deriv(*a, c);
            // `r` matches `c s` ==> the derivative matches `s`
            if matches(r, w) {
                let i = choose|i: int|
                    1 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        r,
                        w.subrange(i, w.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, i - 1));
                assert(w.subrange(0, i) =~= seq![c] + s.subrange(0, i - 1));
                assert(w.subrange(i, w.len() as int) =~= s.subrange(i - 1, s.len() as int));
                assert(matches(da, s.subrange(0, i - 1)));
            }
            // the derivative matches `s` ==> `r` matches `c s`
            if matches(deriv(r, c), s) {
                let j = choose|j: int|
                    0 <= j <= s.len() && matches(da, #[trigger] s.subrange(0, j)) && matches(
                        r,
                        s.subrange(j, s.len() as int),
                    );
                lemma_deriv_correct(*a, c, s.subrange(0, j));
                assert(w.subrange(0, j + 1) =~= seq![c] + s.subrange(0, j));
                assert(w.subrange(j + 1, w.len() as int) =~= s.subrange(j, s.len() as int));
                assert(matches(*a, w.subrange(0, j + 1)));
            }
        },
        _ => {},
    }
}

/// Exec derivative, tied to the spec.
pub fn deriv_exec(r: &Re, c: char) -> (out: Re)
    ensures
        out == deriv(*r, c),
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == *d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv_exec(a, c)), Box::new(deriv_exec(b, c))),
        Re::Cat(a, b) => if is_nullable(a) {
            Re::Alt(
                Box::new(Re::Cat(Box::new(deriv_exec(a, c)), Box::new(copy_re(b)))),
                Box::new(deriv_exec(b, c)),
            )
        } else {
            Re::Cat(Box::new(deriv_exec(a, c)), Box::new(copy_re(b)))
        },
        Re::Star(a) => Re::Cat(Box::new(deriv_exec(a, c)), Box::new(Re::Star(Box::new(copy_re(a))))),
    }
}

/// The derivative matcher over a `Vec<char>`: whole-string matching.
pub fn deriv_match(r: &Re, s: &Vec<char>) -> (b: bool)
    ensures
        b == matches(*r, s@),
{
    let mut cur = copy_re(r);
    let mut i: usize = 0;
    assert(s@.subrange(0, s@.len() as int) =~= s@);
    while i < s.len()
        invariant
            i <= s.len(),
            matches(cur, s@.subrange(i as int, s@.len() as int)) == matches(*r, s@),
        decreases s.len() - i,
    {
        proof {
            lemma_deriv_correct(cur, s@[i as int], s@.subrange(i + 1, s@.len() as int));
            assert(seq![s@[i as int]] + s@.subrange(i + 1, s@.len() as int) =~= s@.subrange(
                i as int,
                s@.len() as int,
            ));
        }
        cur = deriv_exec(&cur, s[i]);
        i = i + 1;
    }
    proof {
        lemma_nullable_correct(cur);
        assert(s@.subrange(i as int, s@.len() as int) =~= Seq::<char>::empty());
    }
    is_nullable(&cur)
}

/// The derivative matcher over a `&str` (its `view` is the `Seq<char>` of its scalar values).
pub fn matches_str(r: &Re, s: &str) -> (b: bool)
    ensures
        b == matches(*r, s@),
{
    let n = s.unicode_len();
    let mut cur = copy_re(r);
    let mut i: usize = 0;
    assert(s@.subrange(0, s@.len() as int) =~= s@);
    while i < n
        invariant
            n == s@.len(),
            i <= n,
            matches(cur, s@.subrange(i as int, n as int)) == matches(*r, s@),
        decreases n - i,
    {
        let c = s.get_char(i);
        proof {
            lemma_deriv_correct(cur, c, s@.subrange(i + 1, n as int));
            assert(seq![c] + s@.subrange(i + 1, n as int) =~= s@.subrange(i as int, n as int));
        }
        cur = deriv_exec(&cur, c);
        i = i + 1;
    }
    proof {
        lemma_nullable_correct(cur);
        assert(s@.subrange(i as int, n as int) =~= Seq::<char>::empty());
    }
    is_nullable(&cur)
}

} // verus!
