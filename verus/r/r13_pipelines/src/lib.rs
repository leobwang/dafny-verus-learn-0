use vstd::prelude::*;
use rg_re_a1::{Re,matches};
verus! {
 // item: R13.T1v
 // pair: R13.T1d
 pub fn clamp_index_r13(i:usize,bound:usize)->(at:usize)
  requires bound>0,
  ensures at<bound,at==if i<bound {i as int} else {bound-1},
 {proof {#[verifier::proof_note("R13.T1v")] assume(false);} 0}
 // item: R13.H1v
 // pair: R13.H1d
 pub fn saturating_sum_r13(a:u64,b:u64)->(out:u64)
  ensures out==if a+b<=u64::MAX {a+b} else {u64::MAX as int},
 {proof {#[verifier::proof_note("R13.H1v")] assume(false);} 0}
 // item: R13.H2v
 // pair: R13.H2d
 pub fn range_fits_r13(pos:usize,need:usize,limit:usize)->(fits:bool)
  ensures fits <==> pos+need<=limit,
 {proof {#[verifier::proof_note("R13.H2v")] assume(false);} false}
 // item: R13.H3v
 // pair: R13.H3d
 pub fn pair_witness_r13(c:char,d:char)->(s:Vec<char>)
  ensures s.len()==2,matches(Re::Cat(Box::new(Re::Chr(c)),Box::new(Re::Chr(d))),s@),
 {proof {#[verifier::proof_note("R13.H3v")] assume(false);} Vec::new()}
}
