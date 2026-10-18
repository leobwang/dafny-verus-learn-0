// R12_HINT_SITES: [{"name":"loop1","identifiers":["OddSum","i","n","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":6,"end":11}]
module R12_LabCase {
ghost function OddSum(k:nat):nat decreases k {if k==0 then 0 else OddSum(k-1)+2*(k-1)+1}
lemma StepModel(i:nat) ensures OddSum(i+1)==OddSum(i)+2*i+1 {}
 method LabTask(n:nat) returns(out:nat) requires n<=1000 ensures out==OddSum(n)
 {
var i:=0;out:=0;while i<n
 invariant /*R12_HINT:loop1*/ true
 {StepModel(i);out:=out+2*i+1;i:=i+1;}
 }
}
