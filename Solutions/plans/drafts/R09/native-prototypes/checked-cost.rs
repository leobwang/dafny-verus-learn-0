use vstd::prelude::*;
use rg_re_a1::*;
use rg_re_a3::*;
verus! {
pub open spec fn range_nodes_r09(lo:char,hi:char)->nat {
 if range_valid(lo,hi) { (2*((hi as int)-(lo as int))+1) as nat } else {1}
}
pub open spec fn class_nodes_r09(xs:Seq<(char,char)>)->nat
 decreases xs.len(),
{
 if xs.len()==0 {1} else {1+range_nodes_r09(xs[0].0,xs[0].1)+class_nodes_r09(xs.drop_first())}
}
pub open spec fn lowering_nodes_r09(t:Syn)->nat
 decreases t,
{
 match t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => 1,
  SyntaxKind::Class(cc) => class_nodes_r09(cc.ranges@),
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b) => 1+lowering_nodes_r09(*a)+lowering_nodes_r09(*b),
  SyntaxKind::Star(a) => 1+lowering_nodes_r09(*a),
  SyntaxKind::Plus(a) => 2+2*lowering_nodes_r09(*a),
  SyntaxKind::Opt(a) => 2+lowering_nodes_r09(*a),
  SyntaxKind::Group(a) => lowering_nodes_r09(*a),
  SyntaxKind::RepRange(a,n,m) => 3+(n as nat)*(lowering_nodes_r09(*a)+1)+((m as nat-n as nat) as nat)*(lowering_nodes_r09(*a)+3),
 }
}
proof fn lemma_copies_nodes_r09(r:Re,k:nat)
 ensures node_count(copies(r,k))==1+k*(node_count(r)+1),
 decreases k,
{
 reveal_with_fuel(node_count,2);
 reveal_with_fuel(copies,2);
 let b=node_count(r) as int;
 if k>0 {
  let km=(k-1) as nat;
  lemma_copies_nodes_r09(r,km);
  let total=node_count(copies(r,k)) as int;
  let child=node_count(copies(r,km)) as int;
  assert(total==1+b+child);
  assert(total==1+k*(b+1)) by (nonlinear_arith)
   requires total==1+b+child,child==1+km*(b+1),k==km+1;
 } else {
  assert(1+k*(b+1)==1) by (nonlinear_arith) requires k==0;
 }
}
proof fn lemma_optional_nodes_r09(r:Re,k:nat)
 ensures node_count(copies_up_to(r,k))==1+k*(node_count(r)+3),
 decreases k,
{
 reveal_with_fuel(node_count,3);
 reveal_with_fuel(copies_up_to,2);
 let b=node_count(r) as int;
 if k>0 {
  let km=(k-1) as nat;
  lemma_optional_nodes_r09(r,km);
  let total=node_count(copies_up_to(r,k)) as int;
  let child=node_count(copies_up_to(r,km)) as int;
  assert(total==3+b+child);
  assert(total==1+k*(b+3)) by (nonlinear_arith)
   requires total==3+b+child,child==1+km*(b+3),k==km+1;
 } else {
  assert(1+k*(b+3)==1) by (nonlinear_arith) requires k==0;
 }
}
proof fn lemma_range_nodes_r09(lo:char,hi:char)
 requires range_valid(lo,hi),
 ensures node_count(range_re(lo,hi))==range_nodes_r09(lo,hi),
 decreases (hi as int)-(lo as int),
{
 reveal_with_fuel(node_count,2);
 if lo<hi {
  let next=((lo as u32)+1) as char;
  assert((next as u32)==(lo as u32)+1);
  lemma_range_nodes_r09(next,hi);
 }
}
proof fn lemma_class_nodes_r09(xs:Seq<(char,char)>)
 requires class_valid(xs),
 ensures node_count(class_re(xs))==class_nodes_r09(xs),
 decreases xs.len(),
{
 if xs.len()>0 {
  assert forall|i:int| 0<=i<xs.drop_first().len() implies range_valid(xs.drop_first()[i].0,xs.drop_first()[i].1) by {
   assert(xs.drop_first()[i]==xs[i+1]);
  }
  lemma_range_nodes_r09(xs[0].0,xs[0].1);
  lemma_class_nodes_r09(xs.drop_first());
 }
}
pub proof fn lemma_lowering_nodes_r09(t:Syn,len:nat)
 requires wf(t,len),
 ensures node_count(lower(t))==lowering_nodes_r09(t),
 decreases t,
{
 reveal_with_fuel(node_count,3);
 match t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => {},
  SyntaxKind::Class(cc) => {lemma_class_nodes_r09(cc.ranges@);},
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b) => {lemma_lowering_nodes_r09(*a,len);lemma_lowering_nodes_r09(*b,len);},
  SyntaxKind::Star(a) | SyntaxKind::Plus(a) | SyntaxKind::Opt(a) | SyntaxKind::Group(a) => {lemma_lowering_nodes_r09(*a,len);},
  SyntaxKind::RepRange(a,n,m) => {
   lemma_lowering_nodes_r09(*a,len);
   lemma_copies_nodes_r09(lower(*a),n as nat);
   lemma_optional_nodes_r09(lower(*a),(m as nat-n as nat) as nat);
  },
 }
}
}

