// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["a"],"kind":"calls","callees":["lemma_nullable_fact"]},{"name":"h1","identifiers":["matches","a","s","subrange"]},{"name":"h2","identifiers":["matches","Re","Cat","Box","new","a","st","s"]},{"name":"h3","identifiers":["matches","st","s"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_star_unfold","start":76,"end":101}]
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

// Provided fact (rg_re_a1b::lemma_nullable_correct), complete.
pub proof fn lemma_nullable_fact(r: Re)
    ensures
        nullable(r) <==> matches(r, Seq::<char>::empty()),
    decreases r,
{
    let e = Seq::<char>::empty();
    assert(e.subrange(0, 0) =~= e);
    match r {
        Re::Alt(a, b) => {
            lemma_nullable_fact(*a);
            lemma_nullable_fact(*b);
        },
        Re::Cat(a, b) => {
            lemma_nullable_fact(*a);
            lemma_nullable_fact(*b);
        },
        _ => {},
    }
}

// The task (R06.H4 star unfold): unfold a star once.
pub proof fn lemma_star_unfold(a: Re, s: Seq<char>)
    requires
        s.len() > 0 || nullable(a),
    ensures
        matches(Re::Star(Box::new(a)), s) <==> matches(Re::Cat(Box::new(a), Box::new(Re::Star(Box::new(a)))), s),
{
    let st = Re::Star(Box::new(a));
    if s.len() == 0 {
        /*R12_CALLS:c1*/
        assert(s.subrange(0, 0) =~= Seq::<char>::empty());
        assert(s =~= Seq::<char>::empty());
        assert(/*R12_HINT:h1*/ true);
    }
    if matches(st, s) && s.len() > 0 {
        let i = choose|i: int| 1 <= i <= s.len() && matches(a, #[trigger] s.subrange(0, i)) && matches(st, s.subrange(i, s.len() as int));
        assert(/*R12_HINT:h2*/ true);
    }
    if matches(Re::Cat(Box::new(a), Box::new(st)), s) {
        let i = choose|i: int| 0 <= i <= s.len() && matches(a, #[trigger] s.subrange(0, i)) && matches(st, s.subrange(i, s.len() as int));
        if i == 0 {
            assert(s.subrange(i, s.len() as int) =~= s);
        } else {
            assert(/*R12_HINT:h3*/ true);
        }
    }
}

} // verus!
