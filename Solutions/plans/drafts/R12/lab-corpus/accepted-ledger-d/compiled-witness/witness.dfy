// R12_HINT_SITES: [{"name":"loop1","identifiers":["LedgerCount","accepted","flags","i"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":10,"end":17}]
module R12_LabCase {
ghost function LedgerCount(flags:seq<bool>):nat decreases |flags|
 {if flags==[] then 0 else LedgerCount(flags[..|flags|-1])+(if flags[|flags|-1] then 1 else 0)}
 lemma LedgerStep(flags:seq<bool>,i:nat)
 requires i<|flags|
 ensures LedgerCount(flags[..i+1])==LedgerCount(flags[..i])+(if flags[i] then 1 else 0)
 {assert flags[..i+1][..i]==flags[..i];}
 method LabTask(flags:seq<bool>) returns(accepted:nat) ensures accepted==LedgerCount(flags) && accepted<=|flags|
 {
var i:=0;accepted:=0;
 while i<|flags|
 invariant (0<=i<=|flags| && accepted<=i && accepted==LedgerCount(flags[..i]))
 {LedgerStep(flags,i);if flags[i] {accepted:=accepted+1;} i:=i+1;}
 assert flags[..i]==flags;
 }
}

module R12_CorpusObservation {import P=R12_LabCase
 @Test method OriginalDomain() {var actual:=P.LabTask([true,false,true]);expect actual==2;}
}
