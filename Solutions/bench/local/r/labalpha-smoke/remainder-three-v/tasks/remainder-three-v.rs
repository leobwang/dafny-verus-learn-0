// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","n","rest"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(n:usize)->(rest:usize) ensures rest==n%3,
 {
let mut i:usize=0;let mut rest:usize=0;while i<n
 invariant (i<=n && rest<3 && rest==i%3)
 decreases n-i,
 {if rest==2 {rest=0;}else{rest=rest+1;}i=i+1;}rest
 }
}
