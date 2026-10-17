// R12_HINT_SITES: [{"name":"loop1","identifiers":["limit","remaining","spent"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(limit:usize)->(spent:usize) ensures spent==limit,
 {
let mut spent:usize=0;let mut remaining:usize=limit;while remaining>0
 invariant (spent+remaining==limit)
 decreases remaining,
 {remaining=remaining-1;spent=spent+1;}spent
 }
}

verus! {fn original_domain_witness()->usize {lab_task(3)}}
#[cfg(test)]mod r12_observe {use super::*;#[test]fn original_domain(){assert_eq!(original_domain_witness(),3);}}
