// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","identifiers":["u","c"],"kind":"calls","callees":["lemma_append_split"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_literal_append_r09","start":53,"end":65}]
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

// Provided fact: the extensional split of u + [c] (the reference's two =~= bridges, as a lemma,
// since the hint grammar has no =~=), complete.
proof fn lemma_append_split(u: Seq<char>, c: char)
 ensures (u+seq![c]).subrange(0,u.len() as int) == u,
  (u+seq![c]).subrange(u.len() as int,(u+seq![c]).len() as int) == seq![c],
{
 let w=u+seq![c];
 assert(w.subrange(0,u.len() as int) =~= u);
 assert(w.subrange(u.len() as int,w.len() as int) =~= seq![c]);
}

// The task (R09 literal append): appending a literal extends a match by Cat.
pub proof fn lemma_literal_append_r09(a:Re,u:Seq<char>,c:char)
 requires matches(a,u),
 ensures matches(Re::Cat(Box::new(a),Box::new(Re::Chr(c))),u+seq![c]),
{
 let w=u+seq![c];
 reveal_with_fuel(matches,2);
 /*R12_CALLS:c1*/
 assert(exists|i:int| 0<=i<=w.len() && matches(a,#[trigger] w.subrange(0,i)) && matches(Re::Chr(c),w.subrange(i,w.len() as int))) by {
  let i=u.len() as int;
  assert(matches(a,w.subrange(0,i)));
  assert(matches(Re::Chr(c),w.subrange(i,w.len() as int)));
 }
}

} // verus!
