// R12_HINT_SITES: [{"name":"loop1","identifiers":["accepted","flags","i","ledger_count","len","take"]}]
// R12_SOURCE_SPANS: [{"symbol":"lab_task","start":12,"end":21}]
use vstd::prelude::*;
verus! {
pub open spec fn ledger_count(flags:Seq<bool>)->nat decreases flags.len(),
 {if flags.len()==0 {0} else {ledger_count(flags.take(flags.len() as int-1))+(if flags[flags.len() as int-1] {1nat} else {0nat})}}
 proof fn ledger_step(flags:Seq<bool>,i:int)
 requires 0<=i<flags.len(),
 ensures ledger_count(flags.take(i+1))==ledger_count(flags.take(i))+(if flags[i] {1nat} else {0nat}),
 {assert(flags.take(i+1).take(i)=~=flags.take(i));}
 #[verifier::loop_isolation(false)]
 fn lab_task(flags:&Vec<bool>)->(accepted:usize) ensures accepted==ledger_count(flags@),accepted<=flags.len(),
 {
let mut i:usize=0;let mut accepted:usize=0;
 while i<flags.len()
 invariant (i<=flags.len() && accepted<=i && accepted==ledger_count(flags@.take(i as int)))
 decreases flags.len()-i,
 {proof {ledger_step(flags@,i as int);}if flags[i] {accepted=accepted+1;}i=i+1;}
 proof {assert(flags@.take(i as int)=~=flags@);}
 accepted
 }
}
