// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"h1","identifiers":["matches","Re","Star","Box","new","a","s"]},{"name":"h2","identifiers":["matches","Re","Cat","Star","Box","new","a","s"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_star_unfold_refuted","start":42,"end":50}]
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
pub proof fn lemma_star_unfold_refuted()
    ensures exists|a:Re,s:Seq<char>| matches(Re::Star(Box::new(a)),s) && !matches(Re::Cat(Box::new(a),Box::new(Re::Star(Box::new(a)))),s),
{
    let a=Re::Chr('x');let s=Seq::<char>::empty();
    assert(s.subrange(0,0) =~= Seq::<char>::empty());
    assert(/*R12_HINT:h1*/ true);
    assert forall|i:int| 0 <= i <= s.len() implies !matches(a,#[trigger] s.subrange(0,i)) by { }
    assert(/*R12_HINT:h2*/ true);
}

} // verus!
