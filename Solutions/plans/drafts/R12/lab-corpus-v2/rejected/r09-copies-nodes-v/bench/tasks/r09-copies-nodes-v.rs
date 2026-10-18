// R12_HINT_SITES: [{"name":"c1","identifiers":["r","km"],"kind":"calls","callees":["lemma_copies_nodes_r09"]},{"name":"h1","identifiers":["total","b","child"]}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_copies_nodes_r09","start":53,"end":71}]
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

// Provided definitions: rg_re_a3 (layer A3), counted repetition, copied verbatim.
pub open spec fn copies(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Cat(Box::new(r), Box::new(copies(r, (k - 1) as nat)))
    }
}

pub open spec fn copies_up_to(r: Re, k: nat) -> Re
    decreases k,
{
    if k == 0 {
        Re::Eps
    } else {
        Re::Alt(Box::new(Re::Eps), Box::new(Re::Cat(Box::new(r), Box::new(copies_up_to(r, (k - 1) as nat)))))
    }
}

// The task (R09 CopiesNodesR09): the node count of copies(r, k).
proof fn lemma_copies_nodes_r09(r:Re,k:nat)
 ensures node_count(copies(r,k))==1+k*(node_count(r)+1),
 decreases k,
{
 reveal_with_fuel(node_count,2);
 reveal_with_fuel(copies,2);
 let b=node_count(r) as int;
 if k>0 {
  let km=(k-1) as nat;
  /*R12_CALLS:c1*/
  let total=node_count(copies(r,k)) as int;
  let child=node_count(copies(r,km)) as int;
  assert(/*R12_HINT:h1*/ true);
  assert(total==1+k*(b+1)) by (nonlinear_arith)
   requires total==1+b+child,child==1+km*(b+1),k==km+1;
 } else {
  assert(1+k*(b+1)==1) by (nonlinear_arith) requires k==0;
 }
}

} // verus!
