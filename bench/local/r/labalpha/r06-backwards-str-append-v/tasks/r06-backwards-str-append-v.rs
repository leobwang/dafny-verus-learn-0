// R12_HINT_SITES: [{"name":"h1","identifiers":["u","v"]},{"name":"c1","identifiers":["u","v","subrange","len"],"kind":"calls","callees":["lemma_backwards_str_append"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_backwards_str_append","start":29,"end":41}]
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

/// The string read backwards.
pub open spec fn backwards_str(s: Seq<char>) -> Seq<char>
    decreases s.len(),
{
    if s.len() == 0 {
        Seq::empty()
    } else {
        backwards_str(s.subrange(1, s.len() as int)) + seq![s[0]]
    }
}

// The task.
pub proof fn lemma_backwards_str_append(u: Seq<char>,v: Seq<char>)
    ensures backwards_str(u+v) == backwards_str(v)+backwards_str(u),
    decreases u.len(),
{
    if u.len() == 0 {
        assert(u+v =~= v);
    } else {
        assert((u+v).subrange(1,(u+v).len() as int) =~= u.subrange(1,u.len() as int)+v);
        assert(/*R12_HINT:h1*/ true);
        /*R12_CALLS:c1*/
        assert((backwards_str(v)+backwards_str(u.subrange(1,u.len() as int)))+seq![u[0]] =~= backwards_str(v)+(backwards_str(u.subrange(1,u.len() as int))+seq![u[0]]));
    }
}

} // verus!
