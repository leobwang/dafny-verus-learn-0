// R12_HINT_SITES: [{"name":"loop1","identifiers":["answer","flags","i","j"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(flags:seq<bool>) returns(answer:bool) ensures answer==(forall j:nat :: j<|flags| ==> flags[j])
 {
var i:=0;answer:=true;while i<|flags|
 invariant (0<=i<=|flags| && answer==(forall j:nat :: j<i ==> flags[j]))
 {answer:=answer && flags[i];i:=i+1;}
 }
}
