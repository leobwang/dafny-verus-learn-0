// R12_HINT_SITES: [{"name":"h1","identifiers":["i"]},{"name":"h2","identifiers":["i","s","len"]},{"name":"h3","identifiers":["matches","a","s","subrange"]},{"name":"h4","identifiers":["matches","a","s","subrange","len","as","int"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_mk_cat_r10","start":66,"end":93}]
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

// Provided definitions: rg_re_a4 (layer A4), copied verbatim.
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

// The task (R10 agent mk-cat): the smart concatenation keeps the language and the shape.
pub proof fn lemma_mk_cat_r10(a: Re, b: Re, s: Seq<char>)
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
            assert(/*R12_HINT:h1*/ true);
        } else if b is Eps {
            assert(/*R12_HINT:h2*/ true);
        }
    }
    if a is Eps && !(b is Empty) && matches(b, s) {
        assert(/*R12_HINT:h3*/ true);
    }
    if b is Eps && !(a is Empty) && !(a is Eps) && matches(a, s) {
        assert(/*R12_HINT:h4*/ true);
    }
}

} // verus!