use vstd::prelude::*;
use vstd::arithmetic::div_mod::{lemma_fundamental_div_mod,lemma_mod_bound};
use vstd::arithmetic::mul::lemma_mul_is_commutative;
verus! {
proof fn quotient_product_guard_r09(b:int,q:int,r:int,d:int)
 requires d>0,0<=r<d,
 ensures (b<=q)==(b*d<=q*d+r),
{
 assert((b<=q)==(b*d<=q*d+r)) by (nonlinear_arith)
  requires d>0,0<=r<d;
}
proof fn division_budget_guard_r09(base:int,space:int,copies:int)
 requires base>=0,space>=0,copies>0,
 ensures (base<=space/copies)==(base*copies<=space),
{
 lemma_fundamental_div_mod(space,copies);
 lemma_mod_bound(space,copies);
 quotient_product_guard_r09(base,space/copies,space%copies,copies);
 lemma_mul_is_commutative(copies,space/copies);
}

fn repeat_expansion_budget_r09(base:u32,lo:u32,hi:u32,cap:u32)->(res:Option<u32>)
 requires lo<=hi<=9,
 ensures match res {
  Some(cost) => cost<=cap && (cost as int)==3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int)),
  None => 3+(base as int)*(hi as int)+(lo as int)+3*((hi as int)-(lo as int))>(cap as int),
 },
{
 let overhead:u32=3+lo+3*(hi-lo);
 if overhead>cap {return None;}
 proof {
  if hi>0 { division_budget_guard_r09(base as int,(cap-overhead) as int,hi as int); }
 }
 if hi>0 && base>(cap-overhead)/hi {return None;}
 let cost:u32=base*hi+overhead;
 Some(cost)
}
}

