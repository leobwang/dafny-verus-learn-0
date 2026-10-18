// R12_HINT_SITES: [{"name":"c1","identifiers":["a","b"],"kind":"calls","callees":["lemma_backwards_involution"]},{"name":"c2","identifiers":["a","b"],"kind":"calls","callees":["lemma_backwards_involution"]},{"name":"c3","identifiers":["a"],"kind":"calls","callees":["lemma_backwards_involution"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_backwards_involution","start":32,"end":48}]
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

/// The regex read backwards.
pub open spec fn backwards(r: Re) -> Re
    decreases r,
{
    match r {
        Re::Empty => Re::Empty,
        Re::Eps => Re::Eps,
        Re::Chr(c) => Re::Chr(c),
        Re::Alt(a, b) => Re::Alt(Box::new(backwards(*a)), Box::new(backwards(*b))),
        Re::Cat(a, b) => Re::Cat(Box::new(backwards(*b)), Box::new(backwards(*a))),
        Re::Star(a) => Re::Star(Box::new(backwards(*a))),
    }
}

// The task.
pub proof fn lemma_backwards_involution(r: Re)
    ensures backwards(backwards(r)) == r,
    decreases r,
{
    match r {
        Re::Alt(a,b) => {
            /*R12_CALLS:c1*/
        },
        Re::Cat(a,b) => {
            /*R12_CALLS:c2*/
        },
        Re::Star(a) => {
            /*R12_CALLS:c3*/
        },
        _ => { },
    }
}

} // verus!
