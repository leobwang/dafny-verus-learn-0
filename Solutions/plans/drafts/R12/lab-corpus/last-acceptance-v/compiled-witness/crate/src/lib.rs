// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","last","len"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(flags:&Vec<bool>)->(last:usize) ensures last<=flags.len(),last>0 ==> flags@[(last as int)-1],forall|j:int|last<=j<flags.len() ==> !flags@[j],
 {
let mut i:usize=0;let mut last:usize=0;while i<flags.len()
 invariant (last<=i && i<=flags.len() && (last>0 ==> flags@[(last as int)-1]) && (forall|j:int|last<=j<i ==> !flags@[j]))
 decreases flags.len()-i,
 {if flags[i] {last=i+1;}i=i+1;}last
 }
}

verus! {fn original_domain_witness()->usize {let values=vec![false,true,false];lab_task(&values)}}
#[cfg(test)]mod r12_observe {use super::*;#[test]fn original_domain(){assert_eq!(original_domain_witness(),2);}}
