// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(flags:seq<bool>) returns(out:seq<bool>) ensures |out|==|flags| ensures forall j:nat :: j<|flags| ==> out[j]==flags[|flags|-1-j]
 {
var i:=0;out:=[];while i<|flags|
 invariant (0<=i<=|flags| && |out|==i && (forall j:nat :: j<i ==> out[j]==flags[|flags|-1-j]))
 {out:=out+[flags[|flags|-1-i]];i:=i+1;}
 }
}

module R12_CorpusObservation {import P=R12_LabCase
 @Test method OriginalDomain() {var actual:=P.LabTask([true,false,false]);expect actual==[false, false, true];}
}
