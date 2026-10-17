// R12_HINT_SITES: [{"name":"loop1","identifiers":["at","flags","j","len"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(flags:&Vec<bool>)->(at:usize) ensures at<=flags.len(),forall|j:int|0<=j<at ==> flags@[j],at==flags.len() || !flags@[at as int],
 {
let mut at:usize=0;while at<flags.len() && flags[at]
 invariant (at<=flags.len() && (forall|j:int|0<=j<at ==> flags@[j]))
 decreases flags.len()-at,
 {at=at+1;}at
 }
}

verus! {fn original_domain_witness()->usize {let values=vec![true,true,false,true];lab_task(&values)}}
#[cfg(test)]mod r12_observe {use super::*;#[test]fn original_domain(){assert_eq!(original_domain_witness(),2);}}
