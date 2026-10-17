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
 {// did: instantiate the original indexed fact at each tail index.
  if s.len()>0 {
   let tail=s.subrange(1,s.len() as int);
   assert forall|i:int| 0<=i<tail.len() implies 0<=#[trigger] tail[i]<=cap by {
    assert(tail[i]==s[i+1]);
   }
   prefix_cap_r14(tail,cap);
   assert((s.len()-1)*cap+cap==s.len()*cap) by(nonlinear_arith);
  }}
 #[verifier::opaque]
 pub open spec fn odd_trace_r14(n:nat)->nat
  decreases n,
 {if n==0 {0} else {(odd_trace_r14((n-1) as nat)+2*n-1) as nat}}
 // item: R14.H2v
 // pair: R14.H2d
 pub proof fn odd_square_r14(n:nat)
  ensures odd_trace_r14(n)==n*n,
  decreases n,
 {// did: reveal two levels to connect the recursive trace and square recurrence.
  reveal_with_fuel(odd_trace_r14,2);
  if n>0 {
   let previous=(n-1) as nat;
   odd_square_r14(previous);
   assert(previous+1==n);
   assert(odd_trace_r14(n)==(odd_trace_r14(previous)+2*n-1) as nat);
   assert(odd_trace_r14(previous)==previous*previous);
   assert(n*n==previous*previous+2*n-1) by(nonlinear_arith) requires previous+1==n;
  } else {assert(odd_trace_r14(n)==0);}}
 // item: R14.H3v
 // pair: R14.H3d
 // triv: { 0 }
 pub fn clear_low_bit_r14(x:u32)->(out:u32)
  requires x>0,
  ensures out==(x & ((x-1) as u32)),out<x,
 {// did: use the actual word-theory identity without changing the input domain.
  let out=x&(x-1);
  proof {assert((x & ((x-1) as u32))<x) by(bit_vector) requires x>0u32;}
  out}
}

verus! {pub proof fn battery_cell_r14(s:Seq<int>,cap:int)
 requires cap>=0,forall|i:int| 0<=i<s.len() ==> 0<=#[trigger] s[i]<=cap,
 ensures 0<=prefix_mass_r14(s),
 {
 prefix_cap_r14(s,cap);
 }}
