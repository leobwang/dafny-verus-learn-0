//! Regex spike, layer A4 (R10, R11): `NormRe` smart constructors and normal forms behind a
//! `type_invariant`, the normalizing derivative and its matcher; `Derivation` trees, their
//! soundness and completeness, the verified certificate checker and a certifying matcher.
//!
//! `lemma_star_concat` moved to A1b (PLAN §2.5 step 3).
//!
//! Reference material (DVR0, author-only).
#![allow(unused_imports)]
use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a2::*;
use rg_re_a3::*;

verus! {

// ---------------------------------------------------------------------------------------------
// Language lemmas used below
// ---------------------------------------------------------------------------------------------

/// Two regexes with the same language.
pub open spec fn equiv(a: Re, b: Re) -> bool {
    forall|s: Seq<char>| #[trigger] matches(a, s) == matches(b, s)
}

/// `(x*)* = x*`.
pub proof fn lemma_star_star(x: Re, s: Seq<char>)
    ensures
        matches(Re::Star(Box::new(Re::Star(Box::new(x)))), s) == matches(Re::Star(Box::new(x)), s),
    decreases s.len(),
{
    let st = Re::Star(Box::new(x));
    let stst = Re::Star(Box::new(st));
    assert(s.subrange(0, s.len() as int) =~= s);
    assert(s.subrange(s.len() as int, s.len() as int) =~= Seq::<char>::empty());
    if s.len() > 0 {
        if matches(st, s) {
            assert(matches(st, s.subrange(0, s.len() as int)));
            assert(matches(stst, s.subrange(s.len() as int, s.len() as int)));
        }
        if matches(stst, s) {
            let i = choose|i: int|
                1 <= i <= s.len() && matches(st, #[trigger] s.subrange(0, i)) && matches(
                    stst,
                    s.subrange(i, s.len() as int),
                );
            lemma_star_star(x, s.subrange(i, s.len() as int));
            lemma_star_concat(x, s.subrange(0, i), s.subrange(i, s.len() as int));
            assert(s.subrange(0, i) + s.subrange(i, s.len() as int) =~= s);
        }
    }
}

/// `Cat` respects language equivalence.
pub proof fn lemma_cat_cong(a1: Re, a2: Re, b1: Re, b2: Re, s: Seq<char>)
    requires
        equiv(a1, a2),
        equiv(b1, b2),
    ensures
        matches(Re::Cat(Box::new(a1), Box::new(b1)), s) == matches(Re::Cat(Box::new(a2), Box::new(b2)), s),
{
    if matches(Re::Cat(Box::new(a1), Box::new(b1)), s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(a1, #[trigger] s.subrange(0, i)) && matches(
                b1,
                s.subrange(i, s.len() as int),
            );
        assert(matches(a2, s.subrange(0, i)) && matches(b2, s.subrange(i, s.len() as int)));
    }
    if matches(Re::Cat(Box::new(a2), Box::new(b2)), s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(a2, #[trigger] s.subrange(0, i)) && matches(
                b2,
                s.subrange(i, s.len() as int),
            );
        assert(matches(a1, s.subrange(0, i)) && matches(b1, s.subrange(i, s.len() as int)));
    }
}

// ---------------------------------------------------------------------------------------------
// Smart constructors and normal forms
// ---------------------------------------------------------------------------------------------

pub open spec fn mk_alt(a: Re, b: Re) -> Re {
    if a is Empty {
        b
    } else if b is Empty {
        a
    } else if a == b {
        a
    } else {
        Re::Alt(Box::new(a), Box::new(b))
    }
}

pub open spec fn mk_cat(a: Re, b: Re) -> Re {
    if a is Empty || b is Empty {
        Re::Empty
    } else if a is Eps {
        b
    } else if b is Eps {
        a
    } else {
        Re::Cat(Box::new(a), Box::new(b))
    }
}

pub open spec fn mk_star(a: Re) -> Re {
    if a is Empty || a is Eps {
        Re::Eps
    } else if a is Star {
        a
    } else {
        Re::Star(Box::new(a))
    }
}

/// The normal form the smart constructors maintain.
pub open spec fn is_norm(r: Re) -> bool
    decreases r,
{
    match r {
        Re::Alt(a, b) => !(*a is Empty) && !(*b is Empty) && *a != *b && is_norm(*a) && is_norm(*b),
        Re::Cat(a, b) => !(*a is Empty) && !(*b is Empty) && !(*a is Eps) && !(*b is Eps) && is_norm(
            *a,
        ) && is_norm(*b),
        Re::Star(a) => !(*a is Empty) && !(*a is Eps) && !(*a is Star) && is_norm(*a),
        _ => true,
    }
}

pub proof fn lemma_mk_alt(a: Re, b: Re, s: Seq<char>)
    ensures
        matches(mk_alt(a, b), s) == matches(Re::Alt(Box::new(a), Box::new(b)), s),
        is_norm(a) && is_norm(b) ==> is_norm(mk_alt(a, b)),
{
    assert(!matches(Re::Empty, s));
}

pub proof fn lemma_mk_cat(a: Re, b: Re, s: Seq<char>)
    ensures
        matches(mk_cat(a, b), s) == matches(Re::Cat(Box::new(a), Box::new(b)), s),
        is_norm(a) && is_norm(b) ==> is_norm(mk_cat(a, b)),
{
    let cat = Re::Cat(Box::new(a), Box::new(b));
    assert(s.subrange(0, 0) =~= Seq::<char>::empty());
    assert(s.subrange(0, s.len() as int) =~= s);
    assert(s.subrange(s.len() as int, s.len() as int) =~= Seq::<char>::empty());
    if matches(cat, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(a, #[trigger] s.subrange(0, i)) && matches(
                b,
                s.subrange(i, s.len() as int),
            );
        if a is Eps {
            assert(i == 0);
        } else if b is Eps {
            assert(i == s.len());
        }
    }
    if a is Eps && !(b is Empty) && matches(b, s) {
        assert(matches(a, s.subrange(0, 0)));
    }
    if b is Eps && !(a is Empty) && !(a is Eps) && matches(a, s) {
        assert(matches(a, s.subrange(0, s.len() as int)));
    }
}

pub proof fn lemma_mk_star(a: Re, s: Seq<char>)
    ensures
        matches(mk_star(a), s) == matches(Re::Star(Box::new(a)), s),
        is_norm(a) ==> is_norm(mk_star(a)),
{
    if a is Empty || a is Eps {
        if s.len() > 0 && matches(Re::Star(Box::new(a)), s) {
            let i = choose|i: int|
                1 <= i <= s.len() && matches(a, #[trigger] s.subrange(0, i)) && matches(
                    Re::Star(Box::new(a)),
                    s.subrange(i, s.len() as int),
                );
            assert(matches(a, s.subrange(0, i)));
        }
    } else if a is Star {
        lemma_star_star(*a->Star_0, s);
    }
}

/// Exec structural equality.
pub fn eq_re(a: &Re, b: &Re) -> (e: bool)
    ensures
        e == (*a == *b),
    decreases a,
{
    match (a, b) {
        (Re::Empty, Re::Empty) => true,
        (Re::Eps, Re::Eps) => true,
        (Re::Chr(c), Re::Chr(d)) => *c == *d,
        (Re::Alt(a1, a2), Re::Alt(b1, b2)) => eq_re(a1, b1) && eq_re(a2, b2),
        (Re::Cat(a1, a2), Re::Cat(b1, b2)) => eq_re(a1, b1) && eq_re(a2, b2),
        (Re::Star(a1), Re::Star(b1)) => eq_re(a1, b1),
        _ => false,
    }
}

pub fn mk_alt_exec(a: Re, b: Re) -> (out: Re)
    ensures
        out == mk_alt(a, b),
{
    if let Re::Empty = a {
        b
    } else if let Re::Empty = b {
        a
    } else if eq_re(&a, &b) {
        a
    } else {
        Re::Alt(Box::new(a), Box::new(b))
    }
}

pub fn mk_cat_exec(a: Re, b: Re) -> (out: Re)
    ensures
        out == mk_cat(a, b),
{
    if let Re::Empty = a {
        Re::Empty
    } else if let Re::Empty = b {
        Re::Empty
    } else if let Re::Eps = a {
        b
    } else if let Re::Eps = b {
        a
    } else {
        Re::Cat(Box::new(a), Box::new(b))
    }
}

pub fn mk_star_exec(a: Re) -> (out: Re)
    ensures
        out == mk_star(a),
{
    match a {
        Re::Empty => Re::Eps,
        Re::Eps => Re::Eps,
        Re::Star(x) => Re::Star(x),
        _ => Re::Star(Box::new(a)),
    }
}

/// The normalizing derivative.
pub open spec fn nderiv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => mk_alt(nderiv(*a, c), nderiv(*b, c)),
        Re::Cat(a, b) => if nullable(*a) {
            mk_alt(mk_cat(nderiv(*a, c), *b), nderiv(*b, c))
        } else {
            mk_cat(nderiv(*a, c), *b)
        },
        Re::Star(a) => mk_cat(nderiv(*a, c), r),
    }
}

