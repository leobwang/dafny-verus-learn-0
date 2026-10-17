// R12_HINT_SITES: [{"name":"loop1","identifiers":["best","i","j","values"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(values:seq<nat>) returns(best:nat) requires |values|>0 ensures forall j:nat :: j<|values| ==> best<=values[j] ensures exists j:nat :: j<|values| && best==values[j]
 {
var i:=1;best:=values[0];while i<|values|
 invariant /*R12_HINT:loop1*/ true
 {if values[i]<best {best:=values[i];}i:=i+1;}
 }
}
