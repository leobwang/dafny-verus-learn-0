/*! R12 — Driving the verifier + Lab α.
T1 is bounded remaining-budget arithmetic. H1/H2 keep provided executable bodies:
remove their counted assumptions and write only the loop-invariant hints. The
count-step and final slice equality are supplied worked facts. Verifier outcome
flags are input data; counting them does not establish a program's proof status.
*/
use vstd::prelude::*;
verus! {
pub open spec fn accepted_count_r12(flags:Seq<bool>)->nat
 decreases flags.len(),
 {if flags.len()==0 {0} else {accepted_count_r12(flags.take(flags.len() as int-1))+(if flags[flags.len() as int-1] {1nat} else {0nat})}}
// item: R12.W1v
proof fn accepted_step_r12(flags:Seq<bool>,i:int)
 requires 0<=i<flags.len(),
 ensures accepted_count_r12(flags.take(i+1))==accepted_count_r12(flags.take(i))+(if flags[i] {1nat} else {0nat}),
 {assert(flags.take(i+1).take(i)=~=flags.take(i));}
// item: R12.T1v
// pair: R12.T1d
fn remaining_budget_r12(spent:usize,limit:usize)->(out:usize)
 requires spent<=limit,
 ensures out+spent==limit,
 {proof {#[verifier::proof_note("R12.T1v")] assume(false);} 0}
// item: R12.H1v
// pair: R12.H1d
#[verifier::loop_isolation(false)]
fn count_accepted_r12(flags:&Vec<bool>)->(accepted:usize)
 ensures accepted==accepted_count_r12(flags@),accepted<=flags.len(),
 {
 let mut i:usize=0;let mut accepted:usize=0;
 proof {#[verifier::proof_note("R12.H1v")] assume(false);}
 while i<flags.len()
  // @hole-begin R12.H1v

  // @hole-end R12.H1v
  decreases flags.len()-i,
 {
  proof {accepted_step_r12(flags@,i as int);}
  if flags[i] {accepted=accepted+1;}
  i=i+1;
 }
 // did: connect the consumed-prefix slice to the original flags at exit.
 proof {assert(flags@.take(i as int)=~=flags@);}
 accepted
 }
// item: R12.H2v
// pair: R12.H2d
fn first_rejection_r12(flags:&Vec<bool>)->(at:usize)
 ensures at<=flags.len(),forall|j:int| 0<=j<at ==> flags@[j],at==flags.len() || !flags@[at as int],
 {
 let mut at:usize=0;
 proof {#[verifier::proof_note("R12.H2v")] assume(false);}
 while at<flags.len() && flags[at]
  // @hole-begin R12.H2v

  // @hole-end R12.H2v
  decreases flags.len()-at,
 {at=at+1;}
 at
 }
}
