// R12_HINT_SITES: [{"name":"loop1","identifiers":["i","n","rest"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":9}]
module R12_LabCase {
 method LabTask(n:nat) returns(rest:nat) ensures rest==n%3
 {
var i:=0;rest:=0;while i<n
 invariant (0<=i<=n && rest<3 && rest==i%3)
 {if rest==2 {rest:=0;}else{rest:=rest+1;}i:=i+1;}
 }
}