/// The normalizing derivative has the derivative's language and keeps normal forms.
pub proof fn lemma_nderiv(r: Re, c: char)
    ensures
        equiv(nderiv(r, c), deriv(r, c)),
        is_norm(r) ==> is_norm(nderiv(r, c)),
    decreases r,
{
    match r {
        Re::Alt(a, b) => {
            lemma_nderiv(*a, c);
            lemma_nderiv(*b, c);
            assert forall|s: Seq<char>| #[trigger] matches(nderiv(r, c), s) == matches(deriv(r, c), s) by {
                lemma_mk_alt(nderiv(*a, c), nderiv(*b, c), s);
                assert(matches(nderiv(*a, c), s) == matches(deriv(*a, c), s));
                assert(matches(nderiv(*b, c), s) == matches(deriv(*b, c), s));
            }
            lemma_mk_alt(nderiv(*a, c), nderiv(*b, c), Seq::empty());
        },
        Re::Cat(a, b) => {
            lemma_nderiv(*a, c);
            lemma_nderiv(*b, c);
            let na = nderiv(*a, c);
            let da = deriv(*a, c);
            assert(equiv(*b, *b));
            assert forall|s: Seq<char>| #[trigger] matches(nderiv(r, c), s) == matches(deriv(r, c), s) by {
                lemma_mk_cat(na, *b, s);
                lemma_cat_cong(na, da, *b, *b, s);
                lemma_mk_alt(mk_cat(na, *b), nderiv(*b, c), s);
                assert(matches(nderiv(*b, c), s) == matches(deriv(*b, c), s));
            }
            lemma_mk_cat(na, *b, Seq::empty());
            lemma_mk_alt(mk_cat(na, *b), nderiv(*b, c), Seq::empty());
        },
        Re::Star(a) => {
            lemma_nderiv(*a, c);
            let na = nderiv(*a, c);
            let da = deriv(*a, c);
            assert(equiv(r, r));
            assert forall|s: Seq<char>| #[trigger] matches(nderiv(r, c), s) == matches(deriv(r, c), s) by {
                lemma_mk_cat(na, r, s);
                lemma_cat_cong(na, da, r, r, s);
            }
            lemma_mk_cat(na, r, Seq::empty());
        },
        _ => {},
    }
}

