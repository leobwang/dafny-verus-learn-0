// R12_HINT_SITES: [{"name":"loop1","identifiers":["flags","i","j","last"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(flags:seq<bool>) returns(last:nat) ensures last<=|flags| ensures last>0 ==> flags[last-1] ensures forall j:nat :: last<=j<|flags| ==> !flags[j]
 {
var i:=0;last:=0;while i<|flags|
 invariant (0<=last<=i<=|flags| && (last>0 ==> flags[last-1]) && (forall j:nat :: last<=j<i ==> !flags[j]))
 {if flags[i] {last:=i+1;}i:=i+1;}
 }
}

module R12_CorpusObservation {import P=R12_LabCase
 @Test method OriginalDomain() {var actual:=P.LabTask([false,true,false]);expect actual==2;}
}
