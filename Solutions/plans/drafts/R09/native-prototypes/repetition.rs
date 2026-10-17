use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a1b::*;
use rg_re_a3::*;
verus! {
proof fn lemma_cat_right_context_r09(a:Re,b:Re,c:Re,s:Seq<char>)
 requires forall|t:Seq<char>| matches(b,t)==matches(c,t),
 ensures matches(Re::Cat(Box::new(a),Box::new(b)),s)==matches(Re::Cat(Box::new(a),Box::new(c)),s),
{
 if matches(Re::Cat(Box::new(a),Box::new(b)),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(b,s.subrange(i,s.len() as int));
  assert(matches(c,s.subrange(i,s.len() as int)));
 }
 if matches(Re::Cat(Box::new(a),Box::new(c)),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(a,#[trigger] s.subrange(0,i)) && matches(c,s.subrange(i,s.len() as int));
  assert(matches(b,s.subrange(i,s.len() as int)));
 }
}
proof fn lemma_copies_join_r09(r:Re,a:nat,b:nat,s:Seq<char>)
 ensures matches(copies(r,a+b),s)==matches(Re::Cat(Box::new(copies(r,a)),Box::new(copies(r,b))),s),
 decreases a,
{
 if a==0 {lemma_cat_eps_left(copies(r,b),s);}
 else {
  let aa=(a-1) as nat;
  lemma_cat_assoc(r,copies(r,aa),copies(r,b),s);
  let x=copies(r,aa+b);let y=Re::Cat(Box::new(copies(r,aa)),Box::new(copies(r,b)));
  assert forall|t:Seq<char>| matches(x,t)==matches(y,t) by {lemma_copies_join_r09(r,aa,b,t);}
  lemma_cat_right_context_r09(r,x,y,s);
 }
}
proof fn lemma_copies_optional_r09(r:Re,j:nat,s:Seq<char>)
 ensures matches(copies_up_to(r,j),s)==(exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s)),
 decreases j,
{
 if j>0 {
  let jm=(j-1) as nat;let u=copies_up_to(r,jm);
  if matches(copies_up_to(r,j),s) {
   if s.len()!=0 {
    assert(!matches(Re::Eps,s));
    assert(matches(Re::Cat(Box::new(r),Box::new(u)),s));
    let i=choose|i:int| 0<=i<=s.len() && matches(r,#[trigger] s.subrange(0,i)) && matches(u,s.subrange(i,s.len() as int));
    lemma_copies_optional_r09(r,jm,s.subrange(i,s.len() as int));
    let k=choose|k:nat| k<=jm && #[trigger] matches(copies(r,k),s.subrange(i,s.len() as int));
    assert(copies(r,k+1)==Re::Cat(Box::new(r),Box::new(copies(r,k))));
    assert(matches(copies(r,k+1),s));
   } else {assert(matches(copies(r,0),s));}
  }
  if exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s) {
   let k=choose|k:nat| k<=j && #[trigger] matches(copies(r,k),s);
   if k>0 {
    let km=(k-1) as nat;
    assert(copies(r,k)==Re::Cat(Box::new(r),Box::new(copies(r,km))));
    let i=choose|i:int| 0<=i<=s.len() && matches(r,#[trigger] s.subrange(0,i)) && matches(copies(r,km),s.subrange(i,s.len() as int));
    lemma_copies_optional_r09(r,jm,s.subrange(i,s.len() as int));
    assert(exists|kk:nat| kk<=jm && #[trigger] matches(copies(r,kk),s.subrange(i,s.len() as int)));
    assert(matches(Re::Cat(Box::new(r),Box::new(u)),s));
   } else {assert(copies(r,0)==Re::Eps);}
   assert(matches(copies_up_to(r,j),s));
  }
 } else {
  assert(copies(r,0)==Re::Eps);
  if exists|k:nat| k<=j && #[trigger] matches(copies(r,k),s) {
   let k=choose|k:nat| k<=j && #[trigger] matches(copies(r,k),s);assert(k==0);
  }
 }
}
proof fn lemma_repetition_interval_r09(r:Re,n:nat,m:nat,s:Seq<char>)
 requires n<=m,
 ensures matches(rep_range(r,n,m),s)==(exists|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s)),
{
 let extra=(m-n) as nat;
 if matches(rep_range(r,n,m),s) {
  let i=choose|i:int| 0<=i<=s.len() && matches(copies(r,n),#[trigger] s.subrange(0,i)) && matches(copies_up_to(r,extra),s.subrange(i,s.len() as int));
  lemma_copies_optional_r09(r,extra,s.subrange(i,s.len() as int));
  let k=choose|k:nat| k<=extra && #[trigger] matches(copies(r,k),s.subrange(i,s.len() as int));
  lemma_copies_join_r09(r,n,k,s);assert(matches(copies(r,n+k),s));
 }
 if exists|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s) {
  let k=choose|k:nat| n<=k<=m && #[trigger] matches(copies(r,k),s);
  lemma_copies_join_r09(r,n,(k-n) as nat,s);
  let i=choose|i:int| 0<=i<=s.len() && matches(copies(r,n),#[trigger] s.subrange(0,i)) && matches(copies(r,(k-n) as nat),s.subrange(i,s.len() as int));
  lemma_copies_optional_r09(r,extra,s.subrange(i,s.len() as int));
  assert(matches(copies_up_to(r,extra),s.subrange(i,s.len() as int)));
 }
}
}