pub fn nderiv_exec(r: &Re, c: char) -> (out: Re)
    ensures
        out == nderiv(*r, c),
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == *d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => mk_alt_exec(nderiv_exec(a, c), nderiv_exec(b, c)),
        Re::Cat(a, b) => if is_nullable(a) {
            mk_alt_exec(mk_cat_exec(nderiv_exec(a, c), copy_re(b)), nderiv_exec(b, c))
        } else {
            mk_cat_exec(nderiv_exec(a, c), copy_re(b))
        },
        Re::Star(a) => mk_cat_exec(nderiv_exec(a, c), copy_re(r)),
    }
}

/// A regex in normal form; the invariant lives in the type.
pub struct NormRe {
    r: Re,
}

impl NormRe {
    #[verifier::type_invariant]
    spec fn wf(self) -> bool {
        is_norm(self.r)
    }

    pub closed spec fn re(self) -> Re {
        self.r
    }

    /// Borrow the regex; the type invariant comes with it.
    pub fn as_re(&self) -> (r: &Re)
        ensures
            *r == self.re(),
            is_norm(*r),
    {
        proof {
            use_type_invariant(self);
        }
        &self.r
    }

    pub fn empty() -> (out: NormRe)
        ensures
            out.re() == Re::Empty,
    {
        NormRe { r: Re::Empty }
    }

