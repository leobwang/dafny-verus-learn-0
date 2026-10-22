// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","n","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(n:usize)->(out:usize) requires n<=1000, ensures out==2*n,
 {
let mut i:usize=0;let mut out:usize=0;while i<n
 invariant (i<=n && out==2*i)
 decreases n-i,
 {out=out+2;i=i+1;}out
 }
}
