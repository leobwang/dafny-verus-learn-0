// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","j","left","out"]},{"name":"loop2","identifiers":["j","k","left","out","right"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":12}]
module R12_LabCase {
 method LabTask(left:seq<bool>,right:seq<bool>) returns(out:seq<bool>) ensures |out|==|left|+|right| ensures forall j:nat :: j<|left| ==> out[j]==left[j] ensures forall j:nat :: j<|right| ==> out[|left|+j]==right[j]
 {
var i:=0;out:=[];while i<|left|
 invariant /*R12_HINT:loop1*/ true
 {out:=out+[left[i]];i:=i+1;}
 var k:=0;while k<|right|
 invariant /*R12_HINT:loop2*/ true
 {out:=out+[right[k]];k:=k+1;}
 }
}