    pub fn eps() -> (out: NormRe)
        ensures
            out.re() == Re::Eps,
    {
        NormRe { r: Re::Eps }
    }

    pub fn chr(c: char) -> (out: NormRe)
        ensures
            out.re() == Re::Chr(c),
    {
        NormRe { r: Re::Chr(c) }
    }

    pub fn alt(a: NormRe, b: NormRe) -> (out: NormRe)
        ensures
            forall|s: Seq<char>| #[trigger] matches(out.re(), s) == matches(Re::Alt(Box::new(a.re()), Box::new(b.re())), s),
    {
        proof {
            use_type_invariant(&a);
            use_type_invariant(&b);
            lemma_mk_alt(a.r, b.r, Seq::empty());
            assert forall|s: Seq<char>| #[trigger] matches(mk_alt(a.r, b.r), s) == matches(Re::Alt(Box::new(a.r), Box::new(b.r)), s) by {
                lemma_mk_alt(a.r, b.r, s);
            }
        }
        NormRe { r: mk_alt_exec(a.r, b.r) }
    }

    pub fn cat(a: NormRe, b: NormRe) -> (out: NormRe)
        ensures
            forall|s: Seq<char>| #[trigger] matches(out.re(), s) == matches(Re::Cat(Box::new(a.re()), Box::new(b.re())), s),
    {
        proof {
            use_type_invariant(&a);
            use_type_invariant(&b);
            lemma_mk_cat(a.r, b.r, Seq::empty());
            assert forall|s: Seq<char>| #[trigger] matches(mk_cat(a.r, b.r), s) == matches(Re::Cat(Box::new(a.r), Box::new(b.r)), s) by {
                lemma_mk_cat(a.r, b.r, s);
            }
        }
        NormRe { r: mk_cat_exec(a.r, b.r) }
    }

    pub fn star(a: NormRe) -> (out: NormRe)
        ensures
            forall|s: Seq<char>| #[trigger] matches(out.re(), s) == matches(Re::Star(Box::new(a.re())), s),
    {
        proof {
            use_type_invariant(&a);
            lemma_mk_star(a.r, Seq::empty());
            assert forall|s: Seq<char>| #[trigger] matches(mk_star(a.r), s) == matches(Re::Star(Box::new(a.r)), s) by {
                lemma_mk_star(a.r, s);
            }
        }
        NormRe { r: mk_star_exec(a.r) }
    }

    /// The normalizing derivative stays in normal form.
    pub fn deriv(&self, c: char) -> (out: NormRe)
        ensures
            forall|s: Seq<char>| #[trigger] matches(out.re(), s) == matches(self.re(), seq![c] + s),
    {
        proof {
            use_type_invariant(self);
            lemma_nderiv(self.r, c);
            assert forall|s: Seq<char>| #[trigger] matches(nderiv(self.r, c), s) == matches(self.r, seq![c] + s) by {
                lemma_deriv_correct(self.r, c, s);
            }
        }
        NormRe { r: nderiv_exec(&self.r, c) }
    }

    pub fn is_nullable(&self) -> (b: bool)
        ensures
            b == matches(self.re(), Seq::<char>::empty()),
    {
        proof {
            lemma_nullable_correct(self.r);
        }
        rg_re_a1::is_nullable(&self.r)
    }
}

