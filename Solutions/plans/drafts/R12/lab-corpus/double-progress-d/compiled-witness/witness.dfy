// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","n","out"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(n:nat) returns(out:nat) requires n<=1000 ensures out==2*n
 {
var i:=0;out:=0;while i<n
 invariant (0<=i<=n && out==2*i)
 {out:=out+2;i:=i+1;}
 }
}

module R12_CorpusObservation {import P=R12_LabCase
 @Test method OriginalDomain() {var actual:=P.LabTask(3);expect actual==6;}
}
