// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"h1","identifiers":["u","v"]},{"name":"c1","identifiers":["deriv","r","u","v","subrange","len"],"kind":"calls","callees":["lemma_derivs_append"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_derivs_append","start":57,"end":66}]
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

// R06's given one-character derivative (not a task).
pub open spec fn deriv(r: Re, c: char) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Empty,
        Re::Chr(d) => if c == d { Re::Eps } else { Re::Empty },
        Re::Alt(a, b) => Re::Alt(Box::new(deriv(*a, c)), Box::new(deriv(*b, c))),
        Re::Cat(a, b) => if nullable(*a) {
            Re::Alt(Box::new(Re::Cat(Box::new(deriv(*a, c)), b)), Box::new(deriv(*b, c)))
        } else {
            Re::Cat(Box::new(deriv(*a, c)), b)
        },
        Re::Star(a) => Re::Cat(Box::new(deriv(*a, c)), Box::new(Re::Star(a))),
    }
}

// R06's given word derivative (R06 checkpoint, not a task).
pub open spec fn derivs(r: Re,s: Seq<char>) -> Re
    decreases s.len(),
{ if s.len() == 0 { r } else { derivs(deriv(r,s[0]),s.subrange(1,s.len() as int)) } }

// The task.
pub proof fn lemma_derivs_append(r: Re,u: Seq<char>,v: Seq<char>)
    ensures derivs(r,u+v) == derivs(derivs(r,u),v),
    decreases u.len(),
{
    if u.len() > 0 {
        assert(/*R12_HINT:h1*/ true);
        assert((u+v).subrange(1,(u+v).len() as int) =~= u.subrange(1,u.len() as int)+v);
        /*R12_CALLS:c1*/
    } else { assert(u+v =~= v); }
}

} // verus!