/// The normalizing derivative matcher.
pub fn matches_norm(r: NormRe, s: &Vec<char>) -> (b: bool)
    ensures
        b == matches(r.re(), s@),
{
    let ghost r0 = r.re();
    let mut cur = r;
    let mut i: usize = 0;
    assert(s@.subrange(0, s@.len() as int) =~= s@);
    while i < s.len()
        invariant
            i <= s.len(),
            matches(cur.re(), s@.subrange(i as int, s@.len() as int)) == matches(r0, s@),
        decreases s.len() - i,
    {
        let next = cur.deriv(s[i]);
        proof {
            assert(seq![s@[i as int]] + s@.subrange(i + 1, s@.len() as int) =~= s@.subrange(
                i as int,
                s@.len() as int,
            ));
            assert(matches(next.re(), s@.subrange(i + 1, s@.len() as int)) == matches(cur.re(), seq![s@[i as int]] + s@.subrange(i + 1, s@.len() as int)));
        }
        cur = next;
        i = i + 1;
    }
    assert(s@.subrange(i as int, s@.len() as int) =~= Seq::<char>::empty());
    cur.is_nullable()
}

// ---------------------------------------------------------------------------------------------
// Derivations (R11): certificates that `r` matches a slice
// ---------------------------------------------------------------------------------------------

pub enum Derivation {
    DEps,
    DChr,
    DAltL(Box<Derivation>),
    DAltR(Box<Derivation>),
    /// split point (absolute index), left and right derivations
    DCat(usize, Box<Derivation>, Box<Derivation>),
    DStarNil,
    /// first chunk ends at the absolute index (non-empty chunk)
    DStarCons(usize, Box<Derivation>, Box<Derivation>),
}

/// `d` proves that `r` matches `s[lo..hi]`.
pub open spec fn valid(d: Derivation, r: Re, s: Seq<char>, lo: int, hi: int) -> bool
    decreases d,
{
    0 <= lo <= hi <= s.len() && match d {
        Derivation::DEps => r is Eps && lo == hi,
        Derivation::DChr => r is Chr && hi == lo + 1 && s[lo] == r->Chr_0,
        Derivation::DAltL(d1) => r is Alt && valid(*d1, *r->Alt_0, s, lo, hi),
        Derivation::DAltR(d1) => r is Alt && valid(*d1, *r->Alt_1, s, lo, hi),
        Derivation::DCat(k, d1, d2) => r is Cat && lo <= k <= hi && valid(*d1, *r->Cat_0, s, lo, k as int)
            && valid(*d2, *r->Cat_1, s, k as int, hi),
        Derivation::DStarNil => r is Star && lo == hi,
        Derivation::DStarCons(k, d1, d2) => r is Star && lo < k <= hi && valid(*d1, *r->Star_0, s, lo, k as int)
            && valid(*d2, r, s, k as int, hi),
    }
}

/// Soundness: a valid derivation is a match.
pub proof fn lemma_valid_sound(d: Derivation, r: Re, s: Seq<char>, lo: int, hi: int)
    requires
        valid(d, r, s, lo, hi),
    ensures
        matches(r, s.subrange(lo, hi)),
    decreases d,
{
    let w = s.subrange(lo, hi);
    match d {
        Derivation::DChr => {
            assert(w[0] == s[lo]);
        },
        Derivation::DAltL(d1) => {
            lemma_valid_sound(*d1, *r->Alt_0, s, lo, hi);
        },
        Derivation::DAltR(d1) => {
            lemma_valid_sound(*d1, *r->Alt_1, s, lo, hi);
        },
        Derivation::DCat(k, d1, d2) => {
            lemma_valid_sound(*d1, *r->Cat_0, s, lo, k as int);
            lemma_valid_sound(*d2, *r->Cat_1, s, k as int, hi);
            assert(w.subrange(0, k - lo) =~= s.subrange(lo, k as int));
            assert(w.subrange(k - lo, w.len() as int) =~= s.subrange(k as int, hi));
        },
        Derivation::DStarCons(k, d1, d2) => {
            lemma_valid_sound(*d1, *r->Star_0, s, lo, k as int);
            lemma_valid_sound(*d2, r, s, k as int, hi);
            assert(w.subrange(0, k - lo) =~= s.subrange(lo, k as int));
            assert(w.subrange(k - lo, w.len() as int) =~= s.subrange(k as int, hi));
        },
        _ => {},
    }
}

