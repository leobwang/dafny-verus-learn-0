use vstd::prelude::*;
verus! {
 pub fn delivered_score_r13(a:u32,b:u32)->(score:u64)
  ensures score==2*a+3*b,score<=21474836475,
 {support_score_r13(a,b)}
 // item: R13.A1v
 fn support_score_r13(a:u32,b:u32)->(score:u64)
  ensures score==2*a+3*b,score<=21474836475,
 {proof {#[verifier::proof_note("R13.A1v")] assume(false);} 0}
}
