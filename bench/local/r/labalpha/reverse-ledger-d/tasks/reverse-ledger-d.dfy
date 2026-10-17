// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(flags:seq<bool>) returns(out:seq<bool>) ensures |out|==|flags| ensures forall j:nat :: j<|flags| ==> out[j]==flags[|flags|-1-j]
 {
var i:=0;out:=[];while i<|flags|
 invariant /*R12_HINT:loop1*/ true
 {out:=out+[flags[|flags|-1-i]];i:=i+1;}
 }
}