/// Completeness: every match has a derivation.
pub proof fn lemma_valid_complete(r: Re, s: Seq<char>, lo: int, hi: int)
    requires
        0 <= lo <= hi <= s.len(),
        hi <= usize::MAX,
        matches(r, s.subrange(lo, hi)),
    ensures
        exists|d: Derivation| #[trigger] valid(d, r, s, lo, hi),
    decreases r, hi - lo,
{
    let w = s.subrange(lo, hi);
    match r {
        Re::Eps => {
            assert(valid(Derivation::DEps, r, s, lo, hi));
        },
        Re::Chr(c) => {
            assert(w[0] == s[lo]);
            assert(valid(Derivation::DChr, r, s, lo, hi));
        },
        Re::Alt(a, b) => {
            if matches(*a, w) {
                lemma_valid_complete(*a, s, lo, hi);
                let d1 = choose|d: Derivation| #[trigger] valid(d, *a, s, lo, hi);
                assert(valid(Derivation::DAltL(Box::new(d1)), r, s, lo, hi));
            } else {
                lemma_valid_complete(*b, s, lo, hi);
                let d1 = choose|d: Derivation| #[trigger] valid(d, *b, s, lo, hi);
                assert(valid(Derivation::DAltR(Box::new(d1)), r, s, lo, hi));
            }
        },
        Re::Cat(a, b) => {
            let i = choose|i: int|
                0 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                    *b,
                    w.subrange(i, w.len() as int),
                );
            assert(w.subrange(0, i) =~= s.subrange(lo, lo + i));
            assert(w.subrange(i, w.len() as int) =~= s.subrange(lo + i, hi));
            lemma_valid_complete(*a, s, lo, lo + i);
            lemma_valid_complete(*b, s, lo + i, hi);
            let d1 = choose|d: Derivation| #[trigger] valid(d, *a, s, lo, lo + i);
            let d2 = choose|d: Derivation| #[trigger] valid(d, *b, s, lo + i, hi);
            let k = (lo + i) as usize;
            assert(valid(Derivation::DCat(k, Box::new(d1), Box::new(d2)), r, s, lo, hi));
        },
        Re::Star(a) => {
            if lo == hi {
                assert(valid(Derivation::DStarNil, r, s, lo, hi));
            } else {
                let i = choose|i: int|
                    1 <= i <= w.len() && matches(*a, #[trigger] w.subrange(0, i)) && matches(
                        r,
                        w.subrange(i, w.len() as int),
                    );
                assert(w.subrange(0, i) =~= s.subrange(lo, lo + i));
                assert(w.subrange(i, w.len() as int) =~= s.subrange(lo + i, hi));
                lemma_valid_complete(*a, s, lo, lo + i);
                lemma_valid_complete(r, s, lo + i, hi);
                let d1 = choose|d: Derivation| #[trigger] valid(d, *a, s, lo, lo + i);
                let d2 = choose|d: Derivation| #[trigger] valid(d, r, s, lo + i, hi);
                let k = (lo + i) as usize;
                assert(valid(Derivation::DStarCons(k, Box::new(d1), Box::new(d2)), r, s, lo, hi));
            }
        },
        Re::Empty => {},
    }
}

