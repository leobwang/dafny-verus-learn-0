// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["m","drop_first"],"kind":"calls","callees":["lemma_alt_final_law","lemma_nullable_correct"]},{"name":"h1","identifiers":["m","i","int","len","drop_first"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_alt_final_law","start":95,"end":105}]
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

pub open spec fn nullable(r: Re) -> bool
    decreases r,
{
    match r {
        Re::Empty => false,
        Re::Eps => true,
        Re::Chr(_) => false,
        Re::Alt(a, b) => nullable(*a) || nullable(*b),
        Re::Cat(a, b) => nullable(*a) && nullable(*b),
        Re::Star(_) => true,
    }
}

// Provided fact (rg_re_a1b::lemma_nullable_correct), complete, copied verbatim.
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


/// Given: some alternative of the list matches `w`.
pub open spec fn any_matches(st: Seq<Re>, w: Seq<char>) -> bool {
    exists|i: int| 0 <= i < st.len() && matches(#[trigger] st[i], w)
}

/// Given: some alternative of the list is nullable.
pub open spec fn any_nullable(st: Seq<Re>) -> bool
    decreases st.len(),
{
    st.len() > 0 && (nullable(st[0]) || any_nullable(st.drop_first()))
}

/// The engine's model, opaque: revealed with `reveal(alt_res)`.
#[verifier::opaque]
pub open spec fn alt_res(m: Seq<Re>, w: Seq<char>) -> bool {
    any_matches(m, w)
}

// The task (R08.H4 lemma_alt_final_law): the alternative-set engine's final law.
pub proof fn lemma_alt_final_law(m: Seq<Re>)
    ensures
        any_nullable(m) == alt_res(m, Seq::<char>::empty()),
    decreases m.len(),
{
    reveal(alt_res);
    if m.len() > 0 {
        /*R12_CALLS:c1*/
        assert(/*R12_HINT:h1*/ true);
    }
}
} // verus!
