// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","len","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(flags:&Vec<bool>)->(out:Vec<bool>) ensures out.len()==flags.len(),forall|j:int|0<=j<flags.len() ==> out@[j]==flags@[j],
 {
let mut i:usize=0;let mut out:Vec<bool>=Vec::new();while i<flags.len()
 invariant /*R12_HINT:loop1*/ true
 decreases flags.len()-i,
 {out.push(flags[i]);i=i+1;}out
 }
}
