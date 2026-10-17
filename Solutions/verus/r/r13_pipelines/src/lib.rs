// Reference Solution.
use vstd::prelude::*;
use rg_re_a1::{Re,matches};
verus! {
 // item: R13.T1v
 // pair: R13.T1d
 // triv: { 0 }
 pub fn clamp_index_r13(i:usize,bound:usize)->(at:usize)
  requires bound>0,
  ensures at<bound,at==if i<bound {i as int} else {bound-1},
 {// did: preserve the index in range and clamp only the other branch.
  if i<bound {i} else {bound-1}}
 // item: R13.H1v
 // pair: R13.H1d
 // triv: { 0 }
 pub fn saturating_sum_r13(a:u64,b:u64)->(out:u64)
  ensures out==if a+b<=u64::MAX {a+b} else {u64::MAX as int},
 {// did: compare headroom before executing bounded addition.
  if a<=u64::MAX-b {a+b} else {u64::MAX}}
 // item: R13.H2v
 // pair: R13.H2d
 // triv: { false }
 pub fn range_fits_r13(pos:usize,need:usize,limit:usize)->(fits:bool)
  ensures fits <==> pos+need<=limit,
 {// did: guard subtraction while keeping the full mathematical domain.
  pos<=limit && need<=limit-pos}
 // item: R13.H3v
 // pair: R13.H3d
 // triv: { Vec::new() }
 pub fn pair_witness_r13(c:char,d:char)->(s:Vec<char>)
  ensures s.len()==2,matches(Re::Cat(Box::new(Re::Chr(c)),Box::new(Re::Chr(d))),s@),
 {// did: construct a nonempty vector and connect its two slices to the existential.
  let s=vec![c,d];
  proof {
   assert(s@.subrange(0,1)=~=seq![c]);
   assert(s@.subrange(1,2)=~=seq![d]);
   assert(matches(Re::Chr(c),s@.subrange(0,1)));
   assert(matches(Re::Chr(d),s@.subrange(1,2)));
   assert(exists|i:int| 0<=i<=s.len() && matches(Re::Chr(c),#[trigger] s@.subrange(0,i)) && matches(Re::Chr(d),s@.subrange(i,s.len() as int)));
  }
  s}
}
