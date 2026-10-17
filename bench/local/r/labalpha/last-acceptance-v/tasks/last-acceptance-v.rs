// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","last","len"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(flags:&Vec<bool>)->(last:usize) ensures last<=flags.len(),last>0 ==> flags@[(last as int)-1],forall|j:int|last<=j<flags.len() ==> !flags@[j],
 {
let mut i:usize=0;let mut last:usize=0;while i<flags.len()
 invariant /*R12_HINT:loop1*/ true
 decreases flags.len()-i,
 {if flags[i] {last=i+1;}i=i+1;}last
 }
}
