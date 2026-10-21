// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(flags:seq<bool>) returns(out:seq<bool>) requires |flags|>0 ensures |out|==|flags| ensures forall j:nat :: j<|flags| ==> ((j+1<|flags| ==> out[j]==flags[j+1]) && (j+1==|flags| ==> out[j]==flags[0]))
 {
var i:=0;out:=[];while i<|flags|
 invariant (0<=i<=|flags| && |out|==i && (forall j:nat :: j<i ==> ((j+1<|flags| ==> out[j]==flags[j+1]) && (j+1==|flags| ==> out[j]==flags[0]))))
 {var value:=if i+1<|flags| then flags[i+1] else flags[0];out:=out+[value];i:=i+1;}
 }
}
