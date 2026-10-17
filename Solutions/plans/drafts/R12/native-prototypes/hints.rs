use vstd::prelude::*;
verus! {
pub open spec fn accepted_count_r12(flags:Seq<bool>)->nat
 decreases flags.len(),
 {if flags.len()==0 {0} else {accepted_count_r12(flags.take(flags.len() as int-1))+(if flags[flags.len() as int-1] {1nat} else {0nat})}}
proof fn accepted_step_r12(flags:Seq<bool>,i:int)
 requires 0<=i<flags.len(),
 ensures accepted_count_r12(flags.take(i+1))==accepted_count_r12(flags.take(i))+(if flags[i] {1nat} else {0nat}),
 {assert(flags.take(i+1).take(i)=~=flags.take(i));}
// item: R12.T1v
fn remaining_budget_r12(spent:usize,limit:usize)->(out:usize)
 requires spent<=limit,
 ensures out+spent==limit,
 {limit-spent}
// item: R12.H1v
#[verifier::loop_isolation(false)]
fn count_accepted_r12(flags:&Vec<bool>)->(accepted:usize)
 ensures accepted==accepted_count_r12(flags@),accepted<=flags.len(),
 {
 let mut i:usize=0;let mut accepted:usize=0;
 while i<flags.len()
  // @hole-begin R12.H1v
  invariant i<=flags.len(),accepted<=i,accepted==accepted_count_r12(flags@.take(i as int)),
  // @hole-end R12.H1v
  decreases flags.len()-i,
 {
  // @hole-begin R12.H1v
  proof {accepted_step_r12(flags@,i as int);}
  // @hole-end R12.H1v
  if flags[i] {accepted=accepted+1;}
  i=i+1;
 }
 // @hole-begin R12.H1v
 proof {assert(flags@.take(i as int)=~=flags@);}
 // @hole-end R12.H1v
 accepted
 }
// item: R12.H2v
fn first_rejection_r12(flags:&Vec<bool>)->(at:usize)
 ensures at<=flags.len(),forall|j:int| 0<=j<at ==> flags@[j],at==flags.len() || !flags@[at as int],
 {
 let mut at:usize=0;
 while at<flags.len() && flags[at]
  // @hole-begin R12.H2v
  invariant at<=flags.len(),forall|j:int| 0<=j<at ==> flags@[j],
  // @hole-end R12.H2v
  decreases flags.len()-at,
 {at=at+1;}
 at
 }
}
