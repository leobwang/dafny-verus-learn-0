// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["backwards_str","tail","seq","s"],"kind":"calls","callees":["lemma_backwards_str_append"]},{"name":"h1","identifiers":["backwards_str","seq","s","subrange"]},{"name":"c2","identifiers":["tail"],"kind":"calls","callees":["lemma_backwards_str_involution"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_backwards_str_involution","start":49,"end":63}]
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

// Provided facts, complete (not tasks).

// R06 lemma_backwards_str_append (R06 decomposer reference), complete.
pub proof fn lemma_backwards_str_append(u: Seq<char>,v: Seq<char>)
    ensures backwards_str(u+v) == backwards_str(v)+backwards_str(u),
    decreases u.len(),
{
    if u.len() == 0 {
        assert(u+v =~= v);
    } else {
        assert((u+v).subrange(1,(u+v).len() as int) =~= u.subrange(1,u.len() as int)+v);
        assert((u+v)[0] == u[0]);
        lemma_backwards_str_append(u.subrange(1,u.len() as int),v);
        assert((backwards_str(v)+backwards_str(u.subrange(1,u.len() as int)))+seq![u[0]] =~= backwards_str(v)+(backwards_str(u.subrange(1,u.len() as int))+seq![u[0]]));
    }
}

// The task.
pub proof fn lemma_backwards_str_involution(s: Seq<char>)
    ensures backwards_str(backwards_str(s)) == s,
    decreases s.len(),
{
    if s.len() > 0 {
        let tail=s.subrange(1,s.len() as int);
        /*R12_CALLS:c1*/
        assert(seq![s[0]].subrange(1,1) =~= Seq::<char>::empty());
        assert(backwards_str(Seq::<char>::empty()) =~= Seq::<char>::empty());
        assert(/*R12_HINT:h1*/ true);
        assert(backwards_str(seq![s[0]]) =~= seq![s[0]]);
        /*R12_CALLS:c2*/
        assert(s =~= seq![s[0]]+tail);
    }
}

} // verus!
