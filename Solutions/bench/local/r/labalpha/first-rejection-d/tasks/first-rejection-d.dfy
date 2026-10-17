// R12_HINT_SITES: [{"name":"loop1","identifiers":["at","flags","j"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(flags:seq<bool>) returns(at:nat) ensures at<=|flags| ensures forall j:nat :: j<at ==> flags[j] ensures at==|flags| || !flags[at]
 {
at:=0;while at<|flags| && flags[at]
 invariant (0<=at<=|flags| && (forall j:nat :: j<at ==> flags[j]))
 {at:=at+1;}
 }
}
