// R12_HINT_SITES: [{"name":"loop1","identifiers":["best","i","j","len","values"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(values:&Vec<usize>)->(best:usize) requires values.len()>0, ensures forall|j:int|0<=j<values.len() ==> best<=values@[j],exists|j:int|0<=j<values.len() && best==values@[j],
 {
let mut i:usize=1;let mut best:usize=values[0];while i<values.len()
 invariant (1<=i && i<=values.len() && (forall|j:int|0<=j<i ==> best<=values@[j]) && (exists|j:int|0<=j<i && best==values@[j]))
 decreases values.len()-i,
 {if values[i]<best {best=values[i];}i=i+1;}best
 }
}
