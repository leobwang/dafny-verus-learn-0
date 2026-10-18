// R12_HINT_SITES: [{"name":"h1","identifiers":["matches","r","s","subrange","len"]},{"name":"h2","identifiers":["s","i","subrange","len"]},{"name":"h3","identifiers":["s","i","len"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_cat_eps_right","start":39,"end":58}]
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

// The task.
pub proof fn lemma_cat_eps_right(r: Re, s: Seq<char>)
    ensures
        matches(Re::Cat(Box::new(r), Box::new(Re::Eps)), s) <==> matches(r, s),
{
    let e = Re::Cat(Box::new(r), Box::new(Re::Eps));
    assert(s.subrange(0, s.len() as int) =~= s);
    if matches(r, s) {
        assert(s.subrange(s.len() as int, s.len() as int) =~= Seq::<char>::empty());
        assert(/*R12_HINT:h1*/ true);
    }
    if matches(e, s) {
        let i = choose|i: int|
            0 <= i <= s.len() && matches(r, #[trigger] s.subrange(0, i)) && matches(
                Re::Eps,
                s.subrange(i, s.len() as int),
            );
        assert(/*R12_HINT:h2*/ true);
        assert(/*R12_HINT:h3*/ true);
    }
}

} // verus!
