// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","j","left","len","out"]},{"name":"loop2","identifiers":["j","k","left","len","out","right"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":6,"end":16}]
use vstd::prelude::*;
verus! {
 #[verifier::loop_isolation(false)]
 fn lab_task(left:&Vec<bool>,right:&Vec<bool>)->(out:Vec<bool>) requires left.len()+right.len()<=usize::MAX, ensures out.len()==left.len()+right.len(),forall|j:int|0<=j<left.len() ==> out@[j]==left@[j],forall|j:int|0<=j<right.len() ==> out@[left.len()+j]==right@[j],
 {
let mut i:usize=0;let mut out:Vec<bool>=Vec::new();while i<left.len()
 invariant (i<=left.len() && out.len()==i && (forall|j:int|0<=j<i ==> out@[j]==left@[j]))
 decreases left.len()-i,
 {out.push(left[i]);i=i+1;}
 let mut k:usize=0;while k<right.len()
 invariant (k<=right.len() && out.len()==left.len()+k && (forall|j:int|0<=j<left.len() ==> out@[j]==left@[j]) && (forall|j:int|0<=j<k ==> out@[left.len()+j]==right@[j]))
 decreases right.len()-k,
 {out.push(right[k]);k=k+1;}out
 }
}
