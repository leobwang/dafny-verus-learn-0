// R12_HINT_SITES: [{"name":"loop1","identifiers":["answer","flags","i","j","len"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(flags:&Vec<bool>)->(answer:bool) ensures answer==(exists|j:int|0<=j<flags.len() && flags@[j]),
 {
let mut i:usize=0;let mut answer:bool=false;while i<flags.len()
 invariant (i<=flags.len() && answer==(exists|j:int|0<=j<i && flags@[j]))
 decreases flags.len()-i,
 {answer=answer || flags[i];i=i+1;}answer
 }
}
