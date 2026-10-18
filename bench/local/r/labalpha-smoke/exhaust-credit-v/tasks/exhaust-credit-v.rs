// R12_HINT_SITES: [{"name":"loop1","identifiers":["limit","remaining","spent"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(limit:usize)->(spent:usize) ensures spent==limit,
 {
let mut spent:usize=0;let mut remaining:usize=limit;while remaining>0
 invariant /*R12_HINT:loop1*/ true
 decreases remaining,
 {remaining=remaining-1;spent=spent+1;}spent
 }
}
