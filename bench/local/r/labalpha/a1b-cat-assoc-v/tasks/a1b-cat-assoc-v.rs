// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"h1"},{"name":"h2"}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_cat_assoc","start":42,"end":85}]
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
        assert(/*R12_HINT:h1*/ true);
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
        assert(/*R12_HINT:h2*/ true);
    }
}

} // verus!
