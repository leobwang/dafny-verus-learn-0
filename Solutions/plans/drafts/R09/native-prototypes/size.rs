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
