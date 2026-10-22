// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_star_concat"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_star_concat","start":42,"end":64}]
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
        /*R12_CALLS:c1*/
        assert(t.subrange(0, i) =~= u.subrange(0, i));
        assert(t.subrange(i, t.len() as int) =~= u.subrange(i, u.len() as int) + v);
    }
}

} // verus!
