// R12_HINT_SITES: [{"name":"loop1","identifiers":["n","q","rest"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(n:usize)->(q:usize) ensures q==n/3,
 {
let mut q:usize=0;let mut rest:usize=n;while rest>=3
 invariant (3*q+rest==n)
 decreases rest,
 {rest=rest-3;q=q+1;}q
 }
}

verus! {fn original_domain_witness()->usize {lab_task(8)}}
#[cfg(test)]mod r12_observe {use super::*;#[test]fn original_domain(){assert_eq!(original_domain_witness(),2);}}
