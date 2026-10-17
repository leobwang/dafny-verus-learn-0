/*! R14 — SMT mechanics. Three counted native holes per language.
H1 propagates quantified bounds through an original trace. H2 proves a property
of an honestly recursive opaque definition. H3 keeps exact32bitword behavior.
D H1/H2 explicitly disable induction: maximal automation solves their empty
forms. Preserve these levers and all original domains; do not infer toolchain
correctness from an automation result. The12assertion battery is separate.
*/
// item: R14.C1v write:trigger
// Supply a matching term covering every quantified variable, using R14-owned subjects.
// item: R14.C2v write:fuel
// A fixed unfolding budget is not unbounded induction; preserve the original recursion.
// item: R14.C3v write:bit-vector
// Bit-vector arithmetic and mathematical integer arithmetic have different operations.
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
 pub fn clear_low_bit_r14(x:u32)->(out:u32)
  requires x>0,
  ensures out==(x & ((x-1) as u32)),out<x,
 {proof {#[verifier::proof_note("R14.H3v")] assume(false);} 0}
}
