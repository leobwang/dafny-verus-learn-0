// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","index_sum","n","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":8,"end":14}]
use vstd::prelude::*;
verus! {
pub open spec fn index_sum(k:nat)->nat decreases k, {if k==0 {0} else {index_sum((k-1) as nat)+((k-1) as nat)}}
proof fn step_model(i:nat) ensures index_sum(i+1)==index_sum(i)+i, {}
 #[verifier::loop_isolation(false)]
 fn lab_task(n:usize)->(out:usize) requires n<=1000, ensures out==index_sum(n as nat),
 {
let mut i:usize=0;let mut out:usize=0;while i<n
 invariant /*R12_HINT:loop1*/ true
 decreases n-i,
 {proof {step_model(i as nat);}out=out+i;i=i+1;}out
 }
}