verus! {
fn checked_add_cost_r09(a:u32,b:u32,extra:u32,cap:u32)->(res:Option<u32>)
 ensures match res {
  Some(n)=>n<=cap && (n as int)==(a as int)+(b as int)+(extra as int),
  None=>(a as int)+(b as int)+(extra as int)>(cap as int),
 },
{
 if extra>cap {return None;}
 if a>cap-extra {return None;}
 if b>cap-extra-a {return None;}
 Some(a+b+extra)
}
fn checked_class_cost_r09(cc:&SpanClass,cap:u32)->(res:Option<u32>)
 requires class_valid(cc.ranges@),
 ensures match res {Some(n)=>n<=cap && n==class_nodes_r09(cc.ranges@),None=>class_nodes_r09(cc.ranges@)>cap},
{
 proof {assert(class_nodes_r09(cc.ranges@)>=1);}
 if cap<1 {return None;}
 let mut cost:u32=1;let mut i:usize=0;
 proof {assert(cc.ranges@.subrange(0,cc.ranges.len() as int) =~= cc.ranges@);}
 while i<cc.ranges.len()
  invariant i<=cc.ranges.len(),cost<=cap,class_valid(cc.ranges@),
   (cost as nat)+class_nodes_r09(cc.ranges@.subrange(i as int,cc.ranges.len() as int))==class_nodes_r09(cc.ranges@)+1,
  decreases cc.ranges.len()-i,
 {
  let (lo,hi)=cc.ranges[i];
  let width=(hi as u32)-(lo as u32);
  let range:u32=2*width+1;
  proof {
   let suffix=cc.ranges@.subrange(i as int,cc.ranges.len() as int);
   let tail=cc.ranges@.subrange(i+1,cc.ranges.len() as int);
   assert(suffix[0]==cc.ranges@[i as int]);
   assert(suffix.drop_first() =~= tail);
   assert(class_nodes_r09(tail)>=1);
   assert(range==range_nodes_r09(lo,hi));
  }
  cost=checked_add_cost_r09(cost,range,1,cap)?;
  i=i+1;
 }
 proof {assert(cc.ranges@.subrange(cc.ranges.len() as int,cc.ranges.len() as int) =~= Seq::<(char,char)>::empty());}
 Some(cost)
}
proof fn lemma_repetition_cost_grows_r09(base:nat,n:nat,m:nat)
 requires n<=m,m>0,
 ensures 3+n*(base+1)+(m-n)*(base+3)>=base,
{
 assert(3+n*(base+1)+(m-n)*(base+3)>=base) by (nonlinear_arith)
  requires n<=m,m>0,base>=0,n>=0;
}
fn checked_lowering_cost_r09(t:&Syn,len:usize,cap:u32)->(res:Option<u32>)
 requires wf(*t,len as nat),
 ensures match res {Some(n)=>n<=cap && n==lowering_nodes_r09(*t),None=>lowering_nodes_r09(*t)>cap},
 decreases *t,
{
 reveal_with_fuel(lowering_nodes_r09,2);
 let result=match &t.node {
  SyntaxKind::Eps | SyntaxKind::Chr(_) => if cap>=1 {Some(1)} else {None},
  SyntaxKind::Class(cc)=>checked_class_cost_r09(cc,cap),
  SyntaxKind::Alt(a,b) | SyntaxKind::Cat(a,b)=>{
   let left=checked_lowering_cost_r09(a,len,cap)?;
   let right=checked_lowering_cost_r09(b,len,cap)?;
   checked_add_cost_r09(left,right,1,cap)
  },
  SyntaxKind::Star(a)=>{let child=checked_lowering_cost_r09(a,len,cap)?;checked_add_cost_r09(child,0,1,cap)},
  SyntaxKind::Plus(a)=>{let child=checked_lowering_cost_r09(a,len,cap)?;checked_add_cost_r09(child,child,2,cap)},
  SyntaxKind::Opt(a)=>{let child=checked_lowering_cost_r09(a,len,cap)?;checked_add_cost_r09(child,0,2,cap)},
  SyntaxKind::Group(a)=>checked_lowering_cost_r09(a,len,cap),
  SyntaxKind::RepRange(a,n,m)=>{
   if *m==0 {
    proof {let base=lowering_nodes_r09(**a) as int; assert(3+(*n as int)*(base+1)+((*m as int)-(*n as int))*(base+3)==3) by (nonlinear_arith) requires *m==0,*n==0; assert(lowering_nodes_r09(*t)==3);}
    checked_add_cost_r09(0,0,3,cap)
   }
   else {
    proof {lemma_repetition_cost_grows_r09(lowering_nodes_r09(**a),*n as nat,*m as nat);}
    let child=checked_lowering_cost_r09(a,len,cap)?;
    let result=repeat_expansion_budget_r09(child,*n,*m,cap);
    proof {
     let base=lowering_nodes_r09(**a) as int;
     assert(3+(*n as int)*(base+1)+((*m as int)-(*n as int))*(base+3) == 3+base*(*m as int)+(*n as int)+3*((*m as int)-(*n as int))) by (nonlinear_arith);
    }
    proof {assert(match result {Some(n)=>n<=cap && n==lowering_nodes_r09(*t),None=>lowering_nodes_r09(*t)>cap});}
    result
   }
  },
 };
 assert(match result {Some(n)=>n<=cap && n==lowering_nodes_r09(*t),None=>lowering_nodes_r09(*t)>cap});
 result
}
}
