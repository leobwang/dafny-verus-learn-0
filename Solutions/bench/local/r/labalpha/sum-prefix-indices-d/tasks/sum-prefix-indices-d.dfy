// R12_HINT_SITES: [{"name":"loop1","identifiers":["IndexSum","i","n","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":6,"end":11}]
module R12_LabCase {
ghost function IndexSum(k:nat):nat decreases k {if k==0 then 0 else IndexSum(k-1)+k-1}
lemma StepModel(i:nat) ensures IndexSum(i+1)==IndexSum(i)+i {}
 method LabTask(n:nat) returns(out:nat) requires n<=1000 ensures out==IndexSum(n)
 {
var i:=0;out:=0;while i<n
 invariant (0<=i<=n && out<=1000*i && out==IndexSum(i))
 {StepModel(i);out:=out+i;i:=i+1;}
 }
}
