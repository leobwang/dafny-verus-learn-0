// [R12 header] DO NOT OPEN BEFORE R11 IS DONE. This Lab alpha task form restates a lemma of an
// [R12 header] earlier module (R02-R11, or layer A1b) with parts of its proof; open it from R12 on,
// [R12 header] after those modules' first tries are recorded (a declared later-tier overlap, Delta 294).
// R12_HINT_SITES: [{"name":"c1","kind":"calls","callees":["lemma_copies_optional_r09"]},{"name":"h1"},{"name":"h2"},{"name":"h3"},{"name":"h4"},{"name":"c2","kind":"calls","callees":["lemma_copies_optional_r09"]},{"name":"h5"}]
// R12_SOURCE_SPANS: [{"symbol":"lemma_copies_optional_r09","start":63,"end":100}]
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

// The task (R09 copies optional): copies_up_to(r, j) matches exactly 0..j copies.
proof fn lemma_copies_optional_r09(r:Re,j:nat,s:Seq<char>)
 ensures matches(copies_up_to(r,j),s)==(exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s)),
 decreases j,
{
 if j>0 {
  let jm=(j-1) as nat;let u=copies_up_to(r,jm);
  if matches(copies_up_to(r,j),s) {
   if s.len()!=0 {
    assert(!matches(Re::Eps,s));
    assert(matches(Re::Cat(Box::new(r),Box::new(u)),s));
    let i=choose|i:int| 0<=i<=s.len() && matches(r,#[trigger] s.subrange(0,i)) && matches(u,s.subrange(i,s.len() as int));
    /*R12_CALLS:c1*/
    let k=choose|k:nat| k<=jm && #[trigger] matches(copies(r,k),s.subrange(i,s.len() as int));
    assert(/*R12_HINT:h1*/ true);
    assert(/*R12_HINT:h2*/ true);
   } else {
    assert(/*R12_HINT:h3*/ true);
   }
  }
  if exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s) {
   let k=choose|k:nat| k<=j && #[trigger] matches(copies(r,k),s);
   if k>0 {
    let km=(k-1) as nat;
    assert(/*R12_HINT:h4*/ true);
    let i=choose|i:int| 0<=i<=s.len() && matches(r,#[trigger] s.subrange(0,i)) && matches(copies(r,km),s.subrange(i,s.len() as int));
    /*R12_CALLS:c2*/
    assert(exists|kk:nat| kk<=jm && #[trigger] matches(copies(r,kk),s.subrange(i,s.len() as int)));
    assert(/*R12_HINT:h5*/ true);
   } else {assert(copies(r,0)==Re::Eps);}
   assert(matches(copies_up_to(r,j),s));
  }
 } else {
  assert(copies(r,0)==Re::Eps);
  if exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s) {
   let k=choose|k:nat| k<=j && #[trigger] matches(copies(r,k),s);assert(k==0);
  }
 }
}

} // verus!
