// R12_HINT_SITES: [{"name":"loop1","identifiers":["limit","remaining","spent"]}]
// R12_SOURCE_SPANS: [{"symbol":"R12_LabCase.LabTask","start":4,"end":10}]
module R12_LabCase {
 method LabTask(limit:nat) returns(spent:nat) ensures spent==limit
 {
spent:=0;var remaining:=limit;while remaining>0
 invariant (spent+remaining==limit)
 decreases remaining
 {remaining:=remaining-1;spent:=spent+1;}
 }
}
