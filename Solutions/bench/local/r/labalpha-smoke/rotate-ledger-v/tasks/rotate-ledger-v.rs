// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","len","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(flags:&Vec<bool>)->(out:Vec<bool>) requires flags.len()>0, ensures out.len()==flags.len(),forall|j:int|0<=j<flags.len() ==> ((j+1<flags.len() ==> out@[j]==flags@[j+1]) && (j+1==flags.len() ==> out@[j]==flags@[0])),
 {
let mut i:usize=0;let mut out:Vec<bool>=Vec::new();while i<flags.len()
 invariant (i<=flags.len() && out.len()==i && (forall|j:int|0<=j<i ==> ((j+1<flags.len() ==> out@[j]==flags@[j+1]) && (j+1==flags.len() ==> out@[j]==flags@[0]))))
 decreases flags.len()-i,
 {let value=if i+1<flags.len() {flags[i+1]} else {flags[0]};out.push(value);i=i+1;}out
 }
}