/// The verified certificate checker: decides `valid`.
pub fn check_deriv(d: &Derivation, r: &Re, s: &Vec<char>, lo: usize, hi: usize) -> (ok: bool)
    ensures
        ok == valid(*d, *r, s@, lo as int, hi as int),
    decreases d,
{
    if !(lo <= hi && hi <= s.len()) {
        return false;
    }
    match (d, r) {
        (Derivation::DEps, Re::Eps) => lo == hi,
        (Derivation::DChr, Re::Chr(c)) => lo < hi && hi - lo == 1 && s[lo] == *c,
        (Derivation::DAltL(d1), Re::Alt(a, _)) => check_deriv(d1, a, s, lo, hi),
        (Derivation::DAltR(d1), Re::Alt(_, b)) => check_deriv(d1, b, s, lo, hi),
        (Derivation::DCat(k, d1, d2), Re::Cat(a, b)) => lo <= *k && *k <= hi && check_deriv(d1, a, s, lo, *k)
            && check_deriv(d2, b, s, *k, hi),
        (Derivation::DStarNil, Re::Star(_)) => lo == hi,
        (Derivation::DStarCons(k, d1, d2), Re::Star(a)) => lo < *k && *k <= hi && check_deriv(d1, a, s, lo, *k)
            && check_deriv(d2, r, s, *k, hi),
        _ => false,
    }
}

/// An unverified backtracking search for a derivation (only termination is proved; the
/// checker certifies what it returns).
#[verifier::loop_isolation(false)]
pub fn search(r: &Re, s: &Vec<char>, lo: usize, hi: usize) -> (out: Option<Derivation>)
    requires
        lo <= hi <= s.len(),
    decreases r, hi - lo,
{
    match r {
        Re::Empty => None,
        Re::Eps => if lo == hi { Some(Derivation::DEps) } else { None },
        Re::Chr(c) => if lo < hi && hi - lo == 1 && s[lo] == *c { Some(Derivation::DChr) } else { None },
        Re::Alt(a, b) => match search(a, s, lo, hi) {
            Some(d) => Some(Derivation::DAltL(Box::new(d))),
            None => match search(b, s, lo, hi) {
                Some(d) => Some(Derivation::DAltR(Box::new(d))),
                None => None,
            },
        },
        Re::Cat(a, b) => {
            let mut k = lo;
            loop
                invariant
                    lo <= k <= hi,
                    hi <= s.len(),
                decreases hi - k,
            {
                if let Some(d1) = search(a, s, lo, k) {
                    if let Some(d2) = search(b, s, k, hi) {
                        return Some(Derivation::DCat(k, Box::new(d1), Box::new(d2)));
                    }
                }
                if k == hi {
                    return None;
                }
                k = k + 1;
            }
        },
        Re::Star(a) => {
            if lo == hi {
                return Some(Derivation::DStarNil);
            }
            let mut k = lo + 1;
            loop
                invariant
                    lo < k <= hi,
                    hi <= s.len(),
                decreases hi - k,
            {
                if let Some(d1) = search(a, s, lo, k) {
                    if let Some(d2) = search(r, s, k, hi) {
                        return Some(Derivation::DStarCons(k, Box::new(d1), Box::new(d2)));
                    }
                }
                if k == hi {
                    return None;
                }
                k = k + 1;
            }
        },
    }
}

/// The certifying matcher: `Some(true)` only with a checked certificate; `Some(false)` from
/// the verified derivative matcher; never `None` (kept for the R11 shape "certificate or no").
pub fn cert_match(r: &Re, s: &Vec<char>) -> (out: bool)
    ensures
        out == matches(*r, s@),
{
    assert(s@.subrange(0, s@.len() as int) =~= s@);
    match search(r, s, 0, s.len()) {
        Some(d) => {
            if check_deriv(&d, r, s, 0, s.len()) {
                proof {
                    lemma_valid_sound(d, *r, s@, 0, s@.len() as int);
                }
                return true;
            }
        },
        None => {},
    }
    deriv_match(r, s)
}

} // verus!
