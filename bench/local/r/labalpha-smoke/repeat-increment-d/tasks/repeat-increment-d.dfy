// R12_HINT_SITES: [{"name":"loop1","identifiers":["RepeatSum","amount","i","n","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":6,"end":11}]
module R12_LabCase {
ghost function RepeatSum(amount:nat,k:nat):nat decreases k {if k==0 then 0 else RepeatSum(amount,k-1)+amount}
lemma StepModel(amount:nat,i:nat) ensures RepeatSum(amount,i+1)==RepeatSum(amount,i)+amount {}
 method LabTask(n:nat,amount:nat) returns(out:nat) requires n<=1000 && amount<=1000 ensures out==RepeatSum(amount,n)
 {
var i:=0;out:=0;while i<n
 invariant /*R12_HINT:loop1*/ true
 {StepModel(amount,i);out:=out+amount;i:=i+1;}
 }
}
