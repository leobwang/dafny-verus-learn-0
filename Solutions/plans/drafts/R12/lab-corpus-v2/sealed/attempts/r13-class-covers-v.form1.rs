// R12_HINT_SITES: [{"name":"h1","identifiers":["k","s","len"]},{"name":"h2","identifiers":["cc","contains","s","i","k","int"]}]
// R12_SOURCE_SPANS: [{"symbol":"class_covers_r13","start":15,"end":32}]
use vstd::prelude::*;

verus! {

// Provided layer: rg_re_a2::char_class (layer A2), imported; the class API this task uses
// (its contracts, verbatim from the layer; the representation is private):
//   pub fn class_member(&self, c: char) -> (b: bool)
//     ensures b == self@.contains(c)
//   the view `cc@: ISet<char>` holds the class's characters.
use rg_re_a2::char_class::CharClass;

// The task (R13.H2 class_covers_r13): every character of s lies in the class cc, a verified loop over A2's class API.
pub fn class_covers_r13(cc: &CharClass, s: &Vec<char>) -> (b: bool)
    ensures
        b == (forall|i: int| 0 <= i < s@.len() ==> cc@.contains(#[trigger] s@[i])),
{
    let mut k: usize = 0;
    while k < s.len()
        invariant
            /*R12_HINT:h1*/ true,
            /*R12_HINT:h2*/ true,
        decreases s.len() - k,
    {
        if !cc.class_member(s[k]) {
            return false;
        }
        k = k + 1;
    }
    true
}
} // verus!
