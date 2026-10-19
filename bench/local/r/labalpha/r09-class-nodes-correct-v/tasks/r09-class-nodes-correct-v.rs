// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"h1","identifiers":["xs","drop_first","i"]},{"name":"c1","identifiers":["xs","drop_first"],"kind":"calls","callees":["lemma_range_nodes_r09","lemma_class_nodes_r09"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_class_nodes_r09","start":103,"end":114}]
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

/// The number of nodes of `r`.
pub open spec fn node_count(r: Re) -> nat
    decreases r,
{
    match r {
        Re::Empty => 1,
        Re::Eps => 1,
        Re::Chr(_) => 1,
        Re::Alt(a, b) => 1 + node_count(*a) + node_count(*b),
        Re::Cat(a, b) => 1 + node_count(*a) + node_count(*b),
        Re::Star(a) => 1 + node_count(*a),
    }
}

pub const CLASS_MAX: u32 = 0xd800;

// Provided definitions: rg_re_a3 (layer A3), classes as regexes, copied verbatim.
/// A range that lowers: non-empty and below CLASS_MAX.
pub open spec fn range_valid(lo: u32, hi: u32) -> bool {
    lo <= hi && hi < CLASS_MAX
}

/// A range listing that lowers.
pub open spec fn class_valid(xs: Seq<(u32, u32)>) -> bool {
    forall|i: int| 0 <= i < xs.len() ==> range_valid(xs[i].0, xs[i].1)
}

/// The one place a code becomes a char (spec only): `lo < CLASS_MAX`, so it is a char's code.
pub open spec fn range_re(lo: u32, hi: u32) -> Re
    decreases hi - lo,
{
    if !range_valid(lo, hi) {
        Re::Empty
    } else if lo == hi {
        Re::Chr(lo as char)
    } else {
        Re::Alt(Box::new(Re::Chr(lo as char)), Box::new(range_re((lo + 1) as u32, hi)))
    }
}

pub open spec fn class_re(xs: Seq<(u32, u32)>) -> Re
    decreases xs.len(),
{
    if xs.len() == 0 {
        Re::Empty
    } else {
        Re::Alt(Box::new(range_re(xs[0].0, xs[0].1)), Box::new(class_re(xs.drop_first())))
    }
}

// Provided definitions: R09's size model, copied verbatim.
pub open spec fn range_nodes_r09(lo: u32, hi: u32) -> nat {
    if range_valid(lo, hi) {
        (2 * ((hi as int) - (lo as int)) + 1) as nat
    } else {
        1
    }
}
pub open spec fn class_nodes_r09(xs: Seq<(u32, u32)>) -> nat
    decreases xs.len(),
{
    if xs.len() == 0 {
        1
    } else {
        1 + range_nodes_r09(xs[0].0, xs[0].1) + class_nodes_r09(xs.drop_first())
    }
}

// Provided fact (R09 reference lemma_range_nodes_r09), complete.
proof fn lemma_range_nodes_r09(lo: u32, hi: u32)
    requires
        range_valid(lo, hi),
    ensures
        node_count(range_re(lo, hi)) == range_nodes_r09(lo, hi),
    decreases hi - lo,
{
    reveal_with_fuel(node_count, 2);
    if lo < hi {
        lemma_range_nodes_r09((lo + 1) as u32, hi);
    }
}

// The task (R09 class nodes): the node count of a lowered range listing.
proof fn lemma_class_nodes_r09(xs: Seq<(u32, u32)>)
 requires class_valid(xs),
 ensures node_count(class_re(xs))==class_nodes_r09(xs),
 decreases xs.len(),
{
 if xs.len()>0 {
  assert forall|i:int| 0<=i<xs.drop_first().len() implies range_valid(xs.drop_first()[i].0,xs.drop_first()[i].1) by {
   assert(/*R12_HINT:h1*/ true);
  }
  /*R12_CALLS:c1*/
 }
}

} // verus!
