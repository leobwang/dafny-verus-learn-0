// R12_HINT_SITES: [{"name":"h1","identifiers":["matches","st","s","subrange","len","as","int"]},{"name":"h2","identifiers":["matches","stst","s","subrange","len","as","int"]},{"name":"c1","identifiers":["x","s","i","subrange","len","as","int"],"kind":"calls","callees":["lemma_star_star_r10","lemma_star_concat"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_star_star_r10","start":64,"end":88}]
use vstd::prelude::*;

verus! {

// Provided definitions: rg_re_a1 (layer A1), copied verbatim.
pub enum Re {
    Empty,
    Eps,
    Chr(char),
    Alt(Box<Re>, Box<Re>),
    Cat(Box<Re>, Box<Re>),
    Star(Box<Re>),
}

pub open spec fn matches(r: Re, s: Seq<char>) -> bool
    decreases r, s.len(),
{
    match r {
        Re::Empty => false,
        Re::Eps => s.len() == 0,
        Re::Chr(c) => s.len() == 1 && s[0] == c,
        Re::Alt(a, b) => matches(*a, s) || matches(*b, s),
        Re::Cat(a, b) => exists|i: int|
            0 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                *b,
                s.subrange(i, s.len() as int),
            ),
        Re::Star(a) => s.len() == 0 || exists|i: int|
            1 <= i <= s.len() && matches(*a, #[trigger] s.subrange(0, i)) && matches(
                r,
                s.subrange(i, s.len() as int),
            ),
    }
}

// Provided fact (rg_re_a1b::lemma_star_concat), complete, copied verbatim.
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

// The task (R10 agent star-star): a star of a star is the star.
pub proof fn lemma_star_star_r10(x: Re, s: Seq<char>)
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
            assert(/*R12_HINT:h1*/ true);
            assert(/*R12_HINT:h2*/ true);
        }
        if matches(stst, s) {
            let i = choose|i: int|
                1 <= i <= s.len() && matches(st, #[trigger] s.subrange(0, i)) && matches(
                    stst,
                    s.subrange(i, s.len() as int),
                );
            /*R12_CALLS:c1*/
            assert(s.subrange(0, i) + s.subrange(i, s.len() as int) =~= s);
        }
    }
}

} // verus!
