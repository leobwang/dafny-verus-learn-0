// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b"],"kind":"calls","callees":["lemma_nullable_correct"]},{"name":"c2","identifiers":["a","b"],"kind":"calls","callees":["lemma_nullable_correct"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_nullable_correct","start":55,"end":71}]
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

// The task.
pub proof fn lemma_nullable_correct(r: Re)
    ensures
        nullable(r) <==> matches(r, Seq::<char>::empty()),
    decreases r,
{
    let e = Seq::<char>::empty();
    assert(e.subrange(0, 0) =~= e);
    match r {
        Re::Alt(a, b) => {
            /*R12_CALLS:c1*/
        },
        Re::Cat(a, b) => {
            /*R12_CALLS:c2*/
        },
        _ => {},
    }
}

} // verus!
