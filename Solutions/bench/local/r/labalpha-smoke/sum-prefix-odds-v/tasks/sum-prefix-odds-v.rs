// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","n","odd_sum","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":8,"end":14}]
use vstd::prelude::*;
verus! {
pub open spec fn odd_sum(k:nat)->nat decreases k, {if k==0 {0} else {odd_sum((k-1) as nat)+((2*(k-1)+1) as nat)}}
proof fn step_model(i:nat) ensures odd_sum(i+1)==odd_sum(i)+2*i+1, {}
 #[verifier::loop_isolation(false)]
 fn lab_task(n:usize)->(out:usize) requires n<=1000, ensures out==odd_sum(n as nat),
 {
let mut i:usize=0;let mut out:usize=0;while i<n
 invariant (i<=n && out<=2000*i && out==odd_sum(i as nat))
 decreases n-i,
 {proof {step_model(i as nat);}out=out+2*i+1;i=i+1;}out
 }
}
