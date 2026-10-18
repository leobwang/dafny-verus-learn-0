// R12_HINT_SITES: [{"name":"loop1","identifiers":["at","j","left","right"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(left:seq<bool>,right:seq<bool>) returns(at:nat) requires |left|==|right| ensures at<=|left| ensures forall j:nat :: j<at ==> left[j]==right[j] ensures at==|left| || left[at]!=right[at]
 {
at:=0;while at<|left| && left[at]==right[at]
 invariant /*R12_HINT:loop1*/ true
 {at:=at+1;}
 }
}
