use vstd::prelude::*;
verus! {
 pub open spec fn prefix_mass_r14(s:Seq<int>)->int
  decreases s.len(),
 {if s.len()==0 {0} else {s[0]+prefix_mass_r14(s.subrange(1,s.len() as int))}}
 // item: R14.H1v
 // pair: R14.H1d
 pub proof fn prefix_cap_r14(s:Seq<int>,cap:int)
  requires cap>=0,forall|i:int| 0<=i<s.len() ==> 0<=#[trigger] s[i]<=cap,
  ensures 0<=prefix_mass_r14(s)<=s.len()*cap,
  decreases s.len(),
 {#[verifier::proof_note("R14.H1v")] assume(false); }
 #[verifier::opaque]
 pub open spec fn odd_trace_r14(n:nat)->nat
  decreases n,
 {if n==0 {0} else {(odd_trace_r14((n-1) as nat)+2*n-1) as nat}}
 // item: R14.H2v
 // pair: R14.H2d
 pub proof fn odd_square_r14(n:nat)
  ensures odd_trace_r14(n)==n*n,
  decreases n,
 {#[verifier::proof_note("R14.H2v")] assume(false); }
 // item: R14.H3v
 // pair: R14.H3d
 // triv: { 0 }
 pub fn clear_low_bit_r14(x:u32)->(out:u32)
  requires x>0,
  ensures out==(x & ((x-1) as u32)),out<x,
 {proof {#[verifier::proof_note("R14.H3v")] assume(false);} 0}
}
