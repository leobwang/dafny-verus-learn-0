// R12_HINT_SITES: [{"name":"loop1","identifiers":["amount","i","n","out","repeat_sum"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":8,"end":14}]
use vstd::prelude::*;
verus! {
pub open spec fn repeat_sum(amount:nat,k:nat)->nat decreases k, {if k==0 {0} else {repeat_sum(amount,(k-1) as nat)+((amount) as nat)}}
proof fn step_model(amount:nat,i:nat) ensures repeat_sum(amount,i+1)==repeat_sum(amount,i)+amount, {}
 #[verifier::loop_isolation(false)]
 fn lab_task(n:usize,amount:usize)->(out:usize) requires n<=1000,amount<=1000, ensures out==repeat_sum(amount as nat,n as nat),
 {
let mut i:usize=0;let mut out:usize=0;while i<n
 invariant (i<=n && out<=1000*i && out==repeat_sum(amount as nat,i as nat))
 decreases n-i,
 {proof {step_model(amount as nat,i as nat);}out=out+amount;i=i+1;}out
 }
}

verus! {fn original_domain_witness()->usize {lab_task(3,4)}}
#[cfg(test)]mod r12_observe {use super::*;#[test]fn original_domain(){assert_eq!(original_domain_witness(),12);}}
