// R12_HINT_SITES: [{"name":"loop1","identifiers":["n","q","rest"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":10}]
module R12_LabCase {
 method LabTask(n:nat) returns(q:nat) ensures q==n/3
 {
q:=0;var rest:=n;while rest>=3
 invariant /*R12_HINT:loop1*/ true
 decreases rest
 {rest:=rest-3;q:=q+1;}
 }
}
