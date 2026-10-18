// R12_HINT_SITES: [{"name":"loop1","identifiers":["n","q","rest"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(n:usize)->(q:usize) ensures q==n/3,
 {
let mut q:usize=0;let mut rest:usize=n;while rest>=3
 invariant /*R12_HINT:loop1*/ true
 decreases rest,
 {rest=rest-3;q=q+1;}q
 }
}
