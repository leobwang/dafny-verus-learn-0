// R12_HINT_SITES: [{"name":"loop1","identifiers":["at","j","left","len","right"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":12}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(left:&Vec<bool>,right:&Vec<bool>)->(at:usize) requires left.len()==right.len(), ensures at<=left.len(),forall|j:int|0<=j<at ==> left@[j]==right@[j],at==left.len() || left@[at as int]!=right@[at as int],
 {
let mut at:usize=0;while at<left.len() && left[at]==right[at]
 invariant /*R12_HINT:loop1*/ true
 decreases left.len()-at,
 {at=at+1;}at
 }
}
